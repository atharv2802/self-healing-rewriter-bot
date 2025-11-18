"""FastAPI application for Self-Healing Response Rewriter."""
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from app.models import RewriteRequest, RewriteResponse
from app.rewriter import process_reply
from config import CORS_ORIGINS
from typing import List
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Self-Healing Response Rewriter",
    description="AI-powered compliance and risk rewriting API",
    version="1.0.0"
)

# Configure CORS with strict origin controls
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Custom exception handlers for better error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")
    
    logger.warning(f"Validation error on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request contains invalid or missing fields.",
            "details": error_messages,
            "suggestion": "Please check the API documentation at /docs for the correct request format."
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with actionable messages."""
    logger.error(f"Unexpected error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "suggestion": "Please try again. If the problem persists, contact support with the timestamp of this error."
        }
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
