import os
import logging
import json
from groq import Groq
from typing import List
from config import GROQ_API_KEY, GROQ_MODEL_NAME

client = Groq(api_key=GROQ_API_KEY)

def classify_message(context, draft_reply, policies):
    prompt = f"""
Given the following context and draft reply, classify the risk and issues according to the policies below. Return strict JSON ONLY, with all required fields present:
{{
    "risk_level": "low" | "medium" | "high",
    "confidence_score": 0-100,
    "issues_detected": [...],
    "violation_details": [
        {{
            "policy_id": "POLICY-ID",
            "policy_description": "Description",
            "violated_phrase": "exact phrase from draft",
            "position_in_text": character_position
        }}
    ],
    "can_auto_fix": true/false
}}
Context: {context}
Draft Reply: {draft_reply}
Policies: {policies}

IMPORTANT:
- If the reply can be made compliant by rewriting (removing, rephrasing, or adding required info), set can_auto_fix to true, even for medium risk.
- Only set can_auto_fix to false and escalate if the reply is fundamentally unfixable (e.g., fraud, legal exposure, non-recoverable compliance breach).
- For medium risk, prefer rewriting unless escalation is absolutely required.
- confidence_score should reflect how certain you are about the classification (0-100)
- violation_details must list each specific violation with the exact phrase and its position
- Include all violated phrases found in the draft reply

If you cannot classify or are unsure, return this fallback JSON:
{{
    "risk_level": "high",
    "confidence_score": 95,
    "issues_detected": ["LLM error or invalid response"],
    "violation_details": [],
    "can_auto_fix": false
}}
STRICTLY output valid JSON only. Do not include any explanation or extra text.
"""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
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
    prompt = f"""
Rewrite the draft reply to resolve the following issues: {issues}. Use the policies below. Return only the rewritten reply.
Context: {context}
Draft Reply: {draft_reply}
Policies: {policies}
"""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        rewritten = response.choices[0].message.content
        logging.info(f"Rewrite response: {rewritten}")
        return rewritten
    except Exception as e:
        logging.error(f"Groq rewrite_message failed: {e}")
        return "[Rewrite failed: LLM error]"

def explain_changes(original, rewritten, policies, issues):
        prompt = f"""
    Explain the changes made to the original reply to comply with the policies and resolve issues: {issues}.

    Original: {original}
    Rewritten: {rewritten}
    Policies: {policies}

    Limit your explanation to 30 words maximum. Be concise and clear.
    Also provide a before/after diff highlighting the key changes.
    Return JSON:
    {{
      "explanation": "concise explanation (max 30 words)",
      "before_after_diff": "markdown diff format showing changes"
    }}
    """
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content
            logging.info(f"Explanation response: {result}")
            return result
        except Exception as e:
            logging.error(f"Groq explain_changes failed: {e}")
            return json.dumps({
                "explanation": "[Explanation failed: LLM error]",
                "before_after_diff": ""
            })
