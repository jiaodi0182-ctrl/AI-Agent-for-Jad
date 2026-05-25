"""Memory management endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from agent import LongTermMemory
from api.auth import require_api_key

router = APIRouter(prefix="/memory", tags=["memory"])

_ltm = LongTermMemory()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    n_results: int = Field(5, ge=1, le=20)


class MemoryItem(BaseModel):
    role: str
    content: str
    timestamp: float | None


class SearchResponse(BaseModel):
    results: list[MemoryItem]
    total_stored: int


class StatsResponse(BaseModel):
    total_memories: int


@router.get("/stats", response_model=StatsResponse)
def memory_stats(_: str = Depends(require_api_key)):
    return StatsResponse(total_memories=_ltm.count)


@router.post("/search", response_model=SearchResponse)
def search_memory(req: SearchRequest, _: str = Depends(require_api_key)):
    results = _ltm.retrieve(req.query, n_results=req.n_results)
    return SearchResponse(
        results=[MemoryItem(**r) for r in results],
        total_stored=_ltm.count,
    )


@router.delete("/clear")
def clear_memory(_: str = Depends(require_api_key)):
    _ltm.clear()
    return {"status": "cleared"}
