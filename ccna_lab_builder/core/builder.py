import time

from ccna_lab_builder.core.topology import LINKS, all_node_payloads


class LabBuilder:
    def __init__(self, api, log=print):
        self.api = api
        self.log = log

    def _node_ids(self, lab):
        data = self.api.nodes(lab).get("data", {})
        return {value["name"]: int(key) for key, value in data.items()}

    def _find_interface_index(self, lab, node_id, wanted):
        items = self.api.interfaces(lab, node_id).get("data", {}).get("ethernet", [])
        for idx, item in enumerate(items):
            if item.get("name") == wanted:
                raw_id = item.get("id", idx)
                try:
                    return int(raw_id)
                except (TypeError, ValueError):
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

    @staticmethod
    def _network_inventory(payload):
        data = (payload or {}).get("data", {})
        inventory = {}
        if isinstance(data, dict):
            items = data.items()
        elif isinstance(data, list):
            items = enumerate(data, start=1)
        else:
            items = []

        for key, value in items:
            if not isinstance(value, dict):
                continue
            raw_id = value.get("id", key)
            try:
                network_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if network_id <= 0:
                continue
            inventory[network_id] = str(value.get("name") or "")
        return inventory

    @staticmethod
    def _ethernet_endpoints(payload):
        data = (payload or {}).get("data", {})
        ethernet = data.get("ethernet", {}) if isinstance(data, dict) else {}
        endpoints = {}
        if not isinstance(ethernet, dict):
            return endpoints
        for key, value in ethernet.items():
            try:
                network_id = int(key)
            except (TypeError, ValueError):
                continue
            if network_id > 0:
                endpoints[network_id] = str(value or "")
        return endpoints

    def _wait_for_network_id(self, lab, network_name, timeout=5.0, poll=0.15):
        """Return only a network ID that EVE itself exposes as a link endpoint."""
        deadline = time.monotonic() + max(0.0, timeout)
        last_inventory = {}
        last_endpoints = {}

        while True:
            last_inventory = self._network_inventory(self.api.networks(lab))
            last_endpoints = self._ethernet_endpoints(self.api.links(lab))

            matching_ids = [
                network_id
                for network_id, name in last_inventory.items()
                if name == network_name
            ]
            verified_ids = [
                network_id
                for network_id in matching_ids
                if network_id in last_endpoints
                and last_endpoints[network_id] == network_name
            ]
            if verified_ids:
                return min(verified_ids)

            if time.monotonic() >= deadline:
                break
            time.sleep(max(0.01, poll))

        raise RuntimeError(
            f"EVE-NG created network '{network_name}' but did not expose a verified "
            "Ethernet endpoint for it. "
            f"Networks={last_inventory or 'none'}; "
            f"link_endpoints={last_endpoints or 'none'}"
        )

    def _verify_interface_link(self, lab, node_id, interface_id, network_id):
        items = self.api.interfaces(lab, node_id).get("data", {}).get("ethernet", [])
        if not isinstance(items, list) or interface_id >= len(items):
            return False
        item = items[interface_id]
        try:
            current = int(item.get("network_id", 0))
        except (TypeError, ValueError):
            return False
        return current == int(network_id)

    def _connect_interface_verified(
        self,
        lab,
        node_id,
        interface_id,
        network_id,
        node_name,
        interface_name,
    ):
        endpoints = self._ethernet_endpoints(self.api.links(lab))
        if int(network_id) not in endpoints:
            raise RuntimeError(
                f"Refusing to cable {node_name} {interface_name}: EVE-NG no longer "
                f"advertises network_id={network_id} as a valid Ethernet endpoint."
            )

        self.api.connect_interface_experimental(
            lab,
            node_id,
            interface_id,
            network_id,
        )

        if not self._verify_interface_link(
            lab,
            node_id,
            interface_id,
            network_id,
        ):
            raise RuntimeError(
                f"EVE-NG accepted the cabling request for {node_name} {interface_name}, "
                f"but interface verification did not show network_id={network_id}."
            )

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
            self.api.add_network(
                lab,
                network_name,
                left=str(link.get("left", "1%")),
                top=str(link.get("top", "1%")),
                net_type=link.get("type", "bridge"),
            )

            net_id = self._wait_for_network_id(lab, network_name)
            self.log(f"Network verified: {network_name} -> EVE network_id={net_id}")

            a_idx = self._find_interface_index(lab, ids[a], a_if)
            b_idx = self._find_interface_index(lab, ids[b], b_if)
            self._connect_interface_verified(lab, ids[a], a_idx, net_id, a, a_if)
            self._connect_interface_verified(lab, ids[b], b_idx, net_id, b, b_if)
            self.log(
                f"Link verified: {a} {a_if} <-> {b} {b_if} "
                f"(network_id={net_id})"
            )

    def _cleanup_failed_lab(self, lab, exc):
        self.log(f"ERROR: lab generation failed for {lab}: {exc}")
        cleanup_notes = []
        stop_all = getattr(self.api, "stop_all", None)
        if callable(stop_all):
            try:
                stop_all(lab)
                cleanup_notes.append("nodes stopped")
            except RuntimeError as stop_exc:
                cleanup_notes.append(f"stop failed: {stop_exc}")

        delete_lab = getattr(self.api, "delete_lab", None)
        if callable(delete_lab):
            try:
                delete_lab(lab)
                cleanup_notes.append("partial lab deleted")
            except RuntimeError as delete_exc:
                cleanup_notes.append(f"delete failed: {delete_exc}")

        if cleanup_notes:
            self.log("Partial-lab cleanup: " + "; ".join(cleanup_notes))

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

        try:
            nodes = topology.get("nodes", [])
            if not nodes:
                raise ValueError(
                    f"Scenario {scenario.get('id', '?')} has no topology nodes."
                )
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
                        f"Scenario defines {len(links)} link(s), but automatic cabling "
                        "is disabled."
                    )
            return lab
        except Exception as exc:
            self._cleanup_failed_lab(lab, exc)
            raise

    def create(self, folder, name, router_image, switch_image, cable=False):
        folder = folder.strip() or "/"
        if not folder.startswith("/"):
            folder = "/" + folder

        self.log(f"Ensuring EVE-NG folder exists: {folder}")
        folder = self.api.ensure_folder(folder)

        self.log(f"Creating lab {folder}/{name}...")
        self.api.create_lab(folder, name)
        lab = self.api.lab_path(folder, name)

        try:
            for payload in all_node_payloads(router_image, switch_image):
                self.api.add_node(lab, payload)
                self.log(f"Node: {payload['name']}")

            if cable:
                self.log("Automatic cabling enabled.")
                links = [
                    {"a": a, "a_if": a_if, "b": b, "b_if": b_if}
                    for a, a_if, b, b_if in LINKS
                ]
                self._connect_links(lab, links)

            return lab
        except Exception as exc:
            self._cleanup_failed_lab(lab, exc)
            raise
