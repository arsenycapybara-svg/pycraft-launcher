import json
import re
import time

import minecraft_launcher_lib as mll

from ..paths import CACHE_DIR
from . import optifine


def _cached(key: str, fetch, ttl: int = 6 * 3600):
    """Кэш на диске: свежий используем сразу, а при сбое сети берём старый."""
    path = CACHE_DIR / f"{key}.json"
    try:
        if path.is_file() and time.time() - path.stat().st_mtime < ttl:
            return json.loads(path.read_text())
    except (OSError, ValueError):
        pass
    try:
        data = fetch()
    except Exception:
        if path.is_file():
            try:
                return json.loads(path.read_text())
            except (OSError, ValueError):
                pass
        raise
    try:
        path.write_text(json.dumps(data))
    except OSError:
        pass
    return data


def _vanilla_all() -> list[dict]:
    def fetch():
        items = sorted(mll.utils.get_version_list(), key=lambda v: v["releaseTime"], reverse=True)
        return [{"id": v["id"], "type": v["type"]} for v in items]
    return _cached("vanilla", fetch)


def _fabric_data() -> dict:
    def fetch():
        return {
            "games": [{"version": g["version"], "stable": bool(g["stable"])}
                      for g in mll.fabric.get_all_minecraft_versions()],
            "loader": mll.fabric.get_latest_loader_version(),
        }
    return _cached("fabric", fetch)


def _num_key(text: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", text))


def _forge_latest() -> dict:
    def fetch():
        latest: dict[str, list[str]] = {}
        for full in mll.forge.list_forge_versions():
            mc, _, fv = full.partition("-")
            if not fv:
                continue
            cur = latest.get(mc)
            if cur is None or _num_key(fv) > _num_key(cur[1]):
                latest[mc] = [full, fv]
        return latest
    return _cached("forge", fetch)


def _item(vid: str, mc: str, mod: str, vtype: str) -> dict:
    # id уходит в установщик; mc и mod показываются в списке
    return {"id": vid, "mc": mc, "mod": mod, "type": vtype}


def available(loader: str, include_snapshots: bool) -> list[dict]:
    allowed = {"release", "snapshot"} if include_snapshots else {"release"}
    base = [v for v in _vanilla_all() if v["type"] in allowed]

    if loader == "vanilla":
        return [_item(v["id"], v["id"], "", v["type"]) for v in base]

    if loader == "fabric":
        data = _fabric_data()
        supported = {g["version"] for g in data["games"] if g["stable"] or include_snapshots}
        return [_item(v["id"], v["id"], f"Fabric {data['loader']}", v["type"])
                for v in base if v["id"] in supported]

    if loader == "forge":
        latest = _forge_latest()
        return [_item(latest[v["id"]][0], v["id"], f"Forge {latest[v['id']][1]}", v["type"])
                for v in base if v["id"] in latest]

    if loader == "optifine":
        best: dict[str, dict] = {}
        for e in _cached("optifine", optifine.list_versions):
            cur = best.get(e["mc"])
            if cur is None or optifine.patch_key(e["patch"]) > optifine.patch_key(cur["patch"]):
                best[e["mc"]] = e
        out = []
        for v in base:
            e = best.get(v["id"])
            if e:
                label = f"OptiFine {e['type'].replace('_', ' ')} {e['patch']}"
                out.append(_item(f"{e['mc']}|{e['type']}|{e['patch']}", e["mc"], label, v["type"]))
        return out

    return []


def installed_ids(game_dir: str) -> list[str]:
    try:
        return [v["id"] for v in mll.utils.get_installed_versions(game_dir)]
    except Exception:
        return []


def is_installed(loader: str, vid: str, ids: list[str]) -> bool:
    if loader == "vanilla":
        return vid in ids
    if loader == "fabric":
        return any(i.startswith("fabric-loader-") and i.endswith("-" + vid) for i in ids)
    if loader == "forge":
        mc, _, fv = vid.partition("-")
        return any(i.startswith(mc + "-") and "forge" in i.lower() and fv in i for i in ids)
    if loader == "optifine":
        mc, typ, patch = vid.split("|")
        return f"{mc}-OptiFine_{typ}_{patch}" in ids
    return False