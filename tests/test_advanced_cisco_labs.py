import unittest

from ccna_lab_builder.core.challenges import ChallengeCatalog


class AdvancedCiscoLabTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ChallengeCatalog()

    def test_advanced_pack_contains_eight_labs(self):
        labs = [item for item in self.catalog.all() if item["id"].startswith("ADV-C")]
        self.assertEqual(len(labs), 8)
        self.assertTrue(all(item["pack"] == "Advanced Cisco" for item in labs))

    def test_advanced_labs_use_existing_image_families_only(self):
        allowed = {"vios", "viosl2", "vpcs"}
        for lab in self.catalog.all():
            if not lab["id"].startswith("ADV-C"):
                continue
            templates = {node["template"] for node in lab["topology"]["nodes"]}
            self.assertLessEqual(templates, allowed, lab["id"])

    def test_expected_advanced_topics_are_present(self):
        names = {
            item["id"]: item["name"]
            for item in self.catalog.all()
            if item["id"].startswith("ADV-C")
        }
        self.assertIn("MSTP", names["ADV-C01"])
        self.assertIn("VTP", names["ADV-C02"])
        self.assertIn("RSPAN", names["ADV-C03"])
        self.assertIn("Multi-Area OSPFv2", names["ADV-C04"])
        self.assertIn("Summarization", names["ADV-C05"])
        self.assertIn("OSPFv3", names["ADV-C06"])
        self.assertIn("EIGRP", names["ADV-C07"])
        self.assertIn("BGP", names["ADV-C08"])

    def test_every_advanced_lab_has_tasks_checks_and_source_basis(self):
        for lab in self.catalog.all():
            if not lab["id"].startswith("ADV-C"):
                continue
            self.assertTrue(lab["tasks"], lab["id"])
            self.assertTrue(lab["checks"], lab["id"])
            self.assertTrue(lab["source_basis"], lab["id"])
            self.assertTrue(lab["objective"], lab["id"])


if __name__ == "__main__":
    unittest.main()
