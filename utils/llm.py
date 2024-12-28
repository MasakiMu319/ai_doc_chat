import logging
from functools import cached_property
import typing as t

from openai import AsyncOpenAI

from conf import settings

logger = logging.getLogger(__name__)


class SimpleLLM:
    def __int__(self):
        pass

    @cached_property
    def openai_client(self):
        return AsyncOpenAI(
            api_key=settings.llm.openai.API_KEY,
            base_url=settings.llm.openai.BASE_URL,
        )

    @cached_property
    def voc_client(self):
        return AsyncOpenAI(
            api_key=settings.llm.voc.API_KEY,
            base_url=settings.llm.voc.BASE_URL,
        )

    async def embedding(self, model: str, inputs: str) -> t.List[float]:
        client, model = (
            (self.voc_client, dict(settings.llm.voc)[model])
            if hasattr(settings.llm.voc, model)
            else (self.openai_client, model)
        )
        logger.debug(f"Client for {model}")
        resp = await client.embeddings.create(input=[inputs], model=model)
        return resp.data[0].embedding
