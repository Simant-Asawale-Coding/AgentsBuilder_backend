import os
from azure.appconfiguration import AzureAppConfigurationClient
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
# Get Azure App Configuration connection string
connection_string = os.getenv("APPCONFIGURATION_CONNECTIONSTRING","Endpoint=https://agents-builder-app-config.azconfig.io;Id=HTIL;Secret=CqSfSRB6toHJYmWozz0XAet8tqSFUyLPw66osOnxdQ5be9YDtiE6JQQJ99BEACYeBjFdkwbiAAACAZAC337W")

if not connection_string:
    raise ValueError("APPCONFIGURATION_CONNECTIONSTRING is missing! Set it in environment variables.")

# Initialize Azure App Configuration client
client = AzureAppConfigurationClient.from_connection_string(connection_string)

def get_config_value(key, label=None):
    """Fetch configuration values from Azure App Configuration. Handles key formatting and labels."""
    azure_key = key.replace("_", ":")  # Convert Python-style keys to Azure's format
    try:
        setting = client.get_configuration_setting(key=azure_key, label=label)
        if setting is None or setting.value is None:
            raise ValueError(f"Configuration key '{azure_key}' with label '{label}' not found in Azure App Configuration.")
        return setting.value
    except Exception as e:
        raise ValueError(f"Error retrieving key '{azure_key}' with label '{label}': {str(e)}")

class AppSettings(BaseSettings):
    """Application settings for AgentsBuilder"""

    # AgentsBuilder MSSQL settings
    agentsbuilder_mssqlconnectionstring: str = get_config_value("agentsbuilder:dbconnectionstring", label="mssql")
    
    #AgentsBuilder Github settings
    GITHUB_TOKEN: str = get_config_value("agentsbuilder:githubtoken", label="github")
    GITHUB_REPO: str = get_config_value("agentsbuilder:repo", label="github")
    GITHUB_REF: str = get_config_value("agentsbuilder:ref", label="github")
    GITHUB_REPO_URL: str = get_config_value("agentsbuilder:repourl", label="github")

    
    #AgentsBuilder Azure Blob Storage settings
    AZURE_BLOB_CONNECTION_STRING: str = get_config_value("agentsbuilder:azureblobconnectionstring", label="azure")
    AZURE_AGENTS_CONTAINER_NAME: str = get_config_value("agentsbuilder:azureagentscontainername", label="azure")
    AZURE_TOOLS_CONTAINER_NAME: str = get_config_value("agentsbuilder:azuretoolscontainername", label="azure")
    AZURE_WORKFLOWS_CONTAINER_NAME: str = get_config_value("agentsbuilder:azureworkflowscontainername", label="azure")
    AZURE_LOGS_CONTAINER_NAME: str = get_config_value("agentsbuilder:azurelogscontainername", label="azure")