import base64
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from ccna_lab_builder.gui.ssh_native_cabling import (
    _REMOTE_SCRIPT,
    _lab_fs_path,
)


class SSHNativeCablingTests(unittest.TestCase):
    def test_lab_fs_path_maps_to_eve_lab_directory(self):
        self.assertEqual(
            _lab_fs_path("/CCNA-200-301/Test Lab.unl"),
            "/opt/unetlab/labs/CCNA-200-301/Test Lab.unl",
        )

    def test_lab_fs_path_rejects_traversal(self):
        with self.assertRaises(ValueError):
            _lab_fs_path("/CCNA/../etc/passwd.unl")

    def test_remote_script_creates_invisible_bridge_and_interfaces(self):
        source = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<lab name="test"><topology><nodes>'
            '<node id="1" name="R1" type="qemu" template="vios" ethernet="4" />'
            '<node id="2" name="R2" type="qemu" template="vios" ethernet="4" />'
            '</nodes><networks /></topology></lab>'
        )
        payload = [
            {
                "name": "LINK-01-R1-R2",
                "left": "0",
                "top": "0",
                "a": {
                    "name": "R1",
                    "node_id": 1,
                    "if_name": "Gi0/0",
                    "if_id": 0,
                },
                "b": {
                    "name": "R2",
                    "node_id": 2,
                    "if_name": "Gi0/0",
                    "if_id": 0,
                },
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.unl"
            path.write_text(source, encoding="utf-8")
            encoded = base64.b64encode(
                json.dumps(payload).encode("utf-8")
            ).decode("ascii")
            result = subprocess.run(
                [sys.executable, "-c", _REMOTE_SCRIPT, str(path), encoded],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("EVE_CABLING_OK=", result.stdout)

            root = ET.parse(path).getroot()
            network = root.find("./topology/networks/network")
            self.assertIsNotNone(network)
            self.assertEqual(network.get("id"), "1")
            self.assertEqual(network.get("type"), "bridge")
            self.assertEqual(network.get("visibility"), "0")

            for node_id in ("1", "2"):
                interface = root.find(
                    f"./topology/nodes/node[@id='{node_id}']/interface[@id='0']"
                )
                self.assertIsNotNone(interface)
                self.assertEqual(interface.get("name"), "Gi0/0")
                self.assertEqual(interface.get("network_id"), "1")


if __name__ == "__main__":
    unittest.main()
