from abc import ABC, abstractmethod
import typing as t
from functools import cached_property
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

        self._kwargs = kwargs

    @cached_property
    def text_splitter(self) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            separators=TEXT_SPLITTERS,
            keep_separator="end",
            chunk_size=self._kwargs.get("chunk_size", DEFAULT_CHUNK_SIZE),
            chunk_overlap=self._kwargs.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP),
            is_separator_regex=True,
        )

    def set_text_splitter(self, chunk_size: int = None, chunk_overlap: int = None):
        if chunk_size is not None:
            self._kwargs["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            self._kwargs["chunk_overlap"] = chunk_overlap
        if hasattr(self, "text_splitter"):
            delattr(self, "text_splitter")

    @abstractmethod
    def process(self, **kwargs):
        raise NotImplementedError("Subclass should implement this method.")
