
"""
Models for SHR API requests and responses.

Batch endpoint usage:
    - Input: List[RewriteRequest]
    - Output: List[RewriteResponse]
    - POST /rewrite_batch
"""
from typing import List, Optional
from pydantic import BaseModel

class Message(BaseModel):
    speaker: str
    text: str

class Policy(BaseModel):
    id: str
    description: str
    requires_verification: Optional[bool] = None
    forbidden_phrases: Optional[List[str]] = None
    preferred_pattern: Optional[str] = None

class RewriteRequest(BaseModel):
    agent_id: str
    channel: str
    context: List[Message]
    draft_reply: str
    policies: List[Policy]

class ViolationDetail(BaseModel):
    policy_id: str
    policy_description: str
    violated_phrase: str
    position_in_text: Optional[int] = None

class RewriteResponse(BaseModel):
    risk_level: str
    confidence_score: int  # 0-100, how confident the LLM is in its classification
    issues_detected: List[str]
    violation_details: List[ViolationDetail]  # Enhanced explainability
    action: str
    safe_reply: str
    explanation: str
    before_after_diff: Optional[str] = None  # Highlights changes made
    escalate: bool
