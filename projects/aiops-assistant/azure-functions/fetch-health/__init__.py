import json
import logging
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import azure.functions as func

# Prometheus configuration
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
DEFAULT_NAMESPACE = "boutique"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrometheusError(Exception):
    """Raised when Prometheus query fails"""
    pass


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


def validate_namespace(namespace: str) -> str:
    """Validate and sanitize Kubernetes namespace name"""
    if not namespace or not isinstance(namespace, str):
        raise ValidationError("Namespace must be a non-empty string")
    
    # K8s namespace must match RFC 1123: alphanumeric and hyphens only
    if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', namespace):
        raise ValidationError(f"Invalid namespace format: {namespace}")
    
    if len(namespace) > 63:
        raise ValidationError(f"Namespace exceeds 63 characters: {namespace}")
    
    return namespace


def safe_int(value, field_name: str = "value") -> int:
    """Safely convert value to int with error handling"""
    try:
        return int(float(value))
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Cannot convert {field_name} to int: {value}") from e


def safe_float(value, field_name: str = "value") -> float:
    """Safely convert value to float with error handling"""
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Cannot convert {field_name} to float: {value}") from e


def prometheus_query(query):
    """Execute a PromQL query against Prometheus"""
    try:
        url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(query)}"
        logger.debug(f"Querying Prometheus: {url}")
        
        with urllib.request.urlopen(url, timeout=15) as resp:
            if resp.status != 200:
                raise PrometheusError(f"HTTP {resp.status} from Prometheus")
            
            data = json.loads(resp.read())
            
            if data.get("status") != "success":
                error_msg = data.get("error", "Unknown error")
                raise PrometheusError(f"Prometheus error: {error_msg}")
            
            return data.get("data", {}).get("result", [])
            
    except urllib.error.URLError as e:
        logger.error(f"Connection error to Prometheus: {str(e)}")
        raise PrometheusError(f"Cannot reach Prometheus at {PROMETHEUS_URL}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from Prometheus: {str(e)}")
        raise PrometheusError("Prometheus returned invalid JSON") from e
    except Exception as e:
        logger.error(f"Prometheus query failed: {str(e)}")
        raise PrometheusError(f"Query failed: {str(e)}") from e


