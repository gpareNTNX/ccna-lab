import unittest

from ccna_lab_builder.core.live_validation import LiveValidator


class FakeAPI:
    def __init__(self, existing_labs):
        self.existing_labs = set(existing_labs)
        self.lookups = []

    def get_lab(self, lab):
        self.lookups.append(lab)
        if lab not in self.existing_labs:
            raise RuntimeError("lab not found")
        return {"status": "success", "data": {"path": lab}}


class ValidationTargetTests(unittest.TestCase):
    def test_master_target_switches_to_existing_scenario_lab(self):
        scenario_lab = "/CCNA-200-301/CCNA-01-INITIAL-CONFIGURATION.unl"
        api = FakeAPI({scenario_lab})
        validator = LiveValidator(api, ssh=None, log=lambda _message: None)
        scenario = {"id": "01", "name": "Initial Configuration"}

        resolved = validator._resolve_lab(
            "/CCNA-200-301/CCNA-MASTER-LAB.unl",
            scenario,
        )

        self.assertEqual(resolved, scenario_lab)

    def test_existing_scenario_target_is_not_replaced(self):
        scenario_lab = "/CCNA-200-301/CCNA-01-INITIAL-CONFIGURATION.unl"
        api = FakeAPI(set())
        validator = LiveValidator(api, ssh=None, log=lambda _message: None)
        scenario = {"id": "01", "name": "Initial Configuration"}

        resolved = validator._resolve_lab(scenario_lab, scenario)

        self.assertEqual(resolved, scenario_lab)
        self.assertEqual(api.lookups, [])


if __name__ == "__main__":
    unittest.main()
