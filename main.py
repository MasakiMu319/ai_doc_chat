import asyncio
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import StreamingResponse
import logfire

from schema.chat import ChatRequest

from src.ai_doc_chat.chat import chat as chat_with_ai
from src.ai_doc_chat.chat import prepare_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prepare_data()
    logfire.info("Data loads sucessfully.")
    yield
    print("Application shutdown")


app = FastAPI(
    title="AI Doc Chat",
    description="A simple API to chat any documents with AI.",
    lifespan=lifespan,
)

logfire.configure()
logfire.instrument_fastapi(app=app)


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with AI to get the answer from the documents.
    """

    async def stream():
        async for chunk in chat_with_ai(request.query):
            yield chunk
            await asyncio.sleep(0)

    return StreamingResponse(
        stream(),
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
