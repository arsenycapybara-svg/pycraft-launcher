"""Работа со скинами: загрузка, приведение к 64×64, превью для 3D-вида."""
import base64
import json
import re
import time
from pathlib import Path

import requests
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QColor, QImage, QPainter

from .paths import DATA_DIR

SKIN_DIR = DATA_DIR / "skins"
SKIN_DIR.mkdir(parents=True, exist_ok=True)

SCALE = 16            # должен совпадать с tex в SkinViewer.qml
CACHE_TTL = 6 * 3600
NAME_RE = re.compile(r"[A-Za-z0-9_]{1,16}")


def _safe(acc_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", acc_id)


def override_path(acc) -> Path:
    return SKIN_DIR / f"{_safe(acc.id)}.local.png"


def cache_path(acc) -> Path:
    return SKIN_DIR / f"{_safe(acc.id)}.remote.png"


def clear_files(acc) -> None:
    for p in (override_path(acc), cache_path(acc)):
        p.unlink(missing_ok=True)


# --- получение скинов ---
def _get(url: str):
    return requests.get(url, timeout=(8, 20))


def mojang_by_uuid(uid: str) -> bytes | None:
    r = _get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uid.replace('-', '')}")
    if r.status_code != 200:
        return None
    for prop in r.json().get("properties", []):
        if prop.get("name") == "textures":
            tex = json.loads(base64.b64decode(prop["value"])).get("textures", {}).get("SKIN")
            if tex and tex.get("url"):
                img = _get(tex["url"].replace("http://", "https://"))
                return img.content if img.status_code == 200 else None
    return None


def mojang_by_name(name: str) -> bytes | None:
    if not NAME_RE.fullmatch(name):
        return None
    r = _get(f"https://api.mojang.com/users/profiles/minecraft/{name}")
    if r.status_code != 200:
        return None
    return mojang_by_uuid(r.json().get("id", ""))


def elyby_by_name(name: str) -> bytes | None:
    if not NAME_RE.fullmatch(name):
        return None
    r = _get(f"https://skinsystem.ely.by/skins/{name}.png")
    return r.content if r.status_code == 200 else None


# --- обработка изображения ---
def _legacy_to_modern(src: QImage) -> QImage:
    out = QImage(64, 64, QImage.Format.Format_ARGB32)
    out.fill(0)
    p = QPainter(out)
    p.drawImage(0, 0, src)

    def cp(sx, sy, w, h, dx, dy):
        p.drawImage(dx, dy, src.copy(sx, sy, w, h).mirrored(True, False))

    # левая нога из правой
    cp(4, 16, 4, 4, 20, 48); cp(8, 16, 4, 4, 24, 48)
    cp(8, 20, 4, 12, 16, 52); cp(4, 20, 4, 12, 20, 52)
    cp(0, 20, 4, 12, 24, 52); cp(12, 20, 4, 12, 28, 52)
    # левая рука из правой
    cp(44, 16, 4, 4, 36, 48); cp(48, 16, 4, 4, 40, 48)
    cp(48, 20, 4, 12, 32, 52); cp(44, 20, 4, 12, 36, 52)
    cp(40, 20, 4, 12, 40, 52); cp(52, 20, 4, 12, 44, 52)

    # как в игре: у старых скинов сплошной «слой шляпы» считается фоном
    opaque = all(src.pixelColor(x, y).alpha() >= 128 for x in range(32, 64) for y in range(0, 16))
    if opaque:
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(32, 0, 32, 16, QColor(0, 0, 0, 0))
    p.end()
    return out


def normalize(data: bytes) -> QImage | None:
    img = QImage.fromData(data)
    if img.isNull():
        return None
    img = img.convertToFormat(QImage.Format.Format_ARGB32)
    if img.width() == 64 and img.height() == 32:
        return _legacy_to_modern(img)
    if img.width() == 64 and img.height() == 64:
        return img
    if img.width() == img.height() and img.width() % 64 == 0:  # HD-скины
        return img.scaled(64, 64, Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.FastTransformation)
    return None


def is_slim(img: QImage) -> bool:
    return img.pixelColor(47, 20).alpha() == 0 and img.pixelColor(55, 20).alpha() == 0


def to_png(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def placeholder() -> QImage:
    """Стандартный скин, если настоящий недоступен."""
    img = QImage(64, 64, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)

    def fill(x, y, w, h, c):
        p.fillRect(x, y, w, h, QColor(c))

    def box(u, v, w, h, d, c):
        fill(u + d, v, w * 2, d, c)
        fill(u, v + d, 2 * (d + w), h, c)

    skin, hair, shirt, pants, shoes = "#c58c6b", "#4a3424", "#3b82f6", "#2f3d8f", "#3a3a40"
    box(0, 0, 8, 8, 8, hair)
    fill(8, 8, 8, 8, skin)
    fill(9, 12, 1, 1, "#ffffff"); fill(10, 12, 1, 1, "#2b2350")
    fill(13, 12, 1, 1, "#2b2350"); fill(14, 12, 1, 1, "#ffffff")
    fill(11, 14, 2, 1, "#9c6048")
    box(16, 16, 8, 12, 4, shirt)
    box(40, 16, 4, 12, 4, skin); fill(44, 16, 8, 4, shirt); fill(40, 20, 16, 4, shirt)
    box(32, 48, 4, 12, 4, skin); fill(36, 48, 8, 4, shirt); fill(32, 52, 16, 4, shirt)
    box(0, 16, 4, 12, 4, pants); fill(0, 29, 16, 3, shoes)
    box(16, 48, 4, 12, 4, pants); fill(16, 61, 16, 3, shoes)
    p.end()
    return img


def render_view(img: QImage, key: str) -> tuple[Path, Path]:
    """Увеличенная текстура и её чёрная маска (для затенения граней)."""
    view = SKIN_DIR / f"view-{key}.png"
    mask = SKIN_DIR / f"mask-{key}.png"
    if not (view.is_file() and mask.is_file()):
        big = img.scaled(64 * SCALE, 64 * SCALE, Qt.AspectRatioMode.IgnoreAspectRatio,
                         Qt.TransformationMode.FastTransformation)
        big.save(str(view), "PNG")
        m = QImage(big)
        p = QPainter(m)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(m.rect(), QColor(0, 0, 0))
        p.end()
        m.save(str(mask), "PNG")
    _cleanup(key)
    return view, mask


def _cleanup(keep: str) -> None:
    files = sorted(SKIN_DIR.glob("view-*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[8:]:
        if keep not in f.name:
            f.unlink(missing_ok=True)
            (SKIN_DIR / f.name.replace("view-", "mask-", 1)).unlink(missing_ok=True)


def fresh(path: Path) -> bool:
    return path.is_file() and time.time() - path.stat().st_mtime < CACHE_TTL