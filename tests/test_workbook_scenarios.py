import unittest

from ccna_lab_builder.core.scenarios import ScenarioCatalog


class WorkbookScenarioTests(unittest.TestCase):
    def setUp(self):
        self.scenarios = {item["id"]: item for item in ScenarioCatalog().all()}

    def test_workbook_labs_are_present(self):
        self.assertTrue({"33", "34", "35", "36", "37"}.issubset(self.scenarios))

    def test_source_metadata(self):
        for scenario_id in ("33", "34", "35", "36", "37"):
            source = self.scenarios[scenario_id]["source"]
            self.assertEqual(source["title"], "CCNA Practical Labs Workbook")
            self.assertEqual(source["author"], "Yasser Ramzy Auda")
            self.assertEqual(source["workbook_lab"], int(scenario_id) - 32)

    def test_topologies_use_supported_templates(self):
        for scenario_id in ("33", "34", "35", "36", "37"):
            nodes = self.scenarios[scenario_id]["topology"]["nodes"]
            self.assertTrue(nodes)
            self.assertTrue(all(node["template"] in {"vios", "viosl2"} for node in nodes))

    def test_lab4_documents_answer_key_conflict(self):
        notes = " ".join(self.scenarios["36"]["adaptation_notes"])
        self.assertIn("R1 Gi0/1", notes)
        self.assertIn("10.0.0.1/8", notes)

    def test_lab5_has_hsrp_and_ospfv3_checks(self):
        checks = self.scenarios["37"]["checks"]
        assertions = [a for check in checks for a in check.get("assertions", [])]
        self.assertTrue(any(a.get("type") == "hsrp" for a in assertions))
        self.assertTrue(any(check["command"] == "show ipv6 ospf neighbor" for check in checks))


if __name__ == "__main__":
    unittest.main()
