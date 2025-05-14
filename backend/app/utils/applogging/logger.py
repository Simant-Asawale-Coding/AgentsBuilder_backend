import logging
import os
import atexit
from logging.handlers import RotatingFileHandler
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from app.utils.configuration.appsettings import AppSettings
from colorama import Fore
from typing import Dict, Any
from contextlib import contextmanager
import time
#import signal

class AzureBlobHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = "app/data/logs"
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create session-specific log file
        self.log_file_path = os.path.join(
            self.log_dir, 
            f"application_{self.session_id}.log"
        )
        
        # Initialize blob client and ensure container exists
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.settings.docsextractor_storageconnectionstring
        )
        self.container_name = self.settings.docsextractor_logscontainername
        self._ensure_container_exists()
        
        # Register cleanup method to run at exit
        atexit.register(self.upload_to_blob)
        
        # Register signal handler for SIGTERM
        #signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal"""
        self.upload_to_blob()
        # Optionally, you can add any other cleanup code here
        os._exit(0)

    def _ensure_container_exists(self) -> None:
        """Ensure blob container exists"""
        container_client = self.blob_service_client.get_container_client(self.container_name)
        if not container_client.exists():
            container_client.create_container()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record"""
        try:
            msg = self.format(record)
            # Write to local file using context manager
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception as e:
            print(f"Failed to write log to file: {str(e)}")
            self.handleError(record)

    def upload_to_blob(self) -> None:
        """Upload local log file to Azure Blob Storage when session ends"""
        try:
            if not os.path.exists(self.log_file_path):
                print(f"Log file not found: {self.log_file_path}")
                return

            # Read local log file
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()

            if not log_content:
                print("Log file is empty, skipping upload")
                return

            # Create container client
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Ensure container exists
            if not container_client.exists():
                container_client.create_container()
                print(f"Created container: {self.container_name}")

            # Create blob name with date-based folder structure
            date_folder = datetime.now().strftime("%Y%m%d")
            blob_name = f"{date_folder}/session_{self.session_id}.log"
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)

            # Upload to blob storage with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    blob_client.upload_blob(
                        log_content,
                        blob_type="BlockBlob",
                        overwrite=True
                    )
                    print(f"Successfully uploaded logs to blob storage: {blob_name}")
                    break
                except Exception as upload_error:
                    if attempt == max_retries - 1:  # Last attempt
                        raise upload_error
                    print(f"Upload attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)  # Wait before retry

            # Optionally cleanup local file
            # os.remove(self.log_file_path)
            
        except Exception as e:
            print(f"Failed to upload logs to blob storage: {str(e)}")
            raise  # Re-raise the exception for proper error handling
        finally:
            try:
                self.blob_service_client.close()
            except:
                pass  # Ignore errors during cleanup

class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, 'custom_dimensions'):
            record.custom_dimensions = {}
        return super().format(record)

class ApplicationLogger:
    _instance = None
    _initialized = False

    def __new__(cls) -> 'ApplicationLogger':
        if cls._instance is None:
            cls._instance = super(ApplicationLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, 
                 level: int = logging.DEBUG, 
                 max_bytes: int = 20 * 1024 * 1024,
                 backup_count: int = 5):
        if self._initialized:
            return
            
        self._initialized = True
        self.__logger = logging.getLogger('app.logger')
        self.__logger.setLevel(level)
        self.__role_name = None
        
        # Prevent duplicate handlers
        if not self.__logger.handlers:
            # Console handler setup only
            console_handler = logging.StreamHandler()
            console_formatter = CustomFormatter(
                "%(asctime)s [%(levelname)s]: %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.__logger.addHandler(console_handler)

            # Configure Azure Blob Storage handler automatically
            self.configure_blob_storage()

    def configure_blob_storage(self) -> None:
        """Configure Azure Blob Storage handler using AppSettings"""
        try:
            # Remove any existing blob handlers
            for handler in self.__logger.handlers[:]:
                if isinstance(handler, AzureBlobHandler):
                    self.__logger.removeHandler(handler)

            # Create new blob handler
            blob_handler = AzureBlobHandler()
            blob_formatter = CustomFormatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s\n"
            )
            blob_handler.setFormatter(blob_formatter)
            self.__logger.addHandler(blob_handler)
            self.info(Fore.GREEN + "Azure Blob Storage handler configured successfully" + Fore.RESET)
        except Exception as e:
            self.error(Fore.RED + f"Failed to configure Azure Blob Storage handler: {str(e)}" + Fore.RESET)
            raise

    def _log(self, level: str, message: str, **kwargs: Dict[str, Any]) -> None:
        """Internal logging method"""
        log_func = getattr(self.__logger, level)
        extra = {"custom_dimensions": kwargs} if kwargs else {"custom_dimensions": {}}
        log_func(message, extra=extra)

    def debug(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self._log("debug", message, **kwargs)

    def info(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self._log("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self._log("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self._log("error", message, **kwargs)

    def critical(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self._log("critical", message, **kwargs)

    def exception(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self._log("exception", message, **kwargs)

    def __add_role_name(self, envelope: Dict[str, Any]) -> bool:
        if self.__role_name:
            envelope.tags["ai.cloud.role"] = self.__role_name
        return True