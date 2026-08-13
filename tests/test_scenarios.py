import unittest

from ccna_lab_builder.core.scenarios import ScenarioCatalog
from ccna_lab_builder.core.validator import Validator


class ScenarioTests(unittest.TestCase):
    def test_has_20_labs(self):
        self.assertEqual(len(ScenarioCatalog().all()), 20)

    def test_ids_unique(self):
        ids = [x["id"] for x in ScenarioCatalog().all()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_validator(self):
        check = {
            "node": "R1",
            "command": "show x",
            "contains": ["OSPF", "FULL"],
        }
        result = Validator.validate_output(check, "OSPF neighbor is FULL")
        self.assertTrue(result.passed)

    def test_initial_config_hostname_real_ios_output_passes(self):
        check = {
            "node": "R1-EDGE",
            "command": "show running-config | include hostname",
            "contains": ["hostname R1-EDGE"],
        }
        output = (
            "R1-EDGE#show running-config | include hostname\r\n"
            "hostname R1-EDGE\r\n"
            "R1-EDGE#"
        )
        result = Validator.validate_output(check, output)
        self.assertTrue(result.passed)
        self.assertEqual(result.missing, [])
        self.assertIn("hostname R1-EDGE", result.output)

    def test_initial_config_ssh_real_ios_output_passes(self):
        check = {
            "node": "R1-EDGE",
            "command": "show ip ssh",
            "contains": ["SSH Enabled"],
        }
        output = (
            "R1-EDGE#show ip ssh\r\n"
            "SSH Enabled - version 2.0\r\n"
            "Authentication timeout: 120 secs; Authentication retries: 3\r\n"
            "R1-EDGE#"
        )
        result = Validator.validate_output(check, output)
        self.assertTrue(result.passed)
        self.assertEqual(result.matched, ["SSH Enabled"])

    def test_failed_hostname_includes_exact_fix_commands(self):
        check = {
            "node": "R1-EDGE",
            "command": "show running-config | include hostname",
            "contains": ["hostname R1-EDGE"],
        }
        result = Validator.validate_output(check, "hostname Router\n")
        self.assertFalse(result.passed)
        self.assertIn("hostname R1-EDGE", result.remediation)

    def test_failed_ssh_includes_ssh_configuration_commands(self):
        check = {
            "node": "R1-EDGE",
            "command": "show ip ssh",
            "contains": ["SSH Enabled"],
        }
        result = Validator.validate_output(check, "SSH Disabled - version 1.99\n")
        self.assertFalse(result.passed)
        self.assertIn("ip ssh version 2", result.remediation)
        self.assertIn("transport input ssh", result.remediation)


if __name__ == "__main__":
    unittest.main()
