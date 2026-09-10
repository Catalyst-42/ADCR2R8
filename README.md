# ADCR2R8

## General Information

- Architecture: Harvard (separate imem and dmem)
- Addressability: two-address
- Word size: 16 bits
- General purpose registers: 16 (R0-R15), 16 bits each
- Language: Python
- GUI: tkinter
- Program input: .asm file via parser

## Task

- Task 1: find maximum in an array
- Task 2: convolution of two arrays, 6 elements, unsigned numbers

## Command Format

    [15:12] [11:8] [7:4] [3:0]
    opcode   Rd     Rs    mode

- mode = 0 or 3: command takes 1 word
- mode = 1 or 2: command takes 2 words (second word is number or address)

### Jumps (separate format)

    [15:12] [11:0]
    opcode   address

Always 1 word.

## Opcode Table

| Mnemonic | Code | Action             |
|----------|------|--------------------|
| MOV      | 0x0  | Rd <- Rs           |
| LOAD     | 0x1  | Rd <- dmem[...]    |
| STORE    | 0x2  | dmem[...] <- Rd    |
| ADD      | 0x3  | Rd <- Rd + Rs      |
| ADC      | 0x4  | Rd <- Rd + Rs + CF |
| SUB      | 0x5  | Rd <- Rd - Rs      |
| SBB      | 0x6  | Rd <- Rd - Rs - CF |
| MUL      | 0x7  | Rd:Rd+1 <- Rd * Rs |
| DIV      | 0x8  | Rd <- Rd / Rs      |
| INC      | 0x9  | Rd <- Rd + 1       |
| DEC      | 0xA  | Rd <- Rd - 1       |
| CMP      | 0xB  | flags <- Rd - Rs   |
| AND      | 0xC  | Rd <- Rd and Rs    |
| OR       | 0xD  | Rd <- Rd or Rs     |
| XOR      | 0xE  | Rd <- Rd xor Rs    |
| NOT      | 0xF  | Rd <- not Rd       |

## Jump Table

| Mnemonic | Code | Condition |
|----------|------|-----------|
| JMP      | 0x0  | always    |
| JZ       | 0x1  | ZF=1      |
| JNZ      | 0x2  | ZF=0      |
| JC       | 0x3  | CF=1      |
| JNC      | 0x4  | CF=0      |
| JS       | 0x5  | SF=1      |
| JNS      | 0x6  | SF=0      |
| HALT     | 0x7  | halt      |

## Addressing Modes

| Code | Name                 | Example          |
|------|----------------------|------------------|
| 0    | Register             | ADD R1, R2       |
| 1    | Immediate            | MOV R5, #100     |
| 2    | Direct               | LOAD R3, [0x100] |
| 3    | Indirect register    | LOAD R3, [R2]    |

## Flags

| Flag | = 1 when                      |
|------|-------------------------------|
| ZF   | result = 0                    |
| CF   | carry/borrow from highest bit |
| SF   | highest bit of result = 1     |

## Assembly Syntax

- Comment: ;
- Label: loop:
- Hex: 0x100
- Immediate: #5
- Operand separator: comma

## Memory

- imem: list of numbers, size ~4096
- dmem: list of numbers, size ~4096
- First cell of array holds its size N
- Then N elements

## CPU Interface

cpu.step()          # execute one command
cpu.reset()         # reset
cpu.regs            # list [16]
cpu.imem            # list [N]
cpu.dmem            # list [N]
cpu.pc              # program counter
cpu.ir              # instruction register
cpu.ZF, cpu.CF, cpu.SF

## Encoding Examples

```asm
ADD R1, R2
opcode=3, Rd=1, Rs=2, mode=0
0x3120

MOV R5, #100
word 1: opcode=0, Rd=5, Rs=0, mode=1 -> 0x0501
word 2: 0x0064

STORE [0x100], R3
word 1: opcode=2, Rd=3, Rs=0, mode=2 -> 0x2302
word 2: 0x0100
```

## Work Division

### CPU core

- fields: imem, dmem, regs[16], pc, ir, ZF, CF, SF
- step(), reset()
- decoder via bit shifts
- handle commands of length 1 and 2 words
- update flags after arithmetic
- MUL: Rd = low, Rd+1 = high
- jumps, HALT

### Parser and programs

Parser:

- read .asm
- remove comments and empty lines
- recognize labels
- split into mnemonic and operands
- determine mode by operand
- two passes for labels
- output array of numbers for imem

Programs:

- find maximum in array
- convolution of 6 unsigned (MUL + ADC)

### GUI and report

GUI:

- register table (hex)
- PC, IR (hex + asm), flags
- data memory with scroll
- buttons: Step, Run, Reset, Load
- execution log
- hex output

Report:

- title page, task
- architecture description
- tables (format, codes, modes, registers, flags)
- two programs: numbers + asm
- emulator description
- conclusion

## Dependencies

parser.py -> imem -> cpu.py -> regs/flags -> gui.py

- Parser independent of CPU
- CPU independent of parser
- GUI depends on CPU
