import hashlib
import re
import uuid

from .models import Account

_NAME_RE = re.compile(r"[A-Za-z0-9_]{3,16}")


def offline_uuid(name: str) -> str:
    """Тот же UUID, что генерирует Minecraft для оффлайн-ника
    (аналог Java UUID.nameUUIDFromBytes("OfflinePlayer:<name>"))."""
    digest = bytearray(hashlib.md5(f"OfflinePlayer:{name}".encode("utf-8")).digest())
    digest[6] = (digest[6] & 0x0F) | 0x30
    digest[8] = (digest[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(digest)))


def create(name: str) -> Account:
    name = name.strip()
    if not _NAME_RE.fullmatch(name):
        raise ValueError("Ник: 3–16 символов, латиница, цифры и _")
    return Account(type="offline", username=name, uuid=offline_uuid(name))