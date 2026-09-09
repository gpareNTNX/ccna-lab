import json
from importlib.resources import files

from ccna_lab_builder.data.legacy_topologies import legacy_topology
from ccna_lab_builder.data.workbook_scenarios import workbook_scenarios


def _apply_known_ios_check_fixes(scenario):
    """Keep legacy scenarios aligned with output that real IOS commands actually emit."""
    if str(scenario.get("id", "")).strip() != "11":
        return

    scenario["checks"] = [
        {
            "node": "R2-HQ",
            "command": "show running-config | section ip dhcp",
            "contains": [
                "ip dhcp pool USERS",
                "network 10.10.10.0 255.255.255.0",
                "default-router 10.10.10.1",
            ],
        },
        {
            "node": "R2-HQ",
            "command": "show ip dhcp pool",
            "contains": [
                "USERS",
                "10.10.10.1",
            ],
        },
    ]


class ScenarioCatalog:
    def __init__(self):
        data_dir = files("ccna_lab_builder.data")
        scenarios = []
        for filename in ("scenarios.json", "scenarios_v2.json"):
            path = data_dir.joinpath(filename)
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                continue
            if not isinstance(loaded, list):
                raise ValueError(f"{filename} must contain a JSON list.")
            scenarios.extend(loaded)

        scenarios.extend(workbook_scenarios())

        seen = set()
        for scenario in scenarios:
            scenario_id = str(scenario.get("id", "")).strip()
            if not scenario_id:
                raise ValueError("Every scenario requires a non-empty id.")
            if scenario_id in seen:
                raise ValueError(f"Duplicate scenario id: {scenario_id}")
            seen.add(scenario_id)
            scenario["id"] = scenario_id
            _apply_known_ios_check_fixes(scenario)
            scenario.setdefault("schema_version", 1)
            scenario.setdefault("tasks", [])
            scenario.setdefault("checks", [])

            if not scenario.get("topology"):
                topology = legacy_topology(scenario_id)
                if topology is not None:
                    scenario["topology"] = topology
                    scenario["schema_version"] = max(
                        2,
                        int(scenario.get("schema_version", 1)),
                    )

        self.scenarios = scenarios

    def all(self):
        return self.scenarios

    def get(self, scenario_id):
        wanted = str(scenario_id)
        for scenario in self.scenarios:
            if scenario["id"] == wanted:
                return scenario
        raise KeyError(scenario_id)
