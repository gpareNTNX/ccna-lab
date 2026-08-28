import unittest
from unittest.mock import patch

from ccna_lab_builder.gui import automatic_cabling as auto


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Settings:
    def __init__(self):
        self.data = {
            "lab": {"folder": "/CCNA-200-301", "master_name": "MASTER"},
            "compatibility": {"experimental_cabling": False},
        }
        self.saved = False

    def save(self):
        self.saved = True


class FakeWindow:
    def __init__(self, scenario=None):
        self.api = object()
        self.folder = Var("/CCNA-200-301")
        self.master_name = Var("MASTER")
        self.experimental = Var(False)
        self.settings = Settings()
        self.current_scenario = scenario
        self.logs = []
        self.validation_target = None

    def _selected_images(self):
        return "vios-router", "viosl2-switch"

    def _scenario_lab_name(self, scenario):
        return f"CCNA-{scenario['id']}-TEST"

    def _set_validation_target(self, lab):
        self.validation_target = lab

    def log(self, message):
        self.logs.append(message)


class FakeBuilder:
    last = None

    def __init__(self, api, log):
        self.api = api
        self.log = log
        self.calls = []
        FakeBuilder.last = self

    def create(self, folder, name, router, switch, cable=False):
        self.calls.append(("create", folder, name, cable))
        return f"{folder}/{name}.unl"

    def create_scenario(self, folder, name, router, switch, scenario, cable=False):
        self.calls.append(("scenario", folder, name, cable, scenario["id"]))
        return f"{folder}/{name}.unl"


class AutomaticCablingTests(unittest.TestCase):
    def test_master_generation_always_enables_cabling(self):
        window = FakeWindow()
        with patch.object(auto, "LabBuilder", FakeBuilder):
            lab = auto._build_master(window)

        self.assertEqual(lab, "/CCNA-200-301/MASTER.unl")
        self.assertEqual(
            FakeBuilder.last.calls[0],
            ("create", "/CCNA-200-301", "MASTER", True),
        )
        self.assertTrue(window.experimental.get())
        self.assertTrue(window.settings.data["compatibility"]["experimental_cabling"])
        self.assertTrue(window.settings.saved)

    def test_legacy_training_lab_uses_master_links_and_cables_automatically(self):
        scenario = {"id": "02", "name": "IPv4 Addressing"}
        window = FakeWindow(scenario)
        with patch.object(auto, "LabBuilder", FakeBuilder):
            lab = auto._create_scenario_lab(window)

        self.assertEqual(auto._scenario_link_count(scenario), len(auto.LINKS))
        self.assertEqual(
            FakeBuilder.last.calls[0],
            ("scenario", "/CCNA-200-301", "CCNA-02-TEST", True, "02"),
        )
        self.assertEqual(window.validation_target, lab)

    def test_v2_training_lab_uses_its_defined_links(self):
        scenario = {
            "id": "29",
            "name": "OSPF Multi-Router",
            "topology": {
                "nodes": [{"name": "R1", "template": "vios"}],
                "links": [
                    {"a": "R1", "a_if": "Gi0/0", "b": "R2", "b_if": "Gi0/0"},
                    {"a": "R2", "a_if": "Gi0/1", "b": "R3", "b_if": "Gi0/0"},
                ],
            },
        }
        window = FakeWindow(scenario)
        with patch.object(auto, "LabBuilder", FakeBuilder):
            auto._create_scenario_lab(window)

        self.assertEqual(auto._scenario_link_count(scenario), 2)
        self.assertTrue(FakeBuilder.last.calls[0][3])


if __name__ == "__main__":
    unittest.main()
