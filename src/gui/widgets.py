"""Reusable tkinter widgets used by the ADCR2R8 debugger GUI."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk, messagebox

from src.gui.formatting import to_hex


class RegisterTable(ttk.Frame):
    """A two-column table showing the sixteen CPU registers."""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(
            self,
            columns=("register", "value"),
            show="headings",
            height=16,
            selectmode="browse",
        )
        self.tree.heading("register", text="Register")
        self.tree.heading("value", text="Value")
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
        """Update register values without replacing the table rows."""
        for number, value in enumerate(registers[:16]):
            self.tree.item(str(number), values=(f"R{number}", to_hex(value)))


class MemoryView(ttk.Frame):
    """Scrollable hexadecimal view of a 4096-word memory with editing capabilities."""

    def __init__(self, master: tk.Misc, cpu=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.cpu = cpu
        self.tree = ttk.Treeview(
            self,
            columns=("address", "hex", "dec", "char"),
            show="headings",
            height=16,  # Make it taller
            selectmode="browse",
        )
        self.tree.heading("address", text="Address")
        self.tree.heading("hex", text="Hex")
        self.tree.heading("dec", text="Decimal")
        self.tree.heading("char", text="Char")
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

        # Bind double-click for editing
        self.tree.bind("<Double-1>", self._on_double_click)

        for address in range(4096):
            self.tree.insert(
                "", "end", iid=str(address), values=(to_hex(address, 3), "0x0000", "0", "")
            )

    def _on_double_click(self, event):
        """Handle double-click to edit memory cell."""
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
        
        ttk.Label(input_frame, text=f"Address: {to_hex(address, 3)}").pack(anchor="w", pady=(0, 5))
        ttk.Label(input_frame, text=f"Current: 0x{current_value:04X} | {current_value} | {self._get_character_representation(current_value)}").pack(anchor="w", pady=(0, 10))
        
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
                
                # Clamp to 16-bit unsigned
                new_value = max(0, min(new_value, 0xFFFF))
                
                # Update CPU memory
                self.cpu.dmem[address] = new_value
                
                # Refresh display - update only the edited address
                hex_value = to_hex(new_value)
                decimal_value = str(new_value)
                char_value = self._get_character_representation(new_value)
                self.tree.item(
                    str(address),
                    values=(to_hex(address, 3), hex_value, decimal_value, char_value),
                )
                
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Value", "Please enter a valid hexadecimal or decimal number (0-65535)", parent=dialog)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Save", command=save_value).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right")
        
        # Bind Enter key
        entry.bind("<Return>", lambda e: save_value())

    def _get_character_representation(self, value: int) -> str:
        """Get character representation for a memory value."""
        if 32 <= value <= 126:  # Printable ASCII range
            return chr(value)
        else:
            return ""  # Empty for non-printable characters

    def refresh(
        self, memory: Sequence[int], addresses: Sequence[int] | None = None
    ) -> None:
        """Refresh rows from a detached CPU memory snapshot.

        ``addresses`` can limit the update to changed cells during execution;
        omitting it refreshes the complete memory view.
        """
        selected = range(min(len(memory), 4096)) if addresses is None else addresses
        for address in selected:
            if 0 <= address < len(memory) and address < 4096:
                hex_value = to_hex(memory[address])
                decimal_value = str(memory[address])
                char_value = self._get_character_representation(memory[address])
                self.tree.item(
                    str(address),
                    values=(to_hex(address, 3), hex_value, decimal_value, char_value),
                )

    def show_address(self, address: int) -> None:
        """Select and reveal an address, useful after a STORE instruction."""
        if 0 <= address < 4096:
            item = str(address)
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.tree.see(item)


class ExecutionLog(ttk.Frame):
    """Read-only scrolling text area for execution and error messages."""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.text = tk.Text(self, height=8, width=42, wrap="none", state="disabled")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def append(self, message: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", message.rstrip() + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class HexView(ttk.Frame):
    """Small read-only text view for machine-code or result output."""

    def __init__(self, master: tk.Misc, height: int = 8, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.text = tk.Text(
            self, height=height, width=34, wrap="none", state="disabled"
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def set_lines(self, lines: Sequence[str]) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")
