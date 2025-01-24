import asyncio
import logging
import logfire
from typing import List

import simplemind as sm

from conf import settings
from core.data_processor.markdown_processor import MarkdownProcessor
from core.storage.milvus import MilvusStorage
from utils.llm import SimpleLLM as sl
from utils.llm import try_parse_json_object
from utils.prompt import query_prompt, rewrite_prompt

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


async def search_relevant_contents(queries: List[str]):
    milvus = MilvusStorage(uri=MILVUS_URL)
    with logfire.span("chat.milvus_search"):
        relevant_contents = []
        for query in queries:
            try:
                query_embedding = await sl().embedding(
                    model="text-embedding-3-small", inputs=query
                )
                logfire.info(f"query_embedding: {query_embedding}")
                query_req = MilvusStorage.build_hybrid_search_query(
                    query_embedding=query_embedding, query=query
                )
                relevant_contents.extend(
                    milvus.hybrid_search(
                        collection_name="anyio",
                        query=query_req,
                    )
                )
            except Exception as e:
                logfire.exception(f"milvus_search error: {e}")

        relevant_contents = sorted(
            relevant_contents, key=lambda x: x.get("distance"), reverse=True
        )

        for index, item in enumerate(relevant_contents):
            logfire.info(f"{index}: {item}")

        relevant_contents = [
            str(index + 1) + "." + item.get("entity").get("content")
            for index, item in enumerate(relevant_contents)
        ]
        relevant_contents = list(set(relevant_contents))
        return relevant_contents


async def rewrite(query: str):
    rewrite_query = rewrite_prompt.format(query=query)
    logfire.info(f"rewrite_query: {rewrite_query}")
    with logfire.span("chat.llm_rewrite"):
        try:
            response = sm.generate_text(
                prompt=rewrite_query,
                llm_model="gpt-4o-mini",
            )
            logfire.info(f"raw response: {response}")
            response, queries = try_parse_json_object(response)
            queries = queries.get("query")
            logfire.info(f"queries: {queries}")
        except Exception as e:
            logfire.exception(f"llm_rewrite error: {e}")
            return []
        return queries


async def chat(query: str):
    queries = await rewrite(query=query)
    queries.append(query)
    relevant_contents = await search_relevant_contents(queries=queries)
    prompt = query_prompt.format(relevant_contents=relevant_contents, query=query)
    logfire.info(f"prompt: {prompt}")
    with logfire.span("chat.llm_generate"):
        for chunk in sm.generate_text(
            prompt=prompt, llm_model="gpt-4o-mini", stream=True
        ):
            logfire.info(f"sending chunk: {chunk}")
            yield chunk
            await asyncio.sleep(0)
