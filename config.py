"""Configuration module for SHR application."""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME: Optional[str] = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
SHR_MODE: str = os.getenv("SHR_MODE", "suggestion")
SHR_LOG_LEVEL: str = os.getenv("SHR_LOG_LEVEL", "info")

# Set up logging
LOG_LEVELS = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warning": logging.WARNING,
    "error": logging.ERROR
}
logging.basicConfig(
    level=LOG_LEVELS.get(SHR_LOG_LEVEL.lower(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Validate required configuration
if not GROQ_API_KEY:
    logging.error("GROQ_API_KEY is not set in environment variables.")
    raise ValueError("GROQ_API_KEY environment variable is required")

if SHR_MODE not in ["suggestion", "guardrail"]:
    logging.warning(f"Invalid SHR_MODE '{SHR_MODE}'. Defaulting to 'suggestion'.")
    SHR_MODE = "suggestion"
