import unittest

from ccna_lab_builder.core.validator import Validator
from ccna_lab_builder.gui.validator_vlan_compat import install_vlan_validation_compat


class VlanLabelCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_vlan_validation_compat()

    def test_lab7_spanning_tree_output_accepts_padded_vlan_labels(self):
        check = {
            "node": "SW1-CORE",
            "command": "show spanning-tree root",
            "contains": ["Vl10", "Vl20", "Vl99"],
        }
        output = """
Root Hello Max Fwd
Vlan Root ID Cost Time Age Dly Root Port
---------------- -------------------- ---- --- --- ------------
VLAN0001 32769 5001.0001.0000 0 2 20 15
VLAN0010 10 5001.0001.0000 0 2 20 15
VLAN0020 20 5001.0001.0000 0 2 20 15
VLAN0099 99 5001.0001.0000 0 2 20 15
"""
        result = Validator.validate_output(check, output)
        self.assertTrue(result.passed)
        self.assertEqual(result.missing, [])
        self.assertEqual(result.matched, ["Vl10", "Vl20", "Vl99"])

    def test_vlan_alias_does_not_match_different_vlan(self):
        check = {
            "node": "SW1-CORE",
            "command": "show spanning-tree root",
            "contains": ["Vl10"],
        }
        result = Validator.validate_output(check, "VLAN0100 100 5001.0001.0000 0")
        self.assertFalse(result.passed)
        self.assertEqual(result.missing, ["Vl10"])

    def test_not_contains_respects_vlan_aliases(self):
        check = {
            "node": "SW1-CORE",
            "command": "show spanning-tree root",
            "assertions": [
                {"type": "not_contains", "value": "Vl20", "label": "no VLAN 20"}
            ],
        }
        result = Validator.validate_output(check, "VLAN0020 20 5001.0001.0000 0")
        self.assertFalse(result.passed)
        self.assertEqual(result.missing, ["no VLAN 20"])


if __name__ == "__main__":
    unittest.main()
