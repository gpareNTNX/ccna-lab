import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ccna_lab_builder.gui.eve_inventory_cabling_fix import (
    _classify_qemu_images,
    _parse_inventory_output,
    _relax_node_id_check,
)
from ccna_lab_builder.gui.ssh_native_cabling import _REMOTE_SCRIPT


class EveInventoryCablingFixTests(unittest.TestCase):
    def test_cabling_accepts_stale_api_node_ids_when_unl_names_match(self):
        source = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<lab name="test"><topology><nodes>'
            '<node id="7" name="SW1-CORE" type="qemu" template="viosl2" ethernet="8" />'
            '<node id="9" name="SW2-DIST" type="qemu" template="viosl2" ethernet="8" />'
            '</nodes><networks /></topology></lab>'
        )
        payload = [
            {
                "name": "LINK-01",
                "left": "0",
                "top": "0",
                "a": {
                    "name": "SW1-CORE",
                    "node_id": 1,
                    "if_name": "Gi0/0",
                    "if_id": 0,
                },
                "b": {
                    "name": "SW2-DIST",
                    "node_id": 2,
                    "if_name": "Gi0/0",
                    "if_id": 0,
                },
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "advanced.unl"
            path.write_text(source, encoding="utf-8")
            encoded = base64.b64encode(json.dumps(payload).encode()).decode("ascii")
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    _relax_node_id_check(_REMOTE_SCRIPT),
                    str(path),
                    encoded,
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("EVE_CABLING_OK=", result.stdout)
        self.assertNotIn("node id mismatch", result.stdout)

    def test_qemu_classifier_keeps_every_folder_and_recognizes_aliases(self):
        inventory = _classify_qemu_images(
            [
                "VIOS-adventerprisek9-159",
                "vios_l2-adventerprisek9-159",
                "nxosv9k-10.5.1",
                "csr1000vng-universalk9",
                "linux-ubuntu-24.04",
            ]
        )
        self.assertEqual(inventory["routers"], ["VIOS-adventerprisek9-159"])
        self.assertEqual(inventory["switches"], ["vios_l2-adventerprisek9-159"])
        self.assertEqual(inventory["nxosv9k"], ["nxosv9k-10.5.1"])
        self.assertEqual(
            inventory["other"],
            ["csr1000vng-universalk9", "linux-ubuntu-24.04"],
        )
        self.assertEqual(inventory["all"], 5)
        self.assertEqual(len(inventory["folders"]), 5)

    def test_full_inventory_parser_keeps_all_eve_families(self):
        parsed = _parse_inventory_output(
            """__QEMU__
vios-159
csr1000vng-17.9
__IOL__
i86bi-linux-l2.bin
__DYNAMIPS__
c7200-adventerprisek9.image
__DOCKER__
eve-gui-server:latest"""
        )
        self.assertEqual(parsed["qemu"], ["csr1000vng-17.9", "vios-159"])
        self.assertEqual(parsed["iol"], ["i86bi-linux-l2.bin"])
        self.assertEqual(parsed["dynamips"], ["c7200-adventerprisek9.image"])
        self.assertEqual(parsed["docker"], ["eve-gui-server:latest"])


if __name__ == "__main__":
    unittest.main()
