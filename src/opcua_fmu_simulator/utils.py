# src/mypackage/utils.py
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_config() -> dict:
    cfg_file = PROJECT_ROOT / "config.yaml"
    with open(cfg_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _resolve_path(path: str) -> Path:
    """Resolve absolute or relative paths from config."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p

# ---- Experiments ----
def get_experiments_dir(cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    exp_dir = _resolve_path(cfg.get("experiments", {}).get("dir", "experiments/"))
    exp_dir.mkdir(parents=True, exist_ok=True)
    return exp_dir

EXPERIMENTS_DIR = get_experiments_dir()

# ---- Logs ----
def get_logs_dir(cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    logs_dir = _resolve_path(cfg.get("logging", {}).get("dir", "logs/"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

LOGS_DIR = get_logs_dir()

# ---- Database ----
def db_enabled(cfg: dict | None = None) -> bool:
    cfg = cfg or load_config()
    return bool(cfg.get("database", {}).get("enabled", False))

def get_db_dir(cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    db_dir = _resolve_path(cfg.get("database", {}).get("dir", "db/"))
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir

DB_DIR = get_db_dir() if db_enabled() else None