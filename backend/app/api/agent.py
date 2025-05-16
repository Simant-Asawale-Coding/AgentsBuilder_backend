import os
from fastapi import APIRouter, HTTPException
from app.models.agent import AgentCreateRequest, AgentInfo
from app.services.agent_registry import register_agent, get_agent, get_all_agents
from app.services.agent_creator import render_agent_code, save_agent_code, get_agent_id
import jsonschema
from app.services.framework_registry import FRAMEWORKS, get_framework_creds_schema
import time
from app.services.github_push import push_agent_to_github
from app.services.azure_deploy import trigger_github_workflow, download_deployed_url_artifact
from app.services.agent_registry import update_agent, get_agent
router = APIRouter()



@router.post("/agents", response_model=AgentInfo)
def create_agent(agent_req: AgentCreateRequest):
    # Validate framework
    framework = agent_req.framework
    fw_record = next((f for f in FRAMEWORKS if f["name"] == framework), None)
    if not fw_record:
        raise HTTPException(status_code=400, detail="Invalid framework")
    # Validate credentials
    try:
        schema = get_framework_creds_schema(framework)
        jsonschema.validate(agent_req.credentials, schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid credentials: {e}")
    # Prepare template context
    context = dict(agent_req.credentials)
    context["mcp_servers"] = [tool.model_dump() for tool in agent_req.tools]
    context["system_message"] = agent_req.prompt
    import os
    context["agent_name"] = f"agent_{framework}_{ os.urandom(4).hex()}"
    # Map credential values to template variables for all frameworks
    context["llm_api_key"] = agent_req.credentials.get("AZURE_OPENAI_API_KEY") or agent_req.credentials.get("OPENAI_API_KEY") or ""
    context["llm_endpoint"] = agent_req.credentials.get("AZURE_OPENAI_ENDPOINT") or agent_req.credentials.get("OPENAI_API_BASE") or ""
    context["llm_api_version"] = agent_req.credentials.get("AZURE_OPENAI_API_VERSION") or ""
    context["llm_model"] = agent_req.credentials.get("AZURE_OPENAI_DEPLOYMENT") or agent_req.credentials.get("OPENAI_DEPLOYMENT_NAME") or ""
    # Ensure both mcp_servers and mcp_urls are available for template compatibility
    context["mcp_urls"] = [tool["url"] if isinstance(tool, dict) else tool.url for tool in context["mcp_servers"]]
    print("[DEBUG] Agent creation context:", context)
    
    # Add any other mappings as needed for other templates
    # Render agent code
    try:
        code = render_agent_code(framework, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template rendering failed: {e}")
    # Save generated code
    agent_id = get_agent_id({
        "status": "created",
        "endpoint": "",
        "tools": agent_req.tools,
        "framework": framework,
        "prompt": agent_req.prompt
    })
    print(f"[DEBUG] agent_id (truncated): {agent_id}")
    agent_filename = f"{agent_id}.py"
    code_path = save_agent_code(agent_id, code)
    print(f"[DEBUG] code_path: {code_path}")
    print(f"[DEBUG] agent_filename: {agent_filename}")
    agent_remote_path = f"agents/{framework}/{agent_filename}"
    print(f"[DEBUG] agent_remote_path: {agent_remote_path}")
    # 1. Push to GitHub
    try:
        repo_url = os.environ.get("GITHUB_REPO_URL")
        branch = os.environ.get("GITHUB_REF", "main")
        commit_sha = push_agent_to_github(
            agent_file_path=code_path,
            framework=framework,
            repo_url=repo_url,
            branch=branch
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push agent to GitHub: {e}")
    # 2. Trigger Azure deploy workflow
    try:
        repo = os.environ.get("GITHUB_REPO")
        workflow_file = "deploy-agent.yml"
        agent_filename = os.path.basename(code_path)
        agent_remote_path = f"agents/{framework}/{agent_filename}"
        inputs = {
            "sha": commit_sha,
            "agent_file": agent_remote_path,
            "framework": framework
        }
        ref = os.environ.get("GITHUB_REF", "main")
        print(f"[DEBUG] Triggering workflow with inputs: {inputs}")
        run_id = trigger_github_workflow(repo, workflow_file, ref, inputs)
        print(f"[DEBUG] Workflow run_id: {run_id}")
        agent_id = register_agent({
        "user_id": agent_req.user_id,
        "status": "created",
        "endpoint": "",
        "tools": agent_req.tools,
        "framework": framework,
        "prompt": agent_req.prompt
    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Azure deploy workflow: {e}")
    # 3. Wait and get deployed URL
    #
    try:
        max_retries = 6  # Increased for robustness
        retry_delay = 10
        endpoint = None
        agent_base = os.path.splitext(os.path.basename(agent_remote_path))[0]
        artifact_name = f"deployed-url-{framework}-{agent_base}"
        print(f"[DEBUG] agent_remote_path: {agent_remote_path}")
        print(f"[DEBUG] agent_base: {agent_base}")
        print(f"[DEBUG] expected artifact_name: {artifact_name}")
        for attempt in range(max_retries):
            print(f"[DEBUG] Poll attempt {attempt+1}/{max_retries}")
            # Print all artifact names found
            repo_artifacts_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
            import requests, os
            headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN')}", "Accept": "application/vnd.github+json"}
            resp = requests.get(repo_artifacts_url, headers=headers)
            if resp.ok:
                artifacts = resp.json().get("artifacts", [])
                print(f"[DEBUG] Artifacts found: {[a['name'] for a in artifacts]}")
            else:
                print(f"[DEBUG] Could not fetch artifacts: {resp.status_code} {resp.text}")
            endpoint = download_deployed_url_artifact(repo, run_id, framework, agent_remote_path)
            if endpoint:
                break
            time.sleep(retry_delay)
        if not endpoint:
            raise HTTPException(
                status_code=500,
                detail=f"Deployment succeeded but artifact not found after {max_retries} retries. Check workflow artifact naming and logs."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deployed endpoint: {e}")
    # 4. Update agent info
    update_agent(agent_id, {"endpoint": endpoint, "status": "deployed", "commit_sha": commit_sha, "run_id": run_id})
    agent_info = get_agent(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent not found after creation.")
    return agent_info

@router.get("/agents/{agent_id}", response_model=AgentInfo)
def get_agent_info(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.get("/agents")
def list_agents():
    """Return all registered agents (for UI listing)."""
    return get_all_agents()
