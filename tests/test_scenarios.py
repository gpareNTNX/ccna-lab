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
        check = {"node":"R1","command":"show x","contains":["OSPF","FULL"]}
        result = Validator.validate_output(check, "OSPF neighbor is FULL")
        self.assertTrue(result.passed)

if __name__ == "__main__":
    unittest.main()
