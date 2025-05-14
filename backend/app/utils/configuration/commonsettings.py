import os
from typing import List
from azure.appconfiguration.provider import (
    AzureAppConfigurationKeyVaultOptions,
    SettingSelector,
    load,
)
from azure.core.exceptions import ServiceRequestError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class BaseAppSettings(BaseSettings):
    """Base class for application settings"""

    def __init__(
        self,
        appconfig_endpoint: str,
        appconfig_connectionstring: str,
        appconfig_label_filters: List[str] = [],
        env_file_path: str = None,
    ):
        """
        Initializes a new instance of the BaseAppSettings class.
        Args:
            appconfig_endpoint (str): The endpoint of the Azure App Configuration.
            appconfig_connectionstring (str): The connection string of the Azure App Configuration.
            appconfig_label_filters (List[str], optional): A list of label filters for the Azure App Configuration. Defaults to [].
            env_file_path (str, optional): The path to the environment file. Defaults to None.
        """
        appconfig_data = self.load_appconfig_data(
            appconfig_endpoint=appconfig_endpoint,
            appconfig_connectionstring=appconfig_connectionstring,
            appconfig_label_filters=appconfig_label_filters,
        )
        print("APPconfig_data", appconfig_data)
        transformed_values = self.transform_appconfig_data(appconfig_data)
        values = self.__override_with_env(transformed_values, env_file_path)
        super().__init__(**values)        
        values = dict(values)
        #super().__init__(**values)

    def __env_values(self, env_file_path: str) -> dict:
        """Override the values dictionary with values from the .env file."""
        load_dotenv(dotenv_path=env_file_path)
        values = dict(os.environ).items()
        return values

    def __override_with_env(self, values: dict, env_file_path: str) -> dict:
        """Override the values dictionary with values from the .env file."""
        load_dotenv(dotenv_path=env_file_path)
        env_vars = {k.lower(): v for k, v in dict(os.environ).items()}
        for key in values.keys():
            if key.lower() in env_vars:
                values[key] = env_vars[key]
        return values

    @retry(
        wait=wait_exponential(),
        retry=retry_if_exception_type(ServiceRequestError),
        stop=stop_after_attempt(6),
    )
    def load_appconfig_data(
        self,
        appconfig_endpoint: str = None,
        appconfig_connectionstring: str = None,
        appconfig_label_filters: List[str] = [],
    ) -> dict:
        # credential = DefaultAzureCredential()
        # key_vault_options = AzureAppConfigurationKeyVaultOptions(credential=credential)

        selects: SettingSelector = []
        for label_filter in appconfig_label_filters:
            selects.append(SettingSelector(
                key_filter="*", label_filter=label_filter))

        appconfig_data = load(
            connection_string=appconfig_connectionstring,
            # key_vault_options=key_vault_options,
            selects=selects,
        )
        return appconfig_data

    def transform_appconfig_data(
        self, appconfig_data: dict, from_token: str = ":", to_token: str = "_"
    ) -> dict:
        """Transform application configuration keys to pydantic model settings"""
        return {
            key.replace(from_token, to_token).lower(): value
            for key, value in appconfig_data.items()
        }
