import json
import re
import threading
from urllib.parse import quote

import requests


class EVEApi:
    def __init__(self, host, username, password, https=False, verify_ssl=False):
        clean = re.sub(r"^https?://", "", host.strip()).rstrip("/")
        self.base = ("https://" if https else "http://") + clean
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._auth_lock = threading.Lock()

    def _path(self, path):
        return quote(path.lstrip("/"), safe="/")

    @staticmethod
    def _decode_response(response):
        try:
            return response.json()
        except Exception:
            return {"status": "error", "message": response.text.strip()}

    @staticmethod
    def _is_auth_expired(response, data):
        # Public EVE-NG documentation describes 400/401 for expired or missing
        # sessions. Some EVE-NG builds return HTTP 412 with error 90001.
        return (
            data.get("status") == "unauthorized"
            and (
                response.status_code in (400, 401, 412)
                or "90001" in str(data.get("message", ""))
            )
        )

    def request(self, method, endpoint, _retry_auth=True, **kwargs):
        response = self.session.request(
            method,
            self.base + "/api" + endpoint,
            timeout=30,
            **kwargs,
        )
        data = self._decode_response(response)

        if _retry_auth and self._is_auth_expired(response, data):
            # A user can have only one active EVE-NG Web/API session. A login
            # from another browser/location can invalidate this application's
            # cookie. Re-authenticate once, then replay the original request.
            with self._auth_lock:
                self.login()
            return self.request(method, endpoint, _retry_auth=False, **kwargs)

        if not response.ok or data.get("status") not in (None, "success"):
            raise RuntimeError(
                f"EVE API {method} {endpoint}: HTTP {response.status_code}: {data}"
            )
        return data

    def _login_attempt(self, payload):
        response = self.session.post(
            self.base + "/api/auth/login",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        return response, self._decode_response(response)

    def login(self):
        """Authenticate and request native-console URLs from EVE-NG.

        EVE-NG Pro documents ``html5=0`` for native console mode. Recent
        Community builds also accept the console preference and may otherwise
        return Guacamole/HTML5 client URLs instead of the raw dynamic Telnet
        endpoint needed by the live validator.
        """
        payload = {
            "username": self.username,
            "password": self.password,
            "html5": "0",
        }
        response, data = self._login_attempt(payload)

        # Compatibility fallback for older Community builds that explicitly
        # reject the html5 field. Do not hide ordinary bad-credential errors.
        if (
            not self.base.startswith("https://")
            and (not response.ok or data.get("status") != "success")
        ):
            detail = (data.get("message") or response.text or "").lower()
            if "html5" in detail or "unknown parameter" in detail or "unsupported parameter" in detail:
                payload.pop("html5", None)
                response, data = self._login_attempt(payload)

        if not response.ok or data.get("status") != "success":
            detail = data.get("message") or response.text.strip() or "No response body"
            raise RuntimeError(
                f"EVE API login failed: HTTP {response.status_code}: {detail}. "
                "Use the EVE-NG Web/API account, not the SSH account."
            )
        return data

    def auth_info(self):
        """Return information about the currently authenticated API user."""
        return self.request("GET", "/auth")

    def folder(self, path):
        """Return the content of an existing EVE-NG folder."""
        normalized = "/" + "/".join(part for part in path.split("/") if part)
        if normalized == "/":
            return self.request("GET", "/folders/")
        return self.request("GET", "/folders/" + self._path(normalized))

    def create_folder(self, parent, name):
        return self.request("POST", "/folders", json={"path": parent, "name": name})

    def ensure_folder(self, path):
        """Create a folder path recursively when it does not already exist.

        EVE-NG requires the parent folder to exist before POST /labs. This
        helper walks the requested path from root and creates only missing
        components using the documented POST /folders API.
        """
        parts = [part for part in path.strip().split("/") if part]
        if not parts:
            return "/"

        parent = "/"
        for part in parts:
            current = parent.rstrip("/") + "/" + part
            try:
                self.folder(current)
            except RuntimeError as exc:
                message = str(exc)
                if "60008" not in message and "does not exist" not in message.lower():
                    raise
                self.create_folder(parent, part)
            parent = current

        return parent

    def create_lab(self, folder, name, description="CCNA 200-301 lab"):
        return self.request(
            "POST",
            "/labs",
            json={
                "path": folder,
                "name": name,
                "version": "4",
                "author": "CCNA EVE Lab Builder",
                "description": description,
                "body": "Generated by CCNA EVE Lab Builder V4",
            },
        )

    def lab_path(self, folder, name):
        return folder.rstrip("/") + "/" + name + ".unl"

    def get_lab(self, lab):
        return self.request("GET", "/labs/" + self._path(lab))

    def add_node(self, lab, node):
        return self.request("POST", f"/labs/{self._path(lab)}/nodes", json=node)

    def nodes(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes")

    def node(self, lab, node_id):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes/{node_id}")

    def interfaces(self, lab, node_id):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes/{node_id}/interfaces")

    def add_network(self, lab, name, left="50%", top="50%", net_type="bridge"):
        return self.request(
            "POST",
            f"/labs/{self._path(lab)}/networks",
            json={"type": net_type, "name": name, "left": left, "top": top},
        )

    def networks(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/networks")

    def links(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/links")

    def topology(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/topology")

    def start_all(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes/start")

    def stop_all(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes/stop")

    def wipe_all(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes/wipe")

    def export_all(self, lab):
        return self.request("GET", f"/labs/{self._path(lab)}/nodes/export")

    def connect_interface_experimental(self, lab, node_id, interface_id, network_id):
        return self.request(
            "PUT",
            f"/labs/{self._path(lab)}/nodes/{node_id}/interfaces",
            json={str(interface_id): str(network_id)},
        )
