
from fastapi import FastAPI
from app.models import RewriteRequest, RewriteResponse
from app.rewriter import process_reply
from typing import List

app = FastAPI()

@app.post("/rewrite_reply", response_model=RewriteResponse)
def rewrite_reply(request: RewriteRequest):
    return process_reply(request)

@app.post("/rewrite_batch", response_model=List[RewriteResponse])
def rewrite_batch(requests: List[RewriteRequest]):
    return [process_reply(req) for req in requests]

@app.get("/health")
def health():
    return {"status": "ok"}
