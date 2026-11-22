import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.assembler.parser import assemble_source
from src.cpu.cpu import CPU, CPUError


def create_cpu(program):
    cpu = CPU()
    cpu.load_program(assemble_source(program))
    return cpu


def test_basic_execution():
    program = [0x0101, 7, 0x0201, 5, 0x0310, 0x3320, 0x007F]
    steps = 4
    reg3_val = 12
    first_instr = "MOV R1, #0x0007"
    pc_after_step = 2
    ir_after_step = 0x0101

    cpu = CPU()
    cpu.load_program(program)

    instruction = cpu.step()
    assert instruction.assembly == first_instr
    assert (cpu.pc, cpu.ir) == (pc_after_step, ir_after_step)

    steps_result = cpu.run()
    assert steps_result == steps
    assert cpu.regs[3] == reg3_val

    state_before = cpu.snapshot()
    assert cpu.step() is None
    assert cpu.run() == 0
    assert cpu.snapshot() == state_before


def test_memory_addressing():
    asm = """
        MOV R0, #10
        MOV R1, R0
        STORE [100], R1
        MOV R2, #100
        LOAD R3, [R2]
        ADD R3, [100]
        ADD R3, [R2]
        STORE [R2], R3
        LOAD R4, [100]
        HALT
    """
    reg4_val = 30
    mem100_val = 30

    cpu = create_cpu(asm)
    original_imem = cpu.imem.copy()

    cpu.run()

    assert cpu.regs[4] == reg4_val
    assert cpu.dmem[100] == mem100_val
    assert cpu.imem == original_imem


def test_arithmetic():
    add_asm = "ADD R0, R1"
    add_a = 65535
    add_b = 1
    add_carry = False
    add_result = 0
    add_cf = True

    adc_asm = "ADC R0, R1"
    adc_a = 65535
    adc_b = 0
    adc_carry = True
    adc_result = 0
    adc_cf = True

    sub_asm = "SUB R0, R1"
    sub_a = 0
    sub_b = 1
    sub_carry = False
    sub_result = 65535
    sub_cf = True

    div_asm = "DIV R0, R1"
    div_a = 203
    div_b = 4
    div_carry = True
    div_result = 50
    div_cf = False

    and_asm = "AND R0, R1"
    and_a = 0xAAAA
    and_b = 0x5555
    and_carry = True
    and_result = 0
    and_cf = False

    cases = [
        (add_asm, add_a, add_b, add_carry, add_result, add_cf),
        (adc_asm, adc_a, adc_b, adc_carry, adc_result, adc_cf),
        (sub_asm, sub_a, sub_b, sub_carry, sub_result, sub_cf),
        (div_asm, div_a, div_b, div_carry, div_result, div_cf),
        (and_asm, and_a, and_b, and_carry, and_result, and_cf),
    ]

    for asm, a, b, carry, result, cf in cases:
        cpu = create_cpu(asm)
        cpu.regs[:2] = [a, b]
        cpu.CF = carry
        cpu.step()

        expected_sf = bool(result & 0x8000)
        expected_zf = result == 0

        actual = (cpu.regs[0], cpu.CF, cpu.ZF, cpu.SF)
        expected = (result, cf, expected_zf, expected_sf)

        assert actual == expected, f"Expected {expected}, got {actual}"


def test_unary():
    asm = """
        INC R0
        DEC R0
        NOT R0
        CMP R0, #0
    """
    initial_val = 65535
    ops = ["INC", "DEC", "NOT", "CMP"]
    results = [0, 65535, 0, 0]
    flags = [(True, True), (True, True), (True, False), (True, None)]

    cpu = create_cpu(asm)
    cpu.regs[0] = initial_val

    for i, (op, val, flag_data) in enumerate(zip(ops, results, flags)):
        cpu.step()

        if op == "CMP":
            assert cpu.regs[0] == val
            assert cpu.ZF == flag_data[0]
        else:
            assert cpu.regs[0] == val
            if op in ["INC", "DEC"]:
                assert (cpu.SF if op == "DEC" else cpu.ZF, cpu.CF) == flag_data
            elif op == "NOT":
                assert (cpu.ZF, cpu.CF) == flag_data


def test_branch():
    jz_taken_asm = """
        JZ 4
        MOV R0, #1
        HALT
    """
    jz_not_asm = """
        JZ 4
        MOV R0, #1
        HALT
    """
    jc_taken_asm = """
        JC 4
        MOV R0, #1
        HALT
    """
    jmp_asm = "JMP 0"

    # Test JZ taken
    cpu = create_cpu(jz_taken_asm)
    cpu.ZF = True
    cpu.step()
    assert cpu.pc == 4, f"JZ taken: expected PC=4, got {cpu.pc}"

    # Test JZ not taken
    cpu = create_cpu(jz_not_asm)
    cpu.ZF = False
    cpu.step()
    assert cpu.pc == 2, f"JZ not taken: expected PC=2, got {cpu.pc}"

    # Test JC taken
    cpu = create_cpu(jc_taken_asm)
    cpu.CF = True
    cpu.step()
    assert cpu.pc == 4, f"JC taken: expected PC=4, got {cpu.pc}"

    # Test JMP
    cpu = create_cpu(jmp_asm)
    steps = cpu.run(20)
    assert cpu.pc == 0
    assert steps == 20
    assert not cpu.halted


def test_boundary():
    violation_pc = 4095
    violation_mem = 0x0001
    valid_mem = 0x007F
    invalid_limits = [-1, 1.5, True]

    # Test boundary violation
    cpu = CPU()
    cpu.pc = violation_pc
    cpu.imem[4095] = violation_mem
    state_before = cpu.snapshot()

    try:
        cpu.step()
        assert False, "Expected CPUError for boundary violation"
    except CPUError:
        assert cpu.snapshot() == state_before

    # Test valid boundary
    cpu = CPU()
    cpu.pc = 4095
    cpu.imem[4095] = valid_mem
    cpu.step()
    assert cpu.halted

    # Test invalid limits
    for limit in invalid_limits:
        try:
            cpu.run(limit)
            assert False, f"Expected CPUError for limit {limit}"
        except CPUError:
            pass

    assert cpu.run(0) == 0
