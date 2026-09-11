"""
cpu.py — CPU core for the ADCR2R8 architecture. (NOT YET IMPLEMENTED)

This is a placeholder so the project structure is in place. The interface
below is fixed by the spec — fill in the bodies without changing the
public method/attribute names, so the GUI (src/gui/app.py) and the
assembler integration in main.py keep working unmodified.

Expected public interface:

    cpu.imem            # list[int], length constants.IMEM_SIZE
    cpu.dmem            # list[int], length constants.DMEM_SIZE
    cpu.regs            # list[int], length 16, R0..R15
    cpu.pc              # int, program counter (word address)
    cpu.ir               # int, current instruction register
    cpu.ZF, cpu.CF, cpu.SF   # bool flags
    cpu.halted           # bool, True after HALT executes

    cpu.step()           # execute a single instruction
    cpu.run(limit=10000)  # execute until HALT or `limit` steps reached
    cpu.reset()           # reset regs/flags/pc, keep imem/dmem contents

Decoding notes (see docs/report for the full opcode tables):
    - Data instructions: opcode[15:12], Rd[11:8], Rs[7:4], mode[3:0]
        mode 0 / 3 -> 1 word   (register / indirect register)
        mode 1 / 2 -> 2 words  (immediate / direct — second word follows)
    - Jumps: opcode[15:12], address[11:0], always 1 word.
    - MUL: Rd:Rd+1 <- Rd * Rs (low word in Rd, high word in Rd+1); CF unchanged.
    - Division by zero must raise an exception.
"""

from src.cpu.constants import DMEM_SIZE, IMEM_SIZE, NUM_REGISTERS


class CPU:
    def __init__(self):
        self.imem: list[int] = [0] * IMEM_SIZE
        self.dmem: list[int] = [0] * DMEM_SIZE
        self.regs: list[int] = [0] * NUM_REGISTERS
        self.pc: int = 0
        self.ir: int = 0
        self.ZF = False
        self.CF = False
        self.SF = False
        self.halted = False

    def reset(self):
        self.regs = [0] * NUM_REGISTERS
        self.pc = 0
        self.ir = 0
        self.ZF = self.CF = self.SF = False
        self.halted = False
        # imem / dmem are intentionally left untouched by reset()

    def load_program(self, words: list[int]):
        """Load an already-assembled word list into imem (see
        src.assembler.parser.assemble_file)."""
        for i, w in enumerate(words):
            self.imem[i] = w

    def step(self):
        raise NotImplementedError("CPU.step() is not implemented yet")

    def run(self, limit: int = 10000):
        steps = 0
        while not self.halted and steps < limit:
            self.step()
            steps += 1
