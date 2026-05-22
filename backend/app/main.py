from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import get_settings
from .rag import stream_rag_answer

app = FastAPI(title="Evibot Medical RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "collection": settings.collection_name,
        "knowledge_dir": str(settings.resolved_knowledge_dir),
        "chroma_dir": str(settings.resolved_chroma_dir),
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")

    return StreamingResponse(
        stream_rag_answer(question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
