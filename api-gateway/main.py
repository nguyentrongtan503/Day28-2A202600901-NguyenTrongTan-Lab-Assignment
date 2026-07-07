# api-gateway/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ["VLLM_URL"]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

class ChatPayload(BaseModel):
    query: str
    embedding: Optional[List[float]] = None

@app.post("/api/v1/chat")
async def chat(payload: ChatPayload):
    query = payload.query
    embedding = payload.embedding or [0.0] * 384
    start = time.time()

    # 1. Vector search
    async with httpx.AsyncClient() as client:
        try:
            search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
                "vector": embedding,
                "limit": 3
            })
            context = search_resp.json().get("result", [])
        except Exception as e:
            print(f"Error calling Qdrant: {e}")
            context = []

    # 2. LLM inference
    prompt = f"Context: {context}\n\nQuery: {query}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
                "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                "messages": [{"role": "user", "content": prompt}]
            })
            result = llm_resp.json()
            answer = result["choices"][0]["message"]["content"]
            model_name = result["model"]
        except Exception as e:
            print(f"Error calling LLM: {e}")
            answer = "Sorry, the language model is currently unavailable."
            model_name = "mock-fallback"

    latency = (time.time() - start) * 1000

    return {
        "answer": answer,
        "latency_ms": round(latency, 2),
        "model": model_name
    }

@app.get("/health")
def health():
    return {"status": "ok"}

