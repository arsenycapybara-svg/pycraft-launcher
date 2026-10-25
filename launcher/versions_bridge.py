import threading
from pathlib import Path

from PySide6.QtCore import QObject, Property, QStandardPaths, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .config import Settings
from .minecraft import installer
from .minecraft import versions as mc_versions


class VersionsBridge(QObject):
    versionsChanged = Signal()
    stateChanged = Signal()
    errorOccurred = Signal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._loader = "vanilla"
        self._snapshots = False
        self._versions: list = []
        self._loading = False
        self._installing = False
        self._progress = 0.0
        self._max = 1
        self._status = ""
        self._req = 0

    # --- свойства для QML ---
    @Property("QVariantList", notify=versionsChanged)
    def versions(self) -> list:
        return self._versions

    @Property(str, notify=stateChanged)
    def loader(self) -> str:
        return self._loader

    @Property(bool, notify=stateChanged)
    def snapshots(self) -> bool:
        return self._snapshots

    @Property(bool, notify=stateChanged)
    def loading(self) -> bool:
        return self._loading

    @Property(bool, notify=stateChanged)
    def installing(self) -> bool:
        return self._installing

    @Property(float, notify=stateChanged)
    def progress(self) -> float:
        return self._progress

    @Property(str, notify=stateChanged)
    def status(self) -> str:
        return self._status

    # --- список версий ---
    @Slot(str)
    def setLoader(self, loader: str) -> None:
        if loader != self._loader and not self._installing:
            self._loader = loader
            self._clear_list()
            self.refresh()

    @Slot(bool)
    def setSnapshots(self, value: bool) -> None:
        if value != self._snapshots and not self._installing:
            self._snapshots = value
            self._clear_list()
            self.refresh()

    def _clear_list(self) -> None:
        # не показывать список предыдущего загрузчика, пока грузится новый
        self._versions = []
        self.versionsChanged.emit()
        self.stateChanged.emit()

    @Slot()
    def refresh(self) -> None:
        self._req += 1
        req = self._req
        self._loading = True
        self.stateChanged.emit()
        threading.Thread(
            target=self._load, args=(req, self._loader, self._snapshots), daemon=True
        ).start()

    def _load(self, req: int, loader: str, snapshots: bool) -> None:
        try:
            items = mc_versions.available(loader, snapshots)
            ids = mc_versions.installed_ids(self._settings.game_dir)
            result = [{**v, "installed": mc_versions.is_installed(loader, v["id"], ids)}
                      for v in items]
        except Exception as e:
            if req == self._req:
                self.errorOccurred.emit(f"Не удалось получить список версий ({loader}): {e}")
            result = []

        if req != self._req:  # пока грузили, пользователь переключил загрузчик
            return
        self._versions = result
        self._loading = False
        self.versionsChanged.emit()
        self.stateChanged.emit()

    # --- установка ---
    def _callbacks(self) -> dict:
        def set_status(text: str) -> None:
            self._status = text
            self.stateChanged.emit()

        def set_max(value: int) -> None:
            self._max = max(int(value), 1)

        def set_progress(value: int) -> None:
            self._progress = min(value / self._max, 1.0)
            self.stateChanged.emit()

        return {"setStatus": set_status, "setMax": set_max, "setProgress": set_progress}

    def _start(self, task) -> None:
        self._installing = True
        self._progress = 0.0
        self._status = "Подготовка..."
        self.stateChanged.emit()

        def work() -> None:
            try:
                task(self._callbacks())
                self._status = "Готово"
            except Exception as e:
                self._status = ""
                self.errorOccurred.emit(f"Ошибка установки: {e}")
            finally:
                self._installing = False
                self.stateChanged.emit()
                self.refresh()  # обновить пометки «установлена»

        threading.Thread(target=work, daemon=True).start()

    @Slot(str)
    def install(self, version_id: str) -> None:
        if self._installing or not version_id:
            return
        loader = self._loader
        game_dir = self._settings.game_dir
        if mc_versions.is_installed(loader, version_id, mc_versions.installed_ids(game_dir)):
            self.errorOccurred.emit("Эта версия уже установлена")
            return
        self._start(lambda cb: installer.install(loader, version_id, game_dir, cb))

    # --- OptiFine вручную ---
    @Property(QUrl, constant=True)
    def downloadsUrl(self) -> QUrl:
        loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        return QUrl.fromLocalFile(loc)

    @Slot()
    def openOptifineSite(self) -> None:
        QDesktopServices.openUrl(QUrl("https://optifine.net/downloads"))

    @Slot(str)
    def installFile(self, url: str) -> None:
        """OptiFine из .jar, выбранного вручную."""
        if self._installing or not url:
            return
        path = QUrl(url).toLocalFile() if url.startswith("file:") else url
        game_dir = self._settings.game_dir
        self._start(lambda cb: installer.install_optifine_file(path, game_dir, cb))

    @Slot()
    def installFromDownloads(self) -> None:
        """Берёт самый свежий OptiFine_*.jar из папки «Загрузки»."""
        if self._installing:
            return
        folder = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation))
        files = sorted(folder.glob("OptiFine_*.jar"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            self.errorOccurred.emit(
                f"В папке «{folder}» нет файла OptiFine_*.jar. "
                "Скачайте его на optifine.net и повторите.")
            return
        self.installFile(str(files[0]))