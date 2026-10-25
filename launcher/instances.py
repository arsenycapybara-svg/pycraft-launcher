"""Профили (сборки): у каждого своя папка с модами, мирами и настройками."""
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .minecraft import runner
from .paths import CONFIG_DIR

FILE = CONFIG_DIR / "instances.json"

LOADER_NAMES = {
    "vanilla": "Vanilla", "fabric": "Fabric", "forge": "Forge",
    "neoforge": "NeoForge", "quilt": "Quilt", "optifine": "OptiFine",
}

# встроенные иконки профилей (рисуются в ProfileIcon.qml)
ICON_IDS = ["cube", "sword", "pickaxe", "heart", "star", "shield",
            "flame", "leaf", "skull", "crown", "bolt", "gem"]


@dataclass
class Instance:
    id: str
    name: str
    version: str = ""        # id установленной версии (vanilla / fabric / forge)
    shared: bool = False     # True = общая папка игры (.minecraft)
    ram_mb: int = 0          # 0 = как в настройках
    java_args: str = ""      # добавляется к общим аргументам
    created: float = 0.0
    last_played: float = 0.0
    icon: str = "cube"
    play_seconds: float = 0.0

    def work_dir(self, game_dir: str) -> Path:
        base = Path(game_dir)
        return base if self.shared else base / "instances" / self.id


def loader_and_mc(game_dir: str, version_id: str) -> tuple[str, str]:
    """Загрузчик и версия Minecraft для установленной версии."""
    low = version_id.lower()
    if low.startswith("fabric-loader-"):
        loader = "fabric"
    elif "neoforge" in low:
        loader = "neoforge"
    elif "forge" in low:
        loader = "forge"
    elif low.startswith("quilt-loader-"):
        loader = "quilt"
    elif "optifine" in low:
        loader = "optifine"
    else:
        loader = "vanilla"
    data = runner.read_version_json(game_dir, version_id)
    return loader, data.get("inheritsFrom") or version_id


class InstanceStore:
    def __init__(self) -> None:
        self.items: list[Instance] = []
        self.selected: str = ""
        self.initialized = False
        self._load()

    def _load(self) -> None:
        if not FILE.exists():
            return
        try:
            data = json.loads(FILE.read_text())
            fields = Instance.__dataclass_fields__
            self.items = [Instance(**{k: v for k, v in i.items() if k in fields})
                          for i in data.get("instances", [])]
            self.selected = data.get("selected", "")
            self.initialized = True
        except (OSError, ValueError, TypeError):
            pass

    def save(self) -> None:
        payload = {"instances": [asdict(i) for i in self.items], "selected": self.selected}
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        tmp.replace(FILE)

    def ensure_default(self, game_dir: str, last_version: str) -> None:
        """При первом запуске создаёт профиль «Основной» на общей папке."""
        if self.initialized:
            return
        installed = runner.installed_versions(game_dir)
        version = last_version if last_version in installed else (installed[0] if installed else "")
        inst = Instance(id="main", name="Основной", version=version, shared=True,
                        created=time.time())
        self.items.append(inst)
        self.selected = inst.id
        self.initialized = True
        self.save()

    def new_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:24] or "profile"
        return f"{slug}-{uuid.uuid4().hex[:6]}"

    def get(self, inst_id: str) -> Instance | None:
        return next((i for i in self.items if i.id == inst_id), None)

    def current(self) -> Instance | None:
        return self.get(self.selected) or (self.items[0] if self.items else None)

    def add(self, inst: Instance) -> None:
        self.items.append(inst)
        self.save()

    def update(self, inst: Instance) -> None:
        self.items = [inst if i.id == inst.id else i for i in self.items]
        self.save()

    def remove(self, inst_id: str) -> None:
        self.items = [i for i in self.items if i.id != inst_id]
        if self.selected == inst_id:
            self.selected = self.items[0].id if self.items else ""
        self.save()

    def select(self, inst_id: str) -> None:
        if self.get(inst_id):
            self.selected = inst_id
            self.save()