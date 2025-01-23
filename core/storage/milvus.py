import logging
import typing as t
from abc import ABC

from pymilvus import (
    MilvusClient,
    CollectionSchema,
    FieldSchema,
    DataType,
    Function,
    FunctionType,
    AnnSearchRequest,
    RRFRanker,
)
from pymilvus.milvus_client import IndexParams

from core.storage.base import StorageBase

logger = logging.getLogger(__name__)


class MilvusStorage(StorageBase, ABC):
    def __init__(self, uri: str, **kwargs):
        super().__init__(**kwargs)
        self.client = MilvusClient(uri=uri)

    def create_collection(
        self,
        collection_name: str,
        dimension: int,
        schema: CollectionSchema = None,
        index_params: IndexParams = None,
        enable_bm25: bool = False,
        sparse_field: str = None,
    ):
        dimension = dimension if dimension else 768
        sparse_field = sparse_field if sparse_field else "sparse"
        schema = (
            schema
            if schema
            else MilvusStorage._default_collection_schema(dimension=dimension)
        )
        index_params = (
            index_params if index_params else MilvusStorage._default_collection_index()
        )

        # TODO: Next version will refactor this part.
        # Please note that the BM25 function is only supported in Milvus 2.5.0 and later.
        if enable_bm25:
            logger.debug("Enabling BM25.")
            bm25_function = Function(
                name="content_bm25_emb",
                input_field_names=["content"],
                output_field_names=["sparse"],
                function_type=FunctionType.BM25,
            )
            schema.add_function(bm25_function)

            index_params.add_index(
                field_name=sparse_field,
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="BM25",
            )

        self.client.create_collection(
            collection_name=collection_name,
            dimension=dimension,
            schema=schema,
            index_params=index_params,
        )

    @staticmethod
    def _default_collection_index() -> IndexParams:
        """
        Default index params for collection. Default index is HNSW with COSINE metric.

        Please feel free to change the index params according to your needs.
        """
        logger.debug("Using default index params.")
        return IndexParams(
            field_name="vector",
            metric_type="COSINE",
            index_type="HNSW",
            index_name="vector_index",
            # details of index params please refer to :https://milvus.io/docs/zh/index.md?tab=floating#Indexes-supported-in-Milvus
            params={"M": 16, "efConstruction": 500},
        )

    @staticmethod
    def _default_collection_schema(dimension: int) -> CollectionSchema:
        """
        Default collection schema for collection. Default vector dimension is 768.
        """
        logger.debug("Using default collection schema.")
        return CollectionSchema(
            description="Default collection schema.",
            # this is a preserver field, store like a json string
            enable_dynamic_field=True,
            fields=[
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True,
                ),
                FieldSchema(
                    name="vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=dimension,
                ),
                FieldSchema(
                    name="content",
                    dtype=DataType.VARCHAR,
                    # The Milvus let you must set the max length of content, can't be None
                    max_length=10000,
                    enable_analyzer=True,
                ),
                FieldSchema(
                    name="sparse",
                    dtype=DataType.SPARSE_FLOAT_VECTOR,
                ),
            ],
        )

    def list_collections(self):
        return self.client.list_collections()

    def get_collection_info(self, collection_name: str):
        return self.client.describe_collection(collection_name=collection_name)

    def store(self, collection_name: str, data: t.List[t.Dict[str, t.Any]]):
        try:
            self.client.insert(collection_name=collection_name, data=data)
        except Exception as e:
            logger.error(f"Failed to store data due to: {e}")
            raise e

    def search(
        self,
        collection_name: str,
        anns_field: str | None,
        data: t.List[t.List] | t.List,
        search_params: t.Dict[str, t.Any],
        output_fields: t.List[str],
        consistency_level: str = "Bounded",
        limit: int = 5,
        **kwargs,
    ) -> t.List[t.List[t.Dict[str, t.Any]]]:
        """
        Dense vector search.

        :param collection_name: collection name of the document chunks.
        :param anns_field: the field name of the vectors.
        :param data: the vector of user query, remember you must put query vectors into a list, even you only have one.
        :param search_params: the search parameters.
        :param output_fields: the fields you want to return.
        :param consistency_level: the consistency level of the search.
        :param limit: the number of results you want to return.

        :return: list of dict.
        """
        anns_field = anns_field if anns_field else "vector"
        return self.client.search(
            collection_name=collection_name,
            anns_field=anns_field,
            data=data,
            search_params=search_params,
            limit=limit,
            output_fields=output_fields,
            consistency_level=consistency_level,
        )

    def hierarchical_search(self, **kwargs):
        pass

    def hybrid_search(
        self, collection_name: str, query: t.Dict[str, t.Dict], limit: int = 5
    ) -> t.List[t.Dict]:
        """
        Hybrid search: search with both dense and sparse vectors.
        Please note that this method is experimental and will change in the future.
        This implementation deeply depends on the data backend and the data structure.

        example query:
        query = {
            "dense": {
                "data": [question_embedding],
                "anns_field": "vector",
                "param": {
                    "metric_type": "COSINE",
                    "params": {"ef": 250},
                },
                "limit": 5,
            },
            "sparse": {
                "data": [question_content],
                "anns_field": "sparse",
                "param": {
                    "metric_type": "BM25",
                    "params": {"drop_ratio_build": 0.0},
                 },
                 "limit": 5,
            }
        }
        """
        dense_req, sparse_req = (
            AnnSearchRequest(**query["dense"]),
            AnnSearchRequest(**query["sparse"]),
        )

        ranker = RRFRanker()

        res = self.client.hybrid_search(
            collection_name=collection_name,
            output_fields=["id", "content"],
            reqs=[dense_req, sparse_req],
            ranker=ranker,
            limit=limit,
        )
        return res[0]

    @classmethod
    def build_hybrid_search_query(
        cls, query_embedding: t.List[float], query: str
    ) -> t.Dict:
        """
        Build hybrid search query.
        """
        return {
            "dense": {
                "data": [query_embedding],
                "anns_field": "vector",
                "param": {
                    "metric_type": "COSINE",
                    "params": {"ef": 250},
                },
                "limit": 5,
            },
            "sparse": {
                "data": [query],
                "anns_field": "sparse",
                "param": {
                    "metric_type": "BM25",
                    "params": {"drop_ratio_build": 0.0},
                },
                "limit": 5,
            },
        }
