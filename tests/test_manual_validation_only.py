import unittest

from ccna_lab_builder.gui.manual_validation_only import _clear_validation_widgets


class _Output:
    def __init__(self):
        self.value = "old validation result"

    def delete(self, _start, _end):
        self.value = ""


class _Canvas:
    def __init__(self):
        self.validation = {"R1": {"status": "fail"}}
        self.score = 0

    def set_validation(self, validation, score):
        self.validation = validation
        self.score = score


class _Label:
    def __init__(self):
        self.text = "old"

    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class _Window:
    def __init__(self):
        self.validation_output = _Output()
        self.topology_canvas = _Canvas()
        self._topology_validation_signature = 123


class _Controller:
    def __init__(self):
        self._failed_results = [object()]
        self._failed_index = 4
        self.coach_target = _Label()
        self.coach_text = _Label()


class ManualValidationOnlyTests(unittest.TestCase):
    def test_clear_removes_previous_validator_and_topology_state(self):
        window = _Window()
        controller = _Controller()

        _clear_validation_widgets(window, controller)

        self.assertEqual(window.validation_output.value, "")
        self.assertEqual(window.topology_canvas.validation, {})
        self.assertIsNone(window.topology_canvas.score)
        self.assertIsNone(window._topology_validation_signature)
        self.assertEqual(controller._failed_results, [])
        self.assertEqual(controller._failed_index, 0)
        self.assertEqual(controller.coach_target.text, "Validation in progress…")


if __name__ == "__main__":
    unittest.main()
