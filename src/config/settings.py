"""
Centralized settings - reads from Streamlit secrets or .env
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env for local development
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
SRC_DIR = BASE_DIR / "src"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# File paths
RESUME_MASTER_JSON = DATA_DIR / "resume_master.json"
JD_FILE = DATA_DIR / "job_description.txt"


def get_secret(key, default=None):
    """Get secret from Streamlit secrets or environment variable"""
    # Try Streamlit secrets first (for deployment)
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except:
        pass
    
    # Fallback to environment variable (for local)
    return os.getenv(key, default)


class Settings:
    """Application settings"""
    
    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    OUTPUT_DIR = OUTPUT_DIR
    RESUME_MASTER_JSON = RESUME_MASTER_JSON
    JD_FILE = JD_FILE
    
    # API Keys (securely loaded)
    OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
    
    # Models
    MODEL_JD_ANALYZER = get_secret("MODEL_JD_ANALYZER", "gpt-4o-mini")
    MODEL_RESUME_MATCHER = get_secret("MODEL_RESUME_MATCHER", "gpt-4o-mini")
    MODEL_OPTIMIZER = get_secret("MODEL_OPTIMIZER", "gpt-4o-mini")
    
    # Validation
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not found! "
            "Set it in .streamlit/secrets.toml (deployment) or .env (local)"
        )


settings = Settings()
