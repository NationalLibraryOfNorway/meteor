"""Module for utility classes and methods used in FastAPI service"""


# pylint: disable=broad-exception-caught

import traceback
import os
import threading
import uuid
from typing import TypedDict, Optional, Union

import requests
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from metadata_extract.metadata import Results
from metadata_extract.meteor import Meteor
from metadata_extract.registry import PublisherRegistry
from src.settings import get_settings


class Utils:
    """Helper methods for API endpoints"""

    def __init__(self) -> None:
        self.meteor = Meteor(languages=Utils.get_languages())
        if get_settings().REGISTRY_FILE:
            self.meteor.set_registry(
                PublisherRegistry(registry_file=get_settings().REGISTRY_FILE)
            )
        elif get_settings().REGISTRY_HOST:
            self.meteor.set_registry(
                PublisherRegistry(
                    db_credentials={
                        'host': get_settings().REGISTRY_HOST,
                        'user': get_settings().REGISTRY_USER,
                        'database': get_settings().REGISTRY_DATABASE,
                        'password': get_settings().REGISTRY_PASSWORD
                    }
                )
            )

    @staticmethod
    def get_languages() -> list[str] | None:
        if not get_settings().LANGUAGES:
            return None
        return get_settings().LANGUAGES.split(',')

    @staticmethod
    def get_environment_prefix() -> str:
        return "/meteor" if get_settings().ENVIRONMENT in ["stage", "prod"] else ""

    @staticmethod
    def verify_file(file: UploadFile) -> None:
        size_limit = int(get_settings().MAX_FILE_SIZE_MB)
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="File must be a PDF")
        if file.size is not None and file.size > size_limit * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

    @staticmethod
    def verify_url(url: str) -> None:
        size_limit = int(get_settings().MAX_FILE_SIZE_MB)
        if not url:
            raise HTTPException(status_code=400, detail="No URL provided")
        content_size = requests.get(url, stream=True, timeout=30).headers['Content-length']
        if int(content_size) > size_limit * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

    @staticmethod
    def save_file(uploaded_file: UploadFile) -> str:
        file_id = str(uuid.uuid1()) + '.pdf'
        filepath = os.path.join(get_settings().UPLOAD_FOLDER, file_id)
        with open(filepath, 'wb') as outfile:
            outfile.write(uploaded_file.file.read())
        return filepath

    @staticmethod
    def download_file(url: str) -> str:
        file_id = str(uuid.uuid1()) + '.pdf'
        filepath = os.path.join(get_settings().UPLOAD_FOLDER, file_id)
        response = requests.get(url, timeout=300)
        with open(filepath, 'wb') as outfile:
            outfile.write(response.content)
        return filepath

    class Error(TypedDict):
        """Store an error message"""
        error: str

    def process_and_remove(
            self,
            filename: Optional[str],
            filepath: str,
            delete_immediately: bool = False
    ) -> Union[Error, Results]:
        try:
            results = self.meteor.run(filepath)
            return results
        except Exception as exc:
            print(traceback.format_exc())
            raise HTTPException(detail=f'Error while processing file {filename}',
                                status_code=500) from exc
        finally:
            if delete_immediately:
                os.remove(filepath)
            else:
                threading.Timer(5, lambda: os.remove(filepath)).start()
