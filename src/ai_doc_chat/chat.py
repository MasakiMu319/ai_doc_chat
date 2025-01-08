import asyncio
import logging

import simplemind as sm

from conf import settings
from core.data_processor.markdown_processor import MarkdownProcessor
from core.storage.milvus import MilvusStorage
from utils.llm import SimpleLLM as sl

logger = logging.getLogger(__name__)

MILVUS_URL = settings.db.MILVUS_URI
SEMAPHORE = 10


async def prepare_data():
    milvus = MilvusStorage(uri=MILVUS_URL)
    # TODO: Check if the collection exists.
    if "art_design" in milvus.list_collections():
        return
    md_processor = MarkdownProcessor(file_path="data")
    chunks = await md_processor.process()

    embeddings_generator = sl()
    semaphore = asyncio.Semaphore(SEMAPHORE)

    async def gen_chunk_embedding(inputs: str, model: str):
        async with semaphore:
            return {
                "vector": await embeddings_generator.embedding(
                    model=model, inputs=inputs
                ),
                "content": inputs,
            }

    points = await asyncio.gather(
        *(
            gen_chunk_embedding(
                inputs=chunk.page_content, model="text-embedding-3-small"
            )
            for chunk in chunks
        )
    )

    milvus.create_collection(
        collection_name="art_design",
        dimension=1536,
        enable_bm25=True,
    )
    milvus.store(collection_name="art_design", data=points)


async def chat(query: str):
    milvus = MilvusStorage(uri=MILVUS_URL)
    embeddings_generator = sl()
    query_embedding = await embeddings_generator.embedding(
        model="text-embedding-3-small", inputs=query
    )
    query_req = {
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
    relevant_contents = milvus.hybrid_search(
        collection_name="art_design",
        query=query_req,
    )
    relevant_contents = [
        str(index + 1) + "." + item.get("entity").get("content")
        for index, item in enumerate(relevant_contents)
    ]
    # print(relevant_contents)
    prompt = """
    你是一位问答助手，你的任务是根据“参考内容”中的文本信息回答问题，请准确回答问题，不要健谈，如果提供的文本信息无法回答问题。请直接回复“提供的内容无法回答问题”，我相信你能做的很好。\n
    ## 参考内容
    {relevant_contents}
    ## 问题
    {query}
    """

    prompt = prompt.format(relevant_contents=relevant_contents, query=query)
    logger.debug(prompt)
    # for chunk in sm.generate_text(prompt=prompt, llm_model="gpt-4o", stream=True):
    #     yield chunk

    for chunk in sm.generate_text(prompt=prompt, llm_model="gpt-4o", stream=True):
        yield chunk
        await asyncio.sleep(0)
