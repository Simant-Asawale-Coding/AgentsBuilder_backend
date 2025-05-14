import os
from azure.appconfiguration import AzureAppConfigurationClient
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env (for local development)
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

# Get Azure App Configuration connection string
connection_string = os.getenv("APPCONFIGURATION_CONNECTIONSTRING")

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
    """Application settings for configuring Azure OpenAI, HuggingFace embeddings, LlamaParse, and Azure Blob Storage."""

    # AgentsBuilder MSSQL settings
    agentsbuilder_mssqlserver: str = get_config_value("agentsbuilder:mssqlserver", label="agentsbuilder")
    agentsbuilder_mssqldatabase: str = get_config_value("agentsbuilder:mssqldatabase", label="agentsbuilder")
    agentsbuilder_mssqlport: int = get_config_value("agentsbuilder:mssqlport", label="agentsbuilder")
    agentsbuilder_mssqluser: str = get_config_value("agentsbuilder:mssqluser", label="agentsbuilder")
    agentsbuilder_mssqlpassword: str = get_config_value("agentsbuilder:mssqlpassword", label="agentsbuilder")
    agentsbuilder_mssqldriver: str = get_config_value("agentsbuilder:mssqldriver", label="agentsbuilder")
    agentsbuilder_user_table_name: str = get_config_value("agentsbuilder:usertablename", label="agentsbuilder")
    agentsbuilder_user_agents_table_name: str = get_config_value("agentsbuilder:useragentstablename", label="agentsbuilder")
    agents_builder_agents_table_name: str = get_config_value("agentsbuilder:agentstablename", label="agentsbuilder")

    #AgentsBuilder Github settings
    GITHUB_TOKEN: str = get_config_value("agentsbuilder:githubtoken", label="agentsbuilder")
    GITHUB_REPO: str = get_config_value("agentsbuilder:repo", label="agentsbuilder")
    GITHUB_REF: str = get_config_value("agentsbuilder:ref", label="agentsbuilder")
    GITHUB_REPO_URL: str = get_config_value("agentsbuilder:repourl", label="agentsbuilder")


    

