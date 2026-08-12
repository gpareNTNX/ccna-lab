import tkinter as tk
from tkinter import ttk
from ccna_lab_builder.gui.main import MainWindow

def main():
    root = tk.Tk()
    root.title("CCNA 200-301 EVE-NG Lab Builder — V4")
    root.geometry("1240x860")
    root.minsize(1050, 720)
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    MainWindow(root).pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
