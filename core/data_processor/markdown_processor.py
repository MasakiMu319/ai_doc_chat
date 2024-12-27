from abc import ABC
import typing as t
from pathlib import Path

from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document

from core.data_processor.base import BaseDataProcessor
from utils.tools import list_files


class MarkdownProcessor(BaseDataProcessor, ABC):
    def __init__(self, file_path: t.Union[str, Path]):
        """
        Initialize with file path.
        """
        file_path = file_path if isinstance(file_path, Path) else Path(file_path)

        if not file_path.exists():
            raise ValueError("Target: %s is not a valid path." % file_path)

        files_path = (
            list_files(dir_path=file_path) if file_path.is_dir() else [file_path]
        )
        self.documents = []
        for file_path in files_path:
            self.documents += UnstructuredMarkdownLoader(file_path=file_path).load()

    async def process(self) -> t.List[Document]:
        """
        Process markdown file, and return chunks.
        """
        pass
