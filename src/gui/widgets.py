"""Reusable tkinter widgets used by the ADCR2R8 debugger GUI."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk

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
    """Scrollable hexadecimal view of a 4096-word memory."""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(
            self,
            columns=("address", "value"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("address", text="Address")
        self.tree.heading("value", text="Value")
        self.tree.column("address", width=100, anchor="w", stretch=False)
        self.tree.column("value", width=110, anchor="e", stretch=True)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        for address in range(4096):
            self.tree.insert(
                "", "end", iid=str(address), values=(to_hex(address, 3), to_hex(0))
            )

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
                self.tree.item(
                    str(address),
                    values=(to_hex(address, 3), to_hex(memory[address])),
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
