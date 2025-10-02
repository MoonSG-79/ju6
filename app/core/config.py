
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
(DATA_DIR := ROOT / "data").mkdir(parents=True, exist_ok=True)
(ROOT / "db").mkdir(parents=True, exist_ok=True)
(ROOT / "logs").mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env", override=True)

try:
    import yaml  # optional
except Exception:
    yaml = None

CFG = {}
cfg_path = ROOT / "config.yaml"
if yaml and cfg_path.exists():
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            CFG = yaml.safe_load(f) or {}
    except Exception:
        CFG = {}

DB_PATH = ROOT / "db" / "app.sqlite"
LOG_PATH = ROOT / "logs" / "app.log"

def get(key, default=None):
    return os.getenv(key) or CFG.get(key, default)
