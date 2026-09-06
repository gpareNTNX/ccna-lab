"""Pedagogical helpers for live lab feedback, hints, and progress tracking."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ccna_lab_builder.core.validator import CheckResult, Validator


@dataclass(frozen=True)
class LearningHint:
    """Progressive guidance for one failed validation check."""

    title: str
    hint: str
    explanation: str
    remediation: tuple[str, ...]


def normalize_eve_node_state(value: Any) -> str:
    """Normalize EVE-NG node status values into stable UI states."""
    if isinstance(value, bool):
        return "running" if value else "stopped"

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = None

    if numeric is not None:
        if numeric >= 2:
            return "running"
        if numeric == 1:
            return "starting"
        if numeric == 0:
            return "stopped"

    text = str(value or "").strip().casefold()
    if text in {"running", "started", "start", "on", "up"}:
        return "running"
    if text in {"starting", "booting", "loading"}:
        return "starting"
    if text in {"stopped", "stop", "off", "down"}:
        return "stopped"
    return "unknown"


def link_runtime_state(left: str, right: str) -> str:
    """Describe endpoint runtime state without claiming IOS link protocol state."""
    states = {left, right}
    if states == {"running"}:
        return "ready"
    if "starting" in states:
        return "starting"
    if "unknown" in states:
        return "unknown"
    return "stopped"


def _domain_explanation(command: str) -> str:
    command_cf = command.casefold()
    if "spanning-tree" in command_cf:
        return (
            "Compare the expected VLAN instance with the elected root bridge, then inspect "
            "bridge priority, port roles, and port state. For protection checks, verify "
            "BPDU Guard/root guard on the intended edge or uplink ports."
        )
    if "ospf" in command_cf:
        return (
            "Work from Layer 3 outward: confirm addressing/subnet reachability, matching OSPF "
            "area and timers, non-passive interfaces, unique router IDs, and MTU consistency."
        )
    if "vlan" in command_cf:
        return (
            "Confirm the VLAN exists first, then verify its name and every access-port "
            "assignment. A correct VLAN database alone does not prove the ports are in it."
        )
    if "trunk" in command_cf:
        return (
            "Verify the interface is operationally trunking, then compare native VLAN and "
            "allowed VLANs on both ends. A configured trunk can still be operationally down."
        )
    if "etherchannel" in command_cf:
        return (
            "Check that all member ports have compatible Layer-2 settings and that LACP/PAgP "
            "modes can negotiate. Then verify the expected Port-Channel owns the members."
        )
    if "show ip route" in command_cf or "show ipv6 route" in command_cf:
        return (
            "Validate the prefix and mask first, then the route source and next hop. If a "
            "next hop is configured, prove that next-hop reachability exists independently."
        )
    if "show ip ssh" in command_cf or "ssh" in command_cf:
        return (
            "SSH requires the dependency chain to be complete: hostname/domain, RSA keys, "
            "local user authentication, SSH version, and VTY transport/login settings."
        )
    if "interface brief" in command_cf:
        return (
            "Compare interface name, address, administrative state, and protocol state. "
            "If the address is correct but the interface is down, inspect shutdown/cabling."
        )
    if "hsrp" in command_cf or "standby" in command_cf:
        return (
            "Verify that peers use the same HSRP group and virtual IP, then compare priority, "
            "preempt behavior, and the resulting Active/Standby state."
        )
    if "cdp" in command_cf:
        return (
            "Verify CDP is enabled globally and on the local interface, then confirm that the "
            "expected neighbor is physically connected to the interface named by the check."
        )
    return (
        "Use the validation command as the observation point. Compare the expected assertion "
        "with the live output one item at a time before changing configuration."
    )


def build_learning_hint(result: CheckResult) -> LearningHint:
    """Build three progressive help levels without exposing the answer immediately."""
    expected = ", ".join(result.expected) or "the scenario expectation"
    missing = ", ".join(result.missing) or "one or more expected conditions"
    return LearningHint(
        title=f"{result.node} — {result.command}",
        hint=(
            f"Run `{result.command}` and focus only on: {missing}. "
            f"The target state is: {expected}."
        ),
        explanation=_domain_explanation(result.command),
        remediation=tuple(result.remediation),
    )


def validation_summary(results: Sequence[CheckResult]) -> dict[str, Any]:
    """Create a compact progress summary suitable for UI/history storage."""
    items = list(results)
    failed = [item for item in items if not item.passed]
    return {
        "score": Validator.score(items),
        "passed": len(items) - len(failed),
        "total": len(items),
        "failed": [f"{item.node}: {item.command}" for item in failed],
    }


def validation_state_by_node(results: Sequence[CheckResult]) -> dict[str, dict[str, Any]]:
    """Translate CheckResult objects into the Topology Canvas validation overlay format."""
    state: dict[str, dict[str, Any]] = {}
    for result in results:
        status = "pass" if result.passed else "fail"
        entry = state.setdefault(result.node, {"status": status, "checks": []})
        if entry["status"] != status:
            entry["status"] = "mixed"
        entry["checks"].append(
            {
                "status": status,
                "label": result.command,
                "missing": list(result.missing),
            }
        )
    return state


def make_validation_history_entry(
    scenario: dict[str, Any],
    lab: str,
    results: Sequence[CheckResult],
    source: str,
    duration_seconds: float,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Create a compact persistent validation-attempt record."""
    summary = validation_summary(results)
    return {
        "kind": "validation",
        "timestamp": timestamp
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario_id": str(scenario.get("id", "")),
        "scenario_name": str(scenario.get("name", "")),
        "lab": str(lab),
        "source": str(source),
        "score": int(summary["score"]),
        "passed": int(summary["passed"]),
        "total": int(summary["total"]),
        "failed": list(summary["failed"]),
        "duration_seconds": round(max(0.0, float(duration_seconds)), 2),
    }


def make_event_history_entry(
    kind: str,
    scenario: dict[str, Any] | None,
    lab: str,
    detail: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Create a persistent non-validation learning-session event."""
    scenario = scenario or {}
    return {
        "kind": str(kind),
        "timestamp": timestamp
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario_id": str(scenario.get("id", "")),
        "scenario_name": str(scenario.get("name", "")),
        "lab": str(lab),
        "detail": str(detail),
    }
