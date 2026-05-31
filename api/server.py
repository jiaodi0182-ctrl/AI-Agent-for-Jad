"""
FastAPI application factory.
Run: python -m uvicorn api.server:app --reload --port 8000
"""
import sys
sys.path.insert(0, ".")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.chat import router as chat_router
from api.routes.feishu import router as feishu_router
from api.routes.memory import router as memory_router

app = FastAPI(
    title="AI Agent for Jad",
    description="Personal AI agent with tool use, long-term memory, and multi-step planning.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(feishu_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}
