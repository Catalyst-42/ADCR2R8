"""Tkinter debugger interface for the ADCR2R8 emulator."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.assembler.errors import AsmError
from src.assembler.parser import assemble_file
from src.cpu.constants import NUM_REGISTERS
from src.cpu.cpu import CPU, CPUError, DecodedInstruction
from src.gui.formatting import to_hex
from src.gui.widgets import ExecutionLog, HexView, MemoryView, RegisterTable, ProgramCommands


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
        self._asm_file_path: str | None = None
        self._mem_file_path: str | None = None

        self.title("ADCR2R8 - CPU emulator")
        self.geometry("1100x720")
        self.minsize(850, 520)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build_ui()
        self._refresh(full_memory=True)

    def _build_ui(self) -> None:
        self.title("CPU Emulator")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.LabelFrame(self, text="Controls", padding=4)
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 8))
        toolbar.columnconfigure(2, weight=1)
        self.step_button = ttk.Button(toolbar, text="Step", command=self.step)
        self.run_button = ttk.Button(toolbar, text="Run", command=self.start_run)
        self.reset_button = ttk.Button(toolbar, text="Reset", command=self.reset)
        self.load_button = ttk.Button(toolbar, text="Load .asm", command=self.load)
        self.load_mem_button = ttk.Button(
            toolbar, text="Load .mem", command=self.load_mem
        )

        # Main execution buttons (Run, Step, Reset) on left side in separate columns
        self.run_button.grid(row=0, column=0, padx=(0, 0), sticky="w")
        self.step_button.grid(row=0, column=1, padx=(0, 0), sticky="w")
        self.reset_button.grid(row=0, column=2, padx=(0, 0), sticky="w")

        # Load buttons on the right side in separate columns
        self.load_button.grid(row=0, column=3, padx=(0, 0), sticky="e")
        self.load_mem_button.grid(row=0, column=4, padx=(0, 0), sticky="e")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        left = ttk.Frame(body, padding=(0, 0, 0, 0))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)  # Now row 1 is for the paned window
        body.add(left, weight=1)

        # CPU state section (full width at top, row 0)
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

        # Create paned window for registers and program commands (row 1)
        registers_pane = ttk.PanedWindow(left, orient="horizontal")
        registers_pane.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        registers_pane.columnconfigure(0, weight=1)
        registers_pane.columnconfigure(1, weight=1)

        # Registers section (left side of paned window)
        registers_frame = ttk.LabelFrame(registers_pane, text="Registers", padding=4)
        registers_frame.columnconfigure(0, weight=1)
        registers_frame.rowconfigure(0, weight=1)
        self.registers = RegisterTable(registers_frame)
        self.registers.grid(row=0, column=0, sticky="nsew")
        registers_pane.add(registers_frame, weight=1)

        # Program commands section (right side of paned window)
        program_frame = ttk.LabelFrame(registers_pane, text="Program Commands", padding=4)
        program_frame.columnconfigure(0, weight=1)
        program_frame.rowconfigure(0, weight=1)
        self.program_commands = ProgramCommands(program_frame, cpu=self.cpu)
        self.program_commands.grid(row=0, column=0, sticky="nsew")
        registers_pane.add(program_frame, weight=1)

        # Execution log section (full width at bottom, row 2)
        log_frame = ttk.LabelFrame(left, text="Execution log", padding=4)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = ExecutionLog(log_frame)
        self.log.grid(row=0, column=0, sticky="nsew")

        memory_frame = ttk.LabelFrame(body, text="Memory", padding=4)
        memory_frame.rowconfigure(0, weight=1)
        memory_frame.columnconfigure(0, weight=1)
        body.add(memory_frame, weight=2)
        self.memory = MemoryView(memory_frame, cpu=self.cpu)
        self.memory.grid(row=0, column=0, sticky="nsew")

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
        self.program_commands.refresh(state["imem"], self.cpu)

        self.pc_var.set(to_hex(state["pc"], 3))
        self.ir_var.set(to_hex(state["ir"]))
        self.flags_var.set(
            f"ZF={int(state['ZF'])}   CF={int(state['CF'])}   SF={int(state['SF'])}"
        )
        self.halted_var.set("HALTED" if state["halted"] else "INIT")

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

        changed = (
            list(range(4096))
            if full_memory or self._last_memory is None
            else [
                address
                for address, (old, new) in enumerate(
                    zip(self._last_memory, state["dmem"])
                )
                if old != new
            ]
        )
        self.memory.refresh(state["dmem"], changed)
        self._last_memory = state["dmem"]

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
            self.log.append(f"ERROR: {error}")
            self._refresh()
            return
        if instruction is None:
            self._refresh()
            return
        self._log_instruction(instruction)
        self._refresh()

    def start_run(self) -> None:
        if self._running or self.cpu.halted:
            if self.cpu.halted:
                return
        self._running = True
        self._run_steps = 0
        self.step_button.configure(state="disabled")
        self.run_button.configure(state="disabled")
        self._run_next()

    def _run_next(self) -> None:
        if not self._running:
            return
        if self.cpu.halted or self._run_steps >= self.RUN_LIMIT:
            self.stop_run()
            return
        try:
            instruction = self.cpu.step()
        except (CPUError, ZeroDivisionError) as error:
            self.log.append(f"ERROR: {error}")
            self._refresh()
            self.stop_run()
            return
        self._run_steps += 1
        if instruction is not None:
            self._log_instruction(instruction)
        self._refresh()
        self._after_id = self.after(1, self._run_next)

    def stop_run(self) -> None:
        self._running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.step_button.configure(state="normal")
        self.run_button.configure(state="normal")

    def reset(self) -> None:
        """Reset everything - clear all memory, program, and CPU state."""
        self.stop_run()
        self.cpu.reset()  # Complete reset including memory
        self.log.append("CPU reset - ALL memory, program, and registers cleared")
        self._refresh()

    def load(self) -> None:
        path = filedialog.askopenfilename(
            title="Load assembly program",
            filetypes=(("Assembly files", "*.asm"), ("All files", "*.*")),
        )
        if not path:
            return
        self._asm_file_path = path
        self._load_path(path)

    def _load_path(self, path: str | Path) -> None:
        self.stop_run()
        try:
            words = assemble_file(str(path))
            self.cpu.load_program(words)
            # Don't clear memory - just load program
            self.log.append(f"Loaded {Path(path).name} ({len(words)} words)")
        except (OSError, AsmError, CPUError) as error:
            self.log.append(f"LOAD ERROR: {error}")
            messagebox.showerror("Could not load program", str(error), parent=self)
            return
        self._refresh()

    def load_mem(self) -> None:
        """Load memory from a .mem file - clears only memory, preserves program."""
        path = filedialog.askopenfilename(
            title="Load memory file",
            filetypes=(("Memory files", "*.mem"), ("All files", "*.*")),
        )
        if not path:
            return
        self._mem_file_path = path

        try:
            # Clear only data memory, preserve program in instruction memory
            self.cpu.dmem[:] = [0] * len(self.cpu.dmem)
            
            # Then load memory file
            count = self.cpu.load_mem_file(path)
            self.log.append(f"Loaded {Path(path).name} ({count} values) - memory cleared first")
            self._refresh()

        except CPUError as error:
            self.log.append(f"LOAD ERROR: {error}")
            messagebox.showerror("Could not load memory file", str(error), parent=self)

    def _close(self) -> None:
        self.stop_run()
        self.destroy()


def run(cpu: CPU | None = None) -> None:
    """Launch the GUI and block until its window is closed."""
    app = App(cpu or CPU())
    app.mainloop()


if __name__ == "__main__":
    run()
