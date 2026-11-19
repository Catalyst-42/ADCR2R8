"""Tkinter debugger interface for the ADCR2R8 emulator."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.assembler.errors import AsmError
from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU, CPUError, DecodedInstruction
from src.gui.formatting import to_hex
from src.gui.widgets import ExecutionLog, HexView, MemoryView, RegisterTable


class App(tk.Tk):
    """Interactive view of a :class:`~src.cpu.cpu.CPU` instance.

    Execution is scheduled with ``after`` rather than performed in a blocking
    loop, so the window stays responsive while a program is running.
    """

    RUN_LIMIT = 10_000

    def __init__(self, cpu: CPU | None = None):
        super().__init__()
        self.cpu = cpu or CPU()
        self._running = False
        self._run_steps = 0
        self._after_id: str | None = None
        self._last_memory: list[int] | None = None

        self.title("ADCR2R8 — CPU emulator")
        self.geometry("1100x720")
        self.minsize(850, 520)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build_ui()
        self._refresh(full_memory=True)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(8, 8, 8, 4))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(8, weight=1)

        self.step_button = ttk.Button(toolbar, text="Step", command=self.step)
        self.run_button = ttk.Button(toolbar, text="Run", command=self.start_run)
        self.stop_button = ttk.Button(
            toolbar, text="Stop", command=self.stop_run, state="disabled"
        )
        self.reset_button = ttk.Button(toolbar, text="Reset", command=self.reset)
        self.load_button = ttk.Button(toolbar, text="Load .asm", command=self.load)
        for column, button in enumerate(
            (self.step_button, self.run_button, self.stop_button,
             self.reset_button, self.load_button)
        ):
            button.grid(row=0, column=column, padx=(0, 6))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(toolbar, textvariable=self.status_var).grid(
            row=0, column=8, sticky="e", padx=(12, 0)
        )

        body = ttk.PanedWindow(self, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        left = ttk.Frame(body, padding=(0, 0, 6, 0))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)
        body.add(left, weight=1)

        state = ttk.LabelFrame(left, text="CPU state", padding=8)
        state.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        state.columnconfigure(1, weight=1)
        self.pc_var = tk.StringVar()
        self.ir_var = tk.StringVar()
        self.asm_var = tk.StringVar()
        self.flags_var = tk.StringVar()
        self.halted_var = tk.StringVar()
        self._state_row(state, 0, "PC", self.pc_var)
        self._state_row(state, 1, "IR", self.ir_var)
        self._state_row(state, 2, "Instruction", self.asm_var)
        self._state_row(state, 3, "Flags", self.flags_var)
        self._state_row(state, 4, "Status", self.halted_var)

        registers = ttk.LabelFrame(left, text="Registers", padding=4)
        registers.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        registers.columnconfigure(0, weight=1)
        registers.rowconfigure(0, weight=1)
        self.registers = RegisterTable(registers)
        self.registers.grid(row=0, column=0, sticky="nsew")

        output = ttk.LabelFrame(left, text="Hex output", padding=4)
        output.grid(row=2, column=0, sticky="nsew")
        output.columnconfigure(0, weight=1)
        output.rowconfigure(0, weight=1)
        self.output = HexView(output, height=7)
        self.output.grid(row=0, column=0, sticky="nsew")

        memory_frame = ttk.LabelFrame(body, text="Data memory (dmem)", padding=4)
        memory_frame.rowconfigure(0, weight=1)
        memory_frame.columnconfigure(0, weight=1)
        body.add(memory_frame, weight=2)
        self.memory = MemoryView(memory_frame)
        self.memory.grid(row=0, column=0, sticky="nsew")

        right = ttk.Frame(body, padding=(6, 0, 0, 0))
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        body.add(right, weight=1)
        log_frame = ttk.LabelFrame(right, text="Execution log", padding=4)
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log = ExecutionLog(log_frame)
        self.log.grid(row=0, column=0, sticky="nsew")

    @staticmethod
    def _state_row(parent: ttk.LabelFrame, row: int, name: str, variable: tk.StringVar):
        ttk.Label(parent, text=f"{name}:").grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=2
        )
        ttk.Label(parent, textvariable=variable).grid(
            row=row, column=1, sticky="w", pady=2
        )

    def _refresh(self, *, full_memory: bool = False) -> None:
        state = self.cpu.snapshot()
        self.registers.refresh(state["regs"])

        self.pc_var.set(to_hex(state["pc"], 3))
        self.ir_var.set(to_hex(state["ir"]))
        self.flags_var.set(
            f"ZF={int(state['ZF'])}   CF={int(state['CF'])}   SF={int(state['SF'])}"
        )
        self.halted_var.set("HALTED" if state["halted"] else "RUNNING / READY")

        instruction = state["last_instruction"]
        if instruction is None:
            try:
                instruction = self.cpu.decode()
            except CPUError as error:
                self.asm_var.set(f"<invalid: {error}>")
            else:
                self.asm_var.set(instruction.assembly)
        else:
            self.asm_var.set(instruction.assembly)

        changed = list(range(4096)) if full_memory or self._last_memory is None else [
            address
            for address, (old, new) in enumerate(zip(self._last_memory, state["dmem"]))
            if old != new
        ]
        self.memory.refresh(state["dmem"], changed)
        self._last_memory = state["dmem"]
        self._refresh_output(state["dmem"])

    def _refresh_output(self, memory: list[int]) -> None:
        # These are the result locations defined by the project contract.  It
        # is useful to show them even when a program has not been loaded yet.
        lines = [
            f"dmem[0x200] = {to_hex(memory[0x200])}  (maximum)",
            f"dmem[0x300] = {to_hex(memory[0x300])}  (convolution low)",
            f"dmem[0x301] = {to_hex(memory[0x301])}  (convolution middle)",
            f"dmem[0x302] = {to_hex(memory[0x302])}  (convolution high)",
        ]
        self.output.set_lines(lines)

    def _log_instruction(self, instruction: DecodedInstruction) -> None:
        self.log.append(
            f"PC {to_hex(instruction.address, 3)}: "
            f"{to_hex(instruction.word)}  {instruction.assembly}"
        )

    def step(self) -> None:
        if self._running:
            return
        try:
            instruction = self.cpu.step()
        except (CPUError, ZeroDivisionError) as error:
            self.status_var.set(f"Error: {error}")
            self.log.append(f"ERROR: {error}")
            self._refresh()
            return
        if instruction is None:
            self.status_var.set("HALT reached")
            self._refresh()
            return
        self._log_instruction(instruction)
        self.status_var.set(f"Executed {instruction.assembly}")
        self._refresh()

    def start_run(self) -> None:
        if self._running or self.cpu.halted:
            if self.cpu.halted:
                self.status_var.set("HALT reached; press Reset to run again")
            return
        self._running = True
        self._run_steps = 0
        self.step_button.configure(state="disabled")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._run_next()

    def _run_next(self) -> None:
        if not self._running:
            return
        if self.cpu.halted or self._run_steps >= self.RUN_LIMIT:
            self.stop_run()
            if self.cpu.halted:
                self.status_var.set("HALT reached")
            else:
                self.status_var.set(f"Stopped at limit ({self.RUN_LIMIT})")
            return
        try:
            instruction = self.cpu.step()
        except (CPUError, ZeroDivisionError) as error:
            self.log.append(f"ERROR: {error}")
            self.status_var.set(f"Error: {error}")
            self._refresh()
            self.stop_run()
            return
        self._run_steps += 1
        if instruction is not None:
            self._log_instruction(instruction)
        self._refresh()
        self.status_var.set(f"Running: {self._run_steps} instruction(s)")
        self._after_id = self.after(1, self._run_next)

    def stop_run(self) -> None:
        self._running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.step_button.configure(state="normal")
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def reset(self) -> None:
        self.stop_run()
        self.cpu.reset()
        self.log.append("CPU reset (program and data memory preserved)")
        self.status_var.set("Reset")
        self._refresh()

    def load(self) -> None:
        path = filedialog.askopenfilename(
            title="Load assembly program",
            filetypes=(("Assembly files", "*.asm"), ("All files", "*.*")),
        )
        if not path:
            return
        self._load_path(path)

    def _load_path(self, path: str | Path) -> None:
        self.stop_run()
        try:
            words = assemble_file(str(path))
            self.cpu.load_program(words)
        except (OSError, AsmError, CPUError) as error:
            self.status_var.set(f"Load error: {error}")
            self.log.append(f"LOAD ERROR: {error}")
            messagebox.showerror("Could not load program", str(error), parent=self)
            return
        self.log.append(f"Loaded {Path(path).name} ({len(words)} words)")
        self.status_var.set(f"Loaded {Path(path).name}")
        self._refresh()

    def _close(self) -> None:
        self.stop_run()
        self.destroy()


def run(cpu: CPU | None = None) -> None:
    """Launch the GUI and block until its window is closed."""
    app = App(cpu or CPU())
    app.mainloop()


if __name__ == "__main__":
    run()
