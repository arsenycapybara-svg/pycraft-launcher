"""Клиент Modrinth API v2: поиск, зависимости, установка и распознавание файлов по хешу."""
import json
from pathlib import Path

import requests

from .minecraft.downloader import fetch_file, sha1_of

API = "https://api.modrinth.com/v2"
HEADERS = {"User-Agent": "pycraft-launcher/0.1 (personal Minecraft launcher)"}
DIRS = {"mod": "mods", "resourcepack": "resourcepacks", "shader": "shaderpacks"}
LOADERS = ("fabric", "forge", "quilt", "neoforge")


class ModrinthError(Exception):
    pass


def _check(r):
    if r.status_code == 429:
        raise ModrinthError("Modrinth: слишком много запросов, подождите минуту")
    if r.status_code >= 400:
        raise ModrinthError(f"Modrinth: HTTP {r.status_code}")
    return r.json()


def _get(path: str, params: dict | None = None):
    try:
        r = requests.get(API + path, params=params, headers=HEADERS, timeout=(10, 30))
    except requests.RequestException as e:
        raise ModrinthError(f"Нет связи с Modrinth: {e}") from e
    return _check(r)


def _post(path: str, payload: dict):
    try:
        r = requests.post(API + path, json=payload, headers=HEADERS, timeout=(10, 30))
    except requests.RequestException as e:
        raise ModrinthError(f"Нет связи с Modrinth: {e}") from e
    return _check(r)


def fmt_count(n) -> str:
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} млн"
    if n >= 1_000:
        return f"{n // 1000} тыс."
    return str(n)


# ---------- поиск ----------
def search(query: str, ptype: str, mc: str, loader: str,
           offset: int = 0, limit: int = 20) -> tuple[list[dict], int]:
    facets = [[f"project_type:{ptype}"]]
    if mc:
        facets.append([f"versions:{mc}"])
    if ptype == "mod" and loader in LOADERS:
        facets.append([f"categories:{loader}"])
    data = _get("/search", {
        "query": query,
        "facets": json.dumps(facets),
        "limit": limit,
        "offset": offset,
        "index": "relevance" if query else "downloads",
    })
    return data.get("hits", []), int(data.get("total_hits", 0))


# ---------- проекты ----------
_projects: dict[str, dict] = {}


def projects(ids: list[str]) -> dict[str, dict]:
    need = [i for i in ids if i not in _projects]
    for k in range(0, len(need), 50):
        chunk = need[k:k + 50]
        for pr in _get("/projects", {"ids": json.dumps(chunk)}):
            _projects[pr["id"]] = pr
    return {i: _projects[i] for i in ids if i in _projects}


def project_versions(pid: str, mc: str, loader: str, filter_loader: bool) -> list[dict]:
    params = {}
    if mc:
        params["game_versions"] = json.dumps([mc])
    if filter_loader and loader:
        params["loaders"] = json.dumps([loader])
    return _get(f"/project/{pid}/version", params)


def pick(versions: list[dict]) -> dict | None:
    for v in versions:
        if v.get("version_type") == "release":
            return v
    return versions[0] if versions else None


def _try_version(vid: str, mc: str, loader: str, check_loader: bool) -> dict | None:
    try:
        v = _get(f"/version/{vid}")
    except ModrinthError:
        return None
    if mc and mc not in v.get("game_versions", []):
        return None
    if check_loader and loader not in v.get("loaders", []):
        return None
    return v


def _primary_file(ver: dict) -> dict:
    files = ver.get("files") or []
    if not files:
        raise ModrinthError("У этой версии нет файлов")
    return next((f for f in files if f.get("primary")), files[0])


