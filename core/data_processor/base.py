from abc import ABC, abstractmethod
import typing as t
from pathlib import Path
from os import PathLike

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from utils.tools import list_files
from core.data_processor.constants import (
    TEXT_SPLITTERS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)


class BaseDataProcessor(ABC):
    """
    interface for Data Processor.
    """

    def __init__(self, file_path: t.Union[str, PathLike], **kwargs):
        file_path = file_path if isinstance(file_path, PathLike) else Path(file_path)
        if not file_path.exists():
            raise ValueError("Target: %s is not a valid path." % file_path)

        self.files = (
            list_files(dir_path=file_path) if file_path.is_dir() else [file_path]
        )

        self.text_splitter = self.text_splitter = RecursiveCharacterTextSplitter(
            separators=TEXT_SPLITTERS,
            keep_separator="end",
            chunk_size=(
                DEFAULT_CHUNK_SIZE
                if "chunk_size" not in kwargs
                else kwargs["chunk_size"]
            ),
            chunk_overlap=(
                DEFAULT_CHUNK_OVERLAP
                if "chunk_overlap" not in kwargs
                else kwargs["chunk_overlap"]
            ),
            is_separator_regex=True,
        )

    @abstractmethod
    def process(self, **kwargs):
        raise NotImplementedError("Subclass should implement this method.")
