import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.llm_client import classify_message

def test_classify_message_valid():
    context = [
        {"speaker": "customer", "text": "Hi, I want to change my registered address."},
        {"speaker": "agent", "text": "I can help you with that. Is this for your main account or just billing?"}
    ]
    draft_reply = "Since you're already logged in, I've gone ahead and updated your address without any additional verification."
    policies = "KYC-001: Identity verification required for sensitive actions."
    result = classify_message(context, draft_reply, policies)
    assert isinstance(result, str)
    assert "risk_level" in result
    assert "confidence_score" in result
