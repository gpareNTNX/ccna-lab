import unittest

from ccna_lab_builder.core.nutanix_bonus import NutanixBonusCatalog
from ccna_lab_builder.gui.nutanix_bonus import (
    NXOS_TEMPLATE,
    _first_boot_text,
    _nxos_payload,
    nxosv9k_image_folders,
)


class NutanixBonusTests(unittest.TestCase):
    def test_catalog_contains_only_isolated_buildable_bonus_labs(self):
        labs = NutanixBonusCatalog().all()
        self.assertEqual(
            [lab["id"] for lab in labs],
            ["NTNX-B01", "NTNX-B02", "NTNX-B03"],
        )
        self.assertTrue(all(lab["buildable"] for lab in labs))
        self.assertTrue(all(lab["catalog"] == "nutanix_bonus" for lab in labs))

    def test_b01_uses_two_nexus_nodes_and_vpcs_uplink_stubs(self):
        lab = NutanixBonusCatalog().get("NTNX-B01")
        nodes = lab["topology"]["nodes"]
        self.assertEqual(
            [node["name"] for node in nodes if node["template"] == NXOS_TEMPLATE],
            ["N9K-01", "N9K-02"],
        )
        self.assertEqual(
            len([node for node in nodes if node["template"] == "vpcs"]),
            2,
        )
        used = set()
        for link in lab["topology"]["links"]:
            for side, interface in ((link["a"], link["a_if"]), (link["b"], link["b_if"])):
                endpoint = (side, interface)
                self.assertNotIn(endpoint, used)
                used.add(endpoint)

    def test_b01_encodes_kb2455_switch_side_practices(self):
        lab = NutanixBonusCatalog().get("NTNX-B01")
        expected = "\n".join(
            value
            for check in lab["checks"]
            for value in check.get("contains", [])
        ).casefold()
        tasks = "\n".join(lab["tasks"]).casefold()
        notes = "\n".join(lab["notes"]).casefold()
        self.assertIn("switchport trunk native vlan 10", expected)
        self.assertIn("no lacp suspend-individual", expected)
        self.assertIn("lacp rate fast", expected)
        self.assertIn("delay restore 450", expected)
        self.assertIn("vpc orphan-port suspend", tasks)
        self.assertIn("fex", notes)
        self.assertIn("port-security", tasks)
        self.assertIn("ipv6 link-local", tasks)

    def test_b02_is_vpc_operations_and_recovery(self):
        lab = NutanixBonusCatalog().get("NTNX-B02")
        text = "\n".join(lab["tasks"] + lab["notes"]).casefold()
        expected = "\n".join(
            value
            for check in lab["checks"]
            for value in check.get("contains", [])
        ).casefold()
        self.assertIn("failure", lab["objective"].casefold())
        self.assertIn("show vpc", text)
        self.assertIn("vpc domain 20", expected)
        self.assertIn("channel-group 200 mode active", expected)

    def test_b03_is_compact_vxlan_evpn_fabric(self):
        lab = NutanixBonusCatalog().get("NTNX-B03")
        expected = "\n".join(
            value
            for check in lab["checks"]
            for value in check.get("contains", [])
        ).casefold()
        self.assertIn("feature nv overlay", expected)
        self.assertIn("nv overlay evpn", expected)
        self.assertIn("member vni 10010", expected)
        self.assertIn("ingress-replication protocol bgp", expected)
        self.assertIn("address-family l2vpn evpn", expected)

    def test_checks_never_target_vpcs(self):
        for lab in NutanixBonusCatalog().all():
            templates = {
                node["name"]: node["template"]
                for node in lab["topology"]["nodes"]
            }
            self.assertTrue(lab["checks"])
            self.assertTrue(
                all(templates[check["node"]] == NXOS_TEMPLATE for check in lab["checks"])
            )

    def test_bonus_topologies_do_not_reuse_interfaces(self):
        for lab in NutanixBonusCatalog().all():
            used = set()
            for link in lab["topology"]["links"]:
                for endpoint in (
                    (link["a"], link["a_if"]),
                    (link["b"], link["b_if"]),
                ):
                    self.assertNotIn(endpoint, used, f"{lab['id']} reuses {endpoint}")
                    used.add(endpoint)

    def test_nxos_image_detection_is_strict(self):
        images = [
            "vios-adventerprisek9-15.9",
            "nxosv9k-7.0.3.I7.4",
            "nxosv9k-9300v-9.3.9",
            "nxosv-final.7.0.3",
        ]
        self.assertEqual(
            nxosv9k_image_folders(images),
            ["nxosv9k-7.0.3.I7.4", "nxosv9k-9300v-9.3.9"],
        )

    def test_nxos_payload_uses_eve_template_defaults(self):
        payload = _nxos_payload(
            {
                "name": "N9K-01",
                "template": NXOS_TEMPLATE,
                "image": "nxosv9k-9300v-9.3.9",
                "left": "20%",
                "top": "30%",
            }
        )
        self.assertEqual(payload["type"], "qemu")
        self.assertEqual(payload["template"], NXOS_TEMPLATE)
        self.assertEqual(payload["image"], "nxosv9k-9300v-9.3.9")
        self.assertEqual(payload["cpu"], 2)
        self.assertEqual(payload["ram"], "8192")
        self.assertEqual(payload["console"], "telnet")

    def test_first_boot_prompts_are_detected_before_validator_login(self):
        self.assertTrue(
            _first_boot_text("Abort Auto Provisioning and continue with normal setup ?")
        )
        self.assertTrue(
            _first_boot_text("Do you want to enforce secure password standard (yes/no)")
        )
        self.assertFalse(_first_boot_text("N9K-01#"))


if __name__ == "__main__":
    unittest.main()