# ---------- установка с зависимостями ----------
def plan_install(project_id: str, mc: str, loader: str, have: set[str]) -> list[dict]:
    """Список файлов к установке: сначала зависимости, последним сам проект."""
    seen = set(have)
    plan: list[dict] = []

    def visit(pid: str, version_id: str | None = None, depth: int = 0) -> None:
        if pid in seen or depth > 4:
            return
        seen.add(pid)
        info = projects([pid]).get(pid)
        if not info:
            raise ModrinthError("Проект не найден на Modrinth")
        ptype = info.get("project_type", "")
        if ptype not in DIRS:
            raise ModrinthError(f"«{info.get('title', pid)}»: этот тип проектов пока не поддерживается")
        is_mod = ptype == "mod"

        ver = _try_version(version_id, mc, loader, is_mod) if version_id else None
        if ver is None:
            ver = pick(project_versions(pid, mc, loader, is_mod))
        if ver is None:
            suffix = f" ({loader})" if is_mod else ""
            raise ModrinthError(f"Для «{info['title']}» нет версии под Minecraft {mc}{suffix}")

        for d in ver.get("dependencies", []):
            if d.get("dependency_type") != "required":
                continue
            dep = d.get("project_id")
            if not dep and d.get("version_id"):
                dep = _get(f"/version/{d['version_id']}").get("project_id")
            if dep:
                visit(dep, d.get("version_id"), depth + 1)

        f = _primary_file(ver)
        plan.append({
            "project": pid,
            "title": info["title"],
            "type": ptype,
            "url": f["url"],
            "filename": f["filename"],
            "sha1": (f.get("hashes") or {}).get("sha1"),
        })

    visit(project_id)
    return plan


def install_plan(plan: list[dict], work_dir: Path, status, progress) -> None:
    for i, item in enumerate(plan):
        status(f"Загрузка: {item['title']}  ({i + 1}/{len(plan)})")
        dest = work_dir / DIRS[item["type"]] / Path(item["filename"]).name
        if not dest.exists():
            fetch_file(item["url"], dest, item.get("sha1"))
        progress((i + 1) / len(plan))


# ---------- распознавание установленных файлов ----------
_hash_cache: dict[tuple[int, int], str] = {}
_meta: dict[str, dict | None] = {}     # sha1 -> версия Modrinth или None


def file_sha1(p: Path) -> str:
    st = p.stat()
    key = (st.st_size, st.st_mtime_ns)
    h = _hash_cache.get(key)
    if h is None:
        h = sha1_of(p)
        _hash_cache[key] = h
    return h


def identify(paths: list[Path]) -> dict[Path, dict | None]:
    hashes = {p: file_sha1(p) for p in paths}
    todo = sorted({h for h in hashes.values() if h not in _meta})
    for i in range(0, len(todo), 100):
        chunk = todo[i:i + 100]
        found = _post("/version_files", {"hashes": chunk, "algorithm": "sha1"})
        for h in chunk:
            _meta[h] = found.get(h)
    return {p: _meta.get(h) for p, h in hashes.items()}


def installed_projects(directory: Path, exts: tuple = (".jar", ".zip")) -> set[str]:
    """id проектов, которые лежат во включённом виде в папке."""
    if not directory.is_dir():
        return set()
    files = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return {v["project_id"] for v in identify(files).values() if v}


def analyze(rows: list[dict], loader: str, mc: str) -> list[dict]:
    """Предупреждения: нет загрузчика, не хватает зависимостей, не та версия."""
    active = [r for r in rows if r["enabled"]]
    if active and loader not in LOADERS:
        return [{"text": "В профиле нет загрузчика модов (Fabric или Forge): моды не загрузятся.",
                 "project": ""}]

    have = {r["version"]["project_id"] for r in active if r["version"]}
    missing: dict[str, list[str]] = {}
    warns: list[dict] = []
    ok_loaders = {loader} | ({"fabric"} if loader == "quilt" else set())

    for r in active:
        v = r["version"]
        if not v:
            continue
        for d in v.get("dependencies", []):
            pid = d.get("project_id")
            if d.get("dependency_type") == "required" and pid and pid not in have:
                missing.setdefault(pid, []).append(r["title"])
        loaders = v.get("loaders") or []
        if loaders and not (ok_loaders & set(loaders)):
            warns.append({"text": f"«{r['title']}» сделан для {', '.join(loaders)}, а профиль на {loader}.",
                          "project": ""})
        elif mc and v.get("game_versions") and mc not in v["game_versions"]:
            warns.append({"text": f"«{r['title']}» заявлен для других версий игры, профиль на {mc}. "
                                  "Может не работать.", "project": ""})

    names = projects(list(missing)) if missing else {}
    first = []
    for pid, who in missing.items():
        title = names.get(pid, {}).get("title", pid)
        first.append({"text": f"Не хватает «{title}» (нужен для: {', '.join(sorted(set(who)))})",
                      "project": pid})
    return first + warns