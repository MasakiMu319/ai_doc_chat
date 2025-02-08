import asyncio
from typing import List

import lancedb
from lancedb import AsyncConnection, AsyncTable
from lancedb.index import IvfPq
from lancedb.pydantic import Vector, LanceModel
from lancedb.common import DATA
import logfire
from core.storage.base import StorageBase


class Content(LanceModel):
    id: int
    vector: Vector(1536)
    content: str


class LanceDBStorage(StorageBase):
    """
    Storage for LanceDB. We use collection instead of table in LanceDB to make it more consistent with Milvus.
    """

    def __init__(self, client, **kwargs):
        super().__init__(**kwargs)
        self._client: AsyncConnection = client

    @classmethod
    async def create(cls, uri: str, **kwargs):
        client = await lancedb.connect_async(uri=uri)
        return cls(client, **kwargs)

    async def create_collection(
        self,
        collection_name: str,
    ) -> AsyncTable:
        """
        Create a table in LanceDB. If you want to create a table with a specific index, you can use `create_index` method.
        Currently, we don't support customize table schema.

        Args:
            collection_name: The name of the collection to create.

        Returns:
            The created table.
        """
        table = await self._client.create_table(name=collection_name, schema=Content)
        return table

    async def create_index(self, collection_name: str, column: str):
        """
        Create an index for the table.
        Please note that index should be created after have data in the table.

        Args:
            collection_name: The name of the collection to create the index for.
            column: The column to create the index for.
        """
        if (await self.get_collection_size(collection_name=collection_name)) < 256:
            logfire.error(
                f"Collection {collection_name} has less than 256 data, no enough data to create index."
            )
            return

        table = await self._client.open_table(name=collection_name)

        await table.create_index(
            column=column,
            config=IvfPq(
                num_partitions=2,
                num_sub_vectors=4,
            ),
        )

    async def list_collections(self):
        """
        List all tables.
        """
        return await self._client.table_names()

    async def get_collection_info(self, collection_name: str):
        """
        Get table information.
        """
        table = await self._client.open_table(name=collection_name)
        return await table.schema()

    async def get_collection_size(self, collection_name: str):
        """
        Get table size.

        We support this method to help user can customize the search logic, like `hierarchical search`.
        """
        table = await self._client.open_table(name=collection_name)
        table.query()
        return await table.count_rows()

    async def store(self, collection_name: str, data: DATA):
        """
        Store data.

        Args:
            collection_name: The name of the collection to store the data.
            data: The data to store.
        """
        if not isinstance(data, list):
            print(data)
            try:
                data = [data]
            except Exception as e:
                raise ValueError(f"Invalid data type: {type(data)}") from e

        table = await self._client.open_table(name=collection_name)

        # Due to add method design of lancedb, if we set data as list, it will be added as one item.
        # So we need to add data one by one.
        async with asyncio.TaskGroup() as tg:
            for item in data:
                tg.create_task(table.add([item]))

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
        return await table.vector_search(query_vector=data).limit(limit=limit).to_list()

    async def hierarchical_search(self, **kwargs):
        """
        Hierarchical search relevant data.
        """
        raise NotImplementedError

    async def delete_collection(self, collection_name: str):
        """
        Delete a table.
        """
        await self._client.drop_table(name=collection_name)
