"""Chat endpoints — standard and streaming."""
import time
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent import Agent, LongTermMemory, Planner
from agent import logger as audit
from api.auth import require_api_key

router = APIRouter(prefix="/chat", tags=["chat"])

# One shared LongTermMemory instance; one Agent per request (stateless HTTP)
_ltm = LongTermMemory()


def _make_agent() -> Agent:
    return Agent(long_term_memory=_ltm)


# ------------------------------------------------------------------
# Request / response schemas
# ------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32_000)
    use_planner: bool = Field(False, description="Use multi-step planner for complex tasks")


class ChatResponse(BaseModel):
    reply: str
    duration_ms: int


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, user_id: str = Depends(require_api_key)):
    audit.log_request(user_id, req.message, mode="plan" if req.use_planner else "chat")
    agent = _make_agent()
    start = time.monotonic()

    if req.use_planner:
        planner = Planner(agent)
        reply = planner.run(req.message)
    else:
        reply = agent.chat(req.message)

    duration_ms = int((time.monotonic() - start) * 1000)
    audit.log_response(user_id, reply, duration_ms=duration_ms)
    return ChatResponse(reply=reply, duration_ms=duration_ms)


@router.post("/stream")
def stream_chat(req: ChatRequest, user_id: str = Depends(require_api_key)):
    """Server-sent events stream — each chunk is a plain text fragment."""
    audit.log_request(user_id, req.message, mode="stream")
    agent = _make_agent()

    async def generate() -> AsyncIterator[str]:
        try:
            for chunk in agent.stream(req.message):
                yield chunk
        except Exception as e:
            audit.log_error(user_id, str(e))
            yield f"\n[ERROR] {e}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
