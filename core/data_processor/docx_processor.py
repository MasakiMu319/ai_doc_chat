from abc import ABC
from pathlib import Path
from typing import Union, List

from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document

from core.data_processor.base import BaseDataProcessor


class DocxProcessor(BaseDataProcessor, ABC):
    def __init__(self, file_path: Union[str, Path], **kwargs):
        """
        Initialize with file path.
        """
        super().__init__(file_path=file_path, **kwargs)

        self.documents = []
        for file_path in self.files:
            self.documents = Docx2txtLoader(file_path=file_path).load()

    async def process(self) -> List[Document]:
        """
        Process docx file, and return chunks.

        # TODO: Now only return chunks from single Document.
        """
        chunks = self.text_splitter.split_documents(documents=self.documents)
        return chunks
