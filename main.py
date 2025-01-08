import logging
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from utils.log import patch_logger
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader

from schema.chat import ChatRequest
from src.ai_doc_chat.chat import chat as chat_with_ai
from src.ai_doc_chat.chat import prepare_data

patch_logger(__name__, logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prepare_data()
    app.state.api_key = f"adc-{secrets.token_urlsafe(32)}"
    logger.info(f"API key: {app.state.api_key}")
    logger.info("Data loads sucessfully.")
    yield
    print("Application shutdown")


app = FastAPI(
    title="AI Doc Chat",
    description="Chat with AI to get the answer from the documents.",
    lifespan=lifespan,
)


async def verify_api_key(
    api_key: Optional[str] = Depends(APIKeyHeader(name="X-API-Key")),
):
    if not api_key:
        logger.warning("API key is missing.")
        raise HTTPException(status_code=401, detail="API key is missing.")

    if api_key != app.state.api_key:
        logger.warning("API key is invalid.")
        raise HTTPException(status_code=403, detail="API key is invalid.")
    return api_key


@app.post("/chat")
async def chat(request: ChatRequest, api_key: str = Security(verify_api_key)):
    """
    Chat with AI to get the answer from the documents.
    """
    return StreamingResponse(
        chat_with_ai(request.query),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9527,
        reload=True,
    )
