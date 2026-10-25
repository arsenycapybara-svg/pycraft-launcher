"""Вход через Microsoft (device code) -> Xbox Live -> XSTS -> Minecraft."""
import threading
import time
import uuid as uuidlib

import requests

from .models import Account

SCOPE = "XboxLive.signin offline_access"
BASE = "https://login.microsoftonline.com/consumers/oauth2/v2.0"
DEVICE_URL = f"{BASE}/devicecode"
TOKEN_URL = f"{BASE}/token"
XBL_URL = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_API = "https://api.minecraftservices.com"

XERR = {
    2148916233: "У этой учётной записи Microsoft нет профиля Xbox. Создайте его на xbox.com и повторите.",
    2148916235: "Xbox Live недоступен в вашей стране.",
    2148916236: "Для этой учётной записи нужно пройти проверку возраста на сайте Xbox.",
    2148916237: "Для этой учётной записи нужно пройти проверку возраста на сайте Xbox.",
    2148916238: "Детская учётная запись: добавьте её в семейную группу Microsoft и разрешите онлайн-игры.",
}


class MicrosoftError(Exception):
    pass


def _json(resp) -> dict:
    try:
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def _ms_error(data: dict, resp) -> str:
    desc = str(data.get("error_description") or data.get("error") or f"HTTP {resp.status_code}")
    desc = desc.split("\r\n")[0]
    low = desc.lower()
    if "aadsts700016" in low:
        return "Приложение с таким Client ID не найдено. Проверьте Client ID."
    if "aadsts7000218" in low or "public client" in low:
        return "В настройках приложения Azure включите «Allow public client flows»."
    return desc


def _post(url: str, **kw):
    try:
        return requests.post(url, timeout=(10, 30), **kw)
    except requests.RequestException as e:
        raise MicrosoftError(f"Нет связи с сервером: {e}") from e


def request_device_code(client_id: str) -> dict:
    r = _post(DEVICE_URL, data={"client_id": client_id, "scope": SCOPE})
    data = _json(r)
    if r.status_code != 200 or "device_code" not in data:
        raise MicrosoftError(_ms_error(data, r))
    return data


def poll_token(client_id: str, device: dict, cancel: threading.Event) -> dict:
    interval = int(device.get("interval", 5))
    deadline = time.monotonic() + int(device.get("expires_in", 900))
    while time.monotonic() < deadline:
        if cancel.wait(interval):
            raise MicrosoftError("Вход отменён")
        r = _post(TOKEN_URL, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id,
            "device_code": device["device_code"],
        })
        data = _json(r)
        if r.status_code == 200 and "access_token" in data:
            return data
        err = data.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err == "authorization_declined":
            raise MicrosoftError("Вход отклонён на странице Microsoft")
        if err in ("expired_token", "bad_verification_code"):
            raise MicrosoftError("Код устарел, начните вход заново")
        raise MicrosoftError(_ms_error(data, r))
    raise MicrosoftError("Время ожидания входа истекло")


def refresh_tokens(client_id: str, refresh_token: str) -> dict:
    r = _post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
        "scope": SCOPE,
    })
    data = _json(r)
    if r.status_code != 200 or "access_token" not in data:
        if data.get("error") == "invalid_grant":
            raise MicrosoftError("Сессия Microsoft истекла. Войдите заново.")
        raise MicrosoftError(_ms_error(data, r))
    return data


