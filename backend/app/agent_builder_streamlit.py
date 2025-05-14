import streamlit as st
import requests
import time

API_BASE = "http://localhost:8004"

st.set_page_config(page_title="Dynamic Agent Builder", layout="wide")
st.title("🤖 Dynamic Agent Builder (Streamlit)")

# --- Fetch frameworks and tools ---
@st.cache_data(show_spinner=False)
def fetch_frameworks():
    resp = requests.get(f"{API_BASE}/frameworks")
    resp.raise_for_status()
    return resp.json()["frameworks"]

@st.cache_data(show_spinner=False)
def fetch_tools():
    resp = requests.get(f"{API_BASE}/tools")
    resp.raise_for_status()
    return resp.json()["tools"]

def fetch_creds_schema(framework_name):
    resp = requests.get(f"{API_BASE}/creds_schema/{framework_name}")
    resp.raise_for_status()
    return resp.json()

# --- State management ---
if "framework_name" not in st.session_state:
    st.session_state.framework_name = None
if "creds_schema" not in st.session_state:
    st.session_state.creds_schema = None
if "creds" not in st.session_state:
    st.session_state.creds = {}
if "tools_selected" not in st.session_state:
    st.session_state.tools_selected = []
if "prompt" not in st.session_state:
    st.session_state.prompt = "You are a helpful AI agent."
if "agent_deploy_result" not in st.session_state:
    st.session_state.agent_deploy_result = None

frameworks = fetch_frameworks()
tools = fetch_tools()

# --- 1. Framework selection and confirm ---
st.subheader("Step 1: Select Framework")
fw_labels = [fw["label"] for fw in frameworks]
fw_label = st.selectbox("Framework", fw_labels, index=0)
selected_fw = next(fw for fw in frameworks if fw["label"] == fw_label)

if st.button("Confirm Framework"):
    st.session_state.framework_name = selected_fw["name"]
    st.session_state.creds_schema = fetch_creds_schema(selected_fw["name"])
    st.session_state.creds = {}
    st.session_state.agent_deploy_result = None

# --- 2. Dynamic Credentials, Tools, Prompt, Deploy ---
if st.session_state.framework_name and st.session_state.creds_schema:
    st.subheader(f"Step 2: Configure Agent for '{st.session_state.framework_name}'")
    with st.form("creds_tools_form"):
        # Dynamic credentials
        st.markdown("**Enter required credentials:**")
        creds = st.session_state.creds.copy()
        for key, val in st.session_state.creds_schema.items():
            if isinstance(val, list) or isinstance(val, dict):
                continue  # Only support string fields for now
            input_type = "password" if "key" in key.lower() or "password" in key.lower() else "text"
            creds[key] = st.text_input(key.replace("_", " "), value=creds.get(key, ""), type=input_type if input_type == "password" else "default", key=f"creds_{key}")
        # Tool selection
        st.markdown("**Select tools:**")
        tool_labels = [f'{t["name"]} ({t["description"]})' for t in tools]
        tools_selected = st.multiselect("Tools", tool_labels, default=[tool_labels[i] for i in range(len(tool_labels)) if tools[i]["name"] in [t["name"] for t in st.session_state.tools_selected]])
        selected_tools = [t for t, lbl in zip(tools, tool_labels) if lbl in tools_selected]
        # System prompt
        prompt = st.text_area("System Prompt", value=st.session_state.prompt)
        deploy_clicked = st.form_submit_button("Deploy Agent")
        if deploy_clicked:
            st.session_state.creds = creds
            st.session_state.tools_selected = selected_tools
            st.session_state.prompt = prompt
            st.session_state.agent_deploy_result = None
            with st.spinner("Deploying agent and building container (this may take a minute)..."):
                try:
                    payload = {
                        "tools": selected_tools,
                        "framework": st.session_state.framework_name,
                        "credentials": creds,
                        "prompt": prompt
                    }
                    resp = requests.post(f"{API_BASE}/api/agents", json=payload)
                    resp.raise_for_status()
                    agent_info = resp.json()
                    # Poll for status and endpoint
                    status_url = f"{API_BASE}/api/agents/{agent_info['id']}/status"
                    endpoint_url = f"{API_BASE}/api/agents/{agent_info['id']}/endpoint"
                    status = "created"
                    endpoint = ""
                    for i in range(60):
                        status_resp = requests.get(status_url)
                        status_resp.raise_for_status()
                        status = status_resp.json().get("status", "unknown")
                        endpoint_resp = requests.get(endpoint_url)
                        endpoint_resp.raise_for_status()
                        endpoint = endpoint_resp.json().get("endpoint", "")
                        if status == "running" and endpoint:
                            break
                        time.sleep(2)
                    st.session_state.agent_deploy_result = {
                        "agent_info": agent_info,
                        "status": status,
                        "endpoint": endpoint
                    }
                except Exception as e:
                    st.session_state.agent_deploy_result = {"error": str(e)}

# --- 3. Show deployment result ---
if st.session_state.agent_deploy_result:
    res = st.session_state.agent_deploy_result
    if "error" in res:
        st.error(f"Agent deployment failed: {res['error']}")
    else:
        st.success(f"Agent created! ID: {res['agent_info']['id']}")
        st.markdown(f"**Status:** {res['status']}")
        if res['endpoint']:
            st.markdown(f"**Endpoint:** `{res['endpoint']}`")
        st.write(res['agent_info'])

# --- 4. List all agents ---
st.header("All Agents")
try:
    resp = requests.get(f"{API_BASE}/api/agents")
    resp.raise_for_status()
    agents = resp.json()
    if agents:
        for agent in agents:
            st.markdown(f"**ID:** {agent['id']} | **Framework:** {agent['framework']} | **Status:** {agent['status']}")
            st.markdown(f"Endpoint: `{agent.get('endpoint', '')}`")
            st.markdown(f"Prompt: `{agent.get('prompt', '')}`")
            st.markdown("---")
    else:
        st.info("No agents created yet.")
except Exception as e:
    st.error(f"Failed to fetch agents: {e}")
