"""FastAPI application for Self-Healing Response Rewriter."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.models import RewriteRequest, RewriteResponse
from app.rewriter import process_reply
from typing import List
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Self-Healing Response Rewriter",
    description="AI-powered compliance and risk rewriting API",
    version="1.0.0"
)

@app.post("/rewrite_reply", response_model=RewriteResponse)
def rewrite_reply(request: RewriteRequest) -> RewriteResponse:
    """Process a single reply for compliance and risk assessment.
    
    Args:
        request: RewriteRequest containing draft reply, context, and policies
        
    Returns:
        RewriteResponse with risk assessment and safe reply
    """
    try:
        return process_reply(request)
    except Exception as e:
        logger.error(f"Error processing reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rewrite_batch", response_model=List[RewriteResponse])
def rewrite_batch(requests: List[RewriteRequest]) -> List[RewriteResponse]:
    """Process multiple replies in batch for compliance assessment.
    
    Args:
        requests: List of RewriteRequest objects
        
    Returns:
        List of RewriteResponse objects
    """
    try:
        if not requests:
            raise HTTPException(status_code=400, detail="Empty request list")
        if len(requests) > 100:
            raise HTTPException(status_code=400, detail="Batch size exceeds limit of 100")
        return [process_reply(req) for req in requests]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health() -> dict:
    """Health check endpoint.
    
    Returns:
        Status dictionary
    """
    return {"status": "ok", "version": "1.0.0"}
