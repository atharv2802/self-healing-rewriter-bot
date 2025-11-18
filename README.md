# Self-Healing Response Rewriter (SHR)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

A production-ready, stateless FastAPI microservice for real-time compliance and risk rewriting of agent replies in financial services. SHR uses LLM-powered classification to detect policy violations, safely rewrite risky responses, or escalate unrecoverable issues—ensuring operational correctness and regulatory safety before messages reach customers.

---

## Why This Project Is Relevant to Rulebase

This microservice demonstrates **real-time AI rewriting and compliance workflows** directly aligned with Rulebase's agent-intelligence and QA platform capabilities:

- **Guardrails & Safe Rewrites**: Automatically detects and corrects policy violations (KYC, refund guarantees, tax advice, PCI compliance) without halting agent workflows.
- **Escalation Logic**: Distinguishes between auto-fixable issues and critical risks requiring human review (fraud, sanctions, factual insurance claims).
- **Policy-Driven Reasoning**: Structured, versionable policy configs drive classification and rewriting decisions, mirroring enterprise compliance stacks.
- **Real-Time Processing**: Stateless, low-latency API design supports high-throughput agent assistance platforms.
- **Deterministic & Testable**: JSON-serialized prompts, offline test fixtures, and strict schema validation ensure reliability in production environments.

This project showcases the engineering depth required to build **safe, compliant, and observable AI systems** at scale—core competencies for an AI Engineer role at Rulebase.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INCOMING REQUEST                                    │
│  Agent Draft Reply + Conversation Context + Policy Configuration            │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STEP 1: RISK CLASSIFICATION                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • LLM analyzes draft against policies                               │    │
│  │ • Assigns risk level: LOW | MEDIUM | HIGH                          │    │
│  │ • Identifies specific violations (policy ID, phrase, position)      │    │
│  │ • Determines if auto-fixable vs. escalation required               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
                   ▼                           ▼
        ┌──────────────────┐        ┌──────────────────┐
        │   LOW RISK       │        │  MEDIUM/HIGH     │
        │  No violations   │        │   Violations     │
        └────────┬─────────┘        └────────┬─────────┘
                 │                           │
                 ▼                           ▼
        ┌──────────────────┐        ┌──────────────────┐
        │  PASS THROUGH    │        │  Can Auto-Fix?   │
        │  Return original │        └────────┬─────────┘
        └──────────────────┘                 │
                                   ┌─────────┴─────────┐
                                   │                   │
                                   ▼                   ▼
                        ┌──────────────────┐  ┌──────────────────┐
                        │  STEP 2: REWRITE │  │ STEP 3: ESCALATE │
                        │                  │  │                  │
                        │ • LLM rewrites   │  │ • Flag for human │
                        │ • Remove issues  │  │ • Include context│
                        │ • Add disclaimers│  │ • Log violation  │
                        │ • Preserve intent│  │ • Return empty   │
                        └────────┬─────────┘  └────────┬─────────┘
                                 │                     │
                                 ▼                     ▼
                        ┌──────────────────┐  ┌──────────────────┐
                        │ STEP 4: EXPLAIN  │  │  escalate=true   │
                        │                  │  │  safe_reply=""   │
                        │ • Before/after   │  └──────────────────┘
                        │ • Violation list │
                        │ • Confidence     │
                        └────────┬─────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FINAL RESPONSE                                      │
