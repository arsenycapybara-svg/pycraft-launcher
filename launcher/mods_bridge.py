import threading
from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from . import modrinth
from .config import Settings
from .instances import InstanceStore, loader_and_mc
from .minecraft import runner

# вид: (папка, расширения, тип проекта на Modrinth)
KINDS = {
    "mods": ("mods", (".jar",), "mod"),
    "resourcepacks": ("resourcepacks", (".zip",), "resourcepack"),
    "shaderpacks": ("shaderpacks", (".zip",), "shader"),
}


def _parse(name: str, exts: tuple):
    low = name.lower()
    for ext in exts:
        if low.endswith(ext):
            return True, name[:-len(ext)]
        if low.endswith(ext + ".disabled"):
            return False, name[:-(len(ext) + 9)]
    return None


class ModsBridge(QObject):
    installedChanged = Signal()
    resultsChanged = Signal()
    stateChanged = Signal()
    errorOccurred = Signal(str)
    infoMessage = Signal(str)

    def __init__(self, settings: Settings, store: InstanceStore) -> None:
        super().__init__()
        self._settings = settings
        self._store = store
        self._kind = "mods"
        self._items: list[dict] = []
        self._warnings: list[dict] = []
        self._have: set[str] = set()
        self._checking = False
        self._note = ""
        self._raw: list[dict] = []
        self._total = 0
        self._query = ""
        self._searching = False
        self._installing = False
        self._progress = 0.0
        self._status = ""
        self._scan_req = 0
        self._search_req = 0

    # ---------- контекст ----------
    def _ctx(self):
        inst = self._store.current()
        if inst is None:
            return None
        game_dir = self._settings.game_dir
        if inst.version:
            loader, mc = loader_and_mc(game_dir, inst.version)
        else:
            loader, mc = "vanilla", ""
        return inst, inst.work_dir(game_dir), loader, mc

    def _dir(self) -> Path | None:
        ctx = self._ctx()
        return None if ctx is None else ctx[1] / KINDS[self._kind][0]

    # ---------- свойства для QML ----------
    @Property(str, notify=stateChanged)
    def kind(self) -> str:
        return self._kind

    @Property("QVariantList", notify=installedChanged)
    def installed(self) -> list:
        return self._items

    @Property("QVariantList", notify=installedChanged)
    def warnings(self) -> list:
        return self._warnings

    @Property(bool, notify=stateChanged)
    def checking(self) -> bool:
        return self._checking

    @Property(str, notify=stateChanged)
    def note(self) -> str:
        return self._note

    @Property("QVariantList", notify=resultsChanged)
    def results(self) -> list:
        return [{
            "id": h["project_id"],
            "title": h.get("title", ""),
            "description": h.get("description", ""),
            "author": h.get("author", ""),
            "downloads": modrinth.fmt_count(h.get("downloads", 0)),
            "icon": h.get("icon_url") or "",
            "installed": h["project_id"] in self._have,
        } for h in self._raw]

    @Property(bool, notify=resultsChanged)
    def canLoadMore(self) -> bool:
        return 0 < len(self._raw) < self._total

    @Property(bool, notify=stateChanged)
    def searching(self) -> bool:
        return self._searching

    @Property(bool, notify=stateChanged)
    def installing(self) -> bool:
        return self._installing

    @Property(float, notify=stateChanged)
    def progress(self) -> float:
        return self._progress

    @Property(str, notify=stateChanged)
    def status(self) -> str:
        return self._status

    @Property(str, notify=installedChanged)
    def path(self) -> str:
        d = self._dir()
        return str(d) if d else ""

    # ---------- установленные файлы ----------
    @Slot(str)
    def setKind(self, kind: str) -> None:
        if kind in KINDS and kind != self._kind:
            self._kind = kind
            self._raw, self._total = [], 0
            self.resultsChanged.emit()
            self.stateChanged.emit()
            self.refresh()

    def _scan(self) -> list[dict]:
        d = self._dir()
        _, exts, _ = KINDS[self._kind]
        items = []
        if d is not None and d.is_dir():
            for p in d.iterdir():
                if not p.is_file():
                    continue
                parsed = _parse(p.name, exts)
                if parsed is None:
                    continue
                enabled, stem = parsed
                items.append({
                    "file": p.name, "name": stem, "title": stem, "enabled": enabled,
                    "size": f"{p.stat().st_size / 1048576:.1f} МБ",
                    "icon": "", "known": False, "version": "", "project": "",
                })
        items.sort(key=lambda m: m["name"].lower())
        return items

    @Slot()
    def refresh(self) -> None:
        self._scan_req += 1
        req = self._scan_req
        self._items = self._scan()
        self._warnings = []
        self._note = ""
        self._have = set()
        self._checking = bool(self._items)
        self.installedChanged.emit()
        self.stateChanged.emit()
        self.resultsChanged.emit()
        if self._items:
            threading.Thread(target=self._identify,
                             args=(req, [dict(i) for i in self._items], self._kind),
                             daemon=True).start()

    def _identify(self, req: int, items: list[dict], kind: str) -> None:
        folder, _, _ = KINDS[kind]
        warnings: list[dict] = []
        have: set[str] = set()
        note = ""
        try:
            ctx = self._ctx()
            if ctx is None:
                return
            _, work, loader, mc = ctx
            paths = [work / folder / i["file"] for i in items]
            found = modrinth.identify(paths)
            ids = sorted({v["project_id"] for v in found.values() if v})
            info = modrinth.projects(ids) if ids else {}

            rows = []
            for it, p in zip(items, paths):
                v = found.get(p)
                if v:
                    pr = info.get(v["project_id"], {})
                    it["known"] = True
                    it["title"] = pr.get("title") or it["name"]
                    it["icon"] = pr.get("icon_url") or ""
                    it["version"] = v.get("version_number", "")
                    it["project"] = v["project_id"]
                    if it["enabled"]:
                        have.add(v["project_id"])
                rows.append({"title": it["title"], "enabled": it["enabled"], "version": v})
            if kind == "mods":
                warnings = modrinth.analyze(rows, loader, mc)
            items.sort(key=lambda m: m["title"].lower())
        except modrinth.ModrinthError as e:
            note = f"Проверка через Modrinth недоступна: {e}"
        except Exception as e:
            note = f"Не удалось проверить файлы: {e}"

        if req != self._scan_req:
            return
        self._items, self._warnings, self._have, self._note = items, warnings, have, note
        self._checking = False
        self.installedChanged.emit()
        self.stateChanged.emit()
        self.resultsChanged.emit()

    @Slot(int)
    def toggle(self, index: int) -> None:
        d = self._dir()
        if d is None or not 0 <= index < len(self._items):
            return
        it = self._items[index]
        new = it["file"][:-9] if not it["enabled"] else it["file"] + ".disabled"
        try:
            (d / it["file"]).rename(d / new)
        except OSError as e:
            self.errorOccurred.emit(f"Не удалось переименовать файл: {e}")
            return
        self.refresh()

    @Slot(int)
    def remove(self, index: int) -> None:
        d = self._dir()
        if d is None or not 0 <= index < len(self._items):
            return
        try:
            (d / self._items[index]["file"]).unlink()
        except OSError as e:
            self.errorOccurred.emit(f"Не удалось удалить файл: {e}")
            return
        self.refresh()

    @Slot()
    def openFolder(self) -> None:
        d = self._dir()
        if d is None:
            return
        d.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))

    # ---------- поиск ----------
    @Slot(str)
    def search(self, query: str) -> None:
        self._query = query.strip()
        self._raw, self._total = [], 0
        self.resultsChanged.emit()
        self._do_search(append=False)

    @Slot()
    def loadMore(self) -> None:
        if not self._searching and self.canLoadMore:
            self._do_search(append=True)

    def _do_search(self, append: bool) -> None:
        ctx = self._ctx()
        if ctx is None:
            self.errorOccurred.emit("Сначала создайте профиль во вкладке «Профили»")
            return
        _, _, loader, mc = ctx
        ptype = KINDS[self._kind][2]
        self._search_req += 1
        req = self._search_req
        offset = len(self._raw) if append else 0
        query = self._query
        self._searching = True
        self.stateChanged.emit()

        def job() -> None:
            try:
                hits, total = modrinth.search(query, ptype, mc, loader, offset)
                if req != self._search_req:
                    return
                self._raw = (self._raw + hits) if append else hits
                self._total = total
                self.resultsChanged.emit()
            except modrinth.ModrinthError as e:
                if req == self._search_req:
                    self.errorOccurred.emit(str(e))
            except Exception as e:
                if req == self._search_req:
                    self.errorOccurred.emit(f"Ошибка поиска: {e}")
            finally:
                if req == self._search_req:
                    self._searching = False
                    self.stateChanged.emit()

        threading.Thread(target=job, daemon=True).start()

    # ---------- установка ----------
    @Slot(str)
    def install(self, project_id: str) -> None:
        if self._installing:
            return
        ctx = self._ctx()
        if ctx is None:
            self.errorOccurred.emit("Сначала создайте профиль во вкладке «Профили»")
            return
        inst, work, loader, mc = ctx
        if not inst.version or inst.version not in runner.installed_versions(self._settings.game_dir):
            self.errorOccurred.emit("У профиля нет установленной версии. Выберите её во вкладке «Профили».")
            return
        folder, _, ptype = KINDS[self._kind]
        if ptype == "mod" and loader not in modrinth.LOADERS:
            self.errorOccurred.emit(
                "Для модов нужен профиль на Fabric или Forge. Установите такую версию во вкладке "
                "«Версии» и выберите её в профиле.")
            return

        self._installing = True
        self._progress = 0.0
        self._status = "Подбор версии..."
        self.stateChanged.emit()

        def set_status(text: str) -> None:
            self._status = text
            self.stateChanged.emit()

        def set_progress(value: float) -> None:
            self._progress = value
            self.stateChanged.emit()

        def job() -> None:
            try:
                have = modrinth.installed_projects(work / "mods", (".jar",))
                if folder != "mods":
                    have |= modrinth.installed_projects(work / folder, (".zip",))
                plan = modrinth.plan_install(project_id, mc, loader, have)
                if not plan:
                    self.infoMessage.emit("Это уже установлено")
                else:
                    modrinth.install_plan(plan, work, set_status, set_progress)
                    names = [p["title"] for p in plan]
                    msg = f"Установлено: {names[-1]}"
                    if len(names) > 1:
                        msg += "  (+ зависимости: " + ", ".join(names[:-1]) + ")"
                    self.infoMessage.emit(msg)
            except (modrinth.ModrinthError, RuntimeError) as e:
                self.errorOccurred.emit(str(e))
            except Exception as e:
                self.errorOccurred.emit(f"Ошибка установки: {e}")
            finally:
                self._installing = False
                self._status = ""
                self._progress = 0.0
                self.stateChanged.emit()
                self.refresh()

        threading.Thread(target=job, daemon=True).start()