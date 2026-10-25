import inspect
import time
from pathlib import Path

import minecraft_launcher_lib as mll

from . import downloader, optifine, runner


def _status(callback: dict | None, text: str) -> None:
    if callback and "setStatus" in callback:
        callback["setStatus"](text)


def _with_retry(func, callback: dict | None, retries: int = 5, delay: int = 3) -> None:
    """Повторяет установку при сбоях сети (уже скачанное не качается заново)."""
    for attempt in range(1, retries + 1):
        try:
            func()
            return
        except RuntimeError:
            raise  # наши понятные ошибки: повтор не поможет
        except Exception as e:
            print(f"[Установка] Сбой (попытка {attempt}/{retries}): {e}")
            if attempt == retries:
                raise RuntimeError(
                    f"Не удалось скачать файлы. Проверьте соединение и попробуйте снова. "
                    f"Ошибка: {e}") from e
            _status(callback, f"Сбой сети, повтор {attempt}/{retries - 1}...")
            time.sleep(delay)


def install(loader: str, version_id: str, game_dir: str, callback: dict | None = None) -> None:
    """vanilla/fabric: версия Minecraft; forge: '1.20.1-47.2.0'; optifine: 'mc|type|patch'."""
    Path(game_dir).mkdir(parents=True, exist_ok=True)

    if loader == "vanilla":
        _with_retry(lambda: mll.install.install_minecraft_version(
            version_id, game_dir, callback=callback), callback)

    elif loader == "fabric":
        _with_retry(lambda: mll.fabric.install_fabric(
            version_id, game_dir, callback=callback), callback)

    elif loader == "forge":
        mc = version_id.split("-")[0]
        if not mll.forge.supports_automatic_install(version_id):
            raise RuntimeError("Эта версия Forge не поддерживает автоматическую установку")

        def run() -> None:
            mll.install.install_minecraft_version(mc, game_dir, callback=callback)
            downloader.prefetch_forge_libs(version_id, game_dir, callback)
            _status(callback, "Запуск установщика Forge...")
            kwargs = {}
            if "java" in inspect.signature(mll.forge.install_forge_version).parameters:
                kwargs["java"] = runner.find_java(game_dir, mc)
            mll.forge.install_forge_version(version_id, game_dir, callback=callback, **kwargs)

        _with_retry(run, callback)

    elif loader == "optifine":
        mc, typ, patch = version_id.split("|")
        _with_retry(lambda: optifine.install(mc, typ, patch, game_dir, callback), callback)

    else:
        raise RuntimeError(f"Неизвестный загрузчик: {loader}")