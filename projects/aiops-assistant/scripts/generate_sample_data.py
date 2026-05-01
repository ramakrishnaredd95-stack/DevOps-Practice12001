"""
Build sample Azure Function requests for the AIOps demo.

This does not write telemetry into Azure. It helps you test the deployed
HTTP-triggered functions with realistic request payloads.

Examples:
    python scripts/generate_sample_data.py
    python scripts/generate_sample_data.py --url https://<app>.azurewebsites.net/api/fetch-logs --tool logs
"""

import argparse
import json
from typing import Dict

import requests


SAMPLE_PAYLOADS: Dict[str, dict] = {
    "logs": {
        "messageVersion": "1.0",
        "actionGroup": "aiops-azure-functions",
        "apiPath": "/fetch-logs",
        "httpMethod": "POST",
        "parameters": [
            {"name": "filter_pattern", "value": "ERROR"},
            {"name": "log_table", "value": "ContainerLog"},
            {"name": "hours_back", "value": "1"},
        ],
    },
    "metrics": {
        "messageVersion": "1.0",
        "actionGroup": "aiops-azure-functions",
        "apiPath": "/fetch-metrics",
        "httpMethod": "POST",
        "parameters": [
            {"name": "metric_name", "value": "pod_cpu_utilization"},
            {"name": "namespace", "value": "boutique"},
            {"name": "hours_back", "value": "1"},
        ],
    },
    "health": {
        "messageVersion": "1.0",
        "actionGroup": "aiops-azure-functions",
        "apiPath": "/fetch-health",
        "httpMethod": "POST",
        "parameters": [
            {"name": "cluster_name", "value": "boutique-aks"},
            {"name": "namespace", "value": "boutique"},
        ],
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or send sample AIOps Azure Function requests.")
    parser.add_argument("--tool", choices=SAMPLE_PAYLOADS.keys(), default="logs")
    parser.add_argument("--url", help="Azure Function URL to call. If omitted, the payload is printed only.")
    args = parser.parse_args()

    payload = SAMPLE_PAYLOADS[args.tool]

    if not args.url:
        print(json.dumps(payload, indent=2))
        return

    response = requests.post(args.url, json=payload, timeout=30)
    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)


if __name__ == "__main__":
    main()
