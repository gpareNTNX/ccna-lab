"""VT/ANSI rendering compatibility for the interactive IOS console."""

from __future__ import annotations

import platform
import tkinter as tk

from ccna_lab_builder.gui.console_workspace import TerminalSessionView


class TerminalBuffer:
    """Small stateful terminal buffer for the control sequences emitted by IOS."""

    def __init__(self, max_lines=1500, max_cols=512):
        self.max_lines = int(max_lines)
        self.max_cols = int(max_cols)
        self.reset()

    def reset(self):
        self.lines = [[]]
        self.row = 0
        self.col = 0
        self.saved = (0, 0)
        self.pending = ""

    def _ensure_row(self, row):
        while len(self.lines) <= row:
            self.lines.append([])

    def _ensure_col(self, col):
        self._ensure_row(self.row)
        line = self.lines[self.row]
        if col > len(line):
            line.extend([" "] * (col - len(line)))

    def _put(self, char):
        if self.col >= self.max_cols:
            return
        self._ensure_col(self.col)
        line = self.lines[self.row]
        if self.col < len(line):
            line[self.col] = char
        else:
            line.append(char)
        self.col += 1

    def _trim_history(self):
        if len(self.lines) <= self.max_lines:
            return
        drop = len(self.lines) - self.max_lines
        del self.lines[:drop]
        self.row = max(0, self.row - drop)
        saved_row, saved_col = self.saved
        self.saved = (max(0, saved_row - drop), saved_col)

    @staticmethod
    def _params(value):
        value = value.lstrip("?")
        parts = value.split(";") if value else [""]
        result = []
        for part in parts:
            if part == "":
                result.append(None)
                continue
            try:
                result.append(int(part))
            except ValueError:
                result.append(None)
        return result

    @staticmethod
    def _first(values, default=1):
        if not values or values[0] in (None, 0):
            return default
        return values[0]

    def _csi(self, params, final):
        values = self._params(params)
        count = self._first(values)

        if final == "A":
            self.row = max(0, self.row - count)
            self._ensure_row(self.row)
        elif final == "B":
            self.row += count
            self._ensure_row(self.row)
        elif final == "C":
            self.col = min(self.max_cols - 1, self.col + count)
            self._ensure_col(self.col)
        elif final == "D":
            self.col = max(0, self.col - count)
        elif final in {"G", "`"}:
            self.col = max(0, min(self.max_cols - 1, count - 1))
            self._ensure_col(self.col)
        elif final in {"H", "f"}:
            row = (values[0] if values and values[0] else 1) - 1
            col = (values[1] if len(values) > 1 and values[1] else 1) - 1
            self.row = max(0, row)
            self.col = max(0, min(self.max_cols - 1, col))
            self._ensure_row(self.row)
            self._ensure_col(self.col)
        elif final == "K":
            mode = values[0] if values and values[0] is not None else 0
            line = self.lines[self.row]
            if mode == 0:
                del line[self.col :]
            elif mode == 1:
                upto = min(self.col + 1, len(line))
                for index in range(upto):
                    line[index] = " "
            elif mode == 2:
                self.lines[self.row] = []
                self.col = 0
        elif final == "J":
            mode = values[0] if values and values[0] is not None else 0
            if mode in {2, 3}:
                self.lines = [[]]
                self.row = 0
                self.col = 0
        elif final == "P":
            line = self.lines[self.row]
            if self.col < len(line):
                del line[self.col : self.col + count]
        elif final == "@":
            self._ensure_col(self.col)
            line = self.lines[self.row]
            line[self.col : self.col] = [" "] * count
        elif final == "s":
            self.saved = (self.row, self.col)
        elif final == "u":
            self.row, self.col = self.saved
            self._ensure_row(self.row)

    def feed(self, value):
        text = self.pending + str(value or "")
        self.pending = ""
        index = 0

        while index < len(text):
            char = text[index]

            if char == "\x1b":
                if index + 1 >= len(text):
                    self.pending = text[index:]
                    break

                marker = text[index + 1]
                if marker == "[":
                    end = index + 2
                    while end < len(text) and not ("@" <= text[end] <= "~"):
                        end += 1
                    if end >= len(text):
                        self.pending = text[index:]
                        break
                    self._csi(text[index + 2 : end], text[end])
                    index = end + 1
                    continue

                if marker == "]":
                    end = index + 2
                    complete = False
                    while end < len(text):
                        if text[end] == "\x07":
                            end += 1
                            complete = True
                            break
                        if text[end] == "\x1b" and end + 1 < len(text) and text[end + 1] == "\\":
                            end += 2
                            complete = True
                            break
                        end += 1
                    if not complete:
                        self.pending = text[index:]
                        break
                    index = end
                    continue

                if marker == "7":
                    self.saved = (self.row, self.col)
                elif marker == "8":
                    self.row, self.col = self.saved
                    self._ensure_row(self.row)
                index += 2
                continue

            if char == "\r":
                self.col = 0
            elif char == "\n":
                self.row += 1
                self._ensure_row(self.row)
            elif char == "\b":
                self.col = max(0, self.col - 1)
            elif char == "\t":
                target = min(self.max_cols - 1, ((self.col // 8) + 1) * 8)
                self._ensure_col(target)
                self.col = target
            elif char == "\x07" or char == "\x7f" or ord(char) < 32:
                pass
            else:
                self._put(char)

            index += 1

        self._trim_history()

    def snapshot(self):
        rendered = []
        for index, line in enumerate(self.lines):
            text = "".join(line)
            if index != self.row:
                text = text.rstrip()
            rendered.append(text)
        return "\n".join(rendered), self.row + 1, self.col


def _render(view):
    view._terminal_render_pending = False
    terminal = view.terminal
    buffer = view._terminal_buffer
    text, row, col = buffer.snapshot()

    try:
        at_bottom = terminal.yview()[1] >= 0.98
    except tk.TclError:
        at_bottom = True

    try:
        terminal.delete("1.0", "end")
        terminal.insert("1.0", text)
        terminal.mark_set("insert", f"{row}.{col}")
        if at_bottom:
            terminal.see("insert")
    except tk.TclError:
        pass


def _queue_render(view):
    if getattr(view, "_terminal_render_pending", False):
        return
    view._terminal_render_pending = True
    try:
        view.after_idle(lambda: _render(view))
    except tk.TclError:
        view._terminal_render_pending = False


def _install_terminal_stream_renderer():
    if getattr(TerminalSessionView, "_vt_stream_compat", False):
        return

    original_build = TerminalSessionView._build
    original_append = TerminalSessionView._append
    original_clear = TerminalSessionView.clear

    def build(view):
        original_build(view)
        view._terminal_buffer = TerminalBuffer()
        view._terminal_render_pending = False
        try:
            seed = view.terminal.get("1.0", "end-1c")
        except tk.TclError:
            seed = ""
        if seed:
            view._terminal_buffer.feed(seed)

        def interrupt(_event=None):
            view._send(b"\x03")
            return "break"

        view.terminal.bind("<Control-c>", interrupt)
        view.terminal.bind("<Control-Shift-c>", view._copy)
        view.terminal.bind("<Control-Shift-C>", view._copy)
        view.terminal.bind("<Control-Shift-v>", view._paste)
        view.terminal.bind("<Control-Shift-V>", view._paste)
        if platform.system() == "Darwin":
            view.terminal.bind("<Command-c>", view._copy)
            view.terminal.bind("<Command-v>", view._paste)

    def append(view, text):
        buffer = getattr(view, "_terminal_buffer", None)
        if buffer is None:
            return original_append(view, text)
        if not text:
            return None
        buffer.feed(text)
        _queue_render(view)
        return None

    def clear(view):
        buffer = getattr(view, "_terminal_buffer", None)
        if buffer is None:
            return original_clear(view)
        buffer.reset()
        try:
            view.terminal.delete("1.0", "end")
        except tk.TclError:
            pass
        return None

    TerminalSessionView._build = build
    TerminalSessionView._append = append
    TerminalSessionView.clear = clear
    TerminalSessionView._vt_stream_compat = True


def install_terminal_stream_compat(window):
    """Install stateful VT/ANSI rendering for every interactive device console."""
    _install_terminal_stream_renderer()
    try:
        window.winfo_toplevel().title("CCNA 200-301 EVE-NG Lab Builder v4.3.3")
    except tk.TclError:
        pass
    return getattr(window, "_console_workspace", None)
