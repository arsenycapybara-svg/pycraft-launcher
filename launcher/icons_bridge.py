import hashlib
from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Slot
from PySide6.QtGui import QImage

from . import icons, skins


class IconsBridge(QObject):
    def __init__(self, skin_bridge) -> None:
        super().__init__()
        self._skin = skin_bridge

    @Property("QVariantList", constant=True)
    def presets(self) -> list:
        return [{"id": i, "name": n} for i, n in icons.PRESETS]

    @Slot(str, result=str)
    def url(self, icon_id: str) -> str:
        return QUrl.fromLocalFile(str(icons.path_for(icon_id))).toString()

    def _skin_image(self) -> QImage:
        view = getattr(self._skin, "_view", "")
        path = QUrl(view).toLocalFile() if view else ""
        img = QImage(path) if path else QImage()
        if img.isNull():
            return skins.placeholder()
        # файл просмотра увеличен в 16 раз, возвращаем исходные 64×64
        from PySide6.QtCore import Qt
        return img.scaled(64, 64, Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.FastTransformation)

    @Slot(result=str)
    def makeHead(self) -> str:
        """Иконка-голова из скина выбранного аккаунта."""
        try:
            skin = self._skin_image().convertToFormat(QImage.Format.Format_ARGB32)
            key = hashlib.sha1(skins.to_png(skin)).hexdigest()[:12]
            dest = icons.ICON_DIR / f"head-{key}.png"
            if not dest.is_file():
                icons.render_head(skin).save(str(dest), "PNG")
            return f"head:{key}"
        except Exception:
            return ""

    @Slot(str, result=str)
    def importCustom(self, url: str) -> str:
        path = QUrl(url).toLocalFile() if url.startswith("file:") else url
        try:
            if Path(path).stat().st_size > 12_000_000:
                return ""
        except OSError:
            return ""
        img = icons.make_custom(path)
        if img is None:
            return ""
        png = skins.to_png(img)
        key = hashlib.sha1(png).hexdigest()[:12]
        dest = icons.ICON_DIR / f"custom-{key}.png"
        if not dest.is_file():
            dest.write_bytes(png)
        return f"custom:{key}"