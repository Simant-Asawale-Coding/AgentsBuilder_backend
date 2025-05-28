"""
Module: github_push.py
Pushes generated agent code and requirements.txt to a specified GitHub repository/branch.
"""
import os
import base64
import requests
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

def push_agent_to_github(
    agent_file_path: str,
    framework: str,
    repo_url: str,
    branch: str = "main",
    agents_dir: str = "agents",
    commit_message: Optional[str] = None,
    github_token_env: str = "GITHUB_TOKEN"
) -> str:
    """
    Pushes the agent file to the specified GitHub repo/branch using the GitHub REST API.
    The agent file is uploaded to agents/<framework>/<file.py>.
    Returns the commit SHA of the push.
    """
    import json

    token = os.environ.get(github_token_env)
    if not token:
        raise RuntimeError(f"GitHub token not found in environment variable: {github_token_env}")

    # Parse repo owner/name from repo_url
    parts = repo_url.rstrip(".git").split("/")
    owner = parts[-2]
    repo = parts[-1]

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    def upload_file(local_path: str, remote_path: str):
        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{remote_path}"
        # Get the current file SHA if it exists (for updates)
        params = {"ref": branch}
        resp = requests.get(url, headers=headers, params=params)
        sha = resp.json().get("sha") if resp.status_code == 200 else None
        data = {
            "message": commit_message or f"Add/update {os.path.basename(local_path)}",
            "content": content,
            "branch": branch
        }
        if sha:
            data["sha"] = sha
        response = requests.put(url, headers=headers, json=data)
        if not response.ok:
            raise RuntimeError(f"Failed to upload {remote_path}: {response.status_code} {response.text}")
        return response.json()["commit"]["sha"]

    # Push agent file to agents/<framework>/<file.py>
    agent_filename = os.path.basename(agent_file_path)
    agent_remote_path = f"{agents_dir}/{framework}/{agent_filename}"
    commit_sha = upload_file(agent_file_path, agent_remote_path)

    return commit_sha

if __name__ == "__main__":
    # Simulate pushing the generated agent to GitHub under agents/<framework>/
    agent_file_path = r"D:\Desktop Files\Agent Builder\generated_agents\pydantic-ai-8bdc0c9f-9b05.py"
    framework = "pydantic_ai"
    repo_url = "https://github.com/Simant-Asawale-Coding/AgentsBuilder.git"
    branch = "main"
    try:
        commit_sha = push_agent_to_github(
            agent_file_path=agent_file_path,
            framework=framework,
            repo_url=repo_url,
            branch=branch
        )
        print(f"Pushed agent to GitHub. Commit SHA: {commit_sha}")
    except Exception as e:
        print("[ERROR] Failed to push to GitHub:", e)
