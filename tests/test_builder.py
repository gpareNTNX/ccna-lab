import unittest

from ccna_lab_builder.core.builder import LabBuilder


class FakeApi:
    def __init__(self):
        self.calls = []

    def ensure_folder(self, folder):
        self.calls.append(("ensure_folder", folder))
        return folder

    def create_lab(self, folder, name):
        self.calls.append(("create_lab", folder, name))
        return {"status": "success"}

    def lab_path(self, folder, name):
        return f"{folder.rstrip('/')}/{name}.unl"

    def add_node(self, lab, payload):
        self.calls.append(("add_node", lab, payload["name"]))
        return {"status": "success"}


class LabBuilderTests(unittest.TestCase):
    def test_folder_is_ensured_before_lab_creation(self):
        api = FakeApi()
        builder = LabBuilder(api, log=lambda _message: None)

        lab = builder.create(
            "CCNA-200-301",
            "CCNA-TEST",
            "vios-router",
            "viosl2-switch",
            cable=False,
        )

        self.assertEqual(api.calls[0], ("ensure_folder", "/CCNA-200-301"))
        self.assertEqual(
            api.calls[1],
            ("create_lab", "/CCNA-200-301", "CCNA-TEST"),
        )
        self.assertEqual(lab, "/CCNA-200-301/CCNA-TEST.unl")


if __name__ == "__main__":
    unittest.main()
