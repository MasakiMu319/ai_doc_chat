from abc import ABC
from pathlib import Path
from typing import Union, List

from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.data_processor.base import BaseDataProcessor


class DocxProcessor(BaseDataProcessor, ABC):
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize with file path.
        """
        file_path = file_path if isinstance(file_path, Path) else Path(file_path)
        if not file_path.is_file:
            raise ValueError("File path %s is not a valid file." % self.file_path)

        self.documents = Docx2txtLoader(file_path=file_path).load()

        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["。", "！", "？", "\n\n", "\n"],
            keep_separator="end",
            chunk_size=512,
            chunk_overlap=128,
            is_separator_regex=True,
        )

    async def process(self) -> List[Document]:
        """
        Process docx file, and return chunks.

        # TODO: Now only return chunks from single Document.
        """
        chunks = self.text_splitter.split_documents(documents=self.documents)
        return chunks
