"""
AIOps Assistant - Streamlit Chat UI

This Azure version calls the deployed Azure Functions directly:
  - fetch-logs
  - fetch-metrics
  - fetch-health
"""

import json
import os
import re
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

FETCH_LOGS_URL = os.getenv("AZURE_FETCH_LOGS_URL", "").strip()
FETCH_METRICS_URL = os.getenv("AZURE_FETCH_METRICS_URL", "").strip()
FETCH_HEALTH_URL = os.getenv("AZURE_FETCH_HEALTH_URL", "").strip()
AZURE_REGION = os.getenv("AZURE_REGION", "eastus")
AKS_CLUSTER_NAME = os.getenv("AKS_CLUSTER_NAME", "boutique-aks")
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "boutique")


st.set_page_config(
    page_title="Kira - AIOps Assistant",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=DM+Sans:wght@400;500;700&display=swap');

    .stApp {
        background-color: #0a0e14;
        color: #c5c8c6;
    }

    .main-header {
        padding: 1.5rem 0 1rem 0;
        border-bottom: 1px solid #1a1f2e;
        margin-bottom: 1.5rem;
    }

    .main-header h1 {
        font-family: 'JetBrains Mono', monospace;
        color: #22d3ee;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0;
    }

    .main-header p {
        font-family: 'DM Sans', sans-serif;
        color: #8b95a5;
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
    }

    .status-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: #0d1117;
        border: 1px solid #1a1f2e;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        flex-wrap: wrap;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background: #22d3ee;
        border-radius: 50%;
        box-shadow: 0 0 6px #22d3ee;
    }

    .status-dot-error {
        width: 8px;
        height: 8px;
        background: #ef4444;
        border-radius: 50%;
        box-shadow: 0 0 6px #ef4444;
    }

    .stChatMessage {
        background: #0d1117 !important;
        border: 1px solid #1a1f2e !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    .stChatInput textarea {
        font-family: 'DM Sans', sans-serif !important;
        background: #0d1117 !important;
        color: #c5c8c6 !important;
    }

    [data-testid="stSidebar"] {
        background: #0d1117;
        border-right: 1px solid #1a1f2e;
    }

    .stButton > button {
        background: #111820 !important;
        border: 1px solid #1a1f2e !important;
        color: #c5c8c6 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.75rem !important;
        padding: 0.4rem 0.8rem !important;
        border-radius: 4px !important;
    }

    .stButton > button:hover {
        border-color: #22d3ee !important;
        color: #22d3ee !important;
        background: #0d1117 !important;
    }

    #MainMenu, footer, header { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def bedrock_style_body(api_path: str, parameters: dict) -> dict:
    return {
        "messageVersion": "1.0",
        "actionGroup": "aiops-azure-functions",
        "apiPath": api_path,
        "httpMethod": "POST",
        "parameters": [{"name": key, "value": str(value)} for key, value in parameters.items()],
    }


def unwrap_function_response(payload: dict) -> dict:
    response = payload.get("response", {})
    body = response.get("responseBody", {}).get("application/json")
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body}
    if isinstance(body, dict):
        return body
    return payload


def call_function(url: str, api_path: str, parameters: dict) -> dict:
    if not url:
        return {"status": "not_configured", "message": f"No URL configured for {api_path}"}

    try:
        response = requests.post(
            url,
            json=bedrock_style_body(api_path, parameters),
            timeout=30,
        )
        response.raise_for_status()
        return unwrap_function_response(response.json())
    except requests.RequestException as exc:
        return {"status": "error", "message": str(exc)}
    except ValueError as exc:
        return {"status": "error", "message": f"Invalid JSON response: {exc}"}


def infer_hours(prompt: str) -> int:
    match = re.search(r"last\s+(\d+)\s+hour", prompt.lower())
    return int(match.group(1)) if match else 1


def infer_log_filter(prompt: str) -> str:
    lowered = prompt.lower()
    if "503" in lowered:
        return "503"
    if "timeout" in lowered:
        return "timeout"
    if "unauthorized" in lowered or "401" in lowered:
        return "Unauthorized"
    if "memory" in lowered or "oom" in lowered:
        return "OutOfMemory"
    return "ERROR"


def infer_metric(prompt: str) -> str:
    lowered = prompt.lower()
    if "memory" in lowered:
        return "pod_memory_utilization"
    if "restart" in lowered:
        return "pod_restarts"
    if "replica" in lowered or "unavailable" in lowered:
        return "deployment_replicas_unavailable"
    if "latency" in lowered or "duration" in lowered:
        return "http_request_duration_seconds"
    if "request" in lowered:
        return "http_requests_total"
    return "pod_cpu_utilization"


def summarize_json(title: str, data: dict) -> str:
    if data.get("status") == "not_configured":
        return f"### {title}\nNot configured: {data.get('message')}"
    if data.get("status") == "error":
        return f"### {title}\nError: {data.get('message')}"

    return f"### {title}\n```json\n{json.dumps(data, indent=2)[:5000]}\n```"


