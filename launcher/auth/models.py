from dataclasses import dataclass


@dataclass
class Account:
    type: str                 # "offline" | "elyby" | "microsoft"
    username: str
    uuid: str
    access_token: str = "0"
    client_token: str = ""
    refresh_token: str = ""
    expires_at: float = 0.0
    skin_url: str = ""
    skin_variant: str = "classic"

    @property
    def id(self) -> str:
        return f"{self.type}:{self.uuid}"

    def public(self) -> dict:
        """То, что можно отдавать в QML (без токенов)."""
        return {"type": self.type, "username": self.username, "uuid": self.uuid}