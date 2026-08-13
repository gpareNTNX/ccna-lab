import unittest

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.validator import Validator


class FakeBuilderAPI:
    def __init__(self):
        self.added = []
        self.created = []
        self._nodes = {}
        self._next_node_id = 1

    def ensure_folder(self, folder):
        return folder

    def create_lab(self, folder, name, description=""):
        self.created.append((folder, name, description))
        return {"status": "success"}

    def lab_path(self, folder, name):
        return folder.rstrip("/") + "/" + name + ".unl"

    def add_node(self, _lab, payload):
        node_id = str(self._next_node_id)
        self._next_node_id += 1
        self._nodes[node_id] = {"name": payload["name"]}
        self.added.append(payload)
        return {"data": {"id": int(node_id)}}

    def nodes(self, _lab):
        return {"data": self._nodes}


class ScenarioV2Tests(unittest.TestCase):
    def test_builder_uses_per_scenario_node_set(self):
        api = FakeBuilderAPI()
        scenario = {
            "id": "X",
            "topology": {
                "nodes": [
                    {"name": "R1", "template": "vios"},
                    {"name": "SW1", "template": "viosl2"},
                ],
                "links": [],
            },
        }
        lab = LabBuilder(api).create_scenario(
            "/CCNA", "SCENARIO-X", "vios-image", "viosl2-image", scenario
        )
        self.assertEqual(lab, "/CCNA/SCENARIO-X.unl")
        self.assertEqual([item["name"] for item in api.added], ["R1", "SW1"])
        self.assertEqual(api.added[0]["image"], "vios-image")
        self.assertEqual(api.added[1]["image"], "viosl2-image")

    def test_vlan_assertion_requires_id_and_name_on_same_row(self):
        check = {
            "node": "SW1",
            "command": "show vlan brief",
            "assertions": [{"type": "vlan", "id": 10, "name": "USERS"}],
        }
        good = "10 USERS active Gi0/1\n20 SERVERS active Gi0/2"
        bad = "10 ENGINEERING active Gi0/1\n20 USERS active Gi0/2"
        self.assertTrue(Validator.validate_output(check, good).passed)
        self.assertFalse(Validator.validate_output(check, bad).passed)

    def test_interface_assertion_requires_ip_and_up_up(self):
        check = {
            "node": "R1",
            "command": "show ip interface brief",
            "assertions": [{
                "type": "interface_ipv4",
                "interface": "GigabitEthernet0/0",
                "ip": "10.0.12.1",
                "status": "up",
                "protocol": "up",
            }],
        }
        good = "GigabitEthernet0/0 10.0.12.1 YES manual up up"
        bad = "GigabitEthernet0/0 10.0.12.1 YES manual administratively down down"
        self.assertTrue(Validator.validate_output(check, good).passed)
        self.assertFalse(Validator.validate_output(check, bad).passed)

    def test_ospf_neighbor_assertion_checks_router_id_and_state(self):
        check = {
            "node": "R1",
            "command": "show ip ospf neighbor",
            "assertions": [{
                "type": "ospf_neighbor",
                "router_id": "2.2.2.2",
                "state": "FULL",
            }],
        }
        good = "2.2.2.2 1 FULL/DR 00:00:31 10.0.12.2 GigabitEthernet0/0"
        bad = "3.3.3.3 1 FULL/DR 00:00:31 10.0.13.2 GigabitEthernet0/1"
        self.assertTrue(Validator.validate_output(check, good).passed)
        self.assertFalse(Validator.validate_output(check, bad).passed)

    def test_legacy_contains_still_works(self):
        check = {"node": "R1", "command": "show ip ssh", "contains": ["SSH Enabled"]}
        result = Validator.validate_output(check, "SSH Enabled - version 2.0")
        self.assertTrue(result.passed)
        self.assertEqual(result.matched, ["SSH Enabled"])


if __name__ == "__main__":
    unittest.main()
