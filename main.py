import logging
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader

from schema.chat import ChatRequest
from service.chat import prepare_data, chat
from utils.yalog import Log


@asynccontextmanager
async def lifespan(app: FastAPI):
    Log.start()
    await prepare_data(target="anyio")
    app.state.api_key = f"adc-{secrets.token_urlsafe(32)}"
    logging.info(f"API key: {app.state.api_key}")
    logging.info("Data loads sucessfully.")
    yield
    logging.info("Application shutdown")
    Log.close()


app = FastAPI(
    title="AI Doc Chat",
    description="Chat with AI to get the answer from the documents.",
    lifespan=lifespan,
    docs_url=None,
)


async def verify_api_key(
    api_key: Optional[str] = Depends(APIKeyHeader(name="X-API-Key")),
):
    if not api_key:
        logging.warning("API key is missing.")
        raise HTTPException(status_code=401, detail="API key is missing.")

    if api_key != app.state.api_key:
        logging.warning("API key is invalid.")
        raise HTTPException(status_code=403, detail="API key is invalid.")
    return api_key


@app.post("/query")
async def query(request: ChatRequest, api_key: str = Security(verify_api_key)):
    """
    Chat with AI to get the answer from the documents.
    """
    return StreamingResponse(
        chat(request.query),
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
