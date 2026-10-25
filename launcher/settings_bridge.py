import shutil
from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from . import net
from .config import Settings
from .paths import CACHE_DIR


def _total_ram_mb() -> int:
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 8192


class SettingsBridge(QObject):
    settingsChanged = Signal()
    cacheCleared = Signal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._s = settings
        self._max_ram = max(2048, (_total_ram_mb() // 256) * 256 - 1024)
        net.set_source(settings.download_source)

    def _save(self) -> None:
        self._s.save()
        self.settingsChanged.emit()

    @Property(int, notify=settingsChanged)
    def ramMb(self) -> int:
        return self._s.ram_mb

    @Property(int, constant=True)
    def maxRamMb(self) -> int:
        return self._max_ram

    @Property(str, notify=settingsChanged)
    def gameDir(self) -> str:
        return self._s.game_dir

    @Property(int, notify=settingsChanged)
    def resWidth(self) -> int:
        return self._s.width

    @Property(int, notify=settingsChanged)
    def resHeight(self) -> int:
        return self._s.height

    @Property(str, notify=settingsChanged)
    def javaArgs(self) -> str:
        return self._s.java_args

    @Property(bool, notify=settingsChanged)
    def isolate(self) -> bool:
        return self._s.isolate_versions

    @Property(str, notify=settingsChanged)
    def downloadSource(self) -> str:
        return self._s.download_source

    @Slot(str)
    def setDownloadSource(self, value: str) -> None:
        if value in ("mirror", "auto", "official"):
            self._s.download_source = value
            net.set_source(value)
            self._save()

    @Slot(int)
    def setRamMb(self, value: int) -> None:
        self._s.ram_mb = max(1024, min(int(value), self._max_ram))
        self._save()

    @Slot(str)
    def setGameDir(self, value: str) -> None:
        value = value.strip()
        if value.startswith("file:"):
            value = QUrl(value).toLocalFile()
        if value:
            self._s.game_dir = str(Path(value).expanduser())
            self._save()

    @Slot(int, int)
    def setResolution(self, width: int, height: int) -> None:
        self._s.width = max(320, min(int(width), 7680))
        self._s.height = max(240, min(int(height), 4320))
        self._save()

    @Slot(str)
    def setJavaArgs(self, value: str) -> None:
        self._s.java_args = value.strip()
        self._save()

    @Slot(bool)
    def setIsolate(self, value: bool) -> None:
        self._s.isolate_versions = bool(value)
        self._save()

    @Slot()
    def clearCache(self) -> None:
        freed = 0
        for p in CACHE_DIR.glob("*"):
            try:
                if p.is_file():
                    freed += p.stat().st_size
                    p.unlink()
                elif p.is_dir():
                    freed += sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                    shutil.rmtree(p)
            except OSError:
                pass
        self.cacheCleared.emit(f"Кэш очищен ({freed / 1048576:.1f} МБ)")

    @Slot()
    def openGameDir(self) -> None:
        d = Path(self._s.game_dir)
        d.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))