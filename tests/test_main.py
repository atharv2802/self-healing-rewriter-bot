import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import RewriteRequest, Message, Policy

client = TestClient(app)

def sample_request():
    return {
        "agent_id": "test_agent",
        "channel": "test",
        "context": [
            {"speaker": "customer", "text": "Hi, I want to change my registered address."},
            {"speaker": "agent", "text": "I can help you with that. Is this for your main account or just billing?"}
        ],
        "draft_reply": "Since you're already logged in, I've gone ahead and updated your address without any additional verification.",
        "policies": [
            {"id": "KYC-001", "description": "Identity verification required for sensitive actions."}
        ]
    }

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_rewrite_reply():
    req = sample_request()
    response = client.post("/rewrite_reply", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data
    assert "safe_reply" in data
    assert "action" in data
    assert data["risk_level"] in ["low", "medium", "high"]
    assert isinstance(data["safe_reply"], str)
    assert data["action"] in ["rewritten", "pass_through", "escalate"]

def test_rewrite_reply_empty_context():
    req = sample_request()
    req["context"] = []
    response = client.post("/rewrite_reply", json=req)
    assert response.status_code == 200
    assert response.json()["action"] in ["pass_through", "rewritten", "escalate"]

def test_rewrite_reply_missing_policies():
    req = sample_request()
    req["policies"] = []
    response = client.post("/rewrite_reply", json=req)
    assert response.status_code == 200
    assert response.json()["action"] in ["pass_through", "rewritten", "escalate"]

def test_rewrite_reply_invalid_draft():
    req = sample_request()
    req["draft_reply"] = ""
    response = client.post("/rewrite_reply", json=req)
    assert response.status_code == 200
    assert response.json()["action"] in ["pass_through", "rewritten", "escalate"]

def test_rewrite_reply_escalate():
    req = {
        "agent_id": "test_agent",
        "channel": "test",
        "context": [{"speaker": "customer", "text": "I want to commit fraud."}],
        "draft_reply": "I can help you with that.",
        "policies": [{"id": "FRAUD-001", "description": "No assistance with fraud."}]
    }
    response = client.post("/rewrite_reply", json=req)
    assert response.status_code == 200
    assert response.json()["action"] == "escalate"
    assert response.json()["escalate"] is True
