import json
from dataclasses import dataclass, asdict

from .paths import CONFIG_DIR, DEFAULT_GAME_DIR

CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Settings:
    game_dir: str = str(DEFAULT_GAME_DIR)
    ram_mb: int = 4096
    java_args: str = ""
    width: int = 854
    height: int = 480
    isolate_versions: bool = False
    theme: str = "dark"
    accent: str = "#3b82f6"
    last_version: str = ""
    download_source: str = "auto"   # mirror | auto | official
    forge_mirror: str = ""          # свой Forge-мирор
    ms_client_id: str = ""          # Client ID приложения Azure
    discord_enabled: bool = True    # Rich Presence включён по умолчанию
    discord_client_id: str = ""     # пусто = встроенный ID лаунчера
    hide_mode: str = "none"         # none | tray | hide | close
    settings_version: int = 3

    @classmethod
    def load(cls) -> "Settings":
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                version = data.get("settings_version", 1)
                if version < 2:
                    data["download_source"] = "auto"
                if version < 3:
                    data["discord_enabled"] = True   # раньше был выключен, пока не вписан ID
                    data["discord_client_id"] = ""
                data["settings_version"] = 3
                return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2))