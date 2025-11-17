from app.llm_client import classify_message, rewrite_message, explain_changes
from app.policies import format_policies_for_prompt, detect_forbidden_phrases
from app.models import RewriteRequest, RewriteResponse, ViolationDetail
import json
import logging
from config import SHR_MODE

def process_reply(request: RewriteRequest) -> RewriteResponse:
    context = [msg.dict() for msg in request.context]
    policies = [p.dict() for p in request.policies]
    policies_str = format_policies_for_prompt(policies)
    import re
    def clean_text(text):
        # Remove non-UTF-8 and replace common artifacts
        if not isinstance(text, str):
            return text
        text = text.encode('utf-8', errors='replace').decode('utf-8')
        # Replace common smart quote artifacts
        text = text.replace('ΓÇÖ', "’").replace('ΓÇ£', '“').replace('ΓÇ¥', '”').replace('ΓÇæ', '-')
        text = text.replace('├óΓé¼ΓÇ¥', '—').replace('├óΓé¼╦£', '‘').replace('Γé¼', '€')
        # Remove any remaining non-printable chars
        text = re.sub(r'[^\x20-\x7E’“”€—‘]', '', text)
        return text

    classification_raw = classify_message(context, request.draft_reply, policies_str)
    classification_raw = clean_text(classification_raw)
    classification = json.loads(classification_raw)
    
    risk_level = classification["risk_level"]
    confidence_score = classification.get("confidence_score", 50)
    issues_detected = classification["issues_detected"]
    violation_details_raw = classification.get("violation_details", [])
    can_auto_fix = classification["can_auto_fix"]
    
    # Convert violation details to Pydantic models
    violation_details = [
        ViolationDetail(**v) for v in violation_details_raw
    ]

    logging.info(f"Processing reply: risk={risk_level}, confidence={confidence_score}, issues={issues_detected}, mode={SHR_MODE}")

    if SHR_MODE == "guardrail":
        if risk_level == "low" and not issues_detected:
            logging.info("Reply passed through (guardrail mode)")
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
            # Parse explanation JSON
            try:
                explanation_data = json.loads(explanation_raw)
                explanation = clean_text(explanation_data.get("explanation", explanation_raw))
                before_after_diff = clean_text(explanation_data.get("before_after_diff", ""))
            except:
                explanation = explanation_raw
                before_after_diff = ""
            logging.info("Reply auto-rewritten (guardrail mode)")
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
            logging.warning("Reply escalated (guardrail mode)")
            # If LLM raw output is present, include it in explanation for debugging
            llm_raw = classification_raw if "llm_raw" in classification_raw or "llm_error" in classification_raw else None
            explanation = "Escalation required. Issues cannot be auto-fixed."
            if llm_raw:
                explanation += f" LLM raw output: {llm_raw}"
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
    else:  # suggestion mode
        if risk_level == "low" and not issues_detected:
            logging.info("Reply passed through (suggestion mode)")
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
            # Parse explanation JSON
            try:
                explanation_data = json.loads(explanation_raw)
                explanation = clean_text(explanation_data.get("explanation", explanation_raw))
                before_after_diff = clean_text(explanation_data.get("before_after_diff", ""))
            except:
                explanation = explanation_raw
                before_after_diff = ""
            logging.info("Reply suggested rewrite (suggestion mode)")
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
            logging.warning("Reply escalated (suggestion mode)")
            llm_raw = classification_raw if "llm_raw" in classification_raw or "llm_error" in classification_raw else None
            explanation = "Escalation required. Issues cannot be auto-fixed."
            if llm_raw:
                explanation += f" LLM raw output: {llm_raw}"
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
