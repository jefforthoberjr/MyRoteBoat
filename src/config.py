"""Config loader -- reads src/assets/config.yaml once at import into CONFIG.

Access pattern everywhere else in the app:

    from config import CONFIG, stash_dir
    CONFIG["server"]["port"]

Keep this module tiny: loading + path helpers only. Knob documentation lives
in CONFIG_REFERENCE.md, not here."""
from pathlib import Path

import yaml

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_CONFIG_PATH = _ASSETS_DIR / "config.yaml"


def _load_config():
    with open(_CONFIG_PATH, "r") as f:
        loaded = yaml.safe_load(f)
    return loaded


def stash_dir():
    """The read-only file stash root, ~ expanded, as a Path."""
    raw = CONFIG["data"]["stash_dir"]
    return Path(raw).expanduser()


CONFIG = _load_config()
