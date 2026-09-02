import unittest

from ccna_lab_builder.core.challenges import ChallengeCatalog
from ccna_lab_builder.core.scenarios import ScenarioCatalog
from ccna_lab_builder.gui.challenge_pack import (
    _install_vpcs_builder_support,
    _vpcs_runtime_backend,
)
from ccna_lab_builder.core.builder import LabBuilder


class ChallengeCatalogTests(unittest.TestCase):
    def test_challenge_pack_is_separate_from_37_ccna_labs(self):
        self.assertEqual(len(ScenarioCatalog().all()), 37)
        catalog = ChallengeCatalog()
        self.assertEqual(len(catalog.all()), 8)
        self.assertEqual(len(catalog.archive()), 28)
        self.assertTrue(all(item["id"].startswith("PT-C") for item in catalog.all()))

    def test_challenge_topologies_are_self_contained(self):
        for challenge in ChallengeCatalog().all():
            nodes = challenge["topology"]["nodes"]
            links = challenge["topology"]["links"]
            names = {node["name"] for node in nodes}
            used = set()
            for link in links:
                self.assertIn(link["a"], names, challenge["id"])
                self.assertIn(link["b"], names, challenge["id"])
                for endpoint in ((link["a"], link["a_if"]), (link["b"], link["b_if"])):
                    self.assertNotIn(endpoint, used, f"{challenge['id']} reuses {endpoint}")
                    used.add(endpoint)
            for check in challenge.get("checks", []):
                target = next(node for node in nodes if node["name"] == check["node"])
                self.assertNotEqual(target.get("template"), "vpcs")

    def test_archive_tracks_all_unique_pkt_payloads(self):
        archive = ChallengeCatalog().archive()
        self.assertEqual(len({item["id"] for item in archive}), 28)
        self.assertTrue(any(item["status"] == "blocked" for item in archive))
        self.assertTrue(any(item["status"] == "migrated" for item in archive))


class VpcsSupportTests(unittest.TestCase):
    def test_vpcs_payload_uses_builtin_eve_node_type(self):
        _install_vpcs_builder_support()
        payload = LabBuilder._scenario_node_payload(
            {
                "name": "PC-A",
                "template": "vpcs",
                "left": "25%",
                "top": "75%",
                "interfaces": 1,
            },
            "unused-router-image",
            "unused-switch-image",
        )
        self.assertEqual(payload["type"], "vpcs")
        self.assertEqual(payload["template"], "vpcs")
        self.assertEqual(payload["image"], "")
        self.assertEqual(payload["icon"], "Desktop.png")
        self.assertEqual(payload["ethernet"], 1)

    def test_exact_vpcs_runtime_derives_verified_console_port(self):
        class FakeSSH:
            def exec(self, _command):
                return (
                    "__PID__=4321\n"
                    "__CWD__=/opt/unetlab/tmp/1/lab-uuid/5\n",
                    "",
                )

            def console_listener_info(self, port):
                self.port = port
                return [f"127.0.0.1:{port}"]

        class FakeValidator:
            def __init__(self):
                self.ssh = FakeSSH()
                self._active_lab_uuid = "lab-uuid"
                self._runtime_note = ""
                self.messages = []

            def log(self, message):
                self.messages.append(message)

        validator = FakeValidator()
        backend = _vpcs_runtime_backend(validator, 5)
        self.assertEqual(backend["kind"], "tcp")
        self.assertEqual(backend["source"], "vpcs-runtime")
        self.assertEqual(backend["port"], 32768 + 128 + 5)
        self.assertEqual(validator.ssh.port, backend["port"])


if __name__ == "__main__":
    unittest.main()
