import re
import tkinter as tk
from tkinter import messagebox, ttk

from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.gui.main import MainWindow


class SafeMainWindow(MainWindow):
    """Main window with thread-safe Tkinter error reporting and safer lab selection."""

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

    @staticmethod
    def _scenario_lab_name(scenario):
        slug = re.sub(r"[^A-Z0-9]+", "-", scenario["name"].upper()).strip("-")
        return f"CCNA-{scenario['id']}-{slug}"

    def create_scenario_lab(self):
        if not self.current_scenario:
            raise RuntimeError("Select a scenario first.")
        if not self.api:
            raise RuntimeError("Connect to EVE-NG first.")

        router_image, switch_image = self._selected_images()
        scenario = self.current_scenario
        name = self._scenario_lab_name(scenario)
        lab = LabBuilder(self.api, self.log).create(
            self.folder.get().strip(),
            name,
            router_image,
            switch_image,
            cable=self.experimental.get(),
        )
        self.log("Scenario lab created: " + lab)
        self.log("Validator target updated to: " + lab)

        def select_validation_lab():
            self.validation_lab.delete(0, "end")
            self.validation_lab.insert(0, lab)

        self.after(0, select_validation_lab)


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
