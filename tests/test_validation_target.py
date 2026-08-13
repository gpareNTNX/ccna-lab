import unittest

from ccna_lab_builder.core.live_validation import LiveValidator


class FakeAPI:
    def __init__(self):
        self.get_lab_calls = []

    def get_lab(self, lab):
        self.get_lab_calls.append(lab)
        return {
            "status": "success",
            "data": {
                "id": "lab-uuid-123",
                "name": "Selected Lab",
            },
        }


class ValidationTargetTests(unittest.TestCase):
    def test_validator_uses_exact_requested_lab_without_silent_redirect(self):
        api = FakeAPI()
        logs = []
        validator = LiveValidator(api, ssh=None, log=logs.append)
        scenario = {
            "id": "01",
            "name": "Initial Configuration",
            "checks": [],
        }
        requested = "/CCNA-200-301/CCNA-MASTER-LAB.unl"

        results = validator.validate(requested, scenario)

        self.assertEqual(results, [])
        self.assertEqual(api.get_lab_calls, [requested])
        self.assertIn(
            "Validation target (exact): /CCNA-200-301/CCNA-MASTER-LAB.unl; "
            "lab_uuid=lab-uuid-123",
            logs,
        )


if __name__ == "__main__":
    unittest.main()
