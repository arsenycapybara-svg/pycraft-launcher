import uuid

import requests

from .models import Account

AUTH_URL = "https://authserver.ely.by/auth"


class ElybyError(Exception):
    pass


def _post(path: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{AUTH_URL}/{path}", json=payload, timeout=15)
    except requests.RequestException as e:
        raise ElybyError(f"Нет связи с Ely.by: {e}") from e

    try:
        data = r.json()
    except ValueError:
        data = {}

    if r.status_code != 200:
        msg = data.get("errorMessage") or data.get("message") or f"HTTP {r.status_code}"
        if "two factor" in msg.lower():
            msg = "Включена двухфакторная защита: введите код в поле «Код 2FA»"
        elif "invalid credentials" in msg.lower():
            msg = "Неверный логин или пароль"
        raise ElybyError(msg)
    return data


def authenticate(login: str, password: str, totp: str = "") -> Account:
    if not login or not password:
        raise ElybyError("Введите логин и пароль")

    data = _post("authenticate", {
        "username": login,
        # при включённой 2FA Ely.by ждёт "пароль:код"
        "password": f"{password}:{totp}" if totp else password,
        "clientToken": uuid.uuid4().hex,
        "requestUser": True,
    })

    profile = data.get("selectedProfile")
    if not profile:
        raise ElybyError("У аккаунта нет игрового профиля")

    return Account(
        type="elyby",
        username=profile["name"],
        uuid=str(uuid.UUID(profile["id"])),
        access_token=data["accessToken"],
        client_token=data["clientToken"],
    )