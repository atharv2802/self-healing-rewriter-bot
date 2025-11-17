import os
import logging
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
SHR_MODE = os.getenv("SHR_MODE", "suggestion")
SHR_LOG_LEVEL = os.getenv("SHR_LOG_LEVEL", "info")

# Set up logging
LOG_LEVELS = {
	"info": logging.INFO,
	"debug": logging.DEBUG,
	"warning": logging.WARNING
}
logging.basicConfig(level=LOG_LEVELS.get(SHR_LOG_LEVEL, logging.INFO))

if not GROQ_API_KEY:
	logging.error("GROQ_API_KEY is not set in environment variables.")
if not GROQ_MODEL_NAME:
	logging.warning("GROQ_MODEL_NAME is not set. Using default model.")
