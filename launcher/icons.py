"""Иконки профилей: блоки в стиле Minecraft (рисуются кодом), голова скина и свои картинки."""
import random

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath

from .paths import DATA_DIR

ICON_DIR = DATA_DIR / "icons"
ICON_DIR.mkdir(parents=True, exist_ok=True)
ICON_VERSION = "v1"
T = 16        # размер текстуры грани
OUT = 128     # размер готовой иконки

PRESETS = [
    ("grass", "Блок травы"), ("dirt", "Земля"), ("stone", "Камень"), ("planks", "Доски"),
    ("crafting", "Верстак"), ("furnace", "Печь"), ("tnt", "Динамит"),
    ("diamond_ore", "Алмазная руда"), ("gold", "Золотой блок"),
    ("bookshelf", "Книжная полка"), ("obsidian", "Обсидиан"),
]
PRESET_IDS = [p[0] for p in PRESETS]

STONE = ["#8b8b8b", "#7f7f7f", "#969696", "#737373"]
DIRT = ["#8a5a3b", "#7a4e31", "#96643f", "#6b4429"]
GRASS = ["#5da13b", "#6bb445", "#4e8f32", "#79c250"]
PLANK = ["#b8945f", "#ad8a56", "#c2a06b", "#a58150"]


# ---------- рисование текстур ----------
def _new() -> QImage:
    img = QImage(T, T, QImage.Format.Format_ARGB32)
    img.fill(0)
    return img


def _noise(palette: list[str], seed: int) -> QImage:
    rng = random.Random(seed)
    img = _new()
    for y in range(T):
        for x in range(T):
            img.setPixelColor(x, y, QColor(rng.choice(palette)))
    return img


def _rect(img: QImage, x: int, y: int, w: int, h: int, color: str) -> None:
    c = QColor(color)
    for yy in range(y, min(y + h, T)):
        for xx in range(x, min(x + w, T)):
            img.setPixelColor(xx, yy, c)


def _dots(img: QImage, pts: list, color: str) -> None:
    c = QColor(color)
    for x, y in pts:
        if 0 <= x < T and 0 <= y < T:
            img.setPixelColor(x, y, c)


def _border(img: QImage, color: str) -> None:
    _rect(img, 0, 0, T, 1, color)
    _rect(img, 0, T - 1, T, 1, color)
    _rect(img, 0, 0, 1, T, color)
    _rect(img, T - 1, 0, 1, T, color)


def _grass():
    top = _noise(GRASS, 1)
    side = _noise(DIRT, 2)
    rng = random.Random(3)
    for x in range(T):
        for y in range(3 + rng.randint(0, 2)):
            side.setPixelColor(x, y, QColor(rng.choice(GRASS)))
    return top, side, side


def _dirt():
    t = _noise(DIRT, 4)
    return t, t, t


def _stone():
    t = _noise(STONE, 5)
    return t, t, t


def _planks_tex(seed: int) -> QImage:
    img = _noise(PLANK, seed)
    for y in (3, 7, 11, 15):
        _rect(img, 0, y, T, 1, "#8d6f43")
    for row, x in ((0, 6), (1, 12), (2, 3), (3, 9)):
        _rect(img, x, row * 4, 1, 3, "#8d6f43")
    return img


def _planks():
    t = _planks_tex(6)
    return t, t, t


def _crafting():
    top = _noise(PLANK, 7)
    _border(top, "#5a3d22")
    for k in (5, 10):
        _rect(top, 2, k, 12, 1, "#7a5a35")
        _rect(top, k, 2, 1, 12, "#7a5a35")
    front = _planks_tex(8)
    _rect(front, 0, 0, T, 4, "#6e4d2e")
    _rect(front, 2, 6, 5, 2, "#9aa0a6")
    _rect(front, 2, 8, 1, 4, "#5a3d22")
    _rect(front, 9, 6, 5, 3, "#7d7d7d")
    _rect(front, 11, 9, 1, 5, "#5a3d22")
    side = _planks_tex(9)
    _rect(side, 0, 0, T, 4, "#6e4d2e")
    _rect(side, 3, 7, 10, 2, "#c94a3a")
    _rect(side, 3, 11, 10, 2, "#3b6fb0")
    return top, front, side


def _furnace():
    top = _noise(STONE, 10)
    _border(top, "#5f5f5f")
    _rect(top, 5, 5, 6, 6, "#4a4a4a")
    front = _noise(STONE, 11)
    _rect(front, 3, 2, 10, 3, "#2e2e2e")
    _rect(front, 3, 6, 10, 8, "#262626")
    _rect(front, 4, 11, 8, 3, "#e8761c")
    _dots(front, [(5, 11), (8, 12), (10, 11), (6, 13)], "#ffd24a")
    side = _noise(STONE, 12)
    return top, front, side


def _tnt():
    top = _noise(["#c9c9c9", "#bdbdbd", "#d4d4d4"], 13)
    _rect(top, 6, 6, 4, 4, "#5a4a2b")
    _rect(top, 7, 7, 2, 2, "#2e2410")

    def side(seed: int) -> QImage:
        s = _noise(["#d83a2b", "#c93323", "#e04636"], seed)
        _rect(s, 0, 4, T, 8, "#e9e3d5")
        _dots(s, [(3, 6), (4, 6), (5, 6), (4, 7), (4, 8), (4, 9),
                  (7, 6), (7, 7), (7, 8), (7, 9), (9, 6), (9, 7), (9, 8), (9, 9), (8, 7), (8, 8),
                  (11, 6), (12, 6), (13, 6), (12, 7), (12, 8), (12, 9)], "#3a3a3a")
        return s

    return top, side(14), side(15)


