"""Minimal per-scenario topologies for the original CCNA labs 01-20."""

from __future__ import annotations

from copy import deepcopy

from ccna_lab_builder.core.topology import NODES


def _node(name):
    spec = NODES[name]
    return {
        "name": name,
        "template": spec["template"],
        "left": spec["left"],
        "top": spec["top"],
        "interfaces": spec["interfaces"],
    }


def _topology(node_names, links=()):
    return {
        "nodes": [_node(name) for name in node_names],
        "links": [
            {"a": a, "a_if": a_if, "b": b, "b_if": b_if}
            for a, a_if, b, b_if in links
        ],
    }


LEGACY_TOPOLOGIES = {
    "01": _topology(["R1-EDGE"]),
    "02": _topology(
        ["R1-EDGE", "R2-HQ"],
        [("R1-EDGE", "Gi0/0", "R2-HQ", "Gi0/0")],
    ),
    "03": _topology(
        ["R1-EDGE", "R2-HQ"],
        [("R1-EDGE", "Gi0/0", "R2-HQ", "Gi0/0")],
    ),
    "04": _topology(["SW3-ACCESS"]),
    "05": _topology(
        ["SW1-CORE", "SW2-DIST"],
        [("SW1-CORE", "Gi0/1", "SW2-DIST", "Gi0/1")],
    ),
    "06": _topology(
        ["SW1-CORE", "SW2-DIST"],
        [
            ("SW1-CORE", "Gi0/1", "SW2-DIST", "Gi0/1"),
            ("SW1-CORE", "Gi0/3", "SW2-DIST", "Gi0/3"),
        ],
    ),
    "07": _topology(
        ["SW1-CORE", "SW2-DIST", "SW3-ACCESS"],
        [
            ("SW1-CORE", "Gi0/1", "SW2-DIST", "Gi0/1"),
            ("SW1-CORE", "Gi0/2", "SW3-ACCESS", "Gi0/0"),
            ("SW2-DIST", "Gi0/2", "SW3-ACCESS", "Gi0/1"),
        ],
    ),
    "08": _topology(
        ["R2-HQ", "SW1-CORE"],
        [("R2-HQ", "Gi0/2", "SW1-CORE", "Gi0/0")],
    ),
    "09": _topology(
        ["R3-HQ", "R4-BRANCH"],
        [("R3-HQ", "Gi0/1", "R4-BRANCH", "Gi0/0")],
    ),
    "10": _topology(
        ["R2-HQ", "R3-HQ"],
        [("R2-HQ", "Gi0/1", "R3-HQ", "Gi0/0")],
    ),
    "11": _topology(["R2-HQ"]),
    "12": _topology(
        ["R1-EDGE", "R2-HQ", "R5-ISP"],
        [
            ("R1-EDGE", "Gi0/0", "R2-HQ", "Gi0/0"),
            ("R1-EDGE", "Gi0/1", "R5-ISP", "Gi0/0"),
        ],
    ),
    "13": _topology(["R2-HQ"]),
    "14": _topology(["SW3-ACCESS"]),
    "15": _topology(
        ["SW1-CORE", "SW3-ACCESS"],
        [("SW1-CORE", "Gi0/2", "SW3-ACCESS", "Gi0/0")],
    ),
    "16": _topology(
        ["SW1-CORE", "SW3-ACCESS"],
        [("SW1-CORE", "Gi0/2", "SW3-ACCESS", "Gi0/0")],
    ),
    "17": _topology(["R3-HQ"]),
    "18": _topology(["R2-HQ"]),
    "19": _topology(
        ["R2-HQ", "R3-HQ", "SW1-CORE", "SW2-DIST", "SW3-ACCESS"],
        [
            ("R2-HQ", "Gi0/1", "R3-HQ", "Gi0/0"),
            ("R2-HQ", "Gi0/2", "SW1-CORE", "Gi0/0"),
            ("R3-HQ", "Gi0/2", "SW2-DIST", "Gi0/0"),
            ("SW1-CORE", "Gi0/1", "SW2-DIST", "Gi0/1"),
            ("SW1-CORE", "Gi0/2", "SW3-ACCESS", "Gi0/0"),
        ],
    ),
    "20": _topology(
        [
            "R1-EDGE",
            "R2-HQ",
            "R3-HQ",
            "R5-ISP",
            "SW1-CORE",
            "SW2-DIST",
            "SW3-ACCESS",
        ],
        [
            ("R1-EDGE", "Gi0/0", "R2-HQ", "Gi0/0"),
            ("R2-HQ", "Gi0/1", "R3-HQ", "Gi0/0"),
            ("R1-EDGE", "Gi0/1", "R5-ISP", "Gi0/0"),
            ("R2-HQ", "Gi0/2", "SW1-CORE", "Gi0/0"),
            ("R3-HQ", "Gi0/2", "SW2-DIST", "Gi0/0"),
            ("SW1-CORE", "Gi0/1", "SW2-DIST", "Gi0/1"),
            ("SW1-CORE", "Gi0/2", "SW3-ACCESS", "Gi0/0"),
        ],
    ),
}


def legacy_topology(scenario_id):
    """Return an independent topology definition for a legacy scenario."""
    value = LEGACY_TOPOLOGIES.get(str(scenario_id).zfill(2))
    return deepcopy(value) if value is not None else None
