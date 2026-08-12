from ccna_lab_builder.core.topology import NODES, LINKS, all_node_payloads

class LabBuilder:
    def __init__(self, api, log=print):
        self.api = api
        self.log = log

    @staticmethod
    def _data_id(result):
        data = result.get("data")
        if isinstance(data, dict) and "id" in data:
            return int(data["id"])
        return None

    def _node_ids(self, lab):
        data = self.api.nodes(lab).get("data", {})
        return {value["name"]: int(key) for key, value in data.items()}

    def _find_interface_index(self, lab, node_id, wanted):
        items = self.api.interfaces(lab, node_id).get("data", {}).get("ethernet", [])
        for idx, item in enumerate(items):
            if item.get("name") == wanted:
                return idx
        raise RuntimeError(
            f"Interface {wanted} not found on node {node_id}. "
            f"Available: {[x.get('name') for x in items]}"
        )

    def create(self, folder, name, router_image, switch_image, cable=False):
        self.log(f"Creating lab {folder}/{name}...")
        self.api.create_lab(folder, name)
        lab = self.api.lab_path(folder, name)

        for payload in all_node_payloads(router_image, switch_image):
            self.api.add_node(lab, payload)
            self.log(f"Node: {payload['name']}")

        if cable:
            self.log("Experimental cabling enabled.")
            ids = self._node_ids(lab)
            for a, a_if, b, b_if in LINKS:
                result = self.api.add_network(lab, f"LINK-{a}-{b}", left="1%", top="1%")
                net_id = self._data_id(result)
                if net_id is None:
                    networks = self.api.networks(lab).get("data", {})
                    for key, value in networks.items():
                        if value.get("name") == f"LINK-{a}-{b}":
                            net_id = int(key)
                            break
                if net_id is None:
                    raise RuntimeError(f"Could not discover network ID for {a}<->{b}")

                a_idx = self._find_interface_index(lab, ids[a], a_if)
                b_idx = self._find_interface_index(lab, ids[b], b_if)
                self.api.connect_interface_experimental(lab, ids[a], a_idx, net_id)
                self.api.connect_interface_experimental(lab, ids[b], b_idx, net_id)
                self.log(f"Link: {a} {a_if} <-> {b} {b_if}")

        return lab
