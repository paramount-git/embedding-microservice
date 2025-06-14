from fastapi import FastAPI, Request
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI()
model = SentenceTransformer("all-MiniLM-L6-v2")

class QueryRequest(BaseModel):
    text: str

@app.post("/embed")
async def embed(request: QueryRequest):
    embedding = model.encode([request.text])[0]
    return {"embedding": embedding.tolist()}
