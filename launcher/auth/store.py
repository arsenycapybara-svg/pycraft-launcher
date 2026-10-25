import json
import os
from dataclasses import asdict

from ..paths import CONFIG_DIR
from .models import Account

FILE = CONFIG_DIR / "accounts.json"


class AccountStore:
    def __init__(self) -> None:
        self.accounts: list[Account] = []
        self.selected: str = ""
        self._load()

    def _load(self) -> None:
        if not FILE.exists():
            return
        try:
            data = json.loads(FILE.read_text())
            self.accounts = [Account(**a) for a in data.get("accounts", [])]
            self.selected = data.get("selected", "")
        except (OSError, ValueError, TypeError):
            pass

    def save(self) -> None:
        payload = {"accounts": [asdict(a) for a in self.accounts], "selected": self.selected}
        fd = os.open(FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2)

    def add(self, acc: Account) -> None:
        self.accounts = [a for a in self.accounts if a.id != acc.id] + [acc]
        self.selected = acc.id
        self.save()

    def remove(self, acc_id: str) -> None:
        self.accounts = [a for a in self.accounts if a.id != acc_id]
        if self.selected == acc_id:
            self.selected = self.accounts[0].id if self.accounts else ""
        self.save()

    def select(self, acc_id: str) -> None:
        if any(a.id == acc_id for a in self.accounts):
            self.selected = acc_id
            self.save()

    def current(self) -> Account | None:
        return next((a for a in self.accounts if a.id == self.selected), None)