def investigate(prompt: str) -> str:
    lowered = prompt.lower()
    hours_back = infer_hours(prompt)
    sections = []

    wants_logs = any(word in lowered for word in ["error", "503", "log", "timeout", "failed", "unauthorized"])
    wants_metrics = any(word in lowered for word in ["cpu", "memory", "metric", "latency", "request", "restart"])
    wants_health = any(word in lowered for word in ["health", "healthy", "pod", "service", "deployment", "down", "crash"])

    if not any([wants_logs, wants_metrics, wants_health]):
        wants_logs = wants_metrics = wants_health = True

    if wants_logs:
        data = call_function(
            FETCH_LOGS_URL,
            "/fetch-logs",
            {
                "filter_pattern": infer_log_filter(prompt),
                "log_table": "ContainerLog",
                "hours_back": hours_back,
            },
        )
        sections.append(summarize_json("Log Analytics", data))

    if wants_metrics:
        data = call_function(
            FETCH_METRICS_URL,
            "/fetch-metrics",
            {
                "metric_name": infer_metric(prompt),
                "namespace": K8S_NAMESPACE,
                "hours_back": hours_back,
            },
        )
        sections.append(summarize_json("Prometheus Metrics", data))

    if wants_health:
        data = call_function(
            FETCH_HEALTH_URL,
            "/fetch-health",
            {
                "cluster_name": AKS_CLUSTER_NAME,
                "namespace": K8S_NAMESPACE,
            },
        )
        sections.append(summarize_json("AKS Health", data))

    return "\n\n".join(sections)


config_ok = bool(FETCH_LOGS_URL and FETCH_METRICS_URL and FETCH_HEALTH_URL)


st.markdown(
    """
<div class="main-header">
    <h1>KIRA</h1>
    <p>AIOps Assistant for AKS, Log Analytics, and Prometheus</p>
</div>
""",
    unsafe_allow_html=True,
)


if not config_ok:
    st.markdown(
        """
    <div class="status-bar">
        <div class="status-dot-error"></div>
        <span style="color: #ef4444;">NOT CONFIGURED</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.error("Missing Azure Function URLs. Create a `.env` file with:")
    st.code(
        """AZURE_FETCH_LOGS_URL=https://<app>.azurewebsites.net/api/fetch-logs
AZURE_FETCH_METRICS_URL=https://<app>.azurewebsites.net/api/fetch-metrics
AZURE_FETCH_HEALTH_URL=https://<app>.azurewebsites.net/api/fetch-health
AZURE_REGION=eastus
AKS_CLUSTER_NAME=boutique-aks
K8S_NAMESPACE=boutique""",
        language="bash",
    )
    st.stop()


st.markdown(
    f"""
<div class="status-bar">
    <div class="status-dot"></div>
    <span style="color: #22d3ee;">ONLINE</span>
    <span style="color: #2a3040;">|</span>
    <span style="color: #8b95a5;">Session: {st.session_state.session_id[:8]}</span>
    <span style="color: #2a3040;">|</span>
    <span style="color: #8b95a5;">Region: {AZURE_REGION}</span>
    <span style="color: #2a3040;">|</span>
    <span style="color: #8b95a5;">Cluster: {AKS_CLUSTER_NAME}</span>
</div>
""",
    unsafe_allow_html=True,
)


col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Check 503 errors"):
        st.session_state.quick_action = "Why are we seeing 503 errors in the last hour?"
with col2:
    if st.button("CPU and memory"):
        st.session_state.quick_action = "Check CPU and memory utilization across all services"
with col3:
    if st.button("AKS health"):
        st.session_state.quick_action = "Are all pods and deployments healthy?"
with col4:
    if st.button("Recent errors"):
        st.session_state.quick_action = "What are the most frequent errors in the last hour?"

st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


quick_action = st.session_state.pop("quick_action", None)
user_input = st.chat_input("Describe the issue, for example: why is the API slow?")
prompt = quick_action or user_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Kira is checking Azure telemetry..."):
            response = investigate(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})


with st.sidebar:
    st.markdown("### KIRA")
    st.markdown("AIOps Assistant v2.0")
    st.markdown("---")
    st.markdown("**Tools Available:**")
    st.markdown("- `fetch_logs` - Azure Log Analytics")
    st.markdown("- `fetch_metrics` - Prometheus")
    st.markdown("- `fetch_service_health` - AKS health")
    st.markdown("---")
    st.markdown("**Sample Questions:**")
    st.markdown(
        """
        - Why are we seeing 503 errors?
        - Is CPU usage high?
        - Are all pods healthy?
        - What errors happened in the last 2 hours?
        - Is there a memory issue?
        """
    )
    st.markdown("---")
    if st.button("New Session"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
