"""
test_parser.py — sanity checks for src.assembler.parser.

Run with:  python -m pytest tests/  (from the project root)
"""

import sys
from pathlib import Path

# Allow running the tests without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.assembler.parser import assemble_file, assemble_source
from src.assembler.errors import AsmError

PROGRAMS_DIR = Path(__file__).resolve().parents[1] / "src" / "programs"


def test_spec_worked_examples():
    # ADD R1, R2 -> 0x3120
    assert assemble_source("ADD R1, R2", mem_size=None) == [0x3120]

    # MOV R5, #100 -> 0x0501, 0x0064
    assert assemble_source("MOV R5, #100", mem_size=None) == [0x0501, 0x0064]

    # STORE [0x100], R3 -> 0x2302, 0x0100
    assert assemble_source("STORE [0x100], R3", mem_size=None) == [0x2302, 0x0100]


def test_labels_and_jumps():
    src = """
        MOV R0, #0
loop:   INC R0
        CMP R0, #3
        JNZ loop
        HALT
    """
    words = assemble_source(src, mem_size=None)
    # MOV R0,#0 (2) + INC R0 (1) + CMP R0,#3 (2) + JNZ loop (2) + HALT (1) = 8
    assert len(words) == 8
    assert words[5:] == [0x002F, 2, 0x007F]


def test_undefined_label_raises():
    try:
        assemble_source("JMP nowhere", mem_size=None)
    except AsmError:
        pass
    else:
        raise AssertionError("expected AsmError for undefined label")


def test_find_max_assembles_cleanly():
    words = assemble_file(str(PROGRAMS_DIR / "find_max.asm"), mem_size=None)
    assert len(words) > 0


def test_convolution_assembles_cleanly():
    words = assemble_file(str(PROGRAMS_DIR / "convolution.asm"), mem_size=None)
    assert len(words) > 0


def test_padding_to_mem_size():
    words = assemble_source("HALT", mem_size=4096)
    assert len(words) == 4096
    assert words[0] == 0x007F
    assert all(w == 0 for w in words[1:])


if __name__ == "__main__":
    test_spec_worked_examples()
    test_labels_and_jumps()
    test_undefined_label_raises()
    test_find_max_assembles_cleanly()
    test_convolution_assembles_cleanly()
    test_padding_to_mem_size()
    print("All tests passed.")

# Standard-library discovery, also retaining pytest-compatible functions.
def load_tests(loader, tests, pattern):
    import unittest
    return unittest.TestSuite(unittest.FunctionTestCase(value) for name, value in globals().items()
                              if name.startswith('test_') and callable(value))
