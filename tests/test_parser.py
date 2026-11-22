import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.assembler.errors import AsmError
from src.assembler.parser import assemble_source


def test_basic_assembly_operations():
    add_asm = "ADD R1, R2"
    add_expected = [0x3120]

    move_asm = "MOV R5, #100"
    move_expected = [0x0501, 0x0064]

    store_asm = "STORE [0x100], R3"
    store_expected = [0x2302, 0x0100]

    assert assemble_source(add_asm, mem_size=None) == add_expected
    assert assemble_source(move_asm, mem_size=None) == move_expected
    assert assemble_source(store_asm, mem_size=None) == store_expected


def test_label_handling():
    program = """
        MOV R0, #0
        loop:
            INC R0
            CMP R0, #3
            JNZ loop
            HALT
    """

    word_count = 8
    jump_pos = 5
    jump_data = [0x002F, 2, 0x007F]

    result = assemble_source(program, mem_size=None)
    assert len(result) == word_count
    assert result[jump_pos:] == jump_data


def test_error_handling():
    undef_asm = "JMP nowhere"

    try:
        assemble_source(undef_asm, mem_size=None)
        assert False, "Expected AsmError"
    except AsmError:
        pass


def test_memory_padding():
    instr = "HALT"
    size = 4096
    first_word = 0x007F
    padding = 0

    result = assemble_source(instr, mem_size=size)
    assert len(result) == size
    assert result[0] == first_word
    assert all(w == padding for w in result[1:])
