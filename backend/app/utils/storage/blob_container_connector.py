import io
import json
import os
from pathlib import Path
from typing import Dict, List, Union
from azure.core.exceptions import ServiceRequestError
from azure.storage.blob import BlobServiceClient
from applogging.logger import ApplicationLogger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class AzureBlobContainerConnector:
    """Connects to Azure Blob Storage and can retrieve and upload files.

    Args:
        connection_string (str): Connection string to access Azure Blob Storage
        logger (ApplicationLogger): The Application Logger

    Attributes:
        container_name (str): Name of the container in Azure Blob Storage
        _connection_string (str): Connection string to access Azure Blob Storage
        blob_service_client (BlobServiceClient): Azure Blob Service Client

    Functions:
        _get_blob_service_client: Returns a BlobServiceClient
        _get_container_client: Returns a ContainerClient
        get_file_names: Returns a list of file names that are in the container
        get_file: Downloads a file from the container
        upload_file: Uploads a file to the container
        upload_content_as_stream: Upload bytes array.
    """
    def __init__(self, connection_string: str, logger: ApplicationLogger) -> None:
        self.__logger = logger
        self._connection_string = connection_string

        # Azure Blob Clients for accessing the container
        self.blob_service_client = self._get_blob_service_client()

    def _get_blob_service_client(self) -> BlobServiceClient:
        """Returns a BlobServiceClient"""
        return BlobServiceClient.from_connection_string(self._connection_string)

    def get_file_names(self, container_name: str) -> List[str]:
        """Returns a list of file names that are in the container"""
        container_client = self.blob_service_client.get_container_client(container_name)
        return [blob.name for blob in container_client.list_blobs()]

    def download_file(
        self, file_name: str, output_dir: str, container_name: str
    ) -> Path:
        """Downloads a file from the container into the output directory.

        Args:
            file_name (str): Name of the file to retrieve
            output_dir (str): Directory to save the file to

        Returns:
            Path: Full path to the file
        """

        # create output directory if it does not exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file_path = os.path.join(output_dir, file_name)

        # create blob_client to download the file
        blob_client = self.blob_service_client.get_blob_client(
            container_name, blob=file_name
        )
        with open(file_path, "wb") as file:
            file.write(blob_client.download_blob().readall())

        # return the file path for reference / access
        return file_path    

    def upload_file_from_local_path(
        self,
        file_path: str,
        container_name: str,
        upload_msg: str = None,
        overwrite: bool = True,
    ) -> None:
        """Uploads a file to the blob container

        Args:
            file_path (str): Full path and file name to the file to upload
            upload_msg (str, optional): Message to print to console when uploading the file. Defaults to None.
            overwrite (bool, optional): Whether to overwrite the file if it already exists. Defaults to True.
        """

        # create blob_client to upload the file
        file_name = os.path.basename(file_path)  # remove the path from the file name
        blob_client = self.blob_service_client.get_blob_client(
            container_name, blob=file_name
        )

        # print upload message to console
        if upload_msg:
            self.__logger.debug(upload_msg)
        else:
            self.__logger.debug(
                f"Uploading to Azure Storage ({container_name}) as blob:\n\t"
                + file_name
            )

        # upload the file
        with open(file=file_path, mode="rb") as file:
            blob_client.upload_blob(file, overwrite=overwrite)
       
    def archivefiles_to_container(self, batch: list,source_container_name:str, destination_container_name:str):    
        """
        Archives files from a source container to a destination container in Azure Blob Storage.        
        Args:
            batch (list): A list of blob names to be archived.
            source_container_name (str): The name of the source container.
            destination_container_name (str): The name of the destination container.    
        """   
        # Get source and destination container clients
        source_container_client = self.blob_service_client.get_container_client(source_container_name)
        destination_container_client = self.blob_service_client.get_container_client(destination_container_name)

        # Move each blob from the source container to the destination container
        for blob in batch:
            source_blob_client = source_container_client.get_blob_client(blob)
            destination_blob_client = destination_container_client.get_blob_client(blob)
            destination_blob_client.start_copy_from_url(source_blob_client.url)
            source_blob_client.delete_blob()

   
