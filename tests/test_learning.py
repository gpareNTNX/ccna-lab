import unittest

from ccna_lab_builder.core.learning import (
    build_learning_hint,
    link_runtime_state,
    make_validation_history_entry,
    normalize_eve_node_state,
    validation_state_by_node,
    validation_summary,
)
from ccna_lab_builder.core.validator import CheckResult


class LearningCoreTests(unittest.TestCase):
    def test_eve_node_states_are_normalized(self):
        self.assertEqual(normalize_eve_node_state(2), "running")
        self.assertEqual(normalize_eve_node_state("2"), "running")
        self.assertEqual(normalize_eve_node_state(1), "starting")
        self.assertEqual(normalize_eve_node_state(0), "stopped")
        self.assertEqual(normalize_eve_node_state("booting"), "starting")
        self.assertEqual(normalize_eve_node_state(None), "unknown")

    def test_link_runtime_state_is_only_endpoint_readiness(self):
        self.assertEqual(link_runtime_state("running", "running"), "ready")
        self.assertEqual(link_runtime_state("running", "stopped"), "stopped")
        self.assertEqual(link_runtime_state("starting", "running"), "starting")
        self.assertEqual(link_runtime_state("unknown", "running"), "unknown")

    def test_learning_hint_keeps_remediation_progressive(self):
        result = CheckResult(
            node="R1",
            command="show ip ospf neighbor",
            passed=False,
            missing=["OSPF neighbor 2.2.2.2 FULL"],
            output="",
            expected=["OSPF neighbor 2.2.2.2 FULL"],
            remediation=[
                "configure terminal",
                "router ospf 1",
                "network 10.0.12.0 0.0.0.3 area 0",
            ],
        )
        hint = build_learning_hint(result)
        self.assertIn("show ip ospf neighbor", hint.hint)
        self.assertIn("area", hint.explanation.casefold())
        self.assertEqual(hint.remediation[0], "configure terminal")
        self.assertNotIn("configure terminal", hint.hint)

    def test_validation_summary_and_topology_state(self):
        results = [
            CheckResult(
                node="R1",
                command="show ip interface brief",
                passed=True,
                missing=[],
                output="",
                expected=["Gi0/0"],
                matched=["Gi0/0"],
            ),
            CheckResult(
                node="R1",
                command="show ip ospf neighbor",
                passed=False,
                missing=["FULL"],
                output="",
                expected=["FULL"],
            ),
            CheckResult(
                node="R2",
                command="show ip route",
                passed=True,
                missing=[],
                output="",
                expected=["O 10.0.1.0/24"],
                matched=["O 10.0.1.0/24"],
            ),
        ]
        summary = validation_summary(results)
        self.assertEqual(summary["score"], 67)
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["total"], 3)

        state = validation_state_by_node(results)
        self.assertEqual(state["R1"]["status"], "mixed")
        self.assertEqual(state["R2"]["status"], "pass")

    def test_history_entry_is_compact_and_deterministic(self):
        result = CheckResult(
            node="SW1",
            command="show spanning-tree root",
            passed=False,
            missing=["Vl10"],
            output="large output not stored in history",
            expected=["Vl10"],
        )
        entry = make_validation_history_entry(
            {"id": "07", "name": "STP / RSTP"},
            "/CCNA/CCNA-07.unl",
            [result],
            "manual",
            3.14159,
            timestamp="2026-09-06T17:00:00+00:00",
        )
        self.assertEqual(entry["score"], 0)
        self.assertEqual(entry["failed"], ["SW1: show spanning-tree root"])
        self.assertNotIn("output", entry)
        self.assertEqual(entry["duration_seconds"], 3.14)


if __name__ == "__main__":
    unittest.main()
