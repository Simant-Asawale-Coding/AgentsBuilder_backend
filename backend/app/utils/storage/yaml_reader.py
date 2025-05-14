import yaml
from applogging.logger import ApplicationLogger
from blob_container_connector import AzureBlobContainerConnector

class AzureYamlReader:
    def __init__(self, reader: AzureBlobContainerConnector):
        """
        Initializes an instance of the AzureYamlReader class.
        Args:
            reader (AzureBlobContainerConnector): The Azure blob container connector to be used for reading YAML files.  
        """
        self.__cloud_blob_connector = reader

    def read_yaml(self, file_name, container_name):
        """
        Reads a YAML file from a cloud container and returns its contents as a Python object.
        Args:
            file_name (str): The name of the YAML file to be read.
            container_name (str): The name of the cloud container where the YAML file is stored.
        Returns:
            object: The contents of the YAML file as a Python object.
        """
        # def read_yaml(self, file_name: str, container_name: str) -> str:
        bytes_obj = self.__cloud_blob_connector.load_file_as_bytes(
            file_name=file_name, container_name=container_name
        )
        # Get the byte string from the BytesIO object
        byte_str = bytes_obj.getvalue()
        # Decode the bytes object to a string
        decoded_str = byte_str.decode("utf-8")
        # Load the string as a YAML document
        return yaml.safe_load(decoded_str)


class YamlReader:
    __readers_dict = {AzureBlobContainerConnector: AzureYamlReader}

    def __init__(self, reader):
        """
        Initializes an instance of the YamlReader class.        
        Args:
            reader: The reader object to be used for reading YAML files.      
        """
        self._yaml_reader = None
        if type(reader) in self.__readers_dict:
            self._yaml_reader = self.__readers_dict[type(reader)](reader)
        else:
            raise Exception(f"Unknown reader type [{type(reader) }]")

    def read_from_yaml_to_dict(self, **kwargs):
        """
        Reads a YAML file and returns its contents as a dictionary.        
        Args:
            **kwargs: Keyword arguments to be passed to the underlying YAML reader.        
        Returns:
            dict: The contents of the YAML file as a dictionary.
        """
        return self._yaml_reader.read_yaml(**kwargs)
