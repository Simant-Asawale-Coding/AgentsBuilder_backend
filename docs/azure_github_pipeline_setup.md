# Comprehensive Guide: Setting Up Azure Container Apps Deployment Pipeline with GitHub Actions

This guide documents the entire process of building a DevOps pipeline to deploy Python agent applications to Azure Container Apps using GitHub Actions. It covers everything from Azure credential setup, service principal creation, registry configuration, workflow YAML authoring, and containerization rules. This is based on a real-world setup where I (Cascade, your AI assistant) helped configure and troubleshoot the pipeline from scratch.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure Setup](#azure-setup)
   - [Create Resource Group](#create-resource-group)
   - [Create Azure Container Registry (ACR)](#create-azure-container-registry-acr)
   - [Create Azure Container Apps Environment](#create-azure-container-apps-environment)
   - [Create Service Principal & Credentials](#create-service-principal--credentials)
   - [Fetch ACR Credentials](#fetch-acr-credentials)
3. [GitHub Repository Setup](#github-repository-setup)
   - [Configure Secrets](#configure-secrets)
4. [Python Project Structure](#python-project-structure)
5. [GitHub Actions Workflow](#github-actions-workflow)
   - [Sample deploy-agent.yaml](#sample-deploy-agentyaml)
   - [Key Workflow Steps Explained](#key-workflow-steps-explained)
6. [Containerization Rules](#containerization-rules)
7. [Troubleshooting & Best Practices](#troubleshooting--best-practices)
8. [References](#references)

---

## 1. Prerequisites
- Azure subscription
- GitHub account
- Python project with agent scripts and requirements.txt
- Docker installed (for local testing)

---

## 2. Azure Setup

### Create Resource Group
```sh
az group create --name <RESOURCE_GROUP_NAME> --location <LOCATION>
```

### Create Azure Container Registry (ACR)
```sh
az acr create --resource-group <RESOURCE_GROUP_NAME> --name <ACR_NAME> --sku Basic --admin-enabled true
```

### Create Azure Container Apps Environment
```sh
az containerapp env create \
  --name <ENVIRONMENT_NAME> \
  --resource-group <RESOURCE_GROUP_NAME> \
  --location <LOCATION>
```

### Create Service Principal & Credentials (for GitHub Actions)
```sh
az ad sp create-for-rbac --name "github-actions-pipeline" --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP_NAME> \
  --sdk-auth
```
- Save the output JSON; use it as `AZURE_CREDENTIALS` in GitHub Secrets.

### Fetch ACR Credentials (for image push/pull)
Enable admin user for ACR:
```sh
az acr update --name <ACR_NAME> --admin-enabled true
az acr credential show --name <ACR_NAME>
```
- Use the returned username and password as `AZURE_ACR_USERNAME` and `AZURE_ACR_PASSWORD` in GitHub Secrets.
- The registry server will be `<ACR_NAME>.azurecr.io`.

---

## 3. GitHub Repository Setup

### Configure Secrets
Go to your repository → Settings → Secrets and variables → Actions → New repository secret. Add:
- `AZURE_CREDENTIALS` (output from service principal creation)
- `AZURE_RESOURCE_GROUP`
- `AZURE_CONTAINER_REGISTRY` (e.g., myacr.azurecr.io)
- `AZURE_ACR_USERNAME`
- `AZURE_ACR_PASSWORD`
- `AZURE_CONTAINERAPPS_ENVIRONMENT` (resource ID from env creation)

---

## 4. Python Project Structure
```
Agent Builder/
├── agents/                # Agent scripts pushed to GitHub
├── agents_templates/agno/requirements.txt
├── backend/app/services/github_push.py
├── docs/
└── ...
```

---

## 5. GitHub Actions Workflow

### Sample deploy-agent.yaml
Place this in `.github/workflows/deploy-agent.yaml`:
```yaml
name: Deploy Agent to Azure Container Apps

on:
  push:
    paths:
      - 'agents/**'
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Find latest agent file in repo
        id: detect
        run: |
          AGENT_FILE=$(git log -1 --pretty=format: --name-only --diff-filter=AM -- agents/*.py | head -n 1)
          echo "AGENT_FILE=$AGENT_FILE" >> $GITHUB_ENV
          AGENT_DIR=$(dirname "$AGENT_FILE")
          echo "AGENT_DIR=$AGENT_DIR" >> $GITHUB_ENV
          AGENT_NAME=$(basename "$AGENT_FILE" .py)
          echo "AGENT_NAME=$AGENT_NAME" >> $GITHUB_ENV
          echo "Detected agent file: $AGENT_FILE in $AGENT_DIR"

      - name: Build and Push Docker image
        run: |
          cd $AGENT_DIR
          echo -e "FROM python:3.10-slim\nCOPY . /app\nWORKDIR /app\nRUN pip install -r requirements.txt\nCMD [\"python\", \"$(basename $AGENT_FILE)\"]" > Dockerfile
          docker build -t ${{ secrets.AZURE_CONTAINER_REGISTRY }}/$AGENT_NAME:${{ github.sha }} -t ${{ secrets.AZURE_CONTAINER_REGISTRY }}/$AGENT_NAME:latest .
          echo ${{ secrets.AZURE_ACR_PASSWORD }} | docker login ${{ secrets.AZURE_CONTAINER_REGISTRY }} -u ${{ secrets.AZURE_ACR_USERNAME }} --password-stdin
          docker push ${{ secrets.AZURE_CONTAINER_REGISTRY }}/$AGENT_NAME:${{ github.sha }}
          docker push ${{ secrets.AZURE_CONTAINER_REGISTRY }}/$AGENT_NAME:latest

      - name: Create or Update Azure Container App
        run: |
          set -e
          EXISTING_APP=$(az containerapp show --name $AGENT_NAME --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} --query name -o tsv || echo "")
          if [ -z "$EXISTING_APP" ]; then
            az containerapp create \
              --name $AGENT_NAME \
              --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
              --image ${{ secrets.AZURE_CONTAINER_REGISTRY }}/$AGENT_NAME:${{ github.sha }} \
              --environment ${{ secrets.AZURE_CONTAINERAPPS_ENVIRONMENT }} \
              --ingress external --target-port 8005 \
              --registry-server ${{ secrets.AZURE_CONTAINER_REGISTRY }} \
              --registry-username ${{ secrets.AZURE_ACR_USERNAME }} \
              --registry-password ${{ secrets.AZURE_ACR_PASSWORD }}
          else
            az containerapp update \
              --name $AGENT_NAME \
              --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
              --image ${{ secrets.AZURE_CONTAINER_REGISTRY }}/$AGENT_NAME:${{ github.sha }}
          fi
          APP_URL=$(az containerapp show --name $AGENT_NAME --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} --query properties.configuration.ingress.fqdn -o tsv)
          echo "DEPLOYED_URL=https://$APP_URL"
```

#### Key Points:
- The workflow is triggered on changes to `agents/**` or manually.
- It finds the latest changed agent script using Git history.
- Docker images are tagged with both `latest` and `${{ github.sha }}`.
- The container app is created or updated as needed.
- The correct port (`8005` or as used by your app) is specified in `--target-port`.

---

## 6. Containerization Rules
- Ensure `requirements.txt` includes **all** dependencies (e.g., `openai`, `fastapi`, `uvicorn`, etc.).
- The agent script and `requirements.txt` must both be present in the build context (i.e., the same directory).
- The Dockerfile must set the correct working directory and entrypoint.
- The app inside the container must listen on the port specified by `--target-port` (e.g., 8005).

---

## 7. Troubleshooting & Best Practices
- **Image not found:** Ensure both `docker build` and `docker push` use the correct tag (`:${{ github.sha }}`).
- **Unauthorized image pull:** Double-check ACR credentials and registry server format.
- **Container exits/crashes:** Check Azure logs for Python errors, missing packages, or port mismatches.
- **Probe failures:** Ensure the app listens on the same port as `--target-port`.
- **Old files detected:** Use Git history, not filesystem timestamps, to detect the latest file.
- **Deleting obsolete agents:** Remove old agent files from the repo to avoid confusion.

---

## 8. References
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
- [GitHub Actions for Azure](https://github.com/azure/login)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

---

_This documentation was generated by Cascade, your AI DevOps assistant, based on a real project pipeline setup._
