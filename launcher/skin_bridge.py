import hashlib
import threading
from pathlib import Path

import requests
from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot

from . import skins
from .auth import microsoft
from .auth.store import AccountStore
from .config import Settings


class SkinBridge(QObject):
    skinChanged = Signal()
    stateChanged = Signal()
    errorOccurred = Signal(str)
    infoMessage = Signal(str)

    def __init__(self, settings: Settings, store: AccountStore) -> None:
        super().__init__()
        self._settings = settings
        self._store = store
        self._view = ""
        self._mask = ""
        self._slim = False
        self._note = ""
        self._busy = False
        self._req = 0

    @Property(str, notify=skinChanged)
    def viewUrl(self) -> str:
        return self._view

    @Property(str, notify=skinChanged)
    def maskUrl(self) -> str:
        return self._mask

    @Property(bool, notify=skinChanged)
    def slim(self) -> bool:
        return self._slim

    @Property(str, notify=skinChanged)
    def note(self) -> str:
        return self._note

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    # --- загрузка и показ ---
    @Slot()
    def refresh(self) -> None:
        self._start_load(False)

    def _start_load(self, force: bool) -> None:
        self._req += 1
        threading.Thread(target=self._load, args=(self._req, force), daemon=True).start()

    def _reload(self, force: bool) -> None:
        self._req += 1
        self._load(self._req, force)

    def _fetch(self, acc) -> bytes | None:
        if acc.type == "microsoft":
            if acc.skin_url:
                r = requests.get(acc.skin_url.replace("http://", "https://"), timeout=(8, 20))
                if r.status_code == 200:
                    return r.content
            return skins.mojang_by_uuid(acc.uuid)
        if acc.type == "elyby":
            return skins.elyby_by_name(acc.username)
        return skins.mojang_by_name(acc.username)

    def _skin_data(self, acc, force: bool) -> tuple[bytes | None, str]:
        local = skins.override_path(acc)
        if local.is_file():
            return local.read_bytes(), "Локальный скин: виден только в лаунчере"

        source = {"microsoft": "Скин из профиля Minecraft",
                  "elyby": "Скин с Ely.by",
                  "offline": f"Скин игрока «{acc.username}» (в игре у пиратских аккаунтов стандартный)"}[acc.type]
        cache = skins.cache_path(acc)
        if not force and skins.fresh(cache):
            return cache.read_bytes(), source
        try:
            data = self._fetch(acc)
        except requests.RequestException:
            if cache.is_file():
                return cache.read_bytes(), source + " (сохранённый)"
            return None, "Нет связи: показан стандартный скин"
        if data:
            cache.write_bytes(data)
            return data, source
        return None, "Скин не найден: показан стандартный"

    def _load(self, req: int, force: bool = False) -> None:
        acc = self._store.current()
        data, note = None, "Нет аккаунта: показан стандартный скин"
        if acc is not None:
            try:
                data, note = self._skin_data(acc, force)
            except Exception as e:
                note = f"Не удалось получить скин ({type(e).__name__})"

        img = skins.normalize(data) if data else None
        slim = False
        if img is None:
            img, key = skins.placeholder(), "default"
        else:
            key = hashlib.sha1(data).hexdigest()[:16]
            slim = skins.is_slim(img) or bool(acc and acc.type == "microsoft"
                                              and acc.skin_variant == "slim")
        view, mask = skins.render_view(img, key)

        if req != self._req:
            return
        self._view = QUrl.fromLocalFile(str(view)).toString()
        self._mask = QUrl.fromLocalFile(str(mask)).toString()
        self._slim = slim
        self._note = note
        self.skinChanged.emit()

    # --- действия ---
    def _set_busy(self, value: bool) -> None:
        self._busy = value
        self.stateChanged.emit()

    def _spawn(self, job) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            try:
                job()
            except microsoft.MicrosoftError as e:
                self.errorOccurred.emit(str(e))
            except Exception as e:
                self.errorOccurred.emit(f"Скин: {e}")
            finally:
                self._set_busy(False)

        threading.Thread(target=work, daemon=True).start()

    @Slot(str)
    def uploadFile(self, url: str) -> None:
        acc = self._store.current()
        if acc is None:
            self.errorOccurred.emit("Сначала выберите аккаунт")
            return
        path = QUrl(url).toLocalFile() if url.startswith("file:") else url

        def job() -> None:
            p = Path(path)
            if p.stat().st_size > 2_000_000:
                raise RuntimeError("Файл слишком большой для скина")
            img = skins.normalize(p.read_bytes())
            if img is None:
                raise RuntimeError("Нужен PNG-скин 64×64 или 64×32")
            if acc.type == "microsoft":
                fresh = microsoft.ensure_fresh(acc, self._settings.ms_client_id)
                variant = "slim" if skins.is_slim(img) else "classic"
                profile = microsoft.upload_skin(fresh, skins.to_png(img), variant)
                fresh.skin_url, fresh.skin_variant = microsoft.active_skin(
                    profile, fresh.skin_url, variant)
                self._store.add(fresh)
                skins.clear_files(fresh)
                self._reload(True)
                self.infoMessage.emit("Скин загружен в профиль Minecraft")
            else:
                skins.override_path(acc).write_bytes(skins.to_png(img))
                self._reload(False)
                self.infoMessage.emit("Скин сохранён: он виден только в лаунчере")

        self._spawn(job)

    @Slot(str)
    def fetchByNick(self, nick: str) -> None:
        acc = self._store.current()
        nick = nick.strip()
        if acc is None:
            self.errorOccurred.emit("Сначала выберите аккаунт")
            return
        if not skins.NAME_RE.fullmatch(nick):
            self.errorOccurred.emit("Ник: до 16 символов, латиница, цифры и _")
            return

        def job() -> None:
            if acc.type == "microsoft":
                self._reload(True)
                self.infoMessage.emit("Скин обновлён из профиля Minecraft")
                return
            data = skins.elyby_by_name(nick) if acc.type == "elyby" else skins.mojang_by_name(nick)
            if not data or skins.normalize(data) is None:
                raise RuntimeError(f"Скин игрока «{nick}» не найден")
            skins.override_path(acc).write_bytes(data)
            self._reload(False)
            self.infoMessage.emit(f"Установлен скин игрока «{nick}» (только в лаунчере)")

        self._spawn(job)

    @Slot()
    def resetSkin(self) -> None:
        acc = self._store.current()
        if acc is None:
            return

        def job() -> None:
            if acc.type == "microsoft":
                fresh = microsoft.ensure_fresh(acc, self._settings.ms_client_id)
                microsoft.reset_skin(fresh)
                fresh.skin_url = ""
                fresh.skin_variant = "classic"
                self._store.add(fresh)
                skins.clear_files(fresh)
                self.infoMessage.emit("Скин сброшен на стандартный")
            else:
                skins.clear_files(acc)
                self.infoMessage.emit("Локальный скин удалён")
            self._reload(True)

        self._spawn(job)