def _minecraft_token(ms_access: str) -> tuple[str, int]:
    r = _post(XBL_URL, json={
        "Properties": {"AuthMethod": "RPS", "SiteName": "user.auth.xboxlive.com",
                       "RpsTicket": "d=" + ms_access},
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    }, headers={"Accept": "application/json"})
    d = _json(r)
    if r.status_code != 200 or "Token" not in d:
        raise MicrosoftError(f"Xbox Live: HTTP {r.status_code}")
    xbl = d["Token"]
    uhs = d["DisplayClaims"]["xui"][0]["uhs"]

    r = _post(XSTS_URL, json={
        "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl]},
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT",
    }, headers={"Accept": "application/json"})
    d = _json(r)
    if r.status_code != 200 or "Token" not in d:
        raise MicrosoftError(XERR.get(d.get("XErr"), f"XSTS: HTTP {r.status_code}"))
    xsts = d["Token"]

    r = _post(f"{MC_API}/authentication/login_with_xbox",
              json={"identityToken": f"XBL3.0 x={uhs};{xsts}"})
    d = _json(r)
    if r.status_code != 200 or "access_token" not in d:
        if "Invalid app registration" in r.text:
            raise MicrosoftError(
                "Mojang отклонил приложение (Invalid app registration). "
                "Приложению Azure нужно одобрение для Minecraft API: aka.ms/AppRegInfo")
        raise MicrosoftError(f"Minecraft: HTTP {r.status_code}")
    return d["access_token"], int(d.get("expires_in", 86400))


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_profile(mc_token: str) -> dict:
    try:
        r = requests.get(f"{MC_API}/minecraft/profile", headers=_auth(mc_token), timeout=(10, 30))
    except requests.RequestException as e:
        raise MicrosoftError(f"Нет связи с сервером: {e}") from e
    if r.status_code == 404:
        raise MicrosoftError("На этой учётной записи нет Minecraft: Java Edition.")
    if r.status_code != 200:
        raise MicrosoftError(f"Профиль Minecraft: HTTP {r.status_code}")
    return r.json()


def active_skin(profile: dict, default_url: str = "", default_variant: str = "classic") -> tuple[str, str]:
    for s in profile.get("skins", []):
        if s.get("state") == "ACTIVE":
            return s.get("url", default_url), str(s.get("variant", default_variant)).lower()
    return default_url, default_variant


def finish_login(tokens: dict, old_refresh: str = "") -> Account:
    mc_token, expires_in = _minecraft_token(tokens["access_token"])
    profile = get_profile(mc_token)
    url, variant = active_skin(profile)
    return Account(
        type="microsoft",
        username=profile["name"],
        uuid=str(uuidlib.UUID(profile["id"])),
        access_token=mc_token,
        refresh_token=tokens.get("refresh_token") or old_refresh,
        expires_at=time.time() + expires_in,
        skin_url=url,
        skin_variant=variant,
    )


def ensure_fresh(acc: Account, client_id: str, margin: int = 300) -> Account:
    """Обновляет токен Minecraft, если он скоро истечёт."""
    if acc.type != "microsoft" or time.time() < acc.expires_at - margin:
        return acc
    if not acc.refresh_token:
        raise MicrosoftError("Нет токена обновления. Войдите заново.")
    if not client_id:
        raise MicrosoftError("Укажите Client ID приложения Microsoft (вкладка «Аккаунты»).")
    tokens = refresh_tokens(client_id, acc.refresh_token)
    return finish_login(tokens, acc.refresh_token)


def upload_skin(acc: Account, png: bytes, variant: str) -> dict:
    try:
        r = requests.post(f"{MC_API}/minecraft/profile/skins", headers=_auth(acc.access_token),
                          data={"variant": variant}, files={"file": ("skin.png", png, "image/png")},
                          timeout=(10, 60))
    except requests.RequestException as e:
        raise MicrosoftError(f"Нет связи с сервером: {e}") from e
    if r.status_code not in (200, 204):
        raise MicrosoftError(f"Не удалось загрузить скин: HTTP {r.status_code}")
    return _json(r)


def reset_skin(acc: Account) -> None:
    try:
        r = requests.delete(f"{MC_API}/minecraft/profile/skins/active",
                            headers=_auth(acc.access_token), timeout=(10, 30))
    except requests.RequestException as e:
        raise MicrosoftError(f"Нет связи с сервером: {e}") from e
    if r.status_code not in (200, 204):
        raise MicrosoftError(f"Не удалось сбросить скин: HTTP {r.status_code}")