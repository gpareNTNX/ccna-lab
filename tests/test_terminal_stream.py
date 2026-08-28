from ccna_lab_builder.gui.terminal_stream_compat import TerminalBuffer


def test_terminal_buffer_strips_osc_title_sequence():
    buffer = TerminalBuffer()
    buffer.feed("\x1b]0;R1-EDGE\x07Router>")
    text, _, _ = buffer.snapshot()
    assert text == "Router>"


def test_terminal_buffer_handles_split_osc_sequence():
    buffer = TerminalBuffer()
    buffer.feed("\x1b]0;R1-")
    buffer.feed("EDGE\x07Router>")
    text, _, _ = buffer.snapshot()
    assert text == "Router>"


def test_terminal_buffer_applies_backspace_editing():
    buffer = TerminalBuffer()
    buffer.feed("Router>abc\b \bd")
    text, _, _ = buffer.snapshot()
    assert text == "Router>abd"


def test_terminal_buffer_applies_cursor_left_overwrite():
    buffer = TerminalBuffer()
    buffer.feed("Router>abcd\x1b[2DX")
    text, _, _ = buffer.snapshot()
    assert text == "Router>abXd"


def test_terminal_buffer_handles_carriage_return_rewrite():
    buffer = TerminalBuffer()
    buffer.feed("Loading 1%\rLoading 9%")
    text, _, _ = buffer.snapshot()
    assert text == "Loading 9%"


def test_terminal_buffer_clear_screen_sequence():
    buffer = TerminalBuffer()
    buffer.feed("old output\r\nRouter>\x1b[2J\x1b[HRouter#")
    text, _, _ = buffer.snapshot()
    assert text == "Router#"


def test_terminal_buffer_does_not_render_control_characters():
    buffer = TerminalBuffer()
    buffer.feed("Router>\x00\x07show ip int brief")
    text, _, _ = buffer.snapshot()
    assert text == "Router>show ip int brief"
