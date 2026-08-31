"""Reliable EVE-NG cabling by editing the generated .unl topology over SSH."""

from __future__ import annotations

import base64
import json
import shlex

from ccna_lab_builder.core.builder import LabBuilder


VERSION = "4.7.0"

_REMOTE_SCRIPT = r'''
import base64
import json
import os
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET


def fail(message):
    print("EVE_CABLING_ERROR=" + str(message))
    raise SystemExit(2)


path = sys.argv[1]
payload = json.loads(base64.b64decode(sys.argv[2]).decode("utf-8"))

if not os.path.isfile(path):
    fail("lab file does not exist: " + path)

original_stat = os.stat(path)
tree = ET.parse(path)
root = tree.getroot()
topology = root.find("topology")
if topology is None:
    topology = ET.SubElement(root, "topology")

nodes = topology.find("nodes")
if nodes is None:
    fail("lab topology has no nodes section")

networks = topology.find("networks")
if networks is None:
    networks = ET.SubElement(topology, "networks")

node_by_name = {}
for node in nodes.findall("node"):
    name = node.get("name")
    if name:
        node_by_name[name] = node

existing_ids = []
network_by_name = {}
for network in networks.findall("network"):
    try:
        existing_ids.append(int(network.get("id", "0")))
    except ValueError:
        pass
    if network.get("name"):
        network_by_name[network.get("name")] = network

next_network_id = max(existing_ids or [0]) + 1
summary = []

for link in payload:
    network_name = link["name"]
    network = network_by_name.get(network_name)
    if network is None:
        network = ET.SubElement(
            networks,
            "network",
            {
                "id": str(next_network_id),
                "type": "bridge",
                "name": network_name,
                "left": str(link.get("left", "0")),
                "top": str(link.get("top", "0")),
                "visibility": "0",
            },
        )
        network_by_name[network_name] = network
        next_network_id += 1

    network_id = network.get("id")
    if not network_id:
        fail("network has no id: " + network_name)

    for side in ("a", "b"):
        endpoint = link[side]
        node = node_by_name.get(endpoint["name"])
        if node is None:
            fail("node not found in .unl: " + endpoint["name"])
        if str(node.get("id")) != str(endpoint["node_id"]):
            fail("node id mismatch for " + endpoint["name"])

        interface_id = str(endpoint["if_id"])
        interface = None
        for candidate in node.findall("interface"):
            if candidate.get("type") == "ethernet" and candidate.get("id") == interface_id:
                interface = candidate
                break
        if interface is None:
            interface = ET.SubElement(node, "interface")

        interface.set("id", interface_id)
        interface.set("name", endpoint["if_name"])
        interface.set("type", "ethernet")
        interface.set("network_id", str(network_id))

    summary.append(
        {
            "name": network_name,
            "network_id": int(network_id),
            "a": link["a"]["name"] + " " + link["a"]["if_name"],
            "b": link["b"]["name"] + " " + link["b"]["if_name"],
        }
    )

fd, temporary_path = tempfile.mkstemp(
    prefix=".ccna-lab-",
    suffix=".unl",
    dir=os.path.dirname(path),
)
os.close(fd)
try:
    tree.write(temporary_path, encoding="utf-8", xml_declaration=True)
    os.chmod(temporary_path, stat.S_IMODE(original_stat.st_mode))
    try:
        os.chown(temporary_path, original_stat.st_uid, original_stat.st_gid)
    except PermissionError:
        pass
    os.replace(temporary_path, path)
finally:
    if os.path.exists(temporary_path):
        os.unlink(temporary_path)

# Re-read the final file so success means the on-disk topology is really correct.
verify_tree = ET.parse(path)
verify_topology = verify_tree.getroot().find("topology")
verify_nodes = verify_topology.find("nodes") if verify_topology is not None else None
verify_networks = verify_topology.find("networks") if verify_topology is not None else None
if verify_nodes is None or verify_networks is None:
    fail("written topology could not be re-read")

verified_networks = {
    network.get("name"): network.get("id")
    for network in verify_networks.findall("network")
}
verified_nodes = {
    node.get("name"): node
    for node in verify_nodes.findall("node")
}
for link in payload:
    expected_id = verified_networks.get(link["name"])
    if not expected_id:
        fail("network verification failed: " + link["name"])
    for side in ("a", "b"):
        endpoint = link[side]
        node = verified_nodes.get(endpoint["name"])
        if node is None:
            fail("node verification failed: " + endpoint["name"])
        matches = [
            item
            for item in node.findall("interface")
            if item.get("type") == "ethernet"
            and item.get("id") == str(endpoint["if_id"])
            and item.get("network_id") == str(expected_id)
        ]
        if not matches:
            fail(
                "interface verification failed: "
                + endpoint["name"]
                + " "
                + endpoint["if_name"]
            )

print("EVE_CABLING_OK=" + json.dumps(summary, separators=(",", ":")))
'''


