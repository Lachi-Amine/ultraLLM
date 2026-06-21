import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "DATASET"
GREEN_DATA_PATH = DATA_DIR / "Green.yaml"
RED_DATA_PATH = DATA_DIR / "Red.yaml"

OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").lower() not in {"0", "false", "no"}
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:0.8b")
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "2m")
YELLOW_DATA_PATH = DATA_DIR / "Yellow.yaml"
