import os
from azure.appconfiguration import AzureAppConfigurationClient
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
# Get Azure App Configuration connection string
connection_string = os.getenv("APPCONFIGURATION_CONNECTIONSTRING")

if not connection_string:
    raise ValueError("APPCONFIGURATION_CONNECTIONSTRING is missing! Set it in environment variables.")

# Initialize Azure App Configuration client
client = AzureAppConfigurationClient.from_connection_string("Endpoint=https://agents-builder-app-config.azconfig.io;Id=HTIL;Secret=CqSfSRB6toHJYmWozz0XAet8tqSFUyLPw66osOnxdQ5be9YDtiE6JQQJ99BEACYeBjFdkwbiAAACAZAC337W")
print("Endpoint=https://agents-builder-app-config.azconfig.io;Id=HTIL;Secret=CqSfSRB6toHJYmWozz0XAet8tqSFUyLPw66osOnxdQ5be9YDtiE6JQQJ99BEACYeBjFdkwbiAAACAZAC337W")

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
    

    #AgentsBuilder MSSQL Tables
    agentsbuilder_user_table_name: str = get_config_value("agentsbuilder:userstable", label="database")
    agentsbuilder_user_agents_table_name: str = get_config_value("agentsbuilder:useragentstable", label="database")
    agentsbuilder_user_tools_table_name: str = get_config_value("agentsbuilder:usertoolstable", label="database")
    agentsbuilder_agents_table_name: str = get_config_value("agentsbuilder:agentstable", label="database")
    agentsbuilder_marketplace_tools_table_name: str = get_config_value("agentsbuilder:marketplacetoolstable", label="database")
    agentsbuilder_custom_tools_table_name: str = get_config_value("agentsbuilder:customtoolstable", label="database")

    #AgentsBuilder Github settings
    GITHUB_TOKEN: str = get_config_value("agentsbuilder:githubtoken", label="github")
    GITHUB_REPO: str = get_config_value("agentsbuilder:repo", label="github")
    GITHUB_REF: str = get_config_value("agentsbuilder:ref", label="github")
    GITHUB_REPO_URL: str = get_config_value("agentsbuilder:repourl", label="github")


    

