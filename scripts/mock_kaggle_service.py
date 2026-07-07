import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class ChatRequest(BaseModel):
    model: str
    messages: list

class EmbedRequest(BaseModel):
    texts: List[str]

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a mock LLM response from the simulated Kaggle GPU serving service that is long enough to pass tests."
                }
            }
        ],
        "model": req.model
    }

@app.post("/embed")
def embed(req: EmbedRequest):
    embeddings = [[0.1] * 384 for _ in req.texts]
    return {"embeddings": embeddings}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/models")
def get_models():
    return {
        "data": [
            {
                "id": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                "object": "model"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
