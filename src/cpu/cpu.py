"""Independent 16-bit Harvard CPU. Binary/API contract: docs/core.md."""
from dataclasses import dataclass
from src.cpu.constants import (CONTROL_TAG, DATA_OPCODES, DMEM_SIZE, IMEM_SIZE,
                               JUMP_OPCODES, NUM_REGISTERS, WORD_MASK)


class CPUError(ValueError):
    """Invalid instruction, operand or address; the step is not committed."""


@dataclass(frozen=True)
class DecodedInstruction:
    address: int
    word: int
    mnemonic: str
    length: int
    rd: int = 0
    rs: int = 0
    mode: int = 0
    operand: int | None = None

    @property
    def assembly(self):
        if self.mnemonic == 'HALT':
            return 'HALT'
        if self.mnemonic in JUMP_OPCODES:
            return f'{self.mnemonic} 0x{self.operand:03X}'
        if self.mnemonic in {'INC', 'DEC', 'NOT'}:
            return f'{self.mnemonic} R{self.rd}'
        source = (f'R{self.rs}' if self.mode == 0 else
                  f'#0x{self.operand:04X}' if self.mode == 1 else
                  f'[0x{self.operand:03X}]' if self.mode == 2 else
                  f'[R{self.rs}]')
        operands = f'{source}, R{self.rd}' if self.mnemonic == 'STORE' else f'R{self.rd}, {source}'
        return f'{self.mnemonic} {operands}'


