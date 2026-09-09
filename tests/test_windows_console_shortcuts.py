import unittest

from ccna_lab_builder.gui.windows_console_shortcuts import (
    _bind_windows_shortcuts,
    _handle_control_c,
)


class _FakeTerminal:
    def __init__(self, selected=False):
        self.selected = selected
        self.bindings = {}

    def tag_ranges(self, tag):
        if tag == "sel" and self.selected:
            return ("1.0", "1.1")
        return ()

    def bind(self, sequence, callback):
        self.bindings[sequence] = callback


class _FakeView:
    def __init__(self, selected=False):
        self.terminal = _FakeTerminal(selected=selected)
        self.sent = []
        self.copied = 0
        self.pasted = 0

    def _send(self, payload):
        self.sent.append(payload)

    def _copy(self, _event=None):
        self.copied += 1
        return "break"

    def _paste(self, _event=None):
        self.pasted += 1
        return "break"


class WindowsConsoleShortcutTests(unittest.TestCase):
    def test_ctrl_c_copies_selected_text_on_windows(self):
        view = _FakeView(selected=True)

        result = _handle_control_c(view, system_name="Windows")

        self.assertEqual(result, "break")
        self.assertEqual(view.copied, 1)
        self.assertEqual(view.sent, [])

    def test_ctrl_c_without_selection_still_sends_ios_interrupt(self):
        view = _FakeView(selected=False)

        result = _handle_control_c(view, system_name="Windows")

        self.assertEqual(result, "break")
        self.assertEqual(view.copied, 0)
        self.assertEqual(view.sent, [b"\x03"])

    def test_windows_bindings_explicitly_include_ctrl_c_and_ctrl_v(self):
        view = _FakeView()

        _bind_windows_shortcuts(view)

        expected = {
            "<Control-c>",
            "<Control-v>",
            "<Control-Shift-c>",
            "<Control-Shift-C>",
            "<Control-Shift-v>",
            "<Control-Shift-V>",
        }
        self.assertTrue(expected.issubset(view.terminal.bindings))

        view.terminal.bindings["<Control-v>"]()
        self.assertEqual(view.pasted, 1)

    def test_non_windows_ctrl_c_keeps_terminal_interrupt_semantics(self):
        view = _FakeView(selected=True)

        result = _handle_control_c(view, system_name="Linux")

        self.assertEqual(result, "break")
        self.assertEqual(view.copied, 0)
        self.assertEqual(view.sent, [b"\x03"])


if __name__ == "__main__":
    unittest.main()
