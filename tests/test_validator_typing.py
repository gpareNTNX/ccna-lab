import unittest
from typing import get_type_hints

from ccna_lab_builder.core.validator import CheckResult, Validator


class ValidatorTypingTests(unittest.TestCase):
    def test_check_result_repr_is_compact(self):
        result = CheckResult(
            node="SW1-CORE",
            command="show spanning-tree root",
            passed=True,
            missing=[],
            output="VLAN0010\nVLAN0020\nVLAN0099",
            expected=["Vl10", "Vl20", "Vl99"],
            matched=["Vl10", "Vl20", "Vl99"],
        )

        rendered = repr(result)

        self.assertIn("node='SW1-CORE'", rendered)
        self.assertIn("passed=True", rendered)
        self.assertIn("matched=3 assertions", rendered)
        self.assertIn("output_lines=3", rendered)
        self.assertNotIn("VLAN0010", rendered)

    def test_validate_output_remains_a_working_classmethod(self):
        check = {
            "node": "R1-EDGE",
            "command": "show running-config | include hostname",
            "contains": ["hostname R1-EDGE"],
        }
        output = "R1-EDGE#show running-config | include hostname\r\nhostname R1-EDGE\r\nR1-EDGE#"

        from_class = Validator.validate_output(check, output)
        from_instance = Validator().validate_output(check, output)

        self.assertTrue(from_class.passed)
        self.assertTrue(from_instance.passed)
        self.assertEqual(from_class.matched, ["hostname R1-EDGE"])
        self.assertEqual(from_instance.matched, from_class.matched)

    def test_public_result_and_validator_signatures_are_typed(self):
        result_hints = get_type_hints(CheckResult)
        validate_hints = get_type_hints(Validator.validate_output)
        score_hints = get_type_hints(Validator.score)

        self.assertEqual(result_hints["missing"], list[str])
        self.assertEqual(result_hints["expected"], list[str])
        self.assertEqual(result_hints["matched"], list[str])
        self.assertEqual(result_hints["remediation"], list[str])
        self.assertIs(validate_hints["return"], CheckResult)
        self.assertIs(score_hints["return"], int)

    def test_score_behavior_is_unchanged(self):
        passing = CheckResult("R1", "show version", True, [], "ok")
        failing = CheckResult("R2", "show version", False, ["expected"], "bad")

        self.assertEqual(Validator.score([]), 0)
        self.assertEqual(Validator.score([passing, failing]), 50)
        self.assertEqual(Validator.score([passing, passing, failing]), 67)


if __name__ == "__main__":
    unittest.main()
