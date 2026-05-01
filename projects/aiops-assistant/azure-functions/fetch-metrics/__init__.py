import json
import logging
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import azure.functions as func

# Prometheus configuration
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
DEFAULT_NAMESPACE = "boutique"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prometheus_query(query):
    """Execute a PromQL query against Prometheus"""
    try:
        url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(query)}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())["data"]["result"]
    except Exception as e:
        logger.error(f"Prometheus query failed: {str(e)}")
        return []


def prometheus_range_query(query, hours_back, step="5m"):
    """Execute a range PromQL query and return time-series data"""
    try:
        end = int(datetime.utcnow().timestamp())
        start = end - (hours_back * 3600)
        url = (
            f"{PROMETHEUS_URL}/api/v1/query_range"
            f"?query={urllib.parse.quote(query)}"
            f"&start={start}&end={end}&step={step}"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())["data"]["result"]
    except Exception as e:
        logger.error(f"Prometheus range query failed: {str(e)}")
        return []


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to fetch metrics from Prometheus.
    """
    try:
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Request body must be JSON"}),
                status_code=400,
                mimetype="application/json"
            )

        # Extract parameters
        params = {}
        for param in req_body.get("parameters", []):
            params[param["name"]] = param["value"]

        metric_name = params.get("metric_name", "pod_cpu_utilization")
        namespace = params.get("namespace", DEFAULT_NAMESPACE)
        hours_back = int(params.get("hours_back", "1"))

        # Define metric queries for Prometheus
        metric_queries = {
            "pod_cpu_utilization": f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!=""}}[5m])) by (pod)',
            "pod_memory_utilization": f'sum(container_memory_working_set_bytes{{namespace="{namespace}", container!=""}}) by (pod)',
            "pod_restarts": f'increase(kube_pod_container_status_restarts_total{{namespace="{namespace}"}}[1h])',
            "deployment_replicas_unavailable": f'kube_deployment_status_replicas_unavailable{{namespace="{namespace}"}}',
            "deployment_replicas_available": f'kube_deployment_status_replicas_available{{namespace="{namespace}"}}',
            "http_requests_total": f'increase(http_requests_total{{namespace="{namespace}"}}[5m])',
            "http_request_duration_seconds": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{namespace="{namespace}"}}[5m]))',
        }

        if metric_name not in metric_queries:
            available_metrics = list(metric_queries.keys())
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": f"Metric '{metric_name}' not found",
                    "available_metrics": available_metrics
                }),
                status_code=400,
                mimetype="application/json"
            )

        query = metric_queries[metric_name]

        # Execute query
        if hours_back > 0:
            results = prometheus_range_query(query, hours_back)
        else:
            results = prometheus_query(query)

        # Format results
        metrics_data = []
        for result in results:
            metrics_data.append({
                "labels": result.get("metric", {}),
                "values": result.get("values", result.get("value", []))
            })

        result_response = {
            "status": "success",
            "metric_name": metric_name,
            "namespace": namespace,
            "hours_back": hours_back,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics_data,
            "count": len(metrics_data)
        }

        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": req_body.get("actionGroup", ""),
                    "apiPath": req_body.get("apiPath", ""),
                    "httpMethod": req_body.get("httpMethod", ""),
                    "httpStatusCode": 200,
                    "responseBody": {"application/json": json.dumps(result_response)}
                }
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        error_result = {
            "status": "error",
            "message": str(e)
        }
        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "httpStatusCode": 500,
                    "responseBody": {"application/json": json.dumps(error_result)}
                }
            }),
            status_code=500,
            mimetype="application/json"
        )
