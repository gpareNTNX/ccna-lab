import json
from pathlib import Path

DEFAULT = {
    "eve": {
        "host": "",
        "ssh_port": 22,
        "ssh_username": "root",
        "api_username": "admin",
        "https": False,
    },
    "lab": {"folder": "/CCNA-200-301", "master_name": "CCNA-MASTER-LAB"},
    "compatibility": {"experimental_cabling": False},
}


class Settings:
    def __init__(self, path=None):
        self.path = Path(path or Path.home() / ".ccna_eve_lab_builder.json")
        self.data = json.loads(json.dumps(DEFAULT))
        self.load()

    def load(self):
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                for section, values in saved.items():
                    if section in self.data and isinstance(values, dict):
                        self.data[section].update(values)

                # Migrate V4.1 settings, where one username was reused for SSH and API.
                saved_eve = saved.get("eve", {}) if isinstance(saved, dict) else {}
                if "username" in saved_eve and "ssh_username" not in saved_eve:
                    self.data["eve"]["ssh_username"] = saved_eve["username"]
                self.data["eve"].pop("username", None)
            except Exception:
                pass
        return self.data

    def save(self):
        # Passwords are intentionally never persisted.
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
