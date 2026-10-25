import subprocess
import threading
import time
from collections import deque

from PySide6.QtCore import QObject, Property, Signal, Slot

from .auth import microsoft
from .auth.store import AccountStore
from .config import Settings
from .instances import LOADER_NAMES, Instance, InstanceStore, loader_and_mc
from .minecraft import runner
from .paths import DATA_DIR

LOG_DIR = DATA_DIR / "logs"


class GameBridge(QObject):
    stateChanged = Signal()
    logChanged = Signal()
    errorOccurred = Signal(str)
    sessionEnded = Signal(str, float)        # id профиля, секунд игры
    gameStarted = Signal(str, str, float)    # подпись версии, профиль, время старта

    def __init__(self, settings: Settings, accounts: AccountStore, instances: InstanceStore) -> None:
        super().__init__()
        self._settings = settings
        self._accounts = accounts
        self._instances = instances
        self._phase = "idle"          # idle | launching | running
        self._stopped = False
        self._announced = False
        self._status = ""
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._log: deque[str] = deque(maxlen=400)
        # слот выполняется в основном потоке, поэтому хранилище профилей меняется безопасно
        self.sessionEnded.connect(self._add_time)

    @Property(str, notify=stateChanged)
    def phase(self) -> str:
        return self._phase

    @Property(str, notify=stateChanged)
    def status(self) -> str:
        return self._status

    @Property(str, notify=logChanged)
    def log(self) -> str:
        return "\n".join(self._log)

    def _set_phase(self, phase: str, status: str = "") -> None:
        self._phase = phase
        self._status = status
        self.stateChanged.emit()

    @Slot(str, float)
    def _add_time(self, inst_id: str, seconds: float) -> None:
        if seconds < 5:        # мгновенные вылеты не считаем
            return
        fresh = self._instances.get(inst_id)
        if fresh is not None:
            fresh.play_seconds += seconds
            self._instances.update(fresh)

    def _label(self, inst: Instance) -> str:
        loader, mc = loader_and_mc(self._settings.game_dir, inst.version)
        name = LOADER_NAMES.get(loader, loader)
        return f"Minecraft {mc}" + ("" if loader == "vanilla" else f" ({name})")

    @Slot()
    def play(self) -> None:
        if self._phase != "idle":
            return
        inst = self._instances.current()
        if inst is None:
            self.errorOccurred.emit("Создайте профиль во вкладке «Профили»")
            return
        if not inst.version:
            self.errorOccurred.emit(f"В профиле «{inst.name}» не выбрана версия игры")
            return
        if inst.version not in runner.installed_versions(self._settings.game_dir):
            self.errorOccurred.emit(
                f"Версия «{inst.version}» не установлена. Установите её во вкладке «Версии».")
            return
        acc = self._accounts.current()
        if acc is None:
            self.errorOccurred.emit("Сначала добавьте аккаунт во вкладке «Аккаунты»")
            return

        inst.last_played = time.time()
        self._instances.update(inst)

        self._stopped = False
        self._announced = False
        self._log.clear()
        self.logChanged.emit()
        self._set_phase("launching", "Подготовка к запуску...")
        threading.Thread(target=self._run, args=(acc, inst), daemon=True).start()

    # ---------- «игра запущена успешно» ----------
    def _mark_running(self, inst: Instance, started_epoch: float) -> None:
        with self._lock:
            if self._announced or self._phase != "launching":
                return
            self._announced = True
        self._set_phase("running", "Игра запущена")
        self.gameStarted.emit(self._label(inst), inst.name, started_epoch)

    def _promote(self, proc, inst: Instance, started_epoch: float) -> None:
        if self._proc is proc and proc.poll() is None:
            self._mark_running(inst, started_epoch)

    def _handle_line(self, line: str, inst: Instance, started_epoch: float, state: dict) -> None:
        self._log.append(line)
        if "Setting user" in line or "Backend library" in line:
            self._mark_running(inst, started_epoch)
        now = time.monotonic()
        if now - state["last"] > 0.3:       # не перерисовываем лог на каждую строку
            self.logChanged.emit()
            state["last"] = now

    def _follow_log(self, proc, path, inst: Instance, started_epoch: float) -> None:
        state = {"last": 0.0}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            while True:
                pos = f.tell()
                line = f.readline()
                if line:
                    if not line.endswith("\n") and proc.poll() is None:
                        f.seek(pos)         # строка записана не до конца, ждём
                        time.sleep(0.05)
                        continue
                    self._handle_line(line.rstrip(), inst, started_epoch, state)
                    continue
                if proc.poll() is not None:
                    for rest in f.read().splitlines():
                        self._handle_line(rest, inst, started_epoch, state)
                    break
                time.sleep(0.1)
        self.logChanged.emit()

    def _run(self, acc, inst: Instance) -> None:
        try:
            if acc.type == "microsoft":
                self._set_phase("launching", "Обновление сессии Microsoft...")
                acc = microsoft.ensure_fresh(acc, self._settings.ms_client_id)
                self._accounts.add(acc)

            cmd, cwd = runner.build_command(self._settings, acc, inst.version, inst)

            # вывод игры пишем в файл: так игра не зависит от лаунчера и переживает его закрытие
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOG_DIR / "game.log"
            with open(log_path, "wb") as out:
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=out, stderr=subprocess.STDOUT,
                                        start_new_session=True)
            started = time.monotonic()
            started_epoch = time.time()
            self._proc = proc
            self._set_phase("launching", "Запуск игры...")
            threading.Timer(15.0, self._promote, args=(proc, inst, started_epoch)).start()

            self._follow_log(proc, log_path, inst, started_epoch)
            code = proc.wait()
            self.sessionEnded.emit(inst.id, time.monotonic() - started)
            if code != 0 and not self._stopped:
                self.errorOccurred.emit(
                    f"Игра завершилась с ошибкой (код {code}). Подробности в логе ниже.")
        except FileNotFoundError:
            self.errorOccurred.emit(
                "Java не найдена. Установите её: sudo pacman -S jre21-openjdk jre17-openjdk")
        except Exception as e:
            self.errorOccurred.emit(f"Не удалось запустить: {e}")
        finally:
            self._proc = None
            self._set_phase("idle", "")

    @Slot()
    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._stopped = True
            self._proc.terminate()