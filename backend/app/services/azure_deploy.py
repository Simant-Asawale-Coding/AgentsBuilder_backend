import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"

def trigger_github_workflow(repo, workflow_file, ref, inputs, github_token_env="GITHUB_TOKEN"):
    token = os.environ.get(github_token_env)
    if not token:
        raise RuntimeError(f"GitHub token not found in environment variable: {github_token_env}")
    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"ref": ref, "inputs": inputs}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    print("Workflow triggered successfully.")
    # Now, poll for the workflow run
    print("Sleeping for 10 seconds...")
    time.sleep(10)
    return poll_workflow_run(repo, workflow_file, ref, token)

def poll_workflow_run(repo, workflow_file, ref, token, poll_interval=10, timeout=600):
    # Get the workflow ID
    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_file}/runs"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    start_time = time.time()
    while True:
        resp = requests.get(url, headers=headers, params={"branch": ref, "event": "workflow_dispatch"})
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if runs:
            latest_run = runs[0]
            run_id = latest_run["id"]
            status = latest_run["status"]
            conclusion = latest_run.get("conclusion")
            print(f"Workflow run status: {status} (conclusion: {conclusion})")
            if status == "completed":
                if conclusion == "success":
                    print("Workflow completed successfully.")
                    return run_id
                else:
                    print("Workflow failed.")
                    return None
        if time.time() - start_time > timeout:
            raise TimeoutError("Timed out waiting for workflow to complete.")
        time.sleep(poll_interval)

import os
import requests
import zipfile
import io
import time

def download_deployed_url_artifact(repo, run_id, framework, agent_file, github_token_env="GITHUB_TOKEN"):
    token = os.environ.get(github_token_env)
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    # 1. List artifacts for the workflow run
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    artifacts = resp.json().get("artifacts", [])
    agent_base = os.path.splitext(os.path.basename(agent_file))[0]
    artifact_name = f"deployed-url-{framework}-{agent_base}"
    print(f"[DEBUG] agent_file: {agent_file}")
    print(f"[DEBUG] agent_base: {agent_base}")
    print(f"[DEBUG] artifact_name being searched: {artifact_name}")
    print(f"[DEBUG] Artifacts found: {[a['name'] for a in artifacts]}")
    artifact = next((a for a in artifacts if a["name"] == artifact_name), None)
    if not artifact:
        print(f"Artifact {artifact_name} not found.")
        return None
    # 2. Download the artifact zip
    download_url = artifact["archive_download_url"]
    resp = requests.get(download_url, headers=headers)
    resp.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    # 3. Extract the txt file and save to data/urls/<framework>/<agent_file>.txt
    txt_filename = f"{agent_base}.txt"
    extract_dir = os.path.join(os.path.dirname(__file__), "..", "data", "urls", framework)
    os.makedirs(extract_dir, exist_ok=True)
    save_path = os.path.join(extract_dir, txt_filename)
    with z.open(txt_filename) as f_in, open(save_path, "wb") as f_out:
        f_out.write(f_in.read())
    print(f"Deployed URL saved to: {save_path}")
    # 4. Read and return the URL
    with open(save_path, "r") as f:
        url = f.read().strip()
    print(f"Deployed URL: {url}")
    return url

# Example usage:
if __name__ == "__main__":
    repo = os.getenv("GITHUB_REPO")
    workflow_file = "deploy-agent.yml"
    ref = os.getenv("GITHUB_REF")
    agent_file = f"agents/pydantic_ai/pydantic-ai-8bdc0c9f-9b05.py"
    sha = "c4366c71fb0ac0e500e09b73dc3c210bf3a1980a"
    inputs = {
    "sha": "c4366c71fb0ac0e500e09b73dc3c210bf3a1980a",
    "agent_file": "agents/pydantic_ai/pydantic-ai-8bdc0c9f-9b05.py",
    "framework": "pydantic_ai"
}
    run_id = trigger_github_workflow(repo, workflow_file, ref, inputs)
    print(f"Workflow run ID: {run_id}")
    url = download_deployed_url_artifact(repo, run_id, inputs["framework"], inputs["agent_file"])
    if url:
        print(f"Deployed at: {url}")