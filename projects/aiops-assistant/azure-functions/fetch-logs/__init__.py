import json
import logging
import os
from datetime import datetime, timedelta
from azure.monitor.query import LogsQueryClient
from azure.identity import ClientSecretCredential
import azure.functions as func

# Azure Log Analytics configuration
WORKSPACE_ID = os.environ.get("LOG_ANALYTICS_WORKSPACE_ID")
TENANT_ID = os.environ.get("AZURE_TENANT_ID")
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to fetch logs from Azure Log Analytics.
    Replaces AWS Lambda fetch_logs function.
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

        filter_pattern = params.get("filter_pattern", "ERROR")
        log_table = params.get("log_table", "ContainerLog")
        hours_back = int(params.get("hours_back", "1"))

        # Create Log Analytics client
        credential = ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        client = LogsQueryClient(credential)

        # Build KQL query
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)

        query = f"""
        {log_table}
        | where TimeGenerated >= datetime({start_time.isoformat()})
        | where TimeGenerated <= datetime({end_time.isoformat()})
        | where LogMessage contains "{filter_pattern}"
        | order by TimeGenerated desc
        | limit 50
        """

        # Execute query
        response = client.query_workspace(
            workspace_id=WORKSPACE_ID,
            query=query,
            timespan=(start_time, end_time)
        )

        if response.status == "PartialSuccess":
            logger.warning("Query returned partial results")

        # Format results
        logs = []
        if response.tables:
            for table in response.tables:
                for row in table.rows:
                    logs.append({
                        "timestamp": str(row[0]),
                        "message": str(row[1]) if len(row) > 1 else ""
                    })

        if not logs:
            result = {
                "status": "no_logs_found",
                "message": f"No logs matching '{filter_pattern}' in {log_table} for the last {hours_back} hour(s).",
                "log_table": log_table,
                "filter": filter_pattern,
                "time_range_hours": hours_back,
            }
        else:
            result = {
                "status": "logs_found",
                "log_table": log_table,
                "filter": filter_pattern,
                "time_range_hours": hours_back,
                "total_events": len(logs),
                "logs": logs,
            }

        return func.HttpResponse(
            json.dumps({
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": req_body.get("actionGroup", ""),
                    "apiPath": req_body.get("apiPath", ""),
                    "httpMethod": req_body.get("httpMethod", ""),
                    "httpStatusCode": 200,
                    "responseBody": {"application/json": json.dumps(result)}
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
