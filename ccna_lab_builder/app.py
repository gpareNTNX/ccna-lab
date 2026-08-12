import tkinter as tk
from tkinter import ttk, messagebox

from ccna_lab_builder.gui.main import MainWindow


class SafeMainWindow(MainWindow):
    """Main window with thread-safe Tkinter error reporting.

    Python clears the exception target at the end of an ``except`` block.
    Therefore a Tk callback scheduled with ``after()`` must capture the
    rendered message, not the exception variable itself.
    """

    def _safe_run(self, func):
        try:
            func()
        except Exception as exc:
            message = str(exc)
            self.log("ERROR: " + message)
            self.after(
                0,
                lambda msg=message: messagebox.showerror(
                    "CCNA Lab Builder", msg
                ),
            )


def main():
    root = tk.Tk()
    root.title("CCNA 200-301 EVE-NG Lab Builder — V4.1")
    root.geometry("1240x860")
    root.minsize(1050, 720)
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    SafeMainWindow(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
