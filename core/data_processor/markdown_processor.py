from abc import ABC
import typing as t
from pathlib import Path

from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
)

from core.data_processor.base import BaseDataProcessor
from core.data_processor.constants import HEADERS_TO_SPLIT_ON


class MarkdownProcessor(BaseDataProcessor, ABC):
    def __init__(self, file_path: t.Union[str, Path], **kwargs):
        """
        Initialize with file path.
        """
        super().__init__(file_path=file_path, **kwargs)

        self.documents = []
        for file_path in self.files:
            self.documents += UnstructuredMarkdownLoader(file_path=file_path).load()

        self.md_splitter = MarkdownHeaderTextSplitter(
            HEADERS_TO_SPLIT_ON, strip_headers=False
        )

    async def process(self) -> t.List[Document]:
        """
        Process markdown file, and return chunks.
        """
        md_header_splits = []

        for document in self.documents:
            md_header_splits += self.md_splitter.split_text(text=document.page_content)

        # char-level split to solve the problem of long paragraphs.
        chunks = self.text_splitter.split_documents(md_header_splits)
        return chunks
