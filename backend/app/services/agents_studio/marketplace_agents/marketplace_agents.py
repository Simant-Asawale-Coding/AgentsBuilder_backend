"""
Module: marketplace_agents.py

Provides a function to fetch all marketplace agents from the database, including their image URLs from Azure Blob Storage.
"""
import os
from typing import List, Dict, Any
from azure.storage.blob import BlobServiceClient
from ...database import database
from app.utils.configuration.appsettings import AppSettings
import base64

# Azure Blob Storage configuration (should be set as environment variables for security)
AZURE_CONNECTION_STRING = AppSettings().AZURE_BLOB_CONNECTION_STRING
AGENTS_CONTAINER_NAME = AppSettings().AZURE_AGENTS_CONTAINER_NAME

def fetch_all_marketplace_agents_with_images() -> List[Dict[str, Any]]:
    """
    Fetch all agents from the marketplace_agents table and attach their image as base64 from Azure Blob Storage.
    Returns:
        List of agents, each as a dict with an 'image_base64' key added (None if not found).
    """
    agents = database.fetch_all_marketplace_agents()
    if not AZURE_CONNECTION_STRING:
        raise EnvironmentError("Azure Storage connection string not set in environment variables.")
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(AGENTS_CONTAINER_NAME)

    # Try fetching each agent's image with no extension, then .png, .jpg, .jpeg, .webp
    for agent in agents:
        agent_id = agent.get('agent_id')
        image_base64 = None
        found = False
        for ext in ["", ".png", ".jpg", ".jpeg", ".webp"]:
            try:
                blob_client = container_client.get_blob_client(agent_id + ext)
                image_bytes = blob_client.download_blob().readall()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                found = True
                break
            except Exception:
                continue
        agent['image_base64'] = image_base64
    return agents


if __name__ == "__main__":
    try:
        agents = fetch_all_marketplace_agents_with_images()
        from pprint import pprint
        print("Fetched marketplace agents with images:")
        pprint(agents)
    except Exception as e:
        print(f"Error: {e}")





#  {'agent_id': 'agent-003',
#   'chat_enabled': True,
#   'creds_schema': '{"image_url": "string"}',
#   'description': 'Analyzes and describes images.',
#   'details': 'Detects objects and text in images.',
#   'framework': 'pydantic-ai',
#   'image_base64': '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',
#   'name': 'Vision Inspector',
#   'soft_delete': False,
#   'system_prompt': 'You are an image analysis agent.',
#   'tools': '["tool-003"]',
#   'tools_data': [{'admin_id': '1',
#                   'creds_schema': '{"image_url": "string"}',
#                   'description': 'Analyzes images for objects and text.',
#                   'name': 'Image Analyzer',
#                   'sha': 'sha3',
#                   'soft_delete': False,
#                   'tool_details': 'Details about Image Analyzer',
#                   'tool_id': 'tool-003'}],
#   'workflow_enabled': False}]