"""
Shared instruction-set tables for the ADCR2R8 architecture.

Both the assembler (src/assembler/parser.py) and the CPU core
(src/cpu/cpu.py) import from here, so the opcode/mode numbers can never
drift out of sync between the two independently-built halves of the
project.
"""

# Data instructions:
# [15:12] opcode  [11:8] Rd  [7:4] Rs  [3:0] mode

DATA_OPCODES = {
    "MOV": 0x0,  # Rd <- Rs
    "LOAD": 0x1,  # Rd <- dmem[...]
    "STORE": 0x2,  # dmem[...] <- Rd
    "ADD": 0x3,  # Rd <- Rd + Rs
    "ADC": 0x4,  # Rd <- Rd + Rs + CF
    "SUB": 0x5,  # Rd <- Rd - Rs
    "SBB": 0x6,  # Rd <- Rd - Rs - CF
    "MUL": 0x7,  # Rd:Rd+1 <- Rd * Rs
    "DIV": 0x8,  # Rd <- Rd / Rs
    "INC": 0x9,  # Rd <- Rd + 1
    "DEC": 0xA,  # Rd <- Rd - 1
    "CMP": 0xB,  # flags <- Rd - Rs
    "AND": 0xC,  # Rd <- Rd and Rs
    "OR": 0xD,  # Rd <- Rd or Rs
    "XOR": 0xE,  # Rd <- Rd xor Rs
    "NOT": 0xF,  # Rd <- not Rd
}

# Single-operand instructions: Rd only, Rs field unused, always mode 0
SINGLE_OPERAND = {"INC", "DEC", "NOT"}

# Instructions where operand order is "memory, register" instead of the
# usual "register, memory" (STORE [addr]/[Rs], Rd)
REVERSED_OPERANDS = {"STORE"}

# Addressing modes
MODE_REGISTER = 0  # ADD R1, R2
MODE_IMMEDIATE = 1  # MOV R5, #100
MODE_DIRECT = 2  # LOAD R3, [0x100]
MODE_INDIRECT = 3  # LOAD R3, [R2]

# Jumps: [15:12] opcode  [11:0] address  (always 1 word)
JUMP_OPCODES = {
    "JMP": 0x0,
    "JZ": 0x1,
    "JNZ": 0x2,
    "JC": 0x3,
    "JNC": 0x4,
    "JS": 0x5,
    "JNS": 0x6,
    "HALT": 0x7,
}

# Misc
WORD_MASK = 0xFFFF
ADDR12_MASK = 0xFFF
NUM_REGISTERS = 16
IMEM_SIZE = 4096
DMEM_SIZE = 4096

ARRAY_A_BASE = 0x100
ARRAY_B_BASE = 0x200
MAX_RESULT_ADDR = 0x200
CONV_RESULT_LOW_ADDR = 0x300
CONV_RESULT_HIGH_ADDR = 0x301
