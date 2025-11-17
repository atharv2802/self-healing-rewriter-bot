"""FastAPI application for Self-Healing Response Rewriter."""
from fastapi import FastAPI, HTTPException, status
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
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing single reply request")
        return process_reply(request)
    except ValueError as e:
        logger.error(f"Validation error processing reply: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing reply: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/rewrite_batch", response_model=List[RewriteResponse])
def rewrite_batch(requests: List[RewriteRequest]):
    """Process multiple replies in batch for compliance assessment.
    
    Args:
        requests: List of RewriteRequest objects
        
    Returns:
        List of RewriteResponse objects
        
    Raises:
        HTTPException: If batch processing fails
    """
    try:
        if not requests:
            raise HTTPException(status_code=400, detail="Empty request list")
        if len(requests) > 100:
            raise HTTPException(status_code=400, detail="Batch size exceeds limit of 100")
        
        logger.info(f"Processing batch of {len(requests)} requests")
        results: List[RewriteResponse] = []
        failed_indices: List[int] = []
        for idx, req in enumerate(requests):
            try:
                results.append(process_reply(req))
            except Exception as e:
                logger.error(f"Error processing request {idx} in batch: {e}")
                failed_indices.append(idx)
                # Continue processing remaining requests
                results.append(RewriteResponse(
                    risk_level="high",
                    confidence_score=0,
                    issues_detected=[f"Processing error: {str(e)}"],
                    violation_details=[],
                    action="escalate",
                    safe_reply="",
                    explanation=f"Error processing request: {str(e)}",
                    before_after_diff=None,
                    escalate=True
                ))
        if len(failed_indices) == len(requests):
            raise HTTPException(status_code=500, detail="All batch items failed to process")
        if failed_indices:
            return JSONResponse(
                status_code=status.HTTP_207_MULTI_STATUS,
                content={
                    "results": [resp.dict() for resp in results],
                    "failed_indices": failed_indices,
                    "message": "Some batch items failed; see failed_indices for details"
                }
            )
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")

@app.get("/health")
def health() -> dict:
    """Health check endpoint.
    
    Returns:
        Status dictionary
    """
    return {"status": "ok", "version": "1.0.0"}
