"""OptiFine как отдельная версия. Официального API нет: файл берётся с зеркала BMCLAPI
(если оно доступно) или из .jar, который вы скачали на optifine.net сами."""
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import minecraft_launcher_lib as mll

from .. import net
from . import runner

HOSTS = [
    "https://bmclapi2.bangbang93.com/optifine",
    "https://bmclapi.bangbang93.com/optifine",
]


def patch_key(patch: str) -> tuple:
    m = re.match(r"([A-Za-z]+)(\d+)", patch)
    return (m.group(1), int(m.group(2))) if m else (patch, 0)


def list_versions() -> list[dict]:
    r = net.raw_get(f"{HOSTS[0]}/versionList", timeout=(8, 25))
    r.raise_for_status()
    result = []
    for e in r.json():
        patch = str(e.get("patch", ""))
        if str(e.get("filename", "")).startswith("preview") or patch.lower().startswith("pre"):
            continue
        result.append({"mc": e["mcversion"], "type": e["type"], "patch": patch})
    return result


def _download(mc: str, typ: str, patch: str, dest: Path, callback: dict) -> None:
    status = callback.get("setStatus", lambda s: None)
    set_max = callback.get("setMax", lambda v: None)
    set_prog = callback.get("setProgress", lambda v: None)
    errors = []

    for base in HOSTS:
        host = base.split("/")[2]
        try:
            status(f"Подключение к {host}...")
            with net.raw_get(f"{base}/{mc}/{typ}/{patch}", stream=True, timeout=(8, 25)) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length") or 0)
                set_max(total or 1)
                done = 0
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(65536):
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            set_prog(done)
                            status(f"Скачивание OptiFine... {done / 1048576:.1f} / {total / 1048576:.1f} МБ")
                        else:
                            status(f"Скачивание OptiFine... {done / 1048576:.1f} МБ")
            if not zipfile.is_zipfile(dest):
                raise ValueError("сервер вернул не файл OptiFine")
            return
        except Exception as e:
            errors.append(f"{host}: {type(e).__name__}")

    raise RuntimeError(
        "Зеркало OptiFine недоступно из вашей сети (" + "; ".join(errors) + "). "
        "Скачайте файл на optifine.net кнопкой «Открыть optifine.net», затем нажмите "
        "«Найти в Загрузках».")


def install(mc: str, typ: str, patch: str, game_dir: str, callback: dict | None,
            local_jar: Path | None = None) -> None:
    callback = callback or {}
    status = callback.get("setStatus", lambda s: None)
    gd = Path(game_dir)
    of_ver = f"{mc}_{typ}_{patch}"               # например 1.20.1_HD_U_I6
    version_id = f"{mc}-OptiFine_{typ}_{patch}"

    status(f"Установка Minecraft {mc}...")
    mll.install.install_minecraft_version(mc, game_dir, callback=callback)

    with tempfile.TemporaryDirectory() as tmp:
        installer_jar = Path(tmp) / f"OptiFine_{of_ver}.jar"
        if local_jar:
            shutil.copy(local_jar, installer_jar)
        else:
            _download(mc, typ, patch, installer_jar, callback)

        if not zipfile.is_zipfile(installer_jar):
            raise RuntimeError("Файл OptiFine повреждён (это не .jar)")

        with zipfile.ZipFile(installer_jar) as z:
            names = z.namelist()
            lw_ver = "2.3"
            if "launchwrapper-of.txt" in names:
                lw_ver = z.read("launchwrapper-of.txt").decode().strip()
            lw_name = f"launchwrapper-of-{lw_ver}.jar"
            if lw_name not in names:
                raise RuntimeError(
                    f"Для OptiFine {of_ver} автоустановка пока не поддерживается "
                    f"(внутри нет {lw_name})")
            lw_target = gd / "libraries" / "optifine" / "launchwrapper-of" / lw_ver / lw_name
            lw_target.parent.mkdir(parents=True, exist_ok=True)
            lw_target.write_bytes(z.read(lw_name))

        of_jar = gd / "libraries" / "optifine" / "OptiFine" / of_ver / f"OptiFine-{of_ver}.jar"
        of_jar.parent.mkdir(parents=True, exist_ok=True)
        vanilla_jar = gd / "versions" / mc / f"{mc}.jar"
        java = runner.find_java(game_dir, mc)

        status("Применение патча OptiFine...")
        try:
            res = subprocess.run(
                [java, "-Djava.awt.headless=true", "-cp", str(installer_jar),
                 "optifine.Patcher", str(vanilla_jar), str(installer_jar), str(of_jar)],
                capture_output=True, text=True, timeout=300,
            )
        except FileNotFoundError:
            raise RuntimeError("Java не найдена. Установите: sudo pacman -S jre21-openjdk jre17-openjdk")
        if res.returncode != 0 or not of_jar.is_file():
            out = (res.stderr or res.stdout or "").strip()[-600:]
            raise RuntimeError(f"Не удалось применить патч OptiFine: {out}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    data = {
        "id": version_id,
        "inheritsFrom": mc,
        "type": "release",
        "time": now,
        "releaseTime": now,
        "mainClass": "net.minecraft.launchwrapper.Launch",
        "arguments": {"game": ["--tweakClass", "optifine.OptiFineTweaker"]},
        "libraries": [
            {"name": f"optifine:OptiFine:{of_ver}"},
            {"name": f"optifine:launchwrapper-of:{lw_ver}"},
        ],
    }
    vdir = gd / "versions" / version_id
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / f"{version_id}.json").write_text(json.dumps(data, indent=2))
    status("Готово")