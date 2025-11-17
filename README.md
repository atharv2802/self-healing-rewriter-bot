# Self-Healing Response Rewriter (SHR)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview
A stateless FastAPI microservice for financial compliance and risk rewriting of agent replies. SHR uses an LLM (Groq) to classify, rewrite, or escalate agent responses before they reach the customer, ensuring operational correctness and regulatory safety.

---

## Features
- **Stateless API**: No database, no persistence
- **LLM-powered**: Uses Groq for risk assessment and rewriting
- **Policy-driven**: Customizable compliance policies
- **Batch & single processing**: (Single endpoint enabled by default)
- **Audit logging & error handling**
- **SOC II ready**: Stateless, secure, and auditable

---

## API Endpoints
- `POST /rewrite_reply` — Rewrite or escalate risky agent replies
- `GET /health` — Health check

### Example Request
See `data/test_cases_example.json` for realistic payloads.

---

## Quickstart
```sh
# Clone the repo
# git clone https://github.com/your-org/self-healing-response-rewriter.git
cd shr

# Create and activate virtual environment
python -m venv shrenv
shrenv\Scripts\activate  # Windows
# Or: source shrenv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Groq API key and model name

# Run the service
uvicorn app.main:app --reload
```

---

## Testing
Run the test runner to validate compliance logic:
```sh
python post_test_cases.py > results.txt
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
- Future: granular policies, multi-LLM support, advanced escalation logic
---

## Acknowledgments
- [FastAPI](https://fastapi.tiangolo.com/)
- [Groq](https://groq.com/)
- [Pydantic](https://docs.pydantic.dev/)