"""
AIOps Assistant Azure Function reference.

The project now uses HTTP-triggered Azure Functions instead of the previous
serverless implementation. The live function code is split into these folders:

  - azure-functions/fetch-logs
  - azure-functions/fetch-metrics
  - azure-functions/fetch-health

OpenAPI schemas for these functions live in:

  - schemas/fetch_logs.json
  - schemas/fetch_metrics.json
  - schemas/fetch_health.json

This file is kept only as a short index so old bookmarks do not point people
to stale provider-specific code.
"""

AZURE_FUNCTION_ROUTES = {
    "fetch_logs": "/api/fetch-logs",
    "fetch_metrics": "/api/fetch-metrics",
    "fetch_health": "/api/fetch-health",
}


def main() -> None:
    for name, route in AZURE_FUNCTION_ROUTES.items():
        print(f"{name}: {route}")


if __name__ == "__main__":
    main()
