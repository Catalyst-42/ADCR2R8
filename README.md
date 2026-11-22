# ADCR2R8
A 16-bit Harvard architecture CPU emulator written in Python with a Tkinter GUI. Includes an assembler, parser and example programs.

![Emulator](<img/ADCR2R8 - Emulator.png>)

## Architecture
Harvard architecture with separate instruction and data memory. Both memories are arrays of 4096 16-bit words. Instructions have variable length from one to two words.

Registers:
- PC - Program counter
- IR - Instruction register
- ZF - Zero flag
- CF - Carry flag
- SF - Sign flag

Also CPU provides 16 general purpose registers.

## Command format
Every instruction starts with one 16-bit word.

```text
0000 0000 0000 0000
   │    │    │   │
   │    │    │   └─── Addressing mode  [3:0]
   │    │    └─────── Source           [7:4]
   │    └──────────── Destination      [11:8]
   └───────────────── Opcode           [15:12]
```

## Addressing modes
```text
0   Register           ADD R1, R2
1   Immediate          MOV R5, #100
2   Direct             LOAD R3, [0x100]
3   Indirect register  LOAD R3, [R2]
```

- Mode 0 - Register, second operand is taken directly from the source
- Mode 1 - Immediate, second word is a raw number
- Mode 2 - Direct, second word is a memory address
- Mode 3 - Indirect register, source register holds a memory address

## Opcodes
Table shows explicit input and output operands for each instruction.

|  Opcode  |  Hex  |     Format      |             Operation              |
| -------- | ----- | --------------- | ---------------------------------- |
| `MOV`    | `0x0` | `<out>, <in>`   | `<out>        = <in>`              |
| `LOAD`   | `0x1` | `<out>, [addr]` | `<out>        = memory[addr]`      |
| `STORE`  | `0x2` | `[addr], <in>`  | `memory[addr] = <in>`              |
| `ADD`    | `0x3` | `<out>, <in>`   | `<out>        = <out> + <in>`      |
| `ADC`    | `0x4` | `<out>, <in>`   | `<out>        = <out> + <in> + CF` |
| `SUB`    | `0x5` | `<out>, <in>`   | `<out>        = <out> - <in>`      |
| `SBB`    | `0x6` | `<out>, <in>`   | `<out>        = <out> - <in> - CF` |
| `MUL`    | `0x7` | `<out>, <in>`   | `<out:out+1>  = <out> * <in>`      |
| `DIV`    | `0x8` | `<out>, <in>`   | `<out>        = <out> / <in>`      |
| `INC`    | `0x9` | `<out>`         | `<out>        = <out> + 1`         |
| `DEC`    | `0xA` | `<out>`         | `<out>        = <out> - 1`         |
| `CMP`    | `0xB` | `<in1>, <in2>`  | `flags        = <in1> - <in2>`     |
| `AND`    | `0xC` | `<out>, <in>`   | `<out>        = <out> & <in>`      |
| `OR`     | `0xD` | `<out>, <in>`   | `<out>        = <out> \| <in>`     |
| `XOR`    | `0xE` | `<out>, <in>`   | `<out>        = <out> ^ <in>`      |
| `NOT`    | `0xF` | `<out>`         | `<out>        = ~ <out>`           |

## Jump conditions
Instruction threated as jump command when mode is set to `0xF`. There's table of jump types

| Instruction |  Hex  | Condition |
| ----------- | ----- | --------- |
| JMP         | `0x0` |           |
| JZ          | `0x1` | `ZF = 1`  |
| JNZ         | `0x2` | `ZF = 0`  |
| JC          | `0x3` | `CF = 1`  |
| JNC         | `0x4` | `CF = 0`  |
| JS          | `0x5` | `SF = 1`  |
| JNS         | `0x6` | `SF = 0`  |
| HALT        | `0x7` |           |

## Encoding example
Let's encode the instruction `ADC R2, R8`.

```text
opcode      = 0x4  (ADC from table)
destination = 2    (Register R2)
source      = 8    (Register R8)
mode        = 0    (Register addressing)

word = 0x4000 | 0x0200 | 0x0080 | 0x0000
word = 0x4280
```

## Usage
To run GUI simply use `main.py` file: 

```python
python3 main.py
```

It may require additional Tkinter installation depending on OS type. Load `.asm` file of program and additional `.mem` file with working data for program. You can run it until halt or step by step with buttons.
