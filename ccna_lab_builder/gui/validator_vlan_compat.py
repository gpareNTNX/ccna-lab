"""Normalize Cisco VLAN labels in validator contains assertions.

IOS variants render the same VLAN as Vl10, Vlan10 or VLAN0010 depending on
platform and command. The validator should treat those labels as equivalent
without weakening ordinary substring matching.
"""

from __future__ import annotations

import re

from ccna_lab_builder.core.validator import Validator


VERSION = "4.7.1"
_VLAN_TOKEN_RE = re.compile(r"^(?:vl|vlan)0*(\d+)$", re.IGNORECASE)


def _vlan_id(value):
    match = _VLAN_TOKEN_RE.fullmatch(str(value or "").strip())
    return int(match.group(1)) if match else None


def _vlan_label_present(cleaned, vlan_id):
    pattern = re.compile(
        rf"\b(?:vl|vlan)0*{int(vlan_id)}\b",
        re.IGNORECASE,
    )
    return pattern.search(str(cleaned or "")) is not None


def install_vlan_validation_compat(window=None):
    """Make legacy contains/not_contains assertions VLAN-format aware."""
    descriptor = Validator.__dict__["_evaluate_assertion"]
    current = descriptor.__func__
    if getattr(current, "_vlan_label_compat", False):
        return window

    original = current

    def evaluate(cls, assertion, cleaned):
        kind = assertion.get("type", "contains")
        if kind in {"contains", "not_contains"}:
            vlan_id = _vlan_id(assertion.get("value", ""))
            if vlan_id is not None:
                present = _vlan_label_present(cleaned, vlan_id)
                if kind == "contains" and present:
                    return True
                if kind == "not_contains" and present:
                    return False

        return original(cls, assertion, cleaned)

    evaluate._vlan_label_compat = True
    evaluate._original = original
    Validator._evaluate_assertion = classmethod(evaluate)

    if window is not None:
        window._vlan_validation_compat_installed = True
        try:
            window.winfo_toplevel().title(
                f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}"
            )
        except Exception:
            pass
    return window
