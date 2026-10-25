import threading

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication

from . import net
from .auth import elyby, offline
from .auth.store import AccountStore
from .config import Settings


class AppBridge(QObject):
    accentChanged = Signal()
    accountsChanged = Signal()
    busyChanged = Signal()
    msChanged = Signal()
    forgeMirrorChanged = Signal()
    errorOccurred = Signal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self.store = AccountStore()
        self._busy = False
        self._ms_busy = False
        self._ms_code = ""
        self._ms_url = ""
        self._ms_status = ""
        self._ms_cancel = threading.Event()
        net.set_custom_forge(settings.forge_mirror)

    # --- тема ---
    @Property(str, notify=accentChanged)
    def accent(self) -> str:
        return self._settings.accent

    @Slot(str)
    def setAccent(self, color: str) -> None:
        self._settings.accent = color
        self._settings.save()
        self.accentChanged.emit()

    # --- Forge-мирор ---
    @Property(str, notify=forgeMirrorChanged)
    def forgeMirror(self) -> str:
        return self._settings.forge_mirror

    @Slot(str)
    def setForgeMirror(self, value: str) -> None:
        self._settings.forge_mirror = value.strip().rstrip("/")
        net.set_custom_forge(self._settings.forge_mirror)
        self._settings.save()
        self.forgeMirrorChanged.emit()

    # --- аккаунты ---
    @Property("QVariantList", notify=accountsChanged)
    def accounts(self) -> list:
        return [{**a.public(), "selected": a.id == self.store.selected}
                for a in self.store.accounts]

    @Property(str, notify=accountsChanged)
    def selectedName(self) -> str:
        cur = self.store.current()
        return cur.username if cur else ""

    @Property(str, notify=accountsChanged)
    def selectedType(self) -> str:
        cur = self.store.current()
        return cur.type if cur else ""

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    def _set_busy(self, value: bool) -> None:
        self._busy = value
        self.busyChanged.emit()

    @Slot(str, result=bool)
    def selectType(self, kind: str) -> bool:
        """Переключиться на последний добавленный аккаунт этого типа."""
        cur = self.store.current()
        if cur and cur.type == kind:
            return True
        matches = [a for a in self.store.accounts if a.type == kind]
        if not matches:
            return False
        self.store.select(matches[-1].id)
        self.accountsChanged.emit()
        return True

    @Slot(str)
    def addOffline(self, name: str) -> None:
        try:
            self.store.add(offline.create(name))
        except ValueError as e:
            self.errorOccurred.emit(str(e))
            return
        self.accountsChanged.emit()

    @Slot(str, str, str)
    def addElyby(self, login: str, password: str, totp: str) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            try:
                self.store.add(elyby.authenticate(login.strip(), password, totp.strip()))
                self.accountsChanged.emit()
            except elyby.ElybyError as e:
                self.errorOccurred.emit(str(e))
            finally:
                self._set_busy(False)

        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def openElybyRegister(self) -> None:
        QDesktopServices.openUrl(QUrl("https://account.ely.by/register"))

    @Slot(int)
    def selectAccount(self, index: int) -> None:
        if 0 <= index < len(self.store.accounts):
            self.store.select(self.store.accounts[index].id)
            self.accountsChanged.emit()

    @Slot(int)
    def removeAccount(self, index: int) -> None:
        if 0 <= index < len(self.store.accounts):
            self.store.remove(self.store.accounts[index].id)
            self.accountsChanged.emit()

    @Slot(str)
    def copyToClipboard(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)

    # --- Microsoft ---
    @Property(bool, notify=msChanged)
    def msBusy(self) -> bool:
        return self._ms_busy

    @Property(str, notify=msChanged)
    def msCode(self) -> str:
        return self._ms_code

    @Property(str, notify=msChanged)
    def msStatus(self) -> str:
        return self._ms_status

    @Property(str, notify=msChanged)
    def msClientId(self) -> str:
        return self._settings.ms_client_id

    @Slot(str)
    def setMsClientId(self, value: str) -> None:
        self._settings.ms_client_id = value.strip()
        self._settings.save()
        self.msChanged.emit()

    def _set_ms(self, busy: bool, code: str = "", url: str = "", status: str = "") -> None:
        self._ms_busy, self._ms_code, self._ms_url, self._ms_status = busy, code, url, status
        self.msChanged.emit()

    @Slot()
    def openMicrosoftLink(self) -> None:
        QDesktopServices.openUrl(QUrl(self._ms_url or "https://www.microsoft.com/link"))

    @Slot()
    def cancelMicrosoft(self) -> None:
        self._ms_cancel.set()

    @Slot()
    def startMicrosoft(self) -> None:
        if self._ms_busy:
            return
        client_id = self._settings.ms_client_id.strip()
        if not client_id:
            self.errorOccurred.emit("Сначала укажите Client ID приложения Microsoft (блок ниже).")
            return
        self._ms_cancel = threading.Event()
        cancel = self._ms_cancel
        self._set_ms(True, status="Запрашиваем код входа...")

        def work() -> None:
            try:
                dev = microsoft.request_device_code(client_id)
                url = dev.get("verification_uri") or "https://www.microsoft.com/link"
                self._set_ms(True, dev["user_code"], url,
                             "Введите код на странице Microsoft и подтвердите вход...")
                tokens = microsoft.poll_token(client_id, dev, cancel)
                self._set_ms(True, status="Проверяем лицензию Minecraft...")
                self.store.add(microsoft.finish_login(tokens))
                self.accountsChanged.emit()
            except microsoft.MicrosoftError as e:
                self.errorOccurred.emit(str(e))
            except Exception as e:
                self.errorOccurred.emit(f"Ошибка входа: {e}")
            finally:
                self._set_ms(False)

        threading.Thread(target=work, daemon=True).start()