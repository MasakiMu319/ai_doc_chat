from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    code: int
    message: str
    data: str
