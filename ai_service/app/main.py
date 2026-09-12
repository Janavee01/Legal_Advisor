"""
main.py — Persistent FastAPI server for the legal RAG pipeline.

Models (bge-m3 embedder + bge-reranker-v2-m3 cross-encoder) and all
indexes (BM25, Chroma, title-BM25) are loaded ONCE at startup and reused
for every query, instead of being reloaded per process.

This does not change retrieval quality: it runs the exact same
retrieve() path as the one-shot scripts. A lock serializes retrieval
because the embedder is moved GPU<->CPU inside each query, so concurrent
requests would otherwise race on the shared global model state.

Run (from the repo root):
    ai_service/venv/bin/uvicorn ai_service.app.main:app --host 0.0.0.0 --port 8000

Use a SINGLE worker (no --workers / no --reload) so the model is loaded
once per process.
"""

import asyncio
import json
import threading

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai_service.app.rag import retrieve
from ai_service.app.rag.answer import answer_from_results
from ai_service.app.rag.reranker import get_reranker
from ai_service.app.rag.vectordb import get_collection

TOP_K_DEFAULT = 8


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=TOP_K_DEFAULT, ge=1, le=20)
    category_filter: str | None = None


class RetrieveResponse(BaseModel):
    query: str
    results: list[dict]


class AnswerRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=TOP_K_DEFAULT, ge=1, le=20)
    category_filter: str | None = None
    model: str | None = None


class AnswerResponse(BaseModel):
    query: str
    answer: str
    model: str
    usage: dict | None = None
    finish_reason: str | None = None
    sources: list[dict]


app = FastAPI(
    title="Legal Advisor RAG",
    description="Persistent retrieval server for Indian law legal sections.",
)

_retrieve_lock = threading.Lock()


def _warmup():
    """Load every model and index once so the first query is fast."""
    retrieve._load_bm25()
    retrieve._load_vector_docs_by_id()
    retrieve._load_title_bm25()
    get_collection()
    get_reranker()


@app.on_event("startup")
def startup():
    print("Warming up: loading all models and indexes...")
    _warmup()
    print("Warmup complete — ready for queries.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve_endpoint(req: RetrieveRequest):
    with _retrieve_lock:
        try:
            out = retrieve.retrieve(
                req.query,
                top_k=req.top_k,
                category_filter=req.category_filter,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Retrieval failed: {exc}",
            )

    return {
        "query": req.query,
        "results": out["results"],
    }


@app.post("/answer", response_model=AnswerResponse)
def answer_endpoint(req: AnswerRequest):
    # Retrieval races on shared GPU/embedder state, so it holds the lock;
    # the LLM call is pure HTTP and runs outside the lock.
    with _retrieve_lock:
        try:
            out = retrieve.retrieve(
                req.query,
                top_k=req.top_k,
                category_filter=req.category_filter,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Retrieval failed: {exc}",
            )

    try:
        response = answer_from_results(
            req.query,
            out["results"],
            model=req.model,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Answer generation failed: {exc}",
        )

    return {
        "query": req.query,
        "answer": response.get("answer", ""),
        "model": response.get("model", ""),
        "usage": response.get("usage"),
        "finish_reason": response.get("finish_reason"),
        "sources": response.get("sources", []),
    }


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/answer/stream")
async def answer_stream(req: AnswerRequest):
    """SSE variant of /answer: streams stage updates for a live UI.

    Yields retrieval_started -> retrieval_done -> generation_started ->
    generation_done. Retrieval holds the GPU lock (threaded); the Gemini
    call runs off-lock in a separate thread so the event loop stays free.
    """
    async def generate():
        yield _sse("retrieval_started", {"query": req.query})

        def do_retrieve():
            with _retrieve_lock:
                return retrieve.retrieve(
                    req.query,
                    top_k=req.top_k,
                    category_filter=req.category_filter,
                )

        try:
            out = await asyncio.to_thread(do_retrieve)
        except Exception as exc:
            yield _sse("error", {"detail": f"Retrieval failed: {exc}"})
            return

        results = out["results"]
        yield _sse("retrieval_done", {"count": len(results)})

        yield _sse("generation_started", {"count": len(results)})

        def do_answer():
            return answer_from_results(
                req.query,
                results,
                model=req.model,
            )

        try:
            response = await asyncio.to_thread(do_answer)
        except Exception as exc:
            yield _sse("error", {"detail": f"Answer generation failed: {exc}"})
            return

        yield _sse(
            "generation_done",
            {
                "query": req.query,
                "answer": response.get("answer", ""),
                "model": response.get("model", ""),
                "usage": response.get("usage"),
                "finish_reason": response.get("finish_reason"),
                "sources": response.get("sources", []),
            },
        )

    return StreamingResponse(generate(), media_type="text/event-stream")