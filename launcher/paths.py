import os
import sys
from pathlib import Path

APP = "pycraft-launcher"
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"


def _dir(xdg_var: str, linux_default: str, win_var: str, win_default: str) -> Path:
    if IS_WIN:
        return Path(os.environ.get(win_var) or Path.home() / win_default) / APP
    return Path(os.environ.get(xdg_var) or Path.home() / linux_default) / APP


CONFIG_DIR = _dir("XDG_CONFIG_HOME", ".config", "APPDATA", "AppData/Roaming")
DATA_DIR = _dir("XDG_DATA_HOME", ".local/share", "LOCALAPPDATA", "AppData/Local")
CACHE_DIR = (DATA_DIR / "cache") if IS_WIN else _dir("XDG_CACHE_HOME", ".cache", "LOCALAPPDATA", "AppData/Local")

if IS_WIN:
    DEFAULT_GAME_DIR = Path(os.environ.get("APPDATA") or Path.home() / "AppData/Roaming") / ".minecraft"
elif IS_MAC:
    DEFAULT_GAME_DIR = Path.home() / "Library/Application Support/minecraft"
else:
    DEFAULT_GAME_DIR = Path.home() / ".minecraft"

for d in (CONFIG_DIR, DATA_DIR, CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)