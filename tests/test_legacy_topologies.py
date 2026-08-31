import unittest

from ccna_lab_builder.core.scenarios import ScenarioCatalog


class LegacyTopologyTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ScenarioCatalog()

    def test_all_original_labs_have_explicit_topology(self):
        for number in range(1, 21):
            scenario = self.catalog.get(f"{number:02d}")
            self.assertGreaterEqual(scenario.get("schema_version", 1), 2)
            self.assertIn("topology", scenario)
            self.assertTrue(scenario["topology"]["nodes"])

    def test_lab_04_is_only_sw3_and_needs_no_cabling(self):
        scenario = self.catalog.get("04")
        self.assertEqual(
            [node["name"] for node in scenario["topology"]["nodes"]],
            ["SW3-ACCESS"],
        )
        self.assertEqual(scenario["topology"]["links"], [])

    def test_lab_02_is_only_r1_r2_with_one_point_to_point_link(self):
        scenario = self.catalog.get("02")
        self.assertEqual(
            [node["name"] for node in scenario["topology"]["nodes"]],
            ["R1-EDGE", "R2-HQ"],
        )
        self.assertEqual(len(scenario["topology"]["links"]), 1)
        link = scenario["topology"]["links"][0]
        self.assertEqual(
            (link["a"], link["a_if"], link["b"], link["b_if"]),
            ("R1-EDGE", "Gi0/0", "R2-HQ", "Gi0/0"),
        )

    def test_no_legacy_topology_reuses_an_interface(self):
        for number in range(1, 21):
            scenario = self.catalog.get(f"{number:02d}")
            used = set()
            for link in scenario["topology"]["links"]:
                for endpoint in (
                    (link["a"], link["a_if"]),
                    (link["b"], link["b_if"]),
                ):
                    self.assertNotIn(
                        endpoint,
                        used,
                        f"Lab {number:02d} reuses {endpoint}",
                    )
                    used.add(endpoint)


if __name__ == "__main__":
    unittest.main()
