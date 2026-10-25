import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from launcher.behavior import BehaviorBridge
from launcher.bridge import AppBridge
from launcher.config import Settings
from launcher.game_bridge import GameBridge
from launcher.icons_bridge import IconsBridge
from launcher.instances import InstanceStore
from launcher.instances_bridge import InstancesBridge
from launcher.mods_bridge import ModsBridge
from launcher.settings_bridge import SettingsBridge
from launcher.skin_bridge import SkinBridge
from launcher.versions_bridge import VersionsBridge

# в собранной программе файлы лежат в папке _MEIPASS, при обычном запуске рядом с main.py
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
QML_DIR = BASE / "launcher" / "ui" / "qml"


def main() -> int:
    # Фолбэк для проблемных драйверов: MCL_SOFTWARE=1 python main.py
    if os.environ.get("MCL_SOFTWARE") == "1":
        os.environ["QT_QUICK_BACKEND"] = "software"

    QQuickStyle.setStyle("Basic")

    app = QApplication(sys.argv)
    app.setApplicationName("PyCraft Launcher")
    app.setOrganizationName("pycraft")

    families = set(QFontDatabase.families())
    for name in ("Inter", "Segoe UI", "Noto Sans", "Cantarell", "DejaVu Sans"):
        if name in families:
            font = QFont(name)
            font.setPointSize(10)
            app.setFont(font)
            break

    settings = Settings.load()  # один общий объект настроек
    bridge = AppBridge(settings)

    instance_store = InstanceStore()
    instance_store.ensure_default(settings.game_dir, settings.last_version)

    instances = InstancesBridge(settings, instance_store)
    versions = VersionsBridge(settings)
    game = GameBridge(settings, bridge.store, instance_store)
    cfg = SettingsBridge(settings)
    mods = ModsBridge(settings, instance_store)
    skin = SkinBridge(settings, bridge.store)
    icons = IconsBridge(skin)
    behavior = BehaviorBridge(settings, app)

    bridge.accountsChanged.connect(skin.refresh)       # сменили аккаунт: обновить скин
    instances.selectionChanged.connect(mods.refresh)   # сменили профиль: обновить моды
    game.gameStarted.connect(behavior.on_game_started)
    game.sessionEnded.connect(behavior.on_game_ended)
    app.aboutToQuit.connect(behavior.shutdown)

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))
    ctx = engine.rootContext()
    ctx.setContextProperty("backend", bridge)
    ctx.setContextProperty("instances", instances)
    ctx.setContextProperty("versions", versions)
    ctx.setContextProperty("game", game)
    ctx.setContextProperty("cfg", cfg)
    ctx.setContextProperty("mods", mods)
    ctx.setContextProperty("skin", skin)
    ctx.setContextProperty("icons", icons)
    ctx.setContextProperty("behavior", behavior)
    engine.load(QML_DIR / "Main.qml")

    if not engine.rootObjects():
        print("Не удалось загрузить QML. Попробуйте: MCL_SOFTWARE=1 python main.py")
        return 1

    behavior.attach(engine.rootObjects()[0])
    skin.refresh()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())