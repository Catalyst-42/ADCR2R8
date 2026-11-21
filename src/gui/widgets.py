import tkinter as tk
from collections.abc import Sequence
from tkinter import messagebox, ttk

from src.gui.utils import to_hex


class RegisterTable(ttk.Frame):
    def __init__(self, master: tk.Misc, **kwargs) -> None:
        """Init and setup layout"""
        super().__init__(master, **kwargs)

        self.tree = ttk.Treeview(
            self,
            columns=("register", "value"),
            show="headings",
            height=16,
            selectmode="browse",
        )

        # Headers
        self.tree.heading("register", text="Register")
        self.tree.heading("value", text="Value")

        # Columns
        self.tree.column("register", width=85, anchor="w", stretch=False)
        self.tree.column("value", width=105, anchor="e", stretch=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        for number in range(16):
            self.tree.insert(
                "", "end", iid=str(number), values=(f"R{number}", to_hex(0))
            )

    def refresh(self, registers: Sequence[int]) -> None:
        """Refresh values with the given one"""
        for number, value in enumerate(registers[:16]):
            self.tree.item(str(number), values=(f"R{number}", to_hex(value)))


class MemoryView(ttk.Frame):
    def __init__(self, master: tk.Misc, cpu=None, **kwargs) -> None:
        """Init and setup layout"""
        super().__init__(master, **kwargs)

        self.cpu = cpu
        self.tree = ttk.Treeview(
            self,
            columns=("address", "hex", "dec", "char"),
            show="headings",
            height=16,  # Make it taller
            selectmode="browse",
        )

        # Headers
        self.tree.heading("address", text="Address")
        self.tree.heading("hex", text="Hex")
        self.tree.heading("dec", text="Decimal")
        self.tree.heading("char", text="Char")

        # Columns
        self.tree.column("address", width=70, anchor="e")
        self.tree.column("hex", width=70, anchor="e")
        self.tree.column("dec", width=70, anchor="e")
        self.tree.column("char", width=50, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Memory value editing
        self.tree.bind("<Double-1>", self.edit)
        for address in range(4096):
            self.tree.insert(
                "",
                "end",
                iid=str(address),
                values=(to_hex(address, 3), "0x0000", "0", ""),
            )

    def edit(self, event):
        """Edit one memory slot"""
        if not self.cpu:
            return

        item = self.tree.selection()
        if not item:
            return

        address = int(item[0])
        current_value = self.cpu.dmem[address]

        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Memory {to_hex(address, 3)}")
        dialog.geometry("300x150")
        dialog.resizable(False, False)

        # Input frame
        input_frame = ttk.Frame(dialog, padding="10")
        input_frame.pack(fill="both", expand=True)

        ttk.Label(input_frame, text=f"Address: {to_hex(address, 3)}").pack(
            anchor="w", pady=(0, 5)
        )
        ttk.Label(
            input_frame,
            text=f"Current: 0x{current_value:04X} | {current_value} | {chr(current_value)}",
        ).pack(anchor="w", pady=(0, 10))

        # Entry for new value
        value_var = tk.StringVar(value=f"0x{current_value:04X}")
        entry = ttk.Entry(input_frame, textvariable=value_var, width=20)
        entry.pack(pady=(0, 10))
        entry.select_range(0, tk.END)
        entry.focus()

        def save_value():
            try:
                input_value = value_var.get().strip()
                if input_value.startswith("0x") or input_value.startswith("0X"):
                    # Parse as hex
                    new_value = int(input_value, 16)
                else:
                    # Parse as decimal
                    new_value = int(input_value)

                new_value = max(0, min(new_value, 0xFFFF))
                self.cpu.dmem[address] = new_value

                # Refresh
                hex_value = to_hex(new_value)
                decimal_value = str(new_value)
                char_value = chr(new_value)

                self.tree.item(
                    str(address),
                    values=(to_hex(address, 3), hex_value, decimal_value, char_value),
                )
                dialog.destroy()

            except ValueError:
                messagebox.showerror(
                    "Invalid Value",
                    "Please enter a valid hexadecimal or decimal number (0-65535)",
                    parent=dialog,
                )

        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="Save", command=save_value).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side="right"
        )

        # Save on enter
        entry.bind("<Return>", lambda e: save_value())

    def refresh(
        self, memory: Sequence[int], addresses: Sequence[int] | None = None
    ) -> None:
        """Refresh values with the given one"""
        selected = range(min(len(memory), 4096)) if addresses is None else addresses

        if not selected:
            return

        for address in selected:
            if 0 <= address < len(memory) and address < 4096:
                value = memory[address]
                hex_value = to_hex(value)
                decimal_value = str(value)
                char_value = chr(value)
                address_str = to_hex(address, 3)

                self.tree.item(
                    str(address),
                    values=(address_str, hex_value, decimal_value, char_value),
                )


class ExecutionLog(ttk.Frame):
    def __init__(self, master: tk.Misc, **kwargs) -> None:
        """Init and setup layout"""
        super().__init__(master, **kwargs)

        # Text
        self.text = tk.Text(self, height=8, width=42, wrap="none", state="disabled")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)

        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def append(self, message: str) -> None:
        """Adds log message"""
        self.text.configure(state="normal")
        self.text.insert("end", message.rstrip() + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")


class ProgramCommands(ttk.Frame):
    def __init__(self, master: tk.Misc, cpu=None, **kwargs) -> None:
        """Init and setup layout"""
        super().__init__(master, **kwargs)

        self.cpu = cpu
        self.tree = ttk.Treeview(
            self,
            columns=("address", "code", "instruction"),
            show="headings",
            height=20,
            selectmode="browse",
        )

        # Headings
        self.tree.heading("address", text="Address")
        self.tree.heading("code", text="Code")
        self.tree.heading("instruction", text="Instruction")

        # Columns
        self.tree.column("address", width=70, anchor="e", stretch=False)
        self.tree.column("code", width=80, anchor="e", stretch=False)
        self.tree.column("instruction", width=140, anchor="w", stretch=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def refresh(self, program_memory: Sequence[int], cpu=None) -> None:
        """Refresh values with the given one"""
        self.cpu = cpu

        for item in self.tree.get_children():
            self.tree.delete(item)

        for address, instruction in enumerate(program_memory):
            if instruction == 0:
                continue

            address_str = to_hex(address, 3)
            code_str = to_hex(instruction)

            if self.cpu:
                try:
                    decoded = self.cpu.decode(address)
                    instruction_str = decoded.assembly
                except:
                    instruction_str = code_str
            else:
                instruction_str = code_str

            self.tree.insert(
                "",
                "end",
                iid=str(address),
                values=(address_str, code_str, instruction_str),
            )
