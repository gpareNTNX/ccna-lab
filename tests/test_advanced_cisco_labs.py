import unittest
from tkinter import TclError

from ccna_lab_builder.core.challenges import ChallengeCatalog
from ccna_lab_builder.gui.advanced_lab_ui import (
    PAGE_SUBTITLE,
    PAGE_TITLE,
    _rename_page_labels,
)


class AdvancedCiscoLabTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ChallengeCatalog()

    def test_advanced_pack_contains_eight_labs(self):
        labs = [item for item in self.catalog.all() if item["id"].startswith("ADV-C")]
        self.assertEqual(len(labs), 8)
        self.assertTrue(all(item["pack"] == "Advanced Cisco" for item in labs))

    def test_advanced_labs_use_existing_image_families_only(self):
        allowed = {"vios", "viosl2", "vpcs"}
        for lab in self.catalog.all():
            if not lab["id"].startswith("ADV-C"):
                continue
            templates = {node["template"] for node in lab["topology"]["nodes"]}
            self.assertLessEqual(templates, allowed, lab["id"])

    def test_expected_advanced_topics_are_present(self):
        names = {
            item["id"]: item["name"]
            for item in self.catalog.all()
            if item["id"].startswith("ADV-C")
        }
        self.assertIn("MSTP", names["ADV-C01"])
        self.assertIn("VTP", names["ADV-C02"])
        self.assertIn("RSPAN", names["ADV-C03"])
        self.assertIn("Multi-Area OSPFv2", names["ADV-C04"])
        self.assertIn("Summarization", names["ADV-C05"])
        self.assertIn("OSPFv3", names["ADV-C06"])
        self.assertIn("EIGRP", names["ADV-C07"])
        self.assertIn("BGP", names["ADV-C08"])

    def test_every_advanced_lab_has_tasks_checks_and_source_basis(self):
        for lab in self.catalog.all():
            if not lab["id"].startswith("ADV-C"):
                continue
            self.assertTrue(lab["tasks"], lab["id"])
            self.assertTrue(lab["checks"], lab["id"])
            self.assertTrue(lab["source_basis"], lab["id"])
            self.assertTrue(lab["objective"], lab["id"])


class AdvancedLabUiTests(unittest.TestCase):
    class FakeWidget:
        def __init__(self, text=None, raises_tcl=False):
            self.text = text
            self.raises_tcl = raises_tcl
            self.configured = {}

        def keys(self):
            if self.raises_tcl:
                return ["text"]
            return ["text"] if self.text is not None else ["padding"]

        def cget(self, option):
            if self.raises_tcl:
                raise TclError('unknown option "-text"')
            if option != "text" or self.text is None:
                raise TclError('unknown option "-text"')
            return self.text

        def configure(self, **kwargs):
            self.configured.update(kwargs)

    class FakeContainer:
        def __init__(self, children):
            self.children = children

        def winfo_children(self):
            return self.children

    class FakePage:
        def __init__(self, containers):
            self.containers = containers

        def winfo_children(self):
            return self.containers

    class FakeWindow:
        def __init__(self, page):
            self.t_challenges = page

    def test_page_label_rename_ignores_widgets_without_text_option(self):
        title = self.FakeWidget("Cisco Challenge Labs")
        subtitle = self.FakeWidget("Converted EVE-NG challenges only • legacy")
        frame = self.FakeWidget()
        tk9_problem_widget = self.FakeWidget(raises_tcl=True)
        page = self.FakePage(
            [self.FakeContainer([title, frame, tk9_problem_widget, subtitle])]
        )

        _rename_page_labels(self.FakeWindow(page))

        self.assertEqual(title.configured["text"], PAGE_TITLE)
        self.assertEqual(subtitle.configured["text"], PAGE_SUBTITLE)
        self.assertEqual(frame.configured, {})
        self.assertEqual(tk9_problem_widget.configured, {})


if __name__ == "__main__":
    unittest.main()
