import asyncio
import logging
import logfire

import simplemind as sm

from conf import settings
from core.data_processor.markdown_processor import MarkdownProcessor
from core.storage.milvus import MilvusStorage
from utils.llm import SimpleLLM as sl

logger = logging.getLogger(__name__)

MILVUS_URL = settings.db.MILVUS_URI
SEMAPHORE = 10


async def prepare_data(target: str = "art_design"):
    with logfire.span("prepare_data"):
        milvus = MilvusStorage(uri=MILVUS_URL)
        # TODO: Check if the collection exists.
        if target in milvus.list_collections():
            return
        with logfire.span("prepare_data.md_processor"):
            md_processor = MarkdownProcessor(file_path=f"data/{target}")
            chunks = await md_processor.process()

        with logfire.span("embedding data"):
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
            collection_name=target,
            dimension=1536,
            enable_bm25=True,
        )
        milvus.store(collection_name=target, data=points)


async def chat(query: str):
    milvus = MilvusStorage(uri=MILVUS_URL)
    with logfire.span("chat.milvus_search"):
        try:
            query_embedding = await sl().embedding(
                model="text-embedding-3-small", inputs=query
            )
            logfire.info(f"query_embedding: {query_embedding}")
            query_req = MilvusStorage.build_hybrid_search_query(
                query_embedding=query_embedding, query=query
            )
            relevant_contents = milvus.hybrid_search(
                collection_name="anyio",
                query=query_req,
            )
        except Exception as e:
            logfire.exception(f"milvus_search error: {e}")
            return

        for index, item in enumerate(relevant_contents):
            logfire.info(f"{index}: {item}")

        relevant_contents = [
            str(index + 1) + "." + item.get("entity").get("content")
            for index, item in enumerate(relevant_contents)
        ]
    prompt = """
你是一位问答助手，你的任务是根据“参考内容”中的文本信息回答问题，请准确回答问题，不要健谈，如果提供的文本信息无法回答问题。请直接回复“提供的内容无法回答问题”，我相信你能做的很好。\n
## 参考内容
{relevant_contents}
## 问题
{query}
    """

    prompt = prompt.format(relevant_contents=relevant_contents, query=query)
    logfire.info(f"prompt: {prompt}")
    with logfire.span("chat.llm_generate"):
        for chunk in sm.generate_text(prompt=prompt, llm_model="gpt-4o", stream=True):
            logfire.info(f"sending chunk: {chunk}")
            yield chunk
            await asyncio.sleep(0)
