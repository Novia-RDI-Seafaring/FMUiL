from __future__ import annotations
from pathlib import Path
import os, yaml
from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict

# ---- Paths ----
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _resolve_path(p: Path) -> Path:
    """Make relative paths absolute to PROJECT_ROOT."""
    return p if p.is_absolute() else PROJECT_ROOT / p

# ---- Reusable mixin for models that have a `dir: Path` ----
class Dir(BaseModel):
    dir: Path = Field(..., description="Directory path")

    @field_validator("dir", mode="after")
    @classmethod
    def _make_absolute(cls, v: Path) -> Path:
        return _resolve_path(v)

    model_config = ConfigDict(extra="forbid")  # catch typos in config

# ---- Config sections ----
class ExperimentsConfig(Dir):
    dir: Path = Field(default=Path("experiments/"), description="Directory with experiment .yaml configs")

class LoggingConfig(Dir):
    dir: Path = Field(default=Path("logs/"), description="Directory where log files are stored")

class DBConfig(Dir):
    enabled: bool = Field(default=True, description="Whether to use the database")
    dir: Path = Field(default=Path("db/"), description="Directory where the database file is stored")
    name: str = Field(default="database", description="Database filename (without extension or with .db)")

    @property
    def file(self) -> Path:
        # Accept either "database" or "database.db" in config
        return self.dir / (self.name if Path(self.name).suffix else f"{self.name}.db")

class ServerConfig(BaseModel):
    base_port: int = Field(default=7000, description="Base port for the server")

    model_config = ConfigDict(extra="forbid")

class Config(BaseModel):
    experiments: ExperimentsConfig = Field(default_factory=ExperimentsConfig, description="Experiments configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    db: DBConfig = Field(default_factory=DBConfig, description="Database configuration")
    model_config = ConfigDict(extra="forbid")
    server: ServerConfig = Field(default_factory=ServerConfig, description="Server configuration")

# ---- Loader ----
def load_config(path: str | os.PathLike | None = None) -> Config:
    """
    Loads YAML from:
      1) explicit path, or
      2) $MYPACKAGE_CONFIG, or
      3) PROJECT_ROOT/config.yaml (if present)
    Missing file => use defaults.
    """
    cfg_path = Path(path) if path else Path(os.getenv("MYPACKAGE_CONFIG", PROJECT_ROOT / "config.yaml"))
    data: dict = {}
    if cfg_path.is_file():
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return Config.model_validate(data)