def check_aks_health(cluster_name, k8s_namespace):
    """
    Check AKS cluster health by querying Prometheus metrics.
    Requires Prometheus with kube-state-metrics installed.
    """
    try:
        # Validate inputs
        k8s_namespace = validate_namespace(k8s_namespace)
        
        # Check deployment replica status
        logger.info(f"Checking deployments for namespace: {k8s_namespace}")
        desired_results = prometheus_query(
            f'kube_deployment_spec_replicas{{namespace="{k8s_namespace}"}}'
        )
        available_results = prometheus_query(
            f'kube_deployment_status_replicas_available{{namespace="{k8s_namespace}"}}'
        )
        
        available_map = {}
        for r in available_results:
            try:
                deployment = r.get("metric", {}).get("deployment")
                available = safe_int(r.get("value", [None, 0])[1], "replicas_available")
                if deployment:
                    available_map[deployment] = available
            except (ValidationError, KeyError, IndexError) as e:
                logger.warning(f"Skipping malformed metric result: {e}")
                continue

        deployments = []
        unhealthy_deployments = []
        
        for r in desired_results:
            try:
                name = r.get("metric", {}).get("deployment")
                desired = safe_int(r.get("value", [None, 0])[1], "replicas_desired")
                available = available_map.get(name, 0)
                healthy = desired > 0 and available == desired
                
                issue = None
                if desired == 0:
                    issue = "scaled to zero"
                elif not healthy:
                    issue = f"{desired - available} replica(s) unavailable"
                
                deployments.append({
                    "name": name,
                    "desired": desired,
                    "available": available,
                    "healthy": healthy
                })
                
                if not healthy:
                    unhealthy_deployments.append({"name": name, "issue": issue})
                    
            except (ValidationError, KeyError, IndexError) as e:
                logger.warning(f"Skipping malformed deployment result: {e}")
                continue

        # Check pod restart counts
        logger.info("Checking pod restart counts")
        restart_results = prometheus_query(
            f'increase(kube_pod_container_status_restarts_total{{namespace="{k8s_namespace}"}}[1h])'
        )
        
        crashing_pods = []
        for r in restart_results:
            try:
                restarts = safe_float(r.get("value", [None, 0])[1], "restarts")
                if restarts > 0:
                    crashing_pods.append({
                        "pod": r.get("metric", {}).get("pod"),
                        "container": r.get("metric", {}).get("container"),
                        "restarts": round(restarts, 1)
                    })
            except (ValidationError, KeyError, IndexError) as e:
                logger.warning(f"Skipping malformed restart metric: {e}")
                continue
        
        crashing_pods.sort(key=lambda x: x.get("restarts", 0), reverse=True)

        # Check pod memory and CPU
        logger.info("Checking resource utilization")
        memory_results = prometheus_query(
            f'container_memory_working_set_bytes{{namespace="{k8s_namespace}", container!=""}}'
        )
        cpu_results = prometheus_query(
            f'rate(container_cpu_usage_seconds_total{{namespace="{k8s_namespace}", container!=""}}[5m])'
        )

        memory_map = {}
        for r in memory_results:
            try:
                pod = r.get("metric", {}).get("pod")
                memory_bytes = safe_float(r.get("value", [None, 0])[1], "memory_bytes")
                if pod and memory_bytes > 0:
                    memory_map[pod] = memory_bytes / (1024**3)  # Convert to GB
            except (ValidationError, KeyError, IndexError, ZeroDivisionError) as e:
                logger.warning(f"Skipping malformed memory metric: {e}")
                continue

        cpu_map = {}
        for r in cpu_results:
            try:
                pod = r.get("metric", {}).get("pod")
                cpu_cores = safe_float(r.get("value", [None, 0])[1], "cpu_cores")
                if pod:
                    cpu_map[pod] = cpu_cores
            except (ValidationError, KeyError, IndexError) as e:
                logger.warning(f"Skipping malformed CPU metric: {e}")
                continue

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
        
    except (PrometheusError, ValidationError) as e:
        logger.error(f"Health check error: {str(e)}")
        raise


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to fetch AKS cluster health.
    """
    request_id = req.headers.get("x-request-id", "unknown")
    logger.info(f"[{request_id}] Health check request received")
    
    req_body = None
    params = {}
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError as e:
            logger.error(f"[{request_id}] Invalid JSON in request body: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "Request body must be valid JSON",
                    "request_id": request_id
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Extract parameters
        if not isinstance(req_body, dict):
            logger.error(f"[{request_id}] Request body is not a dict")
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "Request body must be a JSON object",
                    "request_id": request_id
                }),
                status_code=400,
                mimetype="application/json"
            )

        for param in req_body.get("parameters", []):
            if isinstance(param, dict) and "name" in param and "value" in param:
                params[param["name"]] = param["value"]

        cluster_name = params.get("cluster_name", "boutique-aks").strip()
        namespace = params.get("namespace", DEFAULT_NAMESPACE).strip()
        
        if not cluster_name:
            cluster_name = "boutique-aks"

        logger.info(f"[{request_id}] Checking cluster: {cluster_name}, namespace: {namespace}")

        # Get health status
        health_status = check_aks_health(cluster_name, namespace)

        logger.info(f"[{request_id}] Health check complete. Cluster healthy: {health_status.get('cluster_healthy')}")

        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": req_body.get("actionGroup", ""),
                    "apiPath": req_body.get("apiPath", ""),
                    "httpMethod": req_body.get("httpMethod", ""),
                    "httpStatusCode": 200,
                    "responseBody": {
                        "application/json": json.dumps({
                            **health_status,
                            "request_id": request_id
                        })
                    }
                }
            }),
            status_code=200,
            mimetype="application/json"
        )

    except ValidationError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        error_result = {
            "status": "validation_error",
            "message": str(e),
            "request_id": request_id
        }
        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "httpStatusCode": 400,
                    "responseBody": {"application/json": json.dumps(error_result)}
                }
            }),
            status_code=400,
            mimetype="application/json"
        )

    except PrometheusError as e:
        logger.error(f"[{request_id}] Prometheus error: {str(e)}")
        error_result = {
            "status": "prometheus_error",
            "message": str(e),
            "request_id": request_id,
            "prometheus_url": PROMETHEUS_URL
        }
        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "httpStatusCode": 503,
                    "responseBody": {"application/json": json.dumps(error_result)}
                }
            }),
            status_code=503,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        error_result = {
            "status": "error",
            "message": str(e),
            "request_id": request_id,
            "cluster_name": params.get("cluster_name", "unknown"),
            "namespace": params.get("namespace", DEFAULT_NAMESPACE)
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
