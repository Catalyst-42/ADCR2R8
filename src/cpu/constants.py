# Format of instruction

# 0000 0000 0000 0000
#    │    │    │    │
#    │    │    │    └── Mode    [3:0]
#    │    │    └─────── Rs      [7:4]
#    │    └──────────── Rd      [11:8]
#    └───────────────── Opcode  [15:12]

DATA_OPCODES = {
    "MOV": 0x0,
    "LOAD": 0x1,
    "STORE": 0x2,
    "ADD": 0x3,
    "ADC": 0x4,
    "SUB": 0x5,
    "SBB": 0x6,
    "MUL": 0x7,
    "DIV": 0x8,
    "INC": 0x9,
    "DEC": 0xA,
    "CMP": 0xB,
    "AND": 0xC,
    "OR": 0xD,
    "XOR": 0xE,
    "NOT": 0xF,
}

SINGLE_OPERAND = {"INC", "DEC", "NOT"}
REVERSED_OPERANDS = {"STORE"}

# Addressing modes
MODE_REGISTER = 0
MODE_IMMEDIATE = 1
MODE_DIRECT = 2
MODE_INDIRECT = 3

# Jumps
CONTROL_TAG = 0x000F
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
