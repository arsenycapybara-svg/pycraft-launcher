import json
import shlex
from pathlib import Path

import minecraft_launcher_lib as mll
import requests

from ..auth.models import Account
from ..config import Settings
from ..paths import DATA_DIR

ELYBY_API = "https://authserver.ely.by/api/authlib-injector"
INJECTOR = DATA_DIR / "authlib-injector.jar"
INJECTOR_LATEST = "https://authlib-injector.yushi.moe/artifact/latest.json"


def installed_versions(game_dir: str) -> list[str]:
    """Установленные версии, недавно установленные сверху."""
    root = Path(game_dir) / "versions"
    if not root.is_dir():
        return []
    items = []
    for d in root.iterdir():
        meta = d / f"{d.name}.json"
        if meta.is_file():
            items.append((meta.stat().st_mtime, d.name))
    items.sort(reverse=True)
    return [name for _, name in items]


def read_version_json(game_dir: str, version_id: str) -> dict:
    path = Path(game_dir) / "versions" / version_id / f"{version_id}.json"
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def find_java(game_dir: str, version_id: str) -> str:
    """Java, которую скачал сам лаунчер для этой версии; иначе системная."""
    data = read_version_json(game_dir, version_id)
    if "javaVersion" not in data and data.get("inheritsFrom"):
        data = read_version_json(game_dir, data["inheritsFrom"])
    component = data.get("javaVersion", {}).get("component")
    if component:
        path = mll.runtime.get_executable_path(component, game_dir)
        if path:
            return str(path)
    return "java"


def ensure_injector() -> Path:
    """authlib-injector нужен, чтобы игра понимала аккаунты и скины Ely.by."""
    if INJECTOR.is_file():
        return INJECTOR
    try:
        meta = requests.get(INJECTOR_LATEST, timeout=20).json()
        data = requests.get(meta["download_url"], timeout=60).content
    except Exception as e:
        raise RuntimeError(f"Не удалось скачать authlib-injector: {e}") from e
    tmp = INJECTOR.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(INJECTOR)
    return INJECTOR


def build_command(settings: Settings, acc: Account, version_id: str,
                  inst=None) -> tuple[list[str], str]:
    game_dir = settings.game_dir
    if inst is not None:
        work = inst.work_dir(game_dir)
        ram = inst.ram_mb or settings.ram_mb
        extra = inst.java_args or ""
    else:
        work, ram, extra = Path(game_dir), settings.ram_mb, ""
    work.mkdir(parents=True, exist_ok=True)

    jvm = [f"-Xmx{ram}M", f"-Xms{min(512, ram)}M"]
    jvm += shlex.split(settings.java_args or "")
    jvm += shlex.split(extra)
    if acc.type == "elyby":
        jvm.append(f"-javaagent:{ensure_injector()}={ELYBY_API}")

    options = {
        "username": acc.username,
        "uuid": acc.uuid.replace("-", ""),
        "token": acc.access_token,
        "jvmArguments": jvm,
        "launcherName": "PyCraft",
        "launcherVersion": "0.1",
        "gameDirectory": str(work),
        "executablePath": find_java(game_dir, version_id),
    }
    if settings.width and settings.height:
        options["customResolution"] = True
        options["resolutionWidth"] = str(settings.width)
        options["resolutionHeight"] = str(settings.height)

    cmd = mll.command.get_minecraft_command(version_id, game_dir, options)
    return cmd, str(work)