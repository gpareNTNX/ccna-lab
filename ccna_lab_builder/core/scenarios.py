import json
from importlib.resources import files


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

        seen = set()
        for scenario in scenarios:
            scenario_id = str(scenario.get("id", "")).strip()
            if not scenario_id:
                raise ValueError("Every scenario requires a non-empty id.")
            if scenario_id in seen:
                raise ValueError(f"Duplicate scenario id: {scenario_id}")
            seen.add(scenario_id)
            scenario["id"] = scenario_id
            scenario.setdefault("schema_version", 1)
            scenario.setdefault("tasks", [])
            scenario.setdefault("checks", [])

        self.scenarios = scenarios

    def all(self):
        return self.scenarios

    def get(self, scenario_id):
        wanted = str(scenario_id)
        for scenario in self.scenarios:
            if scenario["id"] == wanted:
                return scenario
        raise KeyError(scenario_id)
