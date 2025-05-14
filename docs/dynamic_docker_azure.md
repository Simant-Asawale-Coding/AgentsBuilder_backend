# Dynamic Docker Image Generation and Hosting on Azure: A Step-by-Step Guide

This documentation provides a comprehensive, production-grade workflow for dynamically building, pushing, and hosting Docker images for agent tool servers on Azure. It is tailored for scenarios where your backend API receives code uploads, builds and deploys the container, and returns a secure HTTPS endpoint for consumption.

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Prerequisites](#prerequisites)
4. [End-to-End Workflow](#end-to-end-workflow)
5. [Backend API Implementation](#backend-api-implementation)
6. [Azure CLI and SDK References](#azure-cli-and-sdk-references)
7. [Security & Best Practices](#security--best-practices)
8. [Cleanup and Cost Management](#cleanup-and-cost-management)
9. [Further Reading](#further-reading)

---

## Overview

This workflow enables you to:
- Accept code and dependency uploads via a web UI or API.
- Dynamically generate a Docker image for the uploaded code.
- Push the image to Azure Container Registry (ACR).
- Deploy the image to Azure Container Apps (or Web App for Containers).
- Expose the service over HTTPS and return the endpoint to the user/UI.

---

## Architecture Diagram

```
[User/UI] → [Backend API (FastAPI)] → [Docker Build] → [Push to ACR] → [Azure Container Apps] → [HTTPS Endpoint]
```

---

## Prerequisites
- Azure Subscription
- Azure CLI installed and authenticated (`az login`)
- Docker installed and running
- Python 3.8+
- Azure Container Registry (ACR) created (e.g., `myacr.azurecr.io`)
- Azure Container Apps environment set up
- Service Principal or Managed Identity for automation (recommended)

---

## End-to-End Workflow

1. **User uploads code and requirements via UI or API.**
2. **Backend API**:
    - Saves files to a temporary directory.
    - Generates a Dockerfile dynamically.
    - Builds Docker image using Docker SDK for Python.
    - Authenticates and pushes the image to Azure Container Registry.
    - Deploys a new Azure Container App using the pushed image.
    - Retrieves the HTTPS endpoint from Azure and returns it to the UI.

---

## Backend API Implementation (Python/FastAPI)

### Install Dependencies
```bash
pip install fastapi uvicorn docker azure-identity azure-mgmt-containerregistry azure-mgmt-resource azure-mgmt-containerapp
```

### Example API Endpoint (Simplified)
```python
from fastapi import FastAPI, UploadFile, Form
import docker
import os
import tempfile
import subprocess

app = FastAPI()
DOCKER_REGISTRY = "myacr.azurecr.io"
IMAGE_NAME = "myimage"
RESOURCE_GROUP = "my-resource-group"
CONTAINERAPPS_ENVIRONMENT = "my-containerapps-env"
LOCATION = "eastus"

@app.post("/build-deploy/")
async def build_and_deploy(code: UploadFile, requirements: UploadFile, entrypoint: str = Form(...)):
    # 1. Save uploaded files to a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, code.filename)
        req_path = os.path.join(tmpdir, requirements.filename)
        with open(code_path, "wb") as f:
            f.write(await code.read())
        with open(req_path, "wb") as f:
            f.write(await requirements.read())
        # Write Dockerfile
        dockerfile_content = f"""
        FROM python:3.11-slim
        WORKDIR /app
        COPY . /app
        RUN pip install --no-cache-dir -r {requirements.filename}
        EXPOSE 8000
        CMD [\"python\", \"{entrypoint}\"]
        """
        with open(os.path.join(tmpdir, "Dockerfile"), "w") as df:
            df.write(dockerfile_content)
        # 2. Build Docker image
        client = docker.from_env()
        image_tag = f"{DOCKER_REGISTRY}/{IMAGE_NAME}:latest"
        image, logs = client.images.build(path=tmpdir, tag=image_tag)
        # 3. Login to ACR and push image
        subprocess.run(["az", "acr", "login", "--name", DOCKER_REGISTRY.split(".")[0]], check=True)
        client.images.push(image_tag)
        # 4. Deploy to Azure Container Apps (using Azure CLI for simplicity)
        subprocess.run([
            "az", "containerapp", "create",
            "--name", IMAGE_NAME,
            "--resource-group", RESOURCE_GROUP,
            "--environment", CONTAINERAPPS_ENVIRONMENT,
            "--image", image_tag,
            "--target-port", "8000",
            "--ingress", "external",
            "--registry-server", DOCKER_REGISTRY
        ], check=True)
        # 5. Get HTTPS endpoint
        result = subprocess.run([
            "az", "containerapp", "show",
            "--name", IMAGE_NAME,
            "--resource-group", RESOURCE_GROUP,
            "--query", "properties.configuration.ingress.fqdn",
            "--output", "tsv"
        ], capture_output=True, text=True, check=True)
        endpoint = "https://" + result.stdout.strip()
        return {"endpoint": endpoint}
```

**Key Points:**
- All Azure CLI commands can be replaced with Azure SDK calls for production.
- Use Managed Identity or Service Principal for automation (avoid hardcoding credentials).
- Clean up unused resources to save costs.

---

## Azure CLI and SDK References
- [Build and push Docker images to Azure Container Registry with Python](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-python)
- [Deploy a container app from an Azure Container Registry image](https://learn.microsoft.com/en-us/azure/container-apps/get-started?tabs=bash)
- [Azure CLI: az containerapp create](https://learn.microsoft.com/en-us/cli/azure/containerapp?view=azure-cli-latest#az-containerapp-create)
- [Azure Container Apps Ingress and HTTPS](https://learn.microsoft.com/en-us/azure/container-apps/ingress)

---

## Security & Best Practices
- **Authentication**: Use Azure Managed Identity or Service Principal for automation.
- **Validation**: Sanitize and validate all user uploads.
- **Resource Cleanup**: Remove unused images and container apps to avoid unnecessary costs.
- **Monitoring**: Enable logging and monitoring for all deployments.
- **HTTPS**: Azure Container Apps provides HTTPS endpoints by default.

---

## Cleanup and Cost Management
- Delete unused container apps:
  ```bash
  az containerapp delete --name <app-name> --resource-group <resource-group>
  ```
- Delete unused images from ACR via Azure Portal or CLI.

---

## Further Reading
- [Azure Container Registry Documentation](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/)
- [Azure CLI Documentation](https://learn.microsoft.com/en-us/cli/azure/)

---

This guide provides a robust foundation for dynamic, secure, and scalable Docker-based deployments on Azure. For advanced automation, CI/CD, and multi-tenant scenarios, refer to Azure DevOps or GitHub Actions integrations.
