import os
import time
import requests
import re
from dotenv import load_dotenv
load_dotenv()

def extract_containerapp_name(url_or_name):
    if url_or_name.startswith("http"):
        match = re.match(r"https?://([^.]+)\.", url_or_name)
        if match:
            return match.group(1)
        else:
            raise ValueError("Could not extract container app name from URL.")
    return url_or_name


def poll_workflow_run(repo, workflow_file, ref, token, poll_interval=10, timeout=600):
    """
    Polls for the latest completed workflow run for the given workflow file, branch, and event.
    Returns the run_id of the completed run, or raises TimeoutError.
    """
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/runs"
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
                return run_id, conclusion
        if time.time() - start_time > timeout:
            raise TimeoutError("Timed out waiting for workflow to complete.")
        time.sleep(poll_interval)

def trigger_github_workflow(repo, workflow_file, ref, inputs, github_token):
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"ref": ref, "inputs": inputs}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 204:
        raise Exception(f"Failed to trigger workflow: {response.status_code}, {response.text}")
    print("Workflow triggered successfully.")
    # Now, poll for the workflow run
    return poll_workflow_run(repo, workflow_file, ref, github_token)



def download_artifact(repo, run_id, artifact_name, github_token, save_dir="."):
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github+json"}
    url_artifacts = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
    resp = requests.get(url_artifacts, headers=headers)
    artifacts = resp.json().get("artifacts", [])
    artifact = next((a for a in artifacts if a["name"] == artifact_name), None)
    if not artifact:
        print(f"Artifact {artifact_name} not found.")
        return None
    download_url = artifact["archive_download_url"]
    resp = requests.get(download_url, headers=headers)
    zip_path = os.path.join(save_dir, f"{artifact_name}.zip")
    with open(zip_path, "wb") as f:
        f.write(resp.content)
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(save_dir)
    return save_dir


def delete_container_app_via_github(
    repo,
    github_token,
    url_or_name,
    resource_group,
    subscription_id,
    ref="main",
    workflow_file="agent-delete.yml",
    save_dir="."
):
    app_name = extract_containerapp_name(url_or_name)
    inputs = {
        "container_url_or_name": url_or_name,
        "resource_group": resource_group,
        "subscription_id": subscription_id
    }
    run_id, conclusion = trigger_github_workflow(repo, workflow_file, ref, inputs, github_token)
    print(f"Workflow run ID: {run_id}")
    time.sleep(70)
    result_artifact = f"delete-result-{app_name}"
    log_artifact = f"delete-log-{app_name}"
    download_artifact(repo, run_id, result_artifact, github_token, save_dir)
    download_artifact(repo, run_id, log_artifact, github_token, save_dir)
    # Read result.txt for outcome
    result_file = os.path.join(save_dir, "result.txt")
    if os.path.exists(result_file):
        with open(result_file, "r") as f:
            result = f.read().strip()
        print(f"Delete result: {result}")
        return result == "success"
    print("No result.txt found. Deletion status unknown.")
    return False

if __name__ == "__main__":
    # Example usage
    repo = "Simant-Asawale-Coding/AgentsBuilder"  # Change as needed
    github_token = os.environ.get("GITHUB_TOKEN")
    url_or_name = "https://heloworld.wonderfulhill-64c3fbea.eastus.azurecontainerapps.io"
    resource_group = "AgentsBuilder-ResourceGroup"
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID","9b3ab87b-de25-4143-acd1-450bc6810882")
    delete_container_app_via_github(repo, github_token, url_or_name, resource_group, subscription_id)
