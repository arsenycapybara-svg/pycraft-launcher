"""Discord Rich Presence в фоновом потоке (pypresence блокирующий, поэтому не в UI-потоке)."""
import threading

# Application ID лаунчера из Discord Developer Portal
DEFAULT_CLIENT_ID = "1563919540998381610"


class DiscordPresence:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._enabled = False
        self._client_id = ""
        self._payload: dict | None = None
        self._stop = False
        self._wake = threading.Event()
        self._rpc = None
        self._rpc_id = ""
        self._sent: dict | None = None
        self._missing = False
        threading.Thread(target=self._loop, daemon=True).start()

    # ---------- управление ----------
    def configure(self, enabled: bool, client_id: str = "") -> None:
        """client_id необязателен: по умолчанию используется встроенный."""
        with self._lock:
            self._enabled = bool(enabled)
            self._client_id = (client_id or "").strip()
        self._wake.set()

    def menu(self) -> None:
        self._set({"details": "В меню PyCraft Launcher",
                   "large_image": "logo", "large_text": "PyCraft Launcher"})

    def playing(self, details: str, state: str, started: float) -> None:
        self._set({"details": details, "state": state, "start": int(started),
                   "large_image": "logo", "large_text": "PyCraft Launcher"})

    def shutdown(self) -> None:
        with self._lock:
            self._stop = True
        self._wake.set()

    def _set(self, payload: dict) -> None:
        with self._lock:
            self._payload = payload
        self._wake.set()

    # ---------- рабочий поток ----------
    def _close(self, clear: bool) -> None:
        rpc, self._rpc, self._sent = self._rpc, None, None
        if rpc is None:
            return
        try:
            if clear:
                rpc.clear()
            rpc.close()
        except Exception:
            pass

    def _loop(self) -> None:
        while True:
            self._wake.wait(timeout=20)   # по таймауту повторяем подключение, если Discord был закрыт
            self._wake.clear()
            with self._lock:
                stop, enabled, payload = self._stop, self._enabled, self._payload
                cid = self._client_id or DEFAULT_CLIENT_ID
            if stop:
                self._close(clear=True)
                return
            if not enabled or not cid.isdigit() or self._missing:
                self._close(clear=True)
                continue
            if payload is None:
                continue
            try:
                if self._rpc is None or self._rpc_id != cid:
                    self._close(clear=False)
                    try:
                        from pypresence import Presence
                    except ImportError:
                        print("[discord] не установлен pypresence: pip install pypresence")
                        self._missing = True
                        continue
                    rpc = Presence(cid)
                    rpc.connect()
                    self._rpc, self._rpc_id = rpc, cid
                if self._sent != payload:
                    self._rpc.update(**payload)
                    self._sent = dict(payload)
            except Exception as e:
                print(f"[discord] {type(e).__name__}: {e}")
                self._close(clear=False)