│  {                                                                           │
│    risk_level, confidence_score, issues_detected, violation_details,        │
│    action: "pass_through" | "rewritten" | "escalate",                       │
│    safe_reply, explanation, before_after_diff, escalate: bool               │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

1. **Risk Classification**: Incoming draft reply + context + policies → LLM classifies risk level (low/medium/high) and identifies specific violations.
2. **Safe Rewrite**: If violations are auto-fixable, LLM rewrites the message to remove guarantees, add disclaimers, or soften language while preserving intent.
3. **Escalation**: High-risk messages (fraud, factual errors, legal exposure) are flagged for human review with detailed violation context.
4. **Final Response**: Safe, compliant reply returned to the agent interface with full audit trail (before/after diff, explanation, confidence score).

**Key Design Principles**:
- Strict JSON prompts with validated schemas prevent hallucinated outputs
- Policy configs are versionable and environment-driven (`.env` overrides)
- Deterministic decision logic ensures reproducible outcomes across deployments

---

## Features

- **Stateless Architecture**: Zero persistence, horizontally scalable, cloud-native design
- **LLM-Powered Intelligence**: Groq-based classification, rewriting, and explanation generation
- **Policy-Driven Compliance**: Customizable policies with forbidden phrase detection, verification requirements, and preferred patterns
- **Batch & Single Processing**: Supports individual requests and batches up to 100 items with partial failure handling
- **Partial Failure Resilience**: Batch endpoint returns HTTP 207 Multi-Status for partial failures, HTTP 500 only when all items fail
- **Robust Error Handling**: Automatic LLM retries (exponential backoff), fallback responses, and structured error logging
- **Prompt Injection Safety**: All prompt payloads JSON-serialized to prevent template corruption and injection attacks
- **Offline Testability**: Pytest fixtures stub LLM calls for deterministic, credential-free CI/CD pipelines
- **Production Logging**: Structured logs with correlation IDs, error traces, and compliance audit trails
- **Environment-Driven Config**: Forbidden keywords, retry limits, and model parameters configurable via `.env`
- **Prometheus Metrics**: Built-in `/metrics` endpoint for monitoring request latency, throughput, error rates, and HTTP status distributions
- **CORS Protection**: Strict origin controls with environment-based configuration for local development and production deployments
- **User-Friendly Error Messages**: Clear, actionable error responses with field-level validation details and suggestions for resolution

---

## API Endpoints

| Endpoint | Method | Description | Response Codes |
|----------|--------|-------------|----------------|
| `/rewrite_reply` | POST | Process single draft reply for compliance rewriting | 200 (success), 422 (validation error), 500 (server error) |
| `/rewrite_batch` | POST | Process batch of up to 100 draft replies | 200 (all success), 207 (partial failure), 500 (all failed) |
| `/health` | GET | Health check and version info | 200 |
| `/metrics` | GET | Prometheus metrics for monitoring (request count, latency, errors) | 200 |

### Request Schema (`/rewrite_reply`)

```json
{
  "agent_id": "agent_123",
  "channel": "chat",
  "context": [
    {"speaker": "customer", "text": "I want to update my address."},
    {"speaker": "agent", "text": "I can help with that."}
  ],
  "draft_reply": "I've updated your address without verification.",
  "policies": [
    {
      "id": "KYC-001",
      "description": "Identity verification required for sensitive actions",
      "requires_verification": true,
      "forbidden_phrases": ["without verification"],
      "preferred_pattern": "Please verify your identity first"
    }
  ]
}
```

### Response Schema

```json
{
  "risk_level": "medium",
  "confidence_score": 85,
  "issues_detected": ["KYC-001: Missing identity verification"],
  "violation_details": [
    {
      "policy_id": "KYC-001",
      "policy_description": "Identity verification required",
      "violated_phrase": "without verification",
      "position_in_text": 23
    }
  ],
  "action": "rewritten",
  "safe_reply": "I can help update your address. Please verify your identity first by providing your date of birth.",
  "explanation": "Added identity verification requirement to comply with KYC-001.",
  "before_after_diff": "- without verification\n+ Please verify your identity first",
  "escalate": false
}
```

### Batch Endpoint Behavior

- **HTTP 200**: All requests processed successfully
- **HTTP 207 Multi-Status**: Some requests failed; response includes `failed_indices` array
- **HTTP 500**: All requests failed (e.g., LLM service unavailable)

Batch response format for partial failures:
```json
{
  "results": [ /* array of RewriteResponse objects */ ],
  "failed_indices": [2, 7],
  "message": "Some batch items failed; see failed_indices for details"
}
```

---

## Rewrite Examples

### Example 1: Safe Rewrite (Fee Waiver Guarantee)

**Input Draft**:  
`"Don't worry, we waive all overdraft fees anyway, so you won't be charged."`

**Policy Violated**: `REFUND-001` (No blanket refund guarantees)

**Safe Rewrite**:  
`"We'll review your account for potential fee waivers on a case-by-case basis."`

**Explanation**: Removed guarantee of automatic fee waiver; replaced with conditional review language.

---

### Example 2: Escalation Required (Fraud Discussion)

**Input Draft**:  
`"Yes, I can help you structure transactions to avoid reporting requirements."`

**Policy Violated**: Critical compliance breach (fraud/sanctions evasion)

**Action**: `escalate`  
**Escalate**: `true`  
**Explanation**: Draft suggests illegal activity; requires immediate human review and agent coaching.

---

### Example 3: No Changes Needed (Compliant Response)

**Input Draft**:  
`"I've blocked your card and initiated a fraud claim as requested. You'll receive confirmation within 24 hours."`

**Risk Level**: `low`  
**Action**: `pass_through`  
**Explanation**: No policy violations detected; response is compliant and helpful.

---

## Guardrail & Compliance Strategy

### Policy-First Design

SHR implements a **policy-as-code** architecture where compliance rules are:
- Explicitly defined in structured JSON configs (`data/policies_example.json`)
- Version-controlled alongside application code
- Environment-overridable for multi-tenant or regional compliance variations

### Preventing LLM Hallucinations

1. **JSON-Serialized Prompts**: All context, policies, and draft text are serialized to JSON before embedding into LLM prompts, preventing template injection and formatting errors.
2. **Strict Output Schemas**: LLM responses are validated against Pydantic models with required fields; malformed outputs trigger fallback escalation.
3. **Deterministic Classification**: Risk levels and violation detection follow explicit rules (forbidden phrases, pattern matching) before LLM interpretation.

### Real-World Compliance Alignment

This architecture mirrors production compliance stacks in financial services:
- **Pre-send validation**: Messages are checked before customer delivery, not retroactively
- **Explainability**: Every rewrite includes before/after diff, violation details, and confidence scores for audit trails
- **Human-in-the-loop**: Critical issues (fraud, legal exposure) escalate to supervisors rather than risking auto-rewrites
- **Policy evolution**: New regulations can be added as new policy entries without code changes

---

## Microservice Design Philosophy

### Stateless Architecture
- No database or persistent storage required
- Each request is self-contained with context, policies, and draft text
- Horizontally scalable across multiple instances
- Cloud-native deployment (Docker, Kubernetes, serverless)

### Config-Driven Behavior
All operational parameters externalized to `.env` and `config.py`:
- `GROQ_API_KEY`, `GROQ_MODEL_NAME`: LLM provider settings
- `SHR_MODE`: `guardrail` (block unsafe) or `suggestion` (flag only)
- `SHR_FORBIDDEN_KEYWORDS`: Comma-separated escalation triggers
- `SHR_MAX_RETRIES`, `SHR_RETRY_DELAY`: Resilience tuning
- `SHR_LOG_LEVEL`: Observability control
- `CORS_ORIGINS`: Comma-separated list of allowed origins (default: localhost for development)

### Production-Friendly Operations
- **Structured Logging**: JSON-formatted logs with severity, timestamps, and correlation IDs
- **Error Handling**: Graceful degradation with fallback responses for LLM failures
- **Batch Resilience**: Partial failures don't block entire batch; failed items return synthetic escalation responses
- **Health Checks**: `/health` endpoint for liveness/readiness probes in orchestration platforms
- **Prometheus Metrics**: `/metrics` endpoint exposes request count, latency histograms, error rates, and HTTP status code distributions for observability
- **CORS Security**: Configurable cross-origin resource sharing with strict origin allowlists to prevent unauthorized API access
- **Actionable Error Messages**: Validation errors return field-level details with suggestions (e.g., "Missing required field: agent_id. See /docs for schema.")

---

## Quickstart

### Prerequisites
- Python 3.11+
- Groq API key ([sign up here](https://groq.com/))

### Setup

```bash
# Clone repository
git clone https://github.com/atharv2802/selh-healing-rewriter-bot.git
cd shr

# Create virtual environment
python -m venv shrenv
shrenv\Scripts\activate  # Windows
# source shrenv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Groq API key and desired settings
```

### Run Service

```bash
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`  
Metrics endpoint: `http://localhost:8000/metrics`

---

## Observability & Security Features

### Prometheus Metrics

The `/metrics` endpoint provides comprehensive monitoring data in Prometheus format:

- **Request metrics**: Total request count, requests per second
- **Latency histograms**: Response time distribution for all endpoints
- **Error tracking**: HTTP status code counts (2xx, 4xx, 5xx)
- **Policy hit rates**: Track which compliance policies trigger most frequently (via custom labels)

**Example metrics output**:
```
http_requests_total{method="POST",path="/rewrite_reply",status="200"} 1247
http_request_duration_seconds_bucket{le="0.5",path="/rewrite_reply"} 1200
http_request_duration_seconds_sum{path="/rewrite_reply"} 245.3
```

Integrate with Prometheus/Grafana for real-time dashboards and alerting.

### CORS Configuration

Cross-Origin Resource Sharing (CORS) is enabled with strict origin controls to prevent unauthorized access:

**Default behavior** (local development):
- Allows: `http://localhost`, `http://localhost:8000`, `http://127.0.0.1`, `http://127.0.0.1:8000`
- Credentials: Enabled for authenticated requests
- Methods: `GET`, `POST` only

**Production configuration**:
Set the `CORS_ORIGINS` environment variable with your trusted domains:

```bash
# .env file
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

This prevents malicious websites from calling your API from browsers while allowing your own frontend applications.

### Improved Error Messages

All validation and server errors return structured, actionable responses:

**Validation error example** (HTTP 422):
```json
{
  "error": "Validation Error",
  "message": "The request contains invalid or missing fields.",
  "details": [
    "body -> agent_id: field required",
    "body -> draft_reply: field required"
  ],
  "suggestion": "Please check the API documentation at /docs for the correct request format."
}
```

**Server error example** (HTTP 500):
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while processing your request.",
  "suggestion": "Please try again. If the problem persists, contact support with the timestamp of this error."
}
```

---

## Testing

### Sample Test Cases

Run the compliance test suite against realistic scenarios:

```bash
python post_test_cases.py > results.txt
```

View detailed output including risk classifications, rewrites, and violation details in `results.txt`.

### Automated Unit Tests

Run offline tests with mocked LLM calls:

```bash
pytest
```

All tests use deterministic fixtures (no API credentials required) for CI/CD pipelines.

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-policy`)
3. Add tests for new functionality
4. Submit a pull request with clear description

For bug reports or feature requests, open an issue with reproduction steps.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Limitations & Future Roadmap


### Current Limitations
- **No Authentication**: API is unauthenticated; add OAuth2/API keys for production
- **Single LLM Provider**: Groq-only; no fallback to alternative providers
- **No Policy Versioning**: Policies are runtime-loaded; no historical versioning or A/B testing
- **No Multi-Tenant Isolation**: All requests share the same policy set; no per-organization separation

### Planned Enhancements
- **Policy Versioning**: Track policy changes, rollback capabilities, and multi-version testing
- **Multi-Tenant Support**: Isolated policy sets per organization or business unit
- **Advanced Rule Reporting**: Detailed analytics on which policies trigger most frequently
- **Multi-LLM Fallback**: Support for OpenAI, Anthropic, or local models as backup providers
- **Streaming Responses**: Server-sent events for real-time rewrite feedback in agent UIs
- **Pydantic V2 Migration**: Upgrade to latest Pydantic for improved performance and validation
- **Authentication & API Security**: Add OAuth2 or API key support for production deployments
- **Custom Metrics & Dashboards**: Expand Prometheus metrics to include business KPIs and custom compliance analytics

### Proposed Future Scope: ML Training & Reinforcement Learning

- **RL-Based Policy Optimization**: Train a reinforcement learning agent to learn optimal rewriting strategies from human feedback (RLHF). Reward model trained on supervisor approvals/rejections of rewrites, with progressive policy refinement based on escalation rates and customer satisfaction scores.

- **Fine-Tuned Compliance Models**: Domain-specific fine-tuning on financial services compliance data, custom embeddings trained on policy documents and regulatory guidelines, and distillation of large LLM knowledge into smaller, faster specialized models for production deployment.

- **Active Learning Pipeline**: Identify edge cases where model confidence is low, route uncertain cases to human experts for labeling, and continuously retrain on newly labeled examples to improve accuracy and reduce false positives/negatives.

- **Multi-Armed Bandit for Policy Selection**: A/B test multiple rewriting strategies in production, dynamically allocate traffic to best-performing approaches, and optimize for metrics like compliance rate, customer satisfaction, and agent efficiency.

- **Contextual Embeddings & Similarity Search**: Build vector database of compliant response templates, retrieve similar historical rewrites for few-shot prompting, and implement semantic clustering of policy violations for better categorization and faster classification.

- **Automated Policy Discovery**: Use unsupervised learning to detect emerging risky patterns in agent communications, suggest new policy rules based on escalation trends, and implement anomaly detection for novel compliance risks before they become systematic issues.

---

## Acknowledgments

Built with best-in-class tools for production AI systems:
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance async web framework
- [Groq](https://groq.com/) — Ultra-fast LLM inference
- [Pydantic](https://docs.pydantic.dev/) — Runtime type validation and serialization
- [Pytest](https://pytest.org/) — Testing framework with fixtures and mocking support