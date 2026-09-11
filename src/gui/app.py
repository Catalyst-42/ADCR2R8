"""
app.py — tkinter GUI for the ADCR2R8 emulator. (NOT YET IMPLEMENTED)

Planned layout (see docs/report for mockup):
    - register table (hex), PC / IR (hex + disassembled), flags (ZF/CF/SF)
    - data memory view with scroll
    - buttons: Step, Run, Reset, Load
    - execution log panel

The GUI should only depend on src.cpu.cpu.CPU — it must not import the
assembler directly; file loading is orchestrated by main.py, which
assembles the .asm file and hands the CPU a ready word list via
CPU.load_program().
"""

import tkinter as tk

from src.cpu.cpu import CPU


class App(tk.Tk):
    def __init__(self, cpu: CPU):
        super().__init__()
        self.cpu = cpu
        self.title("ADCR2R8 emulator")
        # TODO: register table, memory view, buttons, log — see widgets.py
        placeholder = tk.Label(
            self, text="GUI not implemented yet — see src/gui/widgets.py"
        )
        placeholder.pack(padx=20, pady=20)


def run(cpu: CPU | None = None):
    app = App(cpu or CPU())
    app.mainloop()


if __name__ == "__main__":
    run()
