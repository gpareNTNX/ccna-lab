import threading
import unittest

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.eve_api import EVEApi
from ccna_lab_builder.gui.nutanix_bonus_compat import (
    _install_bonus_build_guard,
    _install_idempotent_folder_create,
    _install_nxos_interface_aliases,
)


class InterfaceAPI:
    def interfaces(self, _lab, _node_id):
        return {
            "data": {
                "ethernet": [
                    {"id": 0, "name": "Mgmt0"},
                    {"id": 1, "name": "E1/1"},
                    {"id": 2, "name": "E1/2"},
                ]
            }
        }


class FolderRaceAPI(EVEApi):
    def __init__(self):
        super().__init__("eve.local", "admin", "secret")
        self.created = []
        self.checked = []

    def folder(self, path):
        self.checked.append(path)
        raise RuntimeError("Requested folder does not exist (60008).")

    def request(self, method, endpoint, **kwargs):
        if method == "POST" and endpoint == "/folders":
            payload = kwargs["json"]
            parent = payload["path"]
            name = payload["name"]
            self.created.append((parent, name))
            if name == "CCNA-200-301":
                raise RuntimeError("Folder already exists (60013).")
            return {"status": "success"}
        raise AssertionError(f"Unexpected request: {method} {endpoint}")


class FakeButton:
    def __init__(self):
        self.state = "normal"

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]


class FakeVar:
    def get(self):
        return "nxosv9k-9.3.1"


class FakeController:
    def __init__(self, window):
        self.window = window
        self.current = {"id": "NTNX-B01"}
        self.image_var = FakeVar()
        self.create_button = FakeButton()
        self.calls = 0
        self.entered = threading.Event()
        self.release = threading.Event()

    def create_lab(self):
        self.calls += 1
        self.entered.set()
        self.release.wait(1)
        return "/lab.unl"


class FakeWindow:
    def __init__(self):
        self.logs = []
        self._nutanix_bonus_controller = FakeController(self)

    def log(self, message):
        self.logs.append(message)

    def after(self, _delay, func):
        func()


class NutanixBonusCompatTests(unittest.TestCase):
    def test_ethernet_name_matches_eve_e_abbreviation(self):
        _install_nxos_interface_aliases()
        builder = LabBuilder(InterfaceAPI())

        self.assertEqual(builder._find_interface_index("/lab.unl", 3, "Ethernet1/1"), 1)
        self.assertEqual(builder._find_interface_index("/lab.unl", 3, "Eth1/2"), 2)

    def test_folder_already_exists_race_is_idempotent(self):
        original = EVEApi.create_folder
        try:
            _install_idempotent_folder_create()
            api = FolderRaceAPI()

            result = api.ensure_folder("/CCNA-200-301/NUTANIX-BONUS")

            self.assertEqual(result, "/CCNA-200-301/NUTANIX-BONUS")
            self.assertEqual(
                api.created,
                [("/", "CCNA-200-301"), ("/CCNA-200-301", "NUTANIX-BONUS")],
            )
        finally:
            EVEApi.create_folder = original

    def test_duplicate_bonus_build_request_is_ignored(self):
        window = FakeWindow()
        controller = window._nutanix_bonus_controller
        _install_bonus_build_guard(window)

        worker = threading.Thread(target=controller.create_lab)
        worker.start()
        self.assertTrue(controller.entered.wait(1))

        duplicate = controller.create_lab()
        controller.release.set()
        worker.join(1)

        self.assertIsNone(duplicate)
        self.assertEqual(controller.calls, 1)
        self.assertTrue(any("duplicate" in line.lower() for line in window.logs))
        self.assertEqual(controller.create_button.state, "normal")


if __name__ == "__main__":
    unittest.main()
