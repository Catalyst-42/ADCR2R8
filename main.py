"""
main.py — entry point.

Usage:
    python main.py                            # launch empty GUI
    python main.py src/programs/find_max.asm  # assemble + load + launch GUI
"""

import sys

from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU
from src.gui.app import run as run_gui


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    cpu = CPU()
    if argv:
        asm_path = argv[0]
        words = assemble_file(asm_path)
        cpu.load_program(words)
        print(f"Loaded {asm_path}")

    run_gui(cpu)


if __name__ == "__main__":
    main()
