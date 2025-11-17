import json
import pytest


@pytest.fixture(autouse=True)
def stub_llm_calls(monkeypatch):
    """Stub out Groq LLM calls for deterministic tests."""

    def fake_call(messages, max_retries=None):
        prompt = messages[0]["content"].lower()
        if "rewrite the draft reply" in prompt:
            return "SAFE REWRITE"
        if "explain the changes" in prompt:
            return json.dumps({
                "explanation": "stub explanation",
                "before_after_diff": "- old\n+ new"
            })
        # classification fallback
        risk = "high" if "fraud" in prompt else "low"
        issues = ["FRAUD-001"] if risk == "high" else []
        can_auto_fix = risk != "high"
        return json.dumps({
            "risk_level": risk,
            "confidence_score": 99 if risk == "low" else 70,
            "issues_detected": issues,
            "violation_details": [
                {
                    "policy_id": "FRAUD-001",
                    "policy_description": "No fraud assistance",
                    "violated_phrase": "fraud",
                    "position_in_text": 0
                }
            ] if risk == "high" else [],
            "can_auto_fix": can_auto_fix
        })

    monkeypatch.setattr("app.llm_client._call_llm_with_retry", fake_call)