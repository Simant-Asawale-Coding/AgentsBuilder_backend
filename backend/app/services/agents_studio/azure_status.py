import os
import time
import requests
import re
import json
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


def get_containerapp_status_via_github(
    repo,
    github_token,
    url_or_name,
    resource_group,
    subscription_id,
    ref="main",
    workflow_file="container-status.yml",
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
    artifact_name = f"status-{app_name}"
    time.sleep(40)  # Wait before fetching artifact
    download_artifact(repo, run_id, artifact_name, github_token, save_dir)
    status_file = os.path.join(save_dir, "status.json")
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            metadata = json.load(f)
        props = metadata.get("properties", {})
        config = props.get("configuration", {})
        ingress = config.get("ingress", {})
        template = props.get("template", {})
        containers = template.get("containers", [{}])
        container_info = containers[0] if containers else {}
        resources = container_info.get("resources", {})
        tags = metadata.get("tags", {})
        errors = props.get("errors", [])
        # Rich status summary
        rich_status = {
            "provisioningState": props.get("provisioningState"),
            "latestRevisionName": props.get("latestRevisionName"),
            "latestReadyRevisionName": props.get("latestReadyRevisionName"),
            "fqdn": ingress.get("fqdn"),
            "ingress": ingress.get("external", "disabled"),
            "container_image": container_info.get("image"),
            "cpu": resources.get("cpu"),
            "memory": resources.get("memory"),
            "createdTime": props.get("createdTime"),
            "environmentId": props.get("environmentId"),
            "tags": tags,
            "errors": errors,
        }
        print("\n--- Azure Container App Status Report ---")
        for k, v in rich_status.items():
            print(f"{k}: {v}")
        print("--- End of Status Report ---\n")
        return metadata, rich_status
    print("No status.json found. Status unknown.")
    return None, None

if __name__ == "__main__":
    repo = "Simant-Asawale-Coding/AgentsBuilder"
    github_token = os.environ.get("GITHUB_TOKEN")
    url_or_name = "https://agno1.politeisland-6a32.eastus.azurecontainerapps.io"
    resource_group = "aressgenai"
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    get_containerapp_status_via_github(repo, github_token, url_or_name, resource_group, subscription_id)
