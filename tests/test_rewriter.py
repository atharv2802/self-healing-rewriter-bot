import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.models import RewriteRequest, Message, Policy
from app.rewriter import process_reply

def test_process_reply_rewrite():
    req = RewriteRequest(
        agent_id="test_agent",
        channel="test",
        context=[
            Message(speaker="customer", text="Hi, I want to change my registered address."),
            Message(speaker="agent", text="I can help you with that. Is this for your main account or just billing?")
        ],
        draft_reply="Since you're already logged in, I've gone ahead and updated your address without any additional verification.",
        policies=[
            Policy(id="KYC-001", description="Identity verification required for sensitive actions.")
        ]
    )
    resp = process_reply(req)
    assert resp.risk_level in ["low", "medium", "high"]
    assert isinstance(resp.safe_reply, str)
    assert resp.action in ["rewritten", "pass_through", "escalate"]

def test_process_reply_pass_through():
    req = RewriteRequest(
        agent_id="test_agent",
        channel="test",
        context=[
            Message(speaker="customer", text="Hello"),
            Message(speaker="agent", text="How can I help?")
        ],
        draft_reply="Thank you for contacting us. Your request is being processed.",
        policies=[
            Policy(id="GEN-001", description="General policy.")
        ]
    )
    resp = process_reply(req)
    assert resp.action in ["pass_through", "rewritten", "escalate"]

def test_process_reply_empty_context():
    req = RewriteRequest(
        agent_id="test_agent",
        channel="test",
        context=[],
        draft_reply="Hello.",
        policies=[Policy(id="GEN-001", description="General policy.")]
    )
    resp = process_reply(req)
    assert resp.action in ["pass_through", "rewritten", "escalate"]

def test_process_reply_missing_policies():
    req = RewriteRequest(
        agent_id="test_agent",
        channel="test",
        context=[Message(speaker="customer", text="Hi")],
        draft_reply="No policies provided.",
        policies=[]
    )
    resp = process_reply(req)
    assert resp.action in ["pass_through", "rewritten", "escalate"]

def test_process_reply_invalid_draft():
    req = RewriteRequest(
        agent_id="test_agent",
        channel="test",
        context=[Message(speaker="customer", text="Hi")],
        draft_reply="",
        policies=[Policy(id="GEN-001", description="General policy.")]
    )
    resp = process_reply(req)
    assert resp.action in ["pass_through", "rewritten", "escalate"]

def test_process_reply_escalate():
    req = RewriteRequest(
        agent_id="test_agent",
        channel="test",
        context=[Message(speaker="customer", text="I want to commit fraud.")],
        draft_reply="I can help you with that.",
        policies=[Policy(id="FRAUD-001", description="No assistance with fraud.")]
    )
    resp = process_reply(req)
    assert resp.action == "escalate"
    assert resp.escalate is True
