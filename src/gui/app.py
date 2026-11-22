import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.assembler.errors import AsmError
from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU, CPUError, DecodedInstruction
from src.gui.utils import to_hex
from src.gui.widgets import ExecutionLog, MemoryView, ProgramCommands, RegisterTable


class App(tk.Tk):
    RUN_LIMIT = 10_000

    def __init__(self, cpu: CPU | None = None):
        """Init GUI"""
        super().__init__()
        self.cpu = cpu or CPU()
        self._last_memory: list[int] | None = None
        self._asm_file_path: str | None = None
        self._mem_file_path: str | None = None

        self.title("ADCR2R8")
        self.geometry("1100x720")
        self.minsize(850, 520)

        self.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()
        self._refresh(full_memory=True)

    def _build_ui(self) -> None:
        """Compose UI elements on window"""
        self.title("CPU Emulator")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.LabelFrame(self, text="Controls", padding=4)
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 8))
        toolbar.columnconfigure(2, weight=1)

        # CPU
        self.step_button = ttk.Button(toolbar, text="Step", command=self.step)
        self.run_button = ttk.Button(toolbar, text="Run", command=self.run_all)
        self.reset_button = ttk.Button(toolbar, text="Reset", command=self.reset)

        # Files
        self.load_asm_button = ttk.Button(
            toolbar, text="Load .asm", command=self.load_asm
        )
        self.load_mem_button = ttk.Button(
            toolbar, text="Load .mem", command=self.load_mem
        )

        # Controls
        self.run_button.grid(row=0, column=0, padx=(0, 0), sticky="w")
        self.step_button.grid(row=0, column=1, padx=(0, 0), sticky="w")
        self.reset_button.grid(row=0, column=2, padx=(0, 0), sticky="w")

        self.load_asm_button.grid(row=0, column=3, padx=(0, 0), sticky="e")
        self.load_mem_button.grid(row=0, column=4, padx=(0, 0), sticky="e")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        left = ttk.Frame(body, padding=(0, 0, 0, 0))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        body.add(left, weight=1)

        # CPU state
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

        # Registers
        registers_pane = ttk.PanedWindow(left, orient="horizontal")
        registers_pane.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        registers_pane.columnconfigure(0, weight=1)
        registers_pane.columnconfigure(1, weight=1)

        registers_frame = ttk.LabelFrame(registers_pane, text="Registers", padding=4)
        registers_frame.columnconfigure(0, weight=1)
        registers_frame.rowconfigure(0, weight=1)
        self.registers = RegisterTable(registers_frame)
        self.registers.grid(row=0, column=0, sticky="nsew")
        registers_pane.add(registers_frame, weight=1)

        # Program commands
        program_frame = ttk.LabelFrame(
            registers_pane, text="Program Commands", padding=4
        )
        program_frame.columnconfigure(0, weight=1)
        program_frame.rowconfigure(0, weight=1)
        self.program_commands = ProgramCommands(program_frame, cpu=self.cpu)
        self.program_commands.grid(row=0, column=0, sticky="nsew")
        registers_pane.add(program_frame, weight=1)

        # Execution log
        log_frame = ttk.LabelFrame(left, text="Execution log", padding=4)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = ExecutionLog(log_frame)
        self.log.grid(row=0, column=0, sticky="nsew")

        # Memory
        memory_frame = ttk.LabelFrame(body, text="Memory", padding=4)
        memory_frame.rowconfigure(0, weight=1)
        memory_frame.columnconfigure(0, weight=1)

        body.add(memory_frame, weight=2)
        self.memory = MemoryView(memory_frame, cpu=self.cpu)
        self.memory.grid(row=0, column=0, sticky="nsew")

    @staticmethod
    def _state_row(parent: ttk.LabelFrame, row: int, name: str, variable: tk.StringVar):
        """Simple wrapper for a key value pairs output"""
        ttk.Label(parent, text=f"{name}:").grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=2
        )
        ttk.Label(parent, textvariable=variable).grid(
            row=row, column=1, sticky="w", pady=2
        )

    def _refresh(self, *, full_memory: bool = False) -> None:
        """Refresh all values in UI"""
        state = self.cpu.snapshot()

        self.registers.refresh(state["regs"])
        self.program_commands.refresh(state["imem"], self.cpu)
        self.pc_var.set(f"{to_hex(state['pc'], 3)} ({state['pc']})")
        self.ir_var.set(f"{to_hex(state['ir'])} ({state['ir']})")
        self.flags_var.set(
            f"ZF={int(state['ZF'])} "
            f"CF={int(state['CF'])} "
            f"SF={int(state['SF'])} "
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
        """Logs last inscruction call"""
        self.log.append(
            f"PC {to_hex(instruction.address, 3)}: "
            f"{to_hex(instruction.word)}  {instruction.assembly}"
        )

    def step(self) -> None:
        """Performs one CPU instruction"""
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

    def run_all(self) -> None:
        """Performs all CPU instructions until HALT or RUN_LIMIT"""
        if self.cpu.halted:
            return

        steps = 0
        while not self.cpu.halted and steps < self.RUN_LIMIT:
            try:
                instruction = self.cpu.step()
                if instruction is not None:
                    self._log_instruction(instruction)

                steps += 1

            except (CPUError, ZeroDivisionError) as error:
                self.log.append(f"ERROR: {error}")
                break

        # Result
        if self.cpu.halted:
            self.log.append(f"Program halted after {steps} steps")

        else:
            self.log.append(f"Program stopped after {steps} steps (limit reached)")

        self._refresh()

    def reset(self) -> None:
        """Rest button"""
        self.cpu.reset()
        self.log.clear()
        self.log.append("CPU reset")

        # Reload program
        if self._asm_file_path:
            words = assemble_file(str(self._asm_file_path))
            self.cpu.load_program(words)

            self.log.append(
                f"Reloaded {Path(self._asm_file_path).name} ({len(words)} words)"
            )

        # Reload memory
        if self._mem_file_path:
            self.cpu.dmem[:] = [0] * len(self.cpu.dmem)
            count = self.cpu.load_mem_file(self._mem_file_path)

            self.log.append(
                f"Reloaded {Path(self._mem_file_path).name} ({count} values)"
            )

        self._refresh()

    def load_asm(self) -> None:
        """Load .asm button"""
        path = filedialog.askopenfilename(
            title="Load assembly program",
            filetypes=(("Assembly files", "*.asm"), ("All files", "*.*")),
        )

        if not path:
            return

        self._asm_file_path = path

        # Load and assemble .asm file
        try:
            words = assemble_file(str(path))
            self.cpu.load_program(words)
            self.log.append(f"Loaded {Path(path).name} ({len(words)} words)")

        except (OSError, AsmError, CPUError) as error:
            self.log.append(f"LOAD ERROR: {error}")
            messagebox.showerror("Could not load program", str(error), parent=self)
            return

        self._refresh()

    def load_mem(self) -> None:
        """Load .mem button"""
        path = filedialog.askopenfilename(
            title="Load memory file",
            filetypes=(("Memory files", "*.mem"), ("All files", "*.*")),
        )

        if not path:
            return

        self._mem_file_path = path

        try:
            # Clean before load
            self.cpu.dmem[:] = [0] * len(self.cpu.dmem)

            count = self.cpu.load_mem_file(path)
            self.log.append(f"Loaded {Path(path).name} ({count} values)")
            self._refresh()

        except CPUError as error:
            self.log.append(f"LOAD ERROR: {error}")
            messagebox.showerror("Could not load memory file", str(error), parent=self)

    def _close(self) -> None:
        self.destroy()
