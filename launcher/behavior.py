"""Поведение окна при запуске игры (трей / скрыть / закрыть) и Discord Rich Presence."""
from PySide6.QtCore import QObject, Property, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtGui import QWindow
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .config import Settings
from .discord_rpc import DiscordPresence

MODES = ("none", "tray", "hide", "close")


class BehaviorBridge(QObject):
    changed = Signal()

    def __init__(self, settings: Settings, app) -> None:
        super().__init__()
        self._s = settings
        self._app = app
        self._win = None
        self._tray = None
        self._menu = None
        self._hidden = False
        self._was_max = True
        self._presence = DiscordPresence()
        self._presence.configure(settings.discord_enabled, settings.discord_client_id)
        self._presence.menu()

    def attach(self, win) -> None:
        self._win = win

    @Slot()
    def shutdown(self) -> None:
        self._presence.shutdown()

    # ---------- настройки для QML ----------
    @Property(bool, notify=changed)
    def discordEnabled(self) -> bool:
        return self._s.discord_enabled

    @Property(str, notify=changed)
    def discordId(self) -> str:
        return self._s.discord_client_id

    @Property(str, notify=changed)
    def hideMode(self) -> str:
        return self._s.hide_mode

    @Property(bool, constant=True)
    def trayAvailable(self) -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    @Slot(bool)
    def setDiscordEnabled(self, value: bool) -> None:
        self._s.discord_enabled = bool(value)
        self._apply_discord()

    @Slot(str)
    def setDiscordId(self, value: str) -> None:
        self._s.discord_client_id = "".join(ch for ch in value if ch.isdigit())
        self._apply_discord()

    def _apply_discord(self) -> None:
        self._s.save()
        self._presence.configure(self._s.discord_enabled, self._s.discord_client_id)
        self.changed.emit()

    @Slot(str)
    def setHideMode(self, mode: str) -> None:
        if mode in MODES:
            self._s.hide_mode = mode
            self._s.save()
            self.changed.emit()

    # ---------- события игры ----------
    @Slot(str, str, float)
    def on_game_started(self, label: str, profile: str, started: float) -> None:
        self._presence.playing(f"Играет в {label}", f"Профиль: {profile}", started)
        mode = self._s.hide_mode
        if mode == "tray":
            self._hide(use_tray=True)
        elif mode == "hide":
            self._hide(use_tray=False)
        elif mode == "close":
            QTimer.singleShot(1500, self._app.quit)

    @Slot(str, float)
    def on_game_ended(self, inst_id: str, seconds: float) -> None:
        self._presence.menu()
        self.restore()

    # ---------- окно и трей ----------
    def _make_icon(self) -> QIcon:
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._s.accent))
        p.drawRoundedRect(4, 4, 56, 56, 14, 14)
        p.setPen(QColor("white"))
        font = QFont()
        font.setBold(True)
        font.setPixelSize(36)
        p.setFont(font)
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "P")
        p.end()
        return QIcon(pm)

    def _ensure_tray(self):
        if self._tray is None and QSystemTrayIcon.isSystemTrayAvailable():
            tray = QSystemTrayIcon(self._make_icon(), self)
            tray.setToolTip("PyCraft Launcher")
            menu = QMenu()
            menu.addAction("Открыть лаунчер").triggered.connect(self.restore)
            menu.addAction("Выйти").triggered.connect(self._app.quit)
            tray.setContextMenu(menu)
            tray.activated.connect(self._on_tray)
            self._menu, self._tray = menu, tray
        return self._tray

    def _on_tray(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.restore()

    def _hide(self, use_tray: bool) -> None:
        win = self._win
        if win is None or self._hidden:
            return
        self._was_max = win.visibility() == QWindow.Visibility.Maximized
        if use_tray:
            tray = self._ensure_tray()
            if tray is None:               # трея нет: просто сворачиваем в панель
                win.showMinimized()
                return
            tray.show()
        self._app.setQuitOnLastWindowClosed(False)
        win.hide()
        self._hidden = True

    @Slot()
    def restore(self) -> None:
        win = self._win
        if win is None:
            return
        if self._tray is not None:
            self._tray.hide()
        if self._hidden:
            win.show()
            if self._was_max:
                win.showMaximized()
            self._hidden = False
        elif win.visibility() == QWindow.Visibility.Minimized:
            win.showMaximized() if self._was_max else win.showNormal()
        else:
            return
        self._app.setQuitOnLastWindowClosed(True)
        win.raise_()
        win.requestActivate()