def _lab_fs_path(lab):
    parts = [part for part in str(lab or "").split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise ValueError(f"Invalid EVE lab path: {lab}")
    if not parts[-1].endswith(".unl"):
        raise ValueError(f"EVE lab path must end in .unl: {lab}")
    return "/opt/unetlab/labs/" + "/".join(parts)


def _build_link_specs(builder, lab, links):
    ids = builder._node_ids(lab)
    used_interfaces = set()
    specs = []

    for index, link in enumerate(links, start=1):
        a = link["a"]
        b = link["b"]
        a_if = link["a_if"]
        b_if = link["b_if"]
        if a not in ids or b not in ids:
            raise RuntimeError(f"Scenario link references missing node: {a}<->{b}")

        a_idx = builder._find_interface_index(lab, ids[a], a_if)
        b_idx = builder._find_interface_index(lab, ids[b], b_if)
        for endpoint in ((a, a_idx), (b, b_idx)):
            if endpoint in used_interfaces:
                raise RuntimeError(
                    f"Topology attempts to reuse {endpoint[0]} interface id {endpoint[1]} "
                    "for more than one generated link."
                )
            used_interfaces.add(endpoint)

        specs.append(
            {
                "name": link.get("name") or f"LINK-{index:02d}-{a}-{b}",
                "left": str(link.get("left", "0")),
                "top": str(link.get("top", "0")),
                "a": {
                    "name": a,
                    "node_id": int(ids[a]),
                    "if_name": a_if,
                    "if_id": int(a_idx),
                },
                "b": {
                    "name": b,
                    "node_id": int(ids[b]),
                    "if_name": b_if,
                    "if_id": int(b_idx),
                },
            }
        )
    return specs


def _apply_unl_cabling(ssh, lab, specs):
    path = _lab_fs_path(lab)
    encoded = base64.b64encode(
        json.dumps(specs, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    command = "python3 -c {} {} {}".format(
        shlex.quote(_REMOTE_SCRIPT),
        shlex.quote(path),
        shlex.quote(encoded),
    )
    stdout, stderr = ssh.exec(command)
    marker = "EVE_CABLING_OK="
    success_line = next(
        (line for line in stdout.splitlines() if line.startswith(marker)),
        None,
    )
    if success_line is None:
        detail = stderr.strip() or stdout.strip() or "no diagnostic output"
        raise RuntimeError(f"SSH-native EVE cabling failed: {detail}")
    return json.loads(success_line[len(marker) :])


def _ssh_connect_links(builder, ssh, lab, links):
    specs = _build_link_specs(builder, lab, links)
    builder.log(
        f"SSH-native EVE cabling: writing {len(specs)} verified link(s) directly "
        "to the generated .unl topology."
    )
    summary = _apply_unl_cabling(ssh, lab, specs)

    for item in summary:
        builder.log(
            f"Link verified in .unl: {item['a']} <-> {item['b']} "
            f"(network_id={item['network_id']})"
        )

    # Force the Web/API session to reload the topology written on disk.
    close_lab = getattr(builder.api, "close_lab", None)
    if callable(close_lab):
        try:
            close_lab()
        except RuntimeError as exc:
            builder.log(f"WARNING: EVE lab-context close after cabling: {exc}")
    builder.api.get_lab(lab)
    builder.log("EVE-NG lab context reloaded after SSH-native cabling.")
    return summary


def install_ssh_native_cabling(window):
    """Prefer .unl-native cabling whenever the application's SSH session exists."""
    current = LabBuilder._connect_links
    if getattr(current, "_ssh_native_cabling", False):
        return window

    def routed(builder, lab, links):
        ssh = getattr(window, "ssh", None)
        if ssh is not None:
            return _ssh_connect_links(builder, ssh, lab, links)
        return current(builder, lab, links)

    routed._ssh_native_cabling = True
    routed._rest_fallback = current
    LabBuilder._connect_links = routed

    window._ssh_native_cabling_installed = True
    try:
        window.winfo_toplevel().title(
            f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
        )
    except Exception:
        pass
    return window
