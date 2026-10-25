import shutil
import threading
import time

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from . import icons
from .config import Settings
from .instances import LOADER_NAMES, Instance, InstanceStore, loader_and_mc
from .minecraft import runner


def format_playtime(seconds: float) -> str:
    s = int(seconds)
    if s <= 0:
        return "0 ч"
    if s < 60:
        return "меньше минуты"
    minutes = s // 60
    if minutes < 60:
        return f"{minutes} мин"
    return f"{minutes // 60} ч {minutes % 60:02d} мин"


class InstancesBridge(QObject):
    changed = Signal()
    selectionChanged = Signal()
    errorOccurred = Signal(str)

    def __init__(self, settings: Settings, store: InstanceStore) -> None:
        super().__init__()
        self._settings = settings
        self._store = store
        self._list: list[dict] = []
        self._names: list[str] = []
        self._current: dict = {}
        self._index = -1
        self._installed: list[str] = []
        self._rebuild()

    # ---------- данные для QML ----------
    def _describe(self, inst: Instance, installed: list[str], cur_id: str) -> dict:
        game_dir = self._settings.game_dir
        loader, mc = loader_and_mc(game_dir, inst.version) if inst.version else ("vanilla", "")
        last = "Ещё не запускался" if not inst.last_played else \
            time.strftime("%d.%m.%Y %H:%M", time.localtime(inst.last_played))
        return {
            "id": inst.id,
            "name": inst.name,
            "icon": icons.normalize(inst.icon),
            "version": inst.version or "Версия не выбрана",
            "versionId": inst.version,
            "loader": LOADER_NAMES.get(loader, loader),
            "mc": mc,
            "shared": inst.shared,
            "ramMb": inst.ram_mb,
            "javaArgs": inst.java_args,
            "selected": inst.id == cur_id,
            "ok": bool(inst.version) and inst.version in installed,
            "path": str(inst.work_dir(game_dir)),
            "lastPlayed": last,
            "playSeconds": inst.play_seconds,
            "playText": format_playtime(inst.play_seconds),
        }

    def _rebuild(self) -> None:
        installed = runner.installed_versions(self._settings.game_dir)
        cur = self._store.current()
        cur_id = cur.id if cur else ""
        self._installed = installed
        self._list = [self._describe(i, installed, cur_id) for i in self._store.items]
        self._names = [d["name"] for d in self._list]
        self._current = next((d for d in self._list if d["id"] == cur_id), {})
        self._index = next((n for n, d in enumerate(self._list) if d["id"] == cur_id), -1)
        self.changed.emit()

    @Property("QVariantList", notify=changed)
    def instances(self) -> list:
        return self._list

    @Property("QVariantList", notify=changed)
    def names(self) -> list:
        return self._names

    @Property("QVariantMap", notify=changed)
    def current(self) -> dict:
        return self._current

    @Property(bool, notify=changed)
    def hasCurrent(self) -> bool:
        return bool(self._current)

    @Property(int, notify=changed)
    def selectedIndex(self) -> int:
        return self._index

    @Property(str, notify=changed)
    def selectedVersion(self) -> str:
        return self._current.get("versionId", "")

    @Property("QVariantList", notify=changed)
    def installedVersions(self) -> list:
        return self._installed

    # ---------- действия ----------
    @Slot()
    def refresh(self) -> None:
        self._rebuild()

    @Slot(int, result=str)
    def idAt(self, index: int) -> str:
        return self._store.items[index].id if 0 <= index < len(self._store.items) else ""

    @Slot(str)
    def select(self, inst_id: str) -> None:
        self._store.select(inst_id)
        self._rebuild()
        self.selectionChanged.emit()

    @Slot(int)
    def selectIndex(self, index: int) -> None:
        if 0 <= index < len(self._store.items):
            self.select(self._store.items[index].id)

    @Slot(str, str, str, int, str, str, str, result=bool)
    def save(self, inst_id: str, name: str, version: str, ram_mb: int,
             java_args: str, copy_from: str, icon: str) -> bool:
        name = name.strip()
        if not name:
            self.errorOccurred.emit("Введите название профиля")
            return False
        if len(name) > 40:
            self.errorOccurred.emit("Название слишком длинное (до 40 символов)")
            return False
        ram_mb = max(0, int(ram_mb))
        icon = icons.normalize(icon)

        if inst_id:
            inst = self._store.get(inst_id)
            if inst is None:
                return False
            inst.name, inst.version, inst.icon = name, version, icon
            inst.ram_mb, inst.java_args = ram_mb, java_args.strip()
            self._store.update(inst)
        else:
            inst = Instance(id=self._store.new_id(name), name=name, version=version,
                            ram_mb=ram_mb, java_args=java_args.strip(),
                            created=time.time(), icon=icon)
            self._store.add(inst)
            inst.work_dir(self._settings.game_dir).mkdir(parents=True, exist_ok=True)
            if copy_from:
                self._copy_settings(copy_from, inst)
            self._store.select(inst.id)

        self._rebuild()
        self.selectionChanged.emit()
        return True

    def _copy_settings(self, src_id: str, dst: Instance) -> None:
        src = self._store.get(src_id)
        if src is None:
            return
        game_dir = self._settings.game_dir
        s, d = src.work_dir(game_dir), dst.work_dir(game_dir)
        for name in ("options.txt", "optionsof.txt", "servers.dat"):
            f = s / name
            if f.is_file():
                try:
                    shutil.copy2(f, d / name)
                except OSError:
                    pass

    @Slot(str, bool)
    def remove(self, inst_id: str, delete_files: bool) -> None:
        inst = self._store.get(inst_id)
        if inst is None:
            return
        path = inst.work_dir(self._settings.game_dir)
        self._store.remove(inst_id)
        self._rebuild()
        self.selectionChanged.emit()
        # удаляем только папку внутри <игра>/instances/<id>, общую папку не трогаем
        if delete_files and not inst.shared and path.parent.name == "instances" and path.name == inst.id:
            threading.Thread(target=lambda: shutil.rmtree(path, ignore_errors=True),
                             daemon=True).start()

    @Slot(str)
    def openFolder(self, inst_id: str) -> None:
        inst = self._store.get(inst_id)
        if inst is None:
            return
        d = inst.work_dir(self._settings.game_dir)
        d.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))