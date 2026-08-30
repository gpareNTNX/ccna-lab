import unittest

from ccna_lab_builder.core.builder import LabBuilder


class FakeCablingApi:
    def __init__(self):
        self.connected = []
        self.networks_by_id = {}
        self.interface_state = {
            1: [
                {"name": "Gi0/0", "network_id": 0},
                {"name": "Gi0/1", "network_id": 0},
            ],
            2: [
                {"name": "Gi0/0", "network_id": 0},
                {"name": "Gi0/1", "network_id": 0},
            ],
        }

    def nodes(self, _lab):
        return {
            "data": {
                "1": {"name": "R1"},
                "2": {"name": "R2"},
            }
        }

    def add_network(self, _lab, name, **_kwargs):
        self.networks_by_id[7] = name
        return {"status": "success", "data": {"id": 999}}

    def networks(self, _lab):
        return {
            "data": {
                str(network_id): {
                    "id": network_id,
                    "name": name,
                    "type": "bridge",
                }
                for network_id, name in self.networks_by_id.items()
            }
        }

    def links(self, _lab):
        return {
            "data": {
                "ethernet": {
                    str(network_id): name
                    for network_id, name in self.networks_by_id.items()
                },
                "serial": {},
            }
        }

    def interfaces(self, _lab, node_id):
        return {"data": {"ethernet": self.interface_state[node_id], "serial": []}}

    def connect_interface_experimental(
        self, _lab, node_id, interface_id, network_id
    ):
        if int(network_id) not in self.networks_by_id:
            raise RuntimeError("Cannot link node, invalid network_id (20033).")
        self.connected.append((int(node_id), int(interface_id), int(network_id)))
        self.interface_state[int(node_id)][int(interface_id)]["network_id"] = int(
            network_id
        )
        return {"status": "success"}


class VerifiedCablingTests(unittest.TestCase):
    def test_cabling_ignores_unverified_post_network_id(self):
        api = FakeCablingApi()
        builder = LabBuilder(api, log=lambda _message: None)

        builder._connect_links(
            "/lab.unl",
            [
                {
                    "a": "R1",
                    "a_if": "Gi0/0",
                    "b": "R2",
                    "b_if": "Gi0/0",
                }
            ],
        )

        self.assertEqual(api.connected, [(1, 0, 7), (2, 0, 7)])

    def test_network_id_must_be_advertised_by_links_endpoint(self):
        api = FakeCablingApi()
        api.networks_by_id[7] = "TEST"
        builder = LabBuilder(api, log=lambda _message: None)

        api.links = lambda _lab: {"data": {"ethernet": {}, "serial": {}}}
        with self.assertRaisesRegex(RuntimeError, "verified Ethernet endpoint"):
            builder._wait_for_network_id("/lab.unl", "TEST", timeout=0, poll=0)


if __name__ == "__main__":
    unittest.main()
