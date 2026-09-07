import types
import unittest

from ccna_lab_builder.gui.manual_validation_only import install_manual_validation_only


class _Var:
    def __init__(self, value=True):
        self.value = value

    def set(self, value):
        self.value = value


class _Settings:
    def __init__(self):
        self.data = {
            "learning": {
                "continuous_validation": True,
                "validation_interval": 25,
                "history": [],
            }
        }
        self.saved = False

    def save(self):
        self.saved = True


class _Output:
    def __init__(self):
        self.value = "stale"

    def delete(self, _start, _end):
        self.value = ""


class _Canvas:
    def set_validation(self, _validation, _score):
        pass


class _Window:
    MUTED = "gray"

    def __init__(self):
        self.settings = _Settings()
        self.validation_output = _Output()
        self.topology_canvas = _Canvas()
        self._topology_validation_signature = 1
        self.cancelled = []
        self.logs = []
        self.called_with_empty_output = False
        self._learning_controller = types.SimpleNamespace(
            _debounce_job="debounce",
            _periodic_job="periodic",
            continuous_var=_Var(True),
            _failed_results=[],
            _failed_index=0,
        )

    def after_cancel(self, job):
        self.cancelled.append(job)

    def validate_live(self):
        self.called_with_empty_output = self.validation_output.value == ""
        return "ok"

    def winfo_toplevel(self):
        return self

    def title(self, _value):
        pass

    def log(self, message):
        self.logs.append(message)


class ManualValidationInstallTests(unittest.TestCase):
    def test_install_disables_automatic_validation_and_clears_before_validate(self):
        window = _Window()
        controller = install_manual_validation_only(window)

        self.assertFalse(controller.continuous_var.value)
        self.assertEqual(set(window.cancelled), {"debounce", "periodic"})
        self.assertNotIn("continuous_validation", window.settings.data["learning"])
        self.assertNotIn("validation_interval", window.settings.data["learning"])
        self.assertTrue(window.settings.saved)

        self.assertEqual(window.validate_live(), "ok")
        self.assertTrue(window.called_with_empty_output)


if __name__ == "__main__":
    unittest.main()
