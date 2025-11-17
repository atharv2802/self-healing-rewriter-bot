"""Configuration module for SHR application."""
import os
import logging
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


def _parse_list_env(var_name: str, default: List[str]) -> List[str]:
    value = os.getenv(var_name)
    if not value:
        return default
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or default


GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME: Optional[str] = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
SHR_MODE: str = os.getenv("SHR_MODE", "suggestion")
SHR_LOG_LEVEL: str = os.getenv("SHR_LOG_LEVEL", "info")

# Forbidden keywords that trigger escalation when found in high-risk replies
DEFAULT_FORBIDDEN = ["fraud", "scam", "money laundering", "embezzle", "bribe"]
FORBIDDEN_KEYWORDS: List[str] = _parse_list_env("SHR_FORBIDDEN_KEYWORDS", DEFAULT_FORBIDDEN)

# LLM retry configuration
MAX_RETRIES: int = int(os.getenv("SHR_MAX_RETRIES", 3))
RETRY_DELAY: float = float(os.getenv("SHR_RETRY_DELAY", 1.0))  # seconds

LOG_LEVELS = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warning": logging.WARNING,
    "error": logging.ERROR
}


def configure_logging(level_name: str = SHR_LOG_LEVEL) -> None:
    """Configure root logging once using provided level name."""
    if logging.getLogger().handlers:
        return
    level = LOG_LEVELS.get(level_name.lower(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


# Validate required configuration
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

if SHR_MODE not in ["guardrail", "suggestion"]:
    raise ValueError(f"Invalid SHR_MODE: {SHR_MODE}. Must be 'guardrail' or 'suggestion'")


configure_logging()
