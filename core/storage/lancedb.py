from abc import ABC
from typing import List

import lancedb
from lancedb import AsyncTable
from lancedb.index import IvfFlat
from lancedb.pydantic import Vector, LanceModel

from core.storage.base import StorageBase


class Content(LanceModel):
    id: int
    vector: Vector(1536)
    content: str


class LanceDBStorage(StorageBase, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None

    async def init(self, uri: str):
        self._client = await lancedb.connect_async(uri=uri)
        return self

    async def create_collection(
        self, collection_name: str, enable_index: bool = True
    ) -> AsyncTable:
        table = await self._client.create_table(name=collection_name, schema=Content)
        # TODO: support choose index type
        if enable_index:
            self.create_index(table, "vector")
        return table

    async def create_index(self, table: AsyncTable, column: str):
        await table.create_index(
            column=column,
            config=IvfFlat(
                num_partitions=2,
                num_sub_vectors=4,
            ),
        )

    async def list_collections(self):
        """
        List all collections.
        """
        return await self._client.table_names()

    async def get_collection_info(self, collection_name: str):
        """
        Get collection information.
        """
        table = await self._client.open_table(name=collection_name)
        return await table.schema()

    async def store(self, collection_name: str, data: LanceModel):
        """
        Store data.
        """
        table = await self._client.open_table(name=collection_name)
        await table.add(data=data)

    async def search(
        self,
        collection_name: str,
        data: List[List] | List,
        limit: int = 5,
        **kwargs,
    ):
        """
        Search relevant data.

        If target table don't have index, it will exhaustively scans the entire vector space.
        """
        table = await self._client.open_table(name=collection_name)
        return await table.query().nearest_to(data).limit(limit=limit).to_list()

    async def hierarchical_search(self, **kwargs):
        """
        Hierarchical search relevant data.
        """
        pass