def _ore(seed: int) -> QImage:
    img = _noise(STONE, seed)
    rng = random.Random(seed + 100)
    for _ in range(4):
        cx, cy = rng.randint(1, 12), rng.randint(1, 12)
        _rect(img, cx, cy, 2, 2, "#35d6d0")
        _dots(img, [(cx, cy)], "#c9fffb")
    return img


def _diamond_ore():
    return _ore(16), _ore(17), _ore(18)


def _gold():
    img = _noise(["#f6d03b", "#f9de5b", "#e9bd23", "#fbe97c"], 19)
    _border(img, "#c99a12")
    _dots(img, [(3, 3), (4, 2), (2, 4)], "#fffbe0")
    return img, img, img


def _bookshelf():
    top = _planks_tex(20)
    side = _planks_tex(21)
    rng = random.Random(22)
    books = ["#8b2e2e", "#2e5a8b", "#3d7a3a", "#7a5c2e", "#6b3d8b", "#b5651d"]
    for y0 in (3, 9):
        x = 0
        while x < T:
            w = rng.choice((1, 2, 2, 3))
            _rect(side, x, y0, min(w, T - x), 5, rng.choice(books))
            x += w
    return top, side, side


def _obsidian():
    img = _noise(["#14101f", "#1d1630", "#0e0b17", "#271d3f"], 23)
    _dots(img, [(3, 4), (9, 2), (12, 9), (5, 12), (10, 13)], "#3b2a63")
    return img, img, img


BUILDERS = {
    "grass": _grass, "dirt": _dirt, "stone": _stone, "planks": _planks,
    "crafting": _crafting, "furnace": _furnace, "tnt": _tnt,
    "diamond_ore": _diamond_ore, "gold": _gold,
    "bookshelf": _bookshelf, "obsidian": _obsidian,
}


# ---------- изометрический куб ----------
def _render_iso(top: QImage, left: QImage, right: QImage) -> QImage:
    n = 64
    s = n // 2
    out = QImage(n, n, QImage.Format.Format_ARGB32)
    out.fill(0)

    for py in range(n):
        y = py + 0.5
        for px in range(n):
            x = px + 0.5
            if abs(x - s) / s + abs(y - s / 2) / (s / 2) <= 1:        # верхняя грань
                u = ((x - s) / s + 2 * y / s) / 2
                v = (2 * y / s - (x - s) / s) / 2
                tex, shade = top, 1.0
            elif x < s:                                                # левая грань
                y0 = s / 2 + x / 2
                if not (y0 <= y < y0 + s):
                    continue
                u, v = x / s, (y - y0) / s
                tex, shade = left, 0.78
            else:                                                      # правая грань
                y0 = s - (x - s) / 2
                if not (y0 <= y < y0 + s):
                    continue
                u, v = (x - s) / s, (y - y0) / s
                tex, shade = right, 0.58

            tx = min(T - 1, max(0, int(u * T)))
            ty = min(T - 1, max(0, int(v * T)))
            c = tex.pixelColor(tx, ty)
            if c.alpha() == 0:
                continue
            out.setPixelColor(px, py, QColor(int(c.red() * shade), int(c.green() * shade),
                                             int(c.blue() * shade), c.alpha()))

    return out.scaled(OUT, OUT, Qt.AspectRatioMode.IgnoreAspectRatio,
                      Qt.TransformationMode.FastTransformation)


def render_block(name: str) -> QImage:
    top, left, right = BUILDERS[name]()
    return _render_iso(top, left, right)


def render_head(skin: QImage) -> QImage:
    """Голова из скина (с внешним слоем) в виде такого же блока."""
    skin = skin.convertToFormat(QImage.Format.Format_ARGB32)

    def face(x: int, y: int, hx: int, hy: int) -> QImage:
        base = skin.copy(x, y, 8, 8)
        hat = skin.copy(hx, hy, 8, 8)
        p = QPainter(base)
        p.drawImage(0, 0, hat)
        p.end()
        return base.scaled(T, T, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.FastTransformation)

    return _render_iso(face(8, 0, 40, 0), face(8, 8, 40, 8), face(16, 8, 48, 8))


def _round(img: QImage, radius: float) -> QImage:
    out = QImage(img.size(), QImage.Format.Format_ARGB32)
    out.fill(0)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, img.width(), img.height()), radius, radius)
    p.setClipPath(path)
    p.drawImage(0, 0, img)
    p.end()
    return out


def make_custom(path: str) -> QImage | None:
    """Своя картинка: квадратная обрезка по центру, 128×128, скруглённые углы."""
    img = QImage(path)
    if img.isNull():
        return None
    side = min(img.width(), img.height())
    img = img.copy((img.width() - side) // 2, (img.height() - side) // 2, side, side)
    img = img.scaled(OUT, OUT, Qt.AspectRatioMode.KeepAspectRatio,
                     Qt.TransformationMode.SmoothTransformation)
    return _round(img.convertToFormat(QImage.Format.Format_ARGB32), OUT * 0.2)


# ---------- идентификаторы и файлы ----------
def normalize(icon_id: str) -> str:
    if icon_id in PRESET_IDS:
        return icon_id
    kind, _, key = (icon_id or "").partition(":")
    if kind in ("head", "custom") and key.isalnum() and (ICON_DIR / f"{kind}-{key}.png").is_file():
        return icon_id
    return "grass"


def path_for(icon_id: str):
    icon_id = normalize(icon_id)
    if icon_id in PRESET_IDS:
        p = ICON_DIR / f"preset-{ICON_VERSION}-{icon_id}.png"
        if not p.is_file():
            render_block(icon_id).save(str(p), "PNG")
        return p
    kind, _, key = icon_id.partition(":")
    return ICON_DIR / f"{kind}-{key}.png"