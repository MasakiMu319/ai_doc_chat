import json
import re
import logging
from functools import cached_property
import typing as t

from openai import AsyncOpenAI
from json_repair import repair_json

from conf import settings

logger = logging.getLogger(__name__)


class SimpleLLM:
    # TODO: Refactor this class to support multiple LLM providers.
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


def try_parse_json_object(input: str) -> tuple[str, dict]:
    """JSON cleaning and formatting utilities.

    return: cleaned json string, parsed json
    """

    result = None
    try:
        # Try parse first
        result = json.loads(input)
    except json.JSONDecodeError:
        logger.info("Warning: Error decoding faulty json, attempting repair")

    if result:
        return input, result

    pattern = r"\{(.*)\}"
    _match = re.search(pattern, input, re.DOTALL)
    input = "{" + _match.group(1) + "}" if _match else input

    # Clean up json string.
    input = (
        input.replace("{{", "{")
        .replace("}}", "}")
        .replace('"[{', "[{")
        .replace('}]"', "}]")
        .replace("\\", " ")
        .replace("\\n", " ")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )

    # Remove JSON Markdown Frame
    if input.startswith("```json"):
        input = input[len("```json") :]
    if input.endswith("```"):
        input = input[: len(input) - len("```")]

    try:
        result = json.loads(input)
    except json.JSONDecodeError:
        # Fixup potentially malformed json string using json_repair.
        input = str(
            repair_json(json_str=input, return_objects=False, ensure_ascii=False)
        )

        # Generate JSON-string output using best-attempt prompting & parsing techniques.
        try:
            result = json.loads(input)
        except json.JSONDecodeError:
            logger.exception("error loading json, json=%s", input)
            return input, {}
        else:
            if not isinstance(result, dict):
                logger.exception("not expected dict type. type=%s:", type(result))
                return input, {}
            return input, result
    else:
        return input, result
