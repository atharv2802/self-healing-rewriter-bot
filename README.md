# Self-Healing Response Rewriter (SHR)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview
A stateless FastAPI microservice for financial compliance and risk rewriting of agent replies. SHR uses an LLM (Groq) to classify, rewrite, or escalate agent responses before they reach the customer, ensuring operational correctness and regulatory safety.

---

## Features
- **Stateless API**: No database, no persistence
- **LLM-powered**: Uses Groq for risk assessment, rewriting, and escalation
- **Policy-driven**: Customizable compliance policies, forbidden phrase detection, and preferred patterns
- **Batch & single processing**: Supports both single and batch requests (up to 100 per batch)
- **Partial failure handling**: Batch endpoint returns HTTP 207 Multi-Status for partial failures, HTTP 500 for total failure
- **Audit logging & error handling**: Structured logs, robust error reporting, and fallback logic for LLM errors
- **Configurable via .env**: Forbidden keywords, retry settings, and model parameters are environment-driven
- **Prompt injection safety**: All LLM prompt payloads are JSON-serialized to prevent injection and formatting errors
- **Offline testability**: Pytest fixture stubs LLM calls for deterministic, credential-free testing
- **SOC II ready**: Stateless, secure, and auditable

---

## API Endpoints
- `POST /rewrite_reply` — Rewrite or escalate risky agent replies (single request)
- `POST /rewrite_batch` — Batch rewrite or escalate (returns HTTP 207 for partial failures)
- `GET /health` — Health check

### Example Request
See `data/test_cases_example.json` for realistic payloads.

---

## Quickstart
```sh
# Clone the repo
cd shr
python -m venv shrenv
shrenv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Groq API key and model name
uvicorn app.main:app --reload
```

---

## Testing

Run the test runner to validate compliance logic:
```sh
python post_test_cases.py > results.txt
```

To view the output on a sample test case, check `results.txt`.

To run the full automated test suite offline:
```sh
pytest
```

---

## Contributing
Pull requests and issues are welcome! Please open an issue for feature requests or bug reports.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Limitations & Roadmap
- No authentication or persistence
- No frontend UI
- No database or stateful storage
- Future: granular policies, multi-LLM support, advanced escalation logic, Pydantic V2 migration

---

## Acknowledgments
- [FastAPI](https://fastapi.tiangolo.com/)
- [Groq](https://groq.com/)
- [Pydantic](https://docs.pydantic.dev/)