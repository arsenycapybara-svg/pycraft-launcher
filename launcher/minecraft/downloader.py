"""Скачивание файлов с проверкой SHA-1 и предзагрузка библиотек Forge."""
import hashlib
import json
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

FORGE_INSTALLER_URL = (
    "https://maven.minecraftforge.net/net/minecraftforge/forge/{v}/forge-{v}-installer.jar"
)


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_file(url: str, dest: Path, sha1: str | None = None, attempts: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    last: Exception | None = None

    for n in range(attempts):
        try:
            h = hashlib.sha1()
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(part, "wb") as f:
                    for chunk in r.iter_content(65536):
                        f.write(chunk)
                        h.update(chunk)
            if sha1 and h.hexdigest() != sha1:
                raise ValueError("контрольная сумма не совпала")
            part.replace(dest)
            return
        except Exception as e:
            last = e
            time.sleep(1 + n)

    raise RuntimeError(f"Не удалось скачать {url.rsplit('/', 1)[-1]}: {last}")


def _missing_forge_libs(installer_jar: Path, game_dir: str) -> list[tuple[str, Path, str | None]]:
    libs: list[dict] = []
    with zipfile.ZipFile(installer_jar) as z:
        names = set(z.namelist())
        for name in ("install_profile.json", "version.json"):
            if name in names:
                try:
                    libs += json.loads(z.read(name)).get("libraries", [])
                except ValueError:
                    pass

    todo, seen = [], set()
    for lib in libs:
        art = lib.get("downloads", {}).get("artifact")
        if not art or not art.get("url") or not art.get("path"):
            continue  # пустой url = файл лежит внутри самого установщика
        dest = Path(game_dir) / "libraries" / art["path"]
        if dest in seen:
            continue
        seen.add(dest)
        sha1 = art.get("sha1")
        if dest.is_file() and (not sha1 or sha1_of(dest) == sha1):
            continue
        todo.append((art["url"], dest, sha1))
    return todo


def prefetch_forge_libs(version_id: str, game_dir: str, callback: dict | None,
                        workers: int = 8) -> None:
    """Скачивает библиотеки Forge заранее (через зеркало), чтобы установщик
    Forge нашёл их на диске и не ходил за ними на официальные серверы."""
    cb = callback or {}
    status = cb.get("setStatus", lambda s: None)
    set_max = cb.get("setMax", lambda v: None)
    set_prog = cb.get("setProgress", lambda v: None)

    with tempfile.TemporaryDirectory() as tmp:
        jar = Path(tmp) / "forge-installer.jar"
        status("Скачивание установщика Forge...")
        fetch_file(FORGE_INSTALLER_URL.format(v=version_id), jar)
        todo = _missing_forge_libs(jar, game_dir)

    if not todo:
        return

    set_max(len(todo))
    set_prog(0)
    done = 0
    status(f"Библиотеки Forge... 0/{len(todo)}")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_file, u, d, s) for u, d, s in todo]
        try:
            for fut in as_completed(futures):
                fut.result()
                done += 1
                set_prog(done)
                status(f"Библиотеки Forge... {done}/{len(todo)}")
        except Exception:
            for f in futures:
                f.cancel()
            raise