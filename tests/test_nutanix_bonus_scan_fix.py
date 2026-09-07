import unittest

from ccna_lab_builder.gui.nutanix_bonus_compat import (
    _classify_qemu_images,
    _select_default_bonus,
)


class _FakeListbox:
    def __init__(self):
        self.selected = []
        self.active = None
        self.visible = None

    def selection_clear(self, _first, _last):
        self.selected = []

    def selection_set(self, index):
        self.selected = [index]

    def activate(self, index):
        self.active = index

    def see(self, index):
        self.visible = index


class _FakeCatalog:
    def __init__(self, labs):
        self._labs = labs

    def all(self):
        return list(self._labs)


class _FakeController:
    def __init__(self, current=None, labs=None):
        self.current = current
        self.catalog = _FakeCatalog(labs or [{"id": "NTNX-B01"}])
        self.listbox = _FakeListbox()
        self.selected = None

    def select(self, index):
        self.selected = index
        self.current = self.catalog.all()[index]


class NutanixBonusScanFixTests(unittest.TestCase):
    def test_global_qemu_inventory_includes_nxosv9k(self):
        inventory = _classify_qemu_images(
            [
                "vios-adventerprisek9-m.spa.159-3.m6",
                "viosl2-adventerprisek9-m.ssa.high_iron_20200929",
                "nxosv9k-9.3.1",
                "linux-ubuntu-22.04",
            ]
        )
        self.assertEqual(
            inventory["routers"],
            ["vios-adventerprisek9-m.spa.159-3.m6"],
        )
        self.assertEqual(
            inventory["switches"],
            ["viosl2-adventerprisek9-m.ssa.high_iron_20200929"],
        )
        self.assertEqual(inventory["nxosv9k"], ["nxosv9k-9.3.1"])
        self.assertEqual(inventory["all"], 4)

    def test_bonus_page_auto_selects_first_lab_once(self):
        controller = _FakeController()
        self.assertTrue(_select_default_bonus(controller))
        self.assertEqual(controller.selected, 0)
        self.assertEqual(controller.listbox.selected, [0])
        self.assertEqual(controller.listbox.active, 0)
        self.assertEqual(controller.listbox.visible, 0)
        self.assertFalse(_select_default_bonus(controller))

    def test_bonus_page_does_not_override_existing_selection(self):
        current = {"id": "NTNX-B99"}
        controller = _FakeController(current=current)
        self.assertFalse(_select_default_bonus(controller))
        self.assertIs(controller.current, current)
        self.assertIsNone(controller.selected)


if __name__ == "__main__":
    unittest.main()
