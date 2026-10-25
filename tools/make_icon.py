import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # экран не нужен (важно на сервере сборки)

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

app = QGuiApplication([])
img = QImage(256, 256, QImage.Format.Format_ARGB32)
img.fill(0)
p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setPen(Qt.PenStyle.NoPen)
p.setBrush(QColor("#3b82f6"))
p.drawRoundedRect(8, 8, 240, 240, 56, 56)
p.setPen(QColor("white"))
font = QFont()
font.setBold(True)
font.setPixelSize(150)
p.setFont(font)
p.drawText(img.rect(), Qt.AlignmentFlag.AlignCenter, "P")
p.end()

out = Path(__file__).resolve().parent.parent / "assets"
out.mkdir(exist_ok=True)
img.save(str(out / "icon.png"))
if not img.save(str(out / "icon.ico"), "ICO"):
    sys.exit("Не удалось сохранить icon.ico")
print("Готово:", out)