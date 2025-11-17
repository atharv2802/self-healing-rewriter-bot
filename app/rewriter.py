from app.llm_client import classify_message, rewrite_message, explain_changes
from app.policies import format_policies_for_prompt, detect_forbidden_phrases
from app.models import RewriteRequest, RewriteResponse, ViolationDetail
from app.utils import clean_text
import json
import logging
from config import SHR_MODE, FORBIDDEN_KEYWORDS

def process_reply(request: RewriteRequest) -> RewriteResponse:
    """Process a reply for compliance and risk assessment.
    
    Args:
        request: RewriteRequest containing draft reply, context, and policies
        
    Returns:
        RewriteResponse with risk level, action, and safe reply
    """
    context = [msg.dict() for msg in request.context]
    policies = [p.dict() for p in request.policies]
    policies_str = format_policies_for_prompt(policies)

    classification_raw = classify_message(context, request.draft_reply, policies_str)
    classification_raw = clean_text(classification_raw)

    try:
        classification = json.loads(classification_raw)
    except json.JSONDecodeError as exc:
        logging.error(f"Invalid classification JSON: {exc}; raw={classification_raw}")
        classification = {
            "risk_level": "high",
            "confidence_score": 95,
            "issues_detected": ["LLM error: invalid classification payload"],
            "violation_details": [],
            "can_auto_fix": False,
        }

    risk_level = classification.get("risk_level", "high")
    confidence_score = classification.get("confidence_score", 50)
    issues_detected = classification.get("issues_detected", []) or []
    if not isinstance(issues_detected, list):
        issues_detected = [str(issues_detected)]
    violation_details_raw = classification.get("violation_details", []) or []
    if not isinstance(violation_details_raw, list):
        violation_details_raw = []
    can_auto_fix = classification.get("can_auto_fix", False)

    # Convert violation details to Pydantic models
    violation_details = [
        ViolationDetail(**v) for v in violation_details_raw
    ]

    logging.info(f"Processing reply: risk={risk_level}, confidence={confidence_score}, issues={issues_detected}, mode={SHR_MODE}")
    llm_raw_details = classification.get("llm_raw") or classification.get("llm_error")

    # Escalate if forbidden phrases are detected in draft_reply AND the reply is already flagged as high risk
    # This prevents false escalations when agents legitimately discuss fraud protection, blocking cards, etc.
    draft_text_lower = request.draft_reply.lower()
    if any(word in draft_text_lower for word in FORBIDDEN_KEYWORDS) and risk_level == "high":
        logging.warning("Escalation triggered by forbidden keyword in high-risk draft reply.")
        return RewriteResponse(
            risk_level="high",
            confidence_score=100,
            issues_detected=["Forbidden keyword detected: escalation required"],
            violation_details=violation_details,
            action="escalate",
            safe_reply="",
            explanation="Escalation required due to forbidden keyword in high-risk draft reply.",
            before_after_diff=None,
            escalate=True
        )

    policy_hits = detect_forbidden_phrases(request.draft_reply, policies)
    if policy_hits:
        logging.warning("Escalation triggered by policy forbidden phrase detection.")
        return RewriteResponse(
            risk_level="high",
            confidence_score=100,
            issues_detected=[f"Forbidden policy phrase detected: {', '.join(policy_hits)}"],
            violation_details=violation_details,
            action="escalate",
            safe_reply="",
            explanation="Escalation required due to forbidden policy phrases in draft reply.",
            before_after_diff=None,
            escalate=True
        )

    # Process based on risk level and fix capability (same logic for both modes)
    if risk_level == "low" and not issues_detected:
        logging.info(f"Reply passed through ({SHR_MODE} mode)")
        return RewriteResponse(
            risk_level=risk_level,
            confidence_score=confidence_score,
            issues_detected=[],
            violation_details=[],
            action="pass_through",
            safe_reply=request.draft_reply,
            explanation="No issues detected.",
            before_after_diff=None,
            escalate=False
        )
    elif can_auto_fix:
        rewritten = rewrite_message(context, request.draft_reply, policies_str, issues_detected)
        rewritten = clean_text(rewritten)
        explanation_raw = explain_changes(request.draft_reply, rewritten, policies_str, issues_detected)
        explanation_raw = clean_text(explanation_raw)
        
        # Parse explanation JSON with better error handling
        try:
            explanation_data = json.loads(explanation_raw)
            explanation = clean_text(explanation_data.get("explanation", explanation_raw))
            before_after_diff = clean_text(explanation_data.get("before_after_diff", ""))
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse explanation JSON: {e}")
            explanation = explanation_raw
            before_after_diff = ""
        
        logging.info(f"Reply auto-rewritten ({SHR_MODE} mode)")
        return RewriteResponse(
            risk_level=risk_level,
            confidence_score=confidence_score,
            issues_detected=issues_detected,
            violation_details=violation_details,
            action="rewritten",
            safe_reply=rewritten,
            explanation=explanation,
            before_after_diff=before_after_diff,
            escalate=False
        )
    else:
        logging.warning(f"Reply escalated ({SHR_MODE} mode)")
        # If LLM raw output is present, include it in explanation for debugging
        explanation = "Escalation required. Issues cannot be auto-fixed."
        if llm_raw_details:
            explanation += f" LLM details: {llm_raw_details}"
        return RewriteResponse(
            risk_level=risk_level,
            confidence_score=confidence_score,
            issues_detected=issues_detected,
            violation_details=violation_details,
            action="escalate",
            safe_reply="",
            explanation=explanation,
            before_after_diff=None,
            escalate=True
        )
