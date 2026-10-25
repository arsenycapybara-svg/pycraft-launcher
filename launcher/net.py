"""Сетевой слой: таймауты 60–120 с, повторы, зеркала и докачка с места обрыва.

Патчит requests, поэтому действует и на minecraft-launcher-lib, и на наш код.
"""
import threading
import time
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BMCL = "https://bmclapi2.bangbang93.com"

MIRRORS = {
    "launchermeta.mojang.com": BMCL,
    "launcher.mojang.com": BMCL,
    "piston-meta.mojang.com": BMCL,
    "piston-data.mojang.com": BMCL,
    "libraries.minecraft.net": BMCL + "/maven",
    "resources.download.minecraft.net": BMCL + "/assets",
    "maven.minecraftforge.net": BMCL + "/maven",
    "maven.fabricmc.net": BMCL + "/maven",
    "meta.fabricmc.net": BMCL + "/fabric-meta",
}

SOURCE = "auto"        # mirror | auto | official
CUSTOM_FORGE = ""      # свой мирор для maven.minecraftforge.net
RESUME_TRIES = 10


def set_source(value: str) -> None:
    global SOURCE
    SOURCE = value if value in ("mirror", "auto", "official") else "auto"


def set_custom_forge(value: str) -> None:
    global CUSTOM_FORGE
    CUSTOM_FORGE = (value or "").strip().rstrip("/")


# --- «здоровье» хостов: если хост подряд падает, пробуем его в последнюю очередь ---
_lock = threading.Lock()
_fails: dict[str, int] = {}
_skip_until: dict[str, float] = {}


def _mark(host: str, ok: bool) -> None:
    with _lock:
        if ok:
            _fails[host] = 0
            return
        _fails[host] = _fails.get(host, 0) + 1
        if _fails[host] >= 3:
            _skip_until[host] = time.monotonic() + 120
            _fails[host] = 0


def _skipped(host: str) -> bool:
    return _skip_until.get(host, 0) > time.monotonic()


def _mirror_urls(url: str) -> list[str]:
    parts = urlsplit(url)
    tail = parts.path + (f"?{parts.query}" if parts.query else "")
    out = []
    if parts.netloc == "maven.minecraftforge.net" and CUSTOM_FORGE:
        out.append(CUSTOM_FORGE + tail)
    base = MIRRORS.get(parts.netloc)
    if base:
        out.append(base + tail)
    return out


def _targets(url: str) -> list[str]:
    mirrors = _mirror_urls(url)
    if not mirrors or SOURCE == "official":
        return [url]
    order = mirrors + [url] if SOURCE == "mirror" else [url] + mirrors
    live = [t for t in order if not _skipped(urlsplit(t).netloc)]
    return live + [t for t in order if t not in live]


def _timeout(given, long: bool, floor: bool):
    if isinstance(given, (int, float)):
        given = (given, given)
    if not floor:  # не файлы игры (вход, скины и т.п.): уважаем запрошенный таймаут
        return given if given is not None else (10, 60)
    conn_min, read_min = (20, 120) if long else (10, 60)
    if given is None:
        return (conn_min, read_min)
    return (max(given[0] or 0, conn_min), max(given[1] or 0, read_min))


_orig_request = requests.sessions.Session.request
_orig_init = requests.sessions.Session.__init__
_orig_iter_content = requests.Response.iter_content

# при сбое соединения повтор; при таймауте чтения сразу идём на другой источник
_RETRY = Retry(total=2, connect=1, read=0, status=1, backoff_factor=0.5,
               status_forcelist=(429, 502, 503, 504), raise_on_status=False)

_STALL = (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
          requests.exceptions.ChunkedEncodingError)


def _init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    adapter = HTTPAdapter(pool_connections=32, pool_maxsize=64, max_retries=_RETRY)
    self.mount("https://", adapter)
    self.mount("http://", adapter)


def _request(self, method, url, *args, **kwargs):
    url = str(url)
    stream = bool(kwargs.get("stream"))
    given = kwargs.get("timeout")
    floor = urlsplit(url).netloc in MIRRORS

    targets = _targets(url)
    if len(targets) > 1:
        plan = [(t, False) for t in targets] + [(url, True)]
    else:
        plan = [(url, True)]

    errors: list[Exception] = []
    for i, (target, long) in enumerate(plan):
        kwargs["timeout"] = _timeout(given, long, floor)
        host = urlsplit(target).netloc
        last = i == len(plan) - 1
        try:
            resp = _orig_request(self, method, target, *args, **kwargs)
        except requests.exceptions.RequestException as e:
            _mark(host, False)
            errors.append(e)
            if not last:
                print(f"[net] {host}: {type(e).__name__}, пробую другой источник")
            continue

        if resp.status_code >= 400 and not last:
            _mark(host, resp.status_code < 500)
            resp.close()
            continue

        _mark(host, resp.status_code < 500)
        if stream and resp.status_code == 200 and not resp.headers.get("Content-Encoding"):
            resp._pc_resume = True
            resp._pc_headers = dict(kwargs.get("headers") or {})
        return resp

    raise errors[-1]


# --- докачка: если поток оборвался или завис, продолжаем с нужного байта ---
def _skip_bytes(chunks, n):
    left = n
    for c in chunks:
        if left <= 0:
            yield c
        elif len(c) > left:
            yield c[left:]
            left = 0
        else:
            left -= len(c)


def _open_from(resp, got, chunk_size):
    headers = dict(getattr(resp, "_pc_headers", None) or {})
    headers["Range"] = f"bytes={got}-"
    headers["Accept-Encoding"] = "identity"
    session = requests.Session()
    r = _orig_request(session, "GET", resp.url, headers=headers, stream=True, timeout=(15, 60))
    r._pc_session = session
    if r.status_code == 206 and r.headers.get("Content-Range", "").startswith(f"bytes {got}-"):
        return _orig_iter_content(r, chunk_size, False)
    if r.status_code == 200:  # сервер не умеет Range: качаем заново и пропускаем уже полученное
        return _skip_bytes(_orig_iter_content(r, chunk_size, False), got)
    r.close()
    return None


def _resumable(resp, chunk_size):
    total = int(resp.headers.get("Content-Length") or 0)
    got = 0
    tries = 0
    source = _orig_iter_content(resp, chunk_size, False)
    while True:
        try:
            if source is None:
                source = _open_from(resp, got, chunk_size)
                if source is None:
                    raise requests.exceptions.ConnectionError("сервер не поддерживает докачку")
            for chunk in source:
                got += len(chunk)
                yield chunk
            resp._content_consumed = True
            return
        except _STALL:
            source = None
            if total and got >= total:
                resp._content_consumed = True
                return
            tries += 1
            if tries > RESUME_TRIES:
                raise
            print(f"[net] обрыв на {got} байтах, докачка {tries}/{RESUME_TRIES}")
            time.sleep(min(2 * tries, 8))


def _iter_content(self, chunk_size=1, decode_unicode=False):
    if (getattr(self, "_pc_resume", False) and not decode_unicode
            and chunk_size and not self._content_consumed):
        return _resumable(self, chunk_size)
    return _orig_iter_content(self, chunk_size, decode_unicode)


def raw_get(url: str, **kwargs) -> requests.Response:
    """Запрос без зеркал и повторов: для быстрых проверок."""
    with requests.Session() as s:
        return _orig_request(s, "GET", url, **kwargs)


requests.sessions.Session.__init__ = _init
requests.sessions.Session.request = _request
requests.Response.iter_content = _iter_content