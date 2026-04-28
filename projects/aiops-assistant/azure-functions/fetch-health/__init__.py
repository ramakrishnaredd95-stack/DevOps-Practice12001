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


def check_aks_health(cluster_name, k8s_namespace):
    """
    Check AKS cluster health by querying Prometheus metrics.
    Requires Prometheus with kube-state-metrics installed.
    """
    # Check deployment replica status
    desired_results = prometheus_query(
        f'kube_deployment_spec_replicas{{namespace="{k8s_namespace}"}}'
    )
    available_results = prometheus_query(
        f'kube_deployment_status_replicas_available{{namespace="{k8s_namespace}"}}'
    )
    available_map = {r["metric"].get("deployment"): int(float(r["value"][1])) for r in available_results}

    deployments = []
    unhealthy_deployments = []
    for r in desired_results:
        name = r["metric"].get("deployment")
        desired = int(float(r["value"][1]))
        available = available_map.get(name, 0)
        healthy = desired > 0 and available == desired
        issue = "scaled to zero" if desired == 0 else (f"{desired - available} replica(s) unavailable" if not healthy else None)
        deployments.append({"name": name, "desired": desired, "available": available, "healthy": healthy})
        if not healthy:
            unhealthy_deployments.append({"name": name, "issue": issue})

    # Check pod restart counts
    restart_results = prometheus_query(
        f'increase(kube_pod_container_status_restarts_total{{namespace="{k8s_namespace}"}}[1h])'
    )
    crashing_pods = [
        {
            "pod": r["metric"].get("pod"),
            "container": r["metric"].get("container"),
            "restarts": round(float(r["value"][1]), 1),
        }
        for r in restart_results if float(r["value"][1]) > 0
    ]
    crashing_pods.sort(key=lambda x: x["restarts"], reverse=True)

    # Check pod memory and CPU
    memory_results = prometheus_query(
        f'container_memory_working_set_bytes{{namespace="{k8s_namespace}", container!=""}}'
    )
    cpu_results = prometheus_query(
        f'rate(container_cpu_usage_seconds_total{{namespace="{k8s_namespace}", container!=""}}[5m])'
    )

    memory_map = {r["metric"].get("pod"): float(r["value"][1]) / (1024**3) for r in memory_results}
    cpu_map = {r["metric"].get("pod"): float(r["value"][1]) for r in cpu_results}

    resource_usage = []
    for pod, memory in memory_map.items():
        resource_usage.append({
            "pod": pod,
            "memory_gb": round(memory, 2),
            "cpu_cores": round(cpu_map.get(pod, 0), 3)
        })

    all_healthy = not unhealthy_deployments and not crashing_pods

    return {
        "cluster_name": cluster_name,
        "namespace": k8s_namespace,
        "cluster_healthy": all_healthy,
        "deployments": deployments,
        "unhealthy_deployments": unhealthy_deployments,
        "crashing_pods": crashing_pods,
        "resource_usage": resource_usage,
    }


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to fetch AKS cluster health.
    Replaces AWS Lambda fetch_health function.
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

        cluster_name = params.get("cluster_name", "boutique-aks")
        namespace = params.get("namespace", DEFAULT_NAMESPACE)

        # Get health status
        health_status = check_aks_health(cluster_name, namespace)

        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": req_body.get("actionGroup", ""),
                    "apiPath": req_body.get("apiPath", ""),
                    "httpMethod": req_body.get("httpMethod", ""),
                    "httpStatusCode": 200,
                    "responseBody": {"application/json": json.dumps(health_status)}
                }
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        error_result = {
            "status": "error",
            "message": str(e),
            "cluster_name": req.args.get("cluster_name", "unknown"),
            "namespace": req.args.get("namespace", DEFAULT_NAMESPACE)
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
