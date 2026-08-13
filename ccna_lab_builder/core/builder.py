from ccna_lab_builder.core.topology import LINKS, all_node_payloads


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

    @staticmethod
    def _scenario_node_payload(spec, router_image, switch_image):
        template = spec.get("template", "vios")
        if template not in {"vios", "viosl2"}:
            raise ValueError(f"Unsupported scenario node template: {template}")
        return {
            "type": "qemu",
            "template": template,
            "config": spec.get("config", "Unconfigured"),
            "delay": int(spec.get("delay", 0)),
            "icon": spec.get(
                "icon",
                "Switch.png" if template == "viosl2" else "Router.png",
            ),
            "image": switch_image if template == "viosl2" else router_image,
            "name": spec["name"],
            "left": str(spec.get("left", "50%")),
            "top": str(spec.get("top", "50%")),
            "ram": str(spec.get("ram", "1024")),
            "console": spec.get("console", "telnet"),
            "cpu": int(spec.get("cpu", 1)),
            "ethernet": int(spec.get("interfaces", 8)),
        }

    def _connect_links(self, lab, links):
        ids = self._node_ids(lab)
        for index, link in enumerate(links, start=1):
            a = link["a"]
            b = link["b"]
            a_if = link["a_if"]
            b_if = link["b_if"]
            if a not in ids or b not in ids:
                raise RuntimeError(f"Scenario link references missing node: {a}<->{b}")

            network_name = link.get("name") or f"LINK-{index:02d}-{a}-{b}"
            result = self.api.add_network(
                lab,
                network_name,
                left=str(link.get("left", "1%")),
                top=str(link.get("top", "1%")),
                net_type=link.get("type", "bridge"),
            )
            net_id = self._data_id(result)
            if net_id is None:
                networks = self.api.networks(lab).get("data", {})
                for key, value in networks.items():
                    if value.get("name") == network_name:
                        net_id = int(key)
                        break
            if net_id is None:
                raise RuntimeError(f"Could not discover network ID for {a}<->{b}")

            a_idx = self._find_interface_index(lab, ids[a], a_if)
            b_idx = self._find_interface_index(lab, ids[b], b_if)
            self.api.connect_interface_experimental(lab, ids[a], a_idx, net_id)
            self.api.connect_interface_experimental(lab, ids[b], b_idx, net_id)
            self.log(f"Link: {a} {a_if} <-> {b} {b_if}")

    def create_scenario(
        self,
        folder,
        name,
        router_image,
        switch_image,
        scenario,
        cable=False,
    ):
        """Create only the nodes and links required by a Scenario V2 definition."""
        topology = scenario.get("topology")
        if not topology:
            return self.create(
                folder,
                name,
                router_image,
                switch_image,
                cable=cable,
            )

        folder = folder.strip() or "/"
        if not folder.startswith("/"):
            folder = "/" + folder
        self.log(f"Ensuring EVE-NG folder exists: {folder}")
        folder = self.api.ensure_folder(folder)

        description = scenario.get("objective", "CCNA 200-301 scenario")
        self.log(f"Creating scenario lab {folder}/{name}...")
        self.api.create_lab(folder, name, description=description)
        lab = self.api.lab_path(folder, name)

        nodes = topology.get("nodes", [])
        if not nodes:
            raise ValueError(f"Scenario {scenario.get('id', '?')} has no topology nodes.")
        for spec in nodes:
            payload = self._scenario_node_payload(spec, router_image, switch_image)
            self.api.add_node(lab, payload)
            self.log(f"Node: {payload['name']} ({payload['template']})")

        links = topology.get("links", [])
        if links:
            if cable:
                self.log("Scenario cabling enabled.")
                self._connect_links(lab, links)
            else:
                self.log(
                    f"Scenario defines {len(links)} link(s), but automatic cabling is disabled. "
                    "Enable experimental API cabling or connect the links manually."
                )
        return lab

    def create(self, folder, name, router_image, switch_image, cable=False):
        folder = folder.strip() or "/"
        if not folder.startswith("/"):
            folder = "/" + folder

        self.log(f"Ensuring EVE-NG folder exists: {folder}")
        folder = self.api.ensure_folder(folder)

        self.log(f"Creating lab {folder}/{name}...")
        self.api.create_lab(folder, name)
        lab = self.api.lab_path(folder, name)

        for payload in all_node_payloads(router_image, switch_image):
            self.api.add_node(lab, payload)
            self.log(f"Node: {payload['name']}")

        if cable:
            self.log("Experimental cabling enabled.")
            links = [
                {"a": a, "a_if": a_if, "b": b, "b_if": b_if}
                for a, a_if, b, b_if in LINKS
            ]
            self._connect_links(lab, links)

        return lab
