import json
from importlib.resources import files

class ScenarioCatalog:
    def __init__(self):
        path = files("ccna_lab_builder.data").joinpath("scenarios.json")
        self.scenarios = json.loads(path.read_text(encoding="utf-8"))

    def all(self):
        return self.scenarios

    def get(self, scenario_id):
        for scenario in self.scenarios:
            if scenario["id"] == scenario_id:
                return scenario
        raise KeyError(scenario_id)
