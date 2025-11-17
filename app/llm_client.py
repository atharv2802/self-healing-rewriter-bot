import os
import logging
import json
import time
from groq import Groq
from typing import List, Any
from config import GROQ_API_KEY, GROQ_MODEL_NAME, MAX_RETRIES, RETRY_DELAY

client = Groq(api_key=GROQ_API_KEY)


def _to_json(data: Any) -> str:
    """Serialize data to compact JSON for prompt injection safety."""
    try:
        return json.dumps(data, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(data), ensure_ascii=False)


def _call_llm_with_retry(messages: List[dict], max_retries: int = MAX_RETRIES) -> str:
    """Call LLM with automatic retry logic.
    
    Args:
        messages: List of message dictionaries for the LLM
        max_retries: Maximum number of retry attempts
        
    Returns:
        LLM response content
        
    Raises:
        Exception: If all retries fail
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logging.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logging.error(f"LLM call failed after {max_retries} attempts: {e}")
    
    raise last_error

def classify_message(context, draft_reply, policies):
    context_json = _to_json(context)
    draft_json = _to_json(draft_reply)
    policies_block = policies if isinstance(policies, str) else _to_json(policies)
    prompt = f"""
You are a compliance classifier. Analyze the draft reply against the policies below and return strict JSON.

Context JSON: {context_json}
Draft Reply JSON: {draft_json}
Policies: {policies_block}

CRITICAL RULES:
1. If the draft reply ALREADY complies with all policies, set risk_level="low" and issues_detected=[].
2. ONLY flag issues if there is an ACTUAL, EXPLICIT violation in the draft reply text.
3. Do NOT add requirements (like ID verification) unless the draft reply VIOLATES a policy that requires them.
4. If the reply is already safe and compliant, do NOT suggest adding extra steps.
5. Only detect violations that are PRESENT in the draft reply, not missing best practices.

REFUND/WAIVER DETECTION (REFUND-001):
- Flag phrases that GUARANTEE automatic refunds/waivers: "we waive all fees anyway", "we always waive", "automatically waive", "guaranteed refund", "always side with cardholder"
- These are VIOLATIONS because they make blanket guarantees without case-by-case review
- If the reply says "may", "might", "case-by-case", "we'll review", it's compliant

INSURANCE/GUARANTEE DETECTION (ADVICE-001):
- Flag false factual claims about insurance coverage, deposit guarantees, or regulatory protections
- If the draft makes a specific factual claim that could be false (like "fully government-insured" for investment products), this is a violation
- Do NOT attempt to correct factual claims by rewriting with opposite facts - these should escalate for human review

IDENTITY VERIFICATION (KYC-001):
- ONLY flag if the draft provides sensitive account info WITHOUT any verification
- Do NOT flag if the draft is refusing access until verification
- Do NOT add ID requirements to compliant responses
- Verification can include: date of birth, full name, phone number, email, security questions, etc. - NOT just government ID

Return this exact JSON structure:
{{
    "risk_level": "low" | "medium" | "high",
    "confidence_score": 0-100,
    "issues_detected": ["list actual policy violations only"],
    "violation_details": [
        {{
            "policy_id": "POLICY-ID",
            "policy_description": "Description",
            "violated_phrase": "exact phrase from draft that violates policy",
            "position_in_text": character_position
        }}
    ],
    "can_auto_fix": true/false
}}

Guidelines:
- risk_level="low" if no violations found
- can_auto_fix=true if violations can be rewritten (remove guarantees, soften language, add disclaimers)
- can_auto_fix=false for: fraud/scam, factual insurance claims (requires human fact-checking), legal exposure, unrecoverable breaches
- Do NOT invent violations that don't exist in the draft reply

STRICTLY output valid JSON only. No explanation or extra text.
"""
    try:
        content = _call_llm_with_retry([{"role": "user", "content": prompt}])
        # Validate output
        try:
            parsed = json.loads(content)
            required_fields = ["risk_level", "confidence_score", "issues_detected", "violation_details", "can_auto_fix"]
            if not all(field in parsed for field in required_fields):
                raise ValueError("Missing required fields in LLM output")
            logging.info(f"Classification response: {content}")
            return content
        except Exception as ve:
            logging.error(f"LLM output invalid: {ve}, raw: {content}")
            return json.dumps({
                "risk_level": "high",
                "confidence_score": 95,
                "issues_detected": ["LLM error or invalid response"],
                "violation_details": [],
                "can_auto_fix": False,
                "llm_raw": content
            })
    except Exception as e:
        logging.error(f"Groq classify_message failed: {e}")
        return json.dumps({
            "risk_level": "high",
            "confidence_score": 95,
            "issues_detected": ["LLM error or invalid response"],
            "violation_details": [],
            "can_auto_fix": False,
            "llm_error": str(e)
        })

def rewrite_message(context, draft_reply, policies, issues):
    context_json = _to_json(context)
    draft_json = _to_json(draft_reply)
    issues_json = _to_json(issues)
    policies_block = policies if isinstance(policies, str) else _to_json(policies)
    prompt = f"""
Rewrite the draft reply to fix ONLY the specific violations listed below. Preserve the original intent and tone.

Issues JSON: {issues_json}
Draft Reply JSON: {draft_json}
Policies: {policies_block}
Context JSON: {context_json}

IMPORTANT REWRITE RULES:
1. Fix ONLY the specific violations mentioned in the issues list.
2. Do NOT add extra requirements (like ID verification) unless explicitly needed to fix a violation.
3. Preserve the helpful, professional tone of the original.
4. Keep the reply concise and natural.
5. Do NOT over-engineer or add unnecessary steps.

SPECIFIC GUIDELINES:
- For refund/fee guarantees: Replace "always", "guaranteed", "automatically" with "may", "we'll review", "case-by-case"
- For ID verification: If the draft is ALREADY denying access until verification, do NOT add ID upload requirements
- For advice violations: Add disclaimers like "we recommend consulting a tax advisor" or "we can't guarantee outcomes"
- Do NOT make factual corrections (like changing "insured" to "not insured") - these should not be rewritten

Return ONLY the rewritten reply text, nothing else.
"""
    try:
        rewritten = _call_llm_with_retry([{"role": "user", "content": prompt}])
        logging.info(f"Rewrite response: {rewritten}")
        return rewritten
    except Exception as e:
        logging.error(f"Groq rewrite_message failed: {e}")
        return "[Rewrite failed: LLM error]"

def explain_changes(original, rewritten, policies, issues):
        original_json = _to_json(original)
        rewritten_json = _to_json(rewritten)
        issues_json = _to_json(issues)
        policies_block = policies if isinstance(policies, str) else _to_json(policies)
        prompt = f"""
    Explain the changes made to the original reply to comply with the policies and resolve issues listed below.

    Issues JSON: {issues_json}
    Original Reply JSON: {original_json}
    Rewritten Reply JSON: {rewritten_json}
    Policies: {policies_block}

    Limit your explanation to 30 words maximum. Be concise and clear.
    Also provide a before/after diff highlighting the key changes.
    Return JSON:
    {{
      "explanation": "concise explanation (max 30 words)",
      "before_after_diff": "markdown diff format showing changes"
    }}
    """
        try:
            result = _call_llm_with_retry([{"role": "user", "content": prompt}])
            logging.info(f"Explanation response: {result}")
            return result
        except Exception as e:
            logging.error(f"Groq explain_changes failed: {e}")
            return json.dumps({
                "explanation": "[Explanation failed: LLM error]",
                "before_after_diff": ""
            })