class CPU:
    def __init__(self):
        self.imem = [0] * IMEM_SIZE
        self.dmem = [0] * DMEM_SIZE
        self.regs = [0] * NUM_REGISTERS
        self.reset()

    def reset(self):
        """Reset execution state; retain program and data memory."""
        self.regs[:] = [0] * NUM_REGISTERS
        self.pc = self.ir = 0
        self.ZF = self.CF = self.SF = self.halted = False
        self.last_instruction = None

    @staticmethod
    def _word(value):
        if type(value) is not int or not 0 <= value <= WORD_MASK:
            raise CPUError(f'Expected a 16-bit unsigned integer, got {value!r}')
        return value

    @staticmethod
    def _address(value, size):
        if type(value) is not int or not 0 <= value < size:
            raise CPUError(f'Address {value!r} outside memory of {size} words')
        return value

    def load_program(self, words):
        """Validate, copy, clear unused imem and reset execution (retain dmem)."""
        words = list(words)
        if len(words) > IMEM_SIZE:
            raise CPUError(f'Program exceeds {IMEM_SIZE} words')
        for word in words:
            self._word(word)
        self.imem[:] = words + [0] * (IMEM_SIZE - len(words))
        self.reset()

    def load_data(self, address, values):
        """Atomically initialize data memory for GUI input and test arrays."""
        self._address(address, DMEM_SIZE)
        values = list(values)
        if address + len(values) > DMEM_SIZE:
            raise CPUError('Data exceeds memory')
        for value in values:
            self._word(value)
        self.dmem[address:address + len(values)] = values

    def snapshot(self):
        """Detached state for GUI; editing it cannot alter the CPU."""
        return dict(regs=self.regs.copy(), imem=self.imem.copy(), dmem=self.dmem.copy(),
                    pc=self.pc, ir=self.ir, ZF=self.ZF, CF=self.CF, SF=self.SF,
                    halted=self.halted, last_instruction=self.last_instruction)

    def decode(self, address=None):
        """Decode without executing. Addresses and lengths are in 16-bit words."""
        address = self.pc if address is None else address
        word = self._word(self.imem[self._address(address, IMEM_SIZE)])
        mode = word & 15
        rd, rs = (word >> 8) & 15, (word >> 4) & 15
        if mode == CONTROL_TAG:
            if word >> 8 or rs not in JUMP_OPCODES.values():
                raise CPUError(f'Invalid control instruction 0x{word:04X}')
            name = next(n for n, code in JUMP_OPCODES.items() if code == rs)
            length = 1 if name == 'HALT' else 2
        else:
            if mode > 3:
                raise CPUError(f'Invalid addressing mode {mode}')
            name = next(n for n, code in DATA_OPCODES.items() if code == word >> 12)
            if name in {'INC', 'DEC', 'NOT'} and (mode != 0 or rs != 0):
                raise CPUError(f'{name} requires mode 0 and an unused Rs field')
            if name in {'LOAD', 'STORE'} and mode not in {2, 3}:
                raise CPUError(f'{name} requires memory addressing')
            if mode in {1, 2} and rs != 0:
                raise CPUError('Unused Rs field must be zero')
            if name == 'MUL' and rd == NUM_REGISTERS - 1:
                raise CPUError('MUL R15 has no high-result register R16')
            length = 2 if mode in {1, 2} else 1
        operand = None
        if length == 2:
            operand = self._word(self.imem[self._address(address + 1, IMEM_SIZE)])
            if name in JUMP_OPCODES or mode == 2:
                self._address(operand, IMEM_SIZE if name in JUMP_OPCODES else DMEM_SIZE)
        return DecodedInstruction(address, word, name, length, rd, rs, mode, operand)

    def step(self):
        """Execute one instruction; return its decode, or None after HALT.

        Execution faults preserve all state, including PC, IR and flags.
        """
        if self.halted:
            return None
        ins = self.decode()
        name, rd = ins.mnemonic, ins.rd
        next_pc = self.pc + ins.length
        result = high = store_address = None
        zf, cf, sf = self.ZF, self.CF, self.SF
        if name in JUMP_OPCODES:
            conditions = dict(JMP=True, JZ=self.ZF, JNZ=not self.ZF,
                              JC=self.CF, JNC=not self.CF, JS=self.SF, JNS=not self.SF)
            if name != 'HALT' and conditions[name]:
                next_pc = ins.operand
        else:
            a = self._word(self.regs[rd])
            if ins.mode in {2, 3}:
                address = ins.operand if ins.mode == 2 else self.regs[ins.rs]
                self._address(address, DMEM_SIZE)
                b = self._word(self.dmem[address]) if name != 'STORE' else 0
            else:
                b = ins.operand if ins.mode == 1 else self._word(self.regs[ins.rs])
            if name == 'STORE':
                store_address = address
            elif name in {'MOV', 'LOAD'}:
                result = b
            elif name in {'ADD', 'ADC', 'INC'}:
                raw = a + (1 if name == 'INC' else b) + (int(cf) if name == 'ADC' else 0)
                result = raw & WORD_MASK
                cf = raw > WORD_MASK
            elif name in {'SUB', 'SBB', 'CMP', 'DEC'}:
                raw = a - (1 if name == 'DEC' else b) - (int(cf) if name == 'SBB' else 0)
                result = raw & WORD_MASK
                cf = raw < 0
            elif name == 'MUL':
                raw = a * b
                result, high = raw & WORD_MASK, raw >> 16
            elif name == 'DIV':
                if b == 0:
                    raise ZeroDivisionError(f'DIV by zero at PC=0x{self.pc:03X}')
                result, cf = a // b, False
            else:
                result = {'AND': lambda: a & b, 'OR': lambda: a | b,
                          'XOR': lambda: a ^ b, 'NOT': lambda: (~a) & WORD_MASK}[name]()
                cf = False
            if name not in {'MOV', 'LOAD', 'STORE'}:
                zf = (raw == 0) if name == 'MUL' else result == 0
                sf = bool((high if name == 'MUL' else result) & 0x8000)

        # Commit only after every fallible operation has completed.
        if store_address is not None:
            self.dmem[store_address] = a
        if result is not None and name != 'CMP':
            self.regs[rd] = result
        if high is not None:
            self.regs[rd + 1] = high
        self.ZF, self.CF, self.SF = zf, cf, sf
        self.pc, self.ir = next_pc, ins.word
        self.halted = name == 'HALT'
        self.last_instruction = ins
        return ins

    def run(self, limit=10000):
        """Run at most limit instructions; return count. Resume with another call."""
        if type(limit) is not int or limit < 0:
            raise CPUError('Run limit must be a non-negative integer')
        steps = 0
        while not self.halted and steps < limit:
            self.step()
            steps += 1
        return steps
