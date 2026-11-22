from collections.abc import Iterable
from dataclasses import dataclass

from src.cpu.constants import (
    CONTROL_TAG,
    DATA_OPCODES,
    DMEM_SIZE,
    IMEM_SIZE,
    JUMP_OPCODES,
    MODE_DIRECT,
    MODE_IMMEDIATE,
    MODE_INDIRECT,
    MODE_REGISTER,
    NUM_REGISTERS,
    SINGLE_OPERAND,
    WORD_MASK,
)

_DATA_MNEMONICS = {code: name for name, code in DATA_OPCODES.items()}
_JUMP_MNEMONICS = {code: name for name, code in JUMP_OPCODES.items()}


class CPUError(ValueError):
    """General CPU error"""


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
    def assembly(self) -> str:
        if self.mnemonic == "HALT":
            return "HALT"

        if self.mnemonic in JUMP_OPCODES:
            return f"{self.mnemonic} 0x{self.operand:03X}"

        if self.mnemonic in SINGLE_OPERAND:
            return f"{self.mnemonic} R{self.rd}"

        if self.mode == MODE_REGISTER:
            source = f"R{self.rs}"

        elif self.mode == MODE_IMMEDIATE:
            source = f"#0x{self.operand:04X}"

        elif self.mode == MODE_DIRECT:
            source = f"[0x{self.operand:03X}]"

        else:
            source = f"[R{self.rs}]"

        operands = f"R{self.rd}, {source}"
        if self.mnemonic == "STORE":
            operands = f"{source}, R{self.rd}"

        return f"{self.mnemonic} {operands}"


class CPU:
    def __init__(self) -> None:
        """Init CPU"""
        self.imem = [0] * IMEM_SIZE
        self.dmem = [0] * DMEM_SIZE
        self.regs = [0] * NUM_REGISTERS

        self.reset()

    def reset(self) -> None:
        """Reset execution state and memory"""
        self.regs[:] = [0] * NUM_REGISTERS
        self.imem[:] = [0] * IMEM_SIZE
        self.dmem[:] = [0] * DMEM_SIZE

        self.pc = self.ir = 0
        self.ZF = self.CF = self.SF = False
        self.halted = False
        self.last_instruction = None

    @staticmethod
    def _word(value: int) -> int:
        """Checks and gathers word"""
        if type(value) is not int or not 0 <= value <= WORD_MASK:
            raise CPUError(f"Expected a 16-bit unsigned integer, got {value!r}")

        return value

    @staticmethod
    def _address(value: int, size: int) -> int:
        """Checks and gathers address"""
        if type(value) is not int or not 0 <= value < size:
            raise CPUError(f"Address {value!r} outside memory of {size} words")

        return value

    def load_program(self, words: Iterable[int]) -> None:
        """Clears CPU and loads program"""
        words = list(words)
        if len(words) > IMEM_SIZE:
            raise CPUError(f"Program exceeds {IMEM_SIZE} words")

        for word in words:
            self._word(word)

        # Rest CPU and memory
        self.imem[:] = words + [0] * (IMEM_SIZE - len(words))
        self.regs[:] = [0] * NUM_REGISTERS
        self.pc = 0
        self.ir = 0
        self.ZF = False
        self.CF = False
        self.SF = False
        self.halted = False
        self.last_instruction = None

    def load_data(self, address: int, values: Iterable[int]) -> None:
        """Validate and load data to memory"""
        self._address(address, DMEM_SIZE)

        values = list(values)
        if address + len(values) > DMEM_SIZE:
            raise CPUError("Data exceeds memory")

        for value in values:
            self._word(value)

        self.dmem[address : address + len(values)] = values

    def snapshot(self):
        """Dump copy of a CPU and memory"""
        return {
            "regs": self.regs.copy(),
            "imem": self.imem.copy(),
            "dmem": self.dmem.copy(),
            "pc": self.pc,
            "ir": self.ir,
            "ZF": self.ZF,
            "CF": self.CF,
            "SF": self.SF,
            "halted": self.halted,
            "last_instruction": self.last_instruction,
        }

    def decode(self, address: int | None = None) -> DecodedInstruction:
        """Decodes instruction by address"""
        address = self.pc if address is None else address
        word = self._word(self.imem[self._address(address, IMEM_SIZE)])
        mode = word & 0xF
        rd, rs = (word >> 8) & 0xF, (word >> 4) & 0xF

        if mode == CONTROL_TAG:
            if word >> 8 or rs not in _JUMP_MNEMONICS:
                raise CPUError(f"Invalid control instruction 0x{word:04X}")

            name = _JUMP_MNEMONICS[rs]
            length = 1 if name == "HALT" else 2

        else:
            if mode not in {MODE_REGISTER, MODE_IMMEDIATE, MODE_DIRECT, MODE_INDIRECT}:
                raise CPUError(f"Invalid addressing mode {mode}")

            name = _DATA_MNEMONICS[word >> 12]

            if name in SINGLE_OPERAND and (mode != MODE_REGISTER or rs != 0):
                raise CPUError(f"{name} requires mode 0 and an unused Rs field")

            if name in {"LOAD", "STORE"} and mode not in {MODE_DIRECT, MODE_INDIRECT}:
                raise CPUError(f"{name} requires memory addressing")

            if mode in {MODE_IMMEDIATE, MODE_DIRECT} and rs != 0:
                raise CPUError("Unused Rs field must be zero")

            if name == "MUL" and rd == NUM_REGISTERS - 1:
                raise CPUError("MUL R15 has no high-result register R16")

            length = 2 if mode in {MODE_IMMEDIATE, MODE_DIRECT} else 1

        operand = None

        if length == 2:
            operand = self._word(self.imem[self._address(address + 1, IMEM_SIZE)])

            if name in JUMP_OPCODES:
                self._address(operand, IMEM_SIZE)

            elif mode == MODE_DIRECT:
                self._address(operand, DMEM_SIZE)

        return DecodedInstruction(address, word, name, length, rd, rs, mode, operand)

    def _memory_address(self, instruction: DecodedInstruction) -> int:
        """Returnds memory address for instruction"""
        if instruction.mode == MODE_DIRECT:
            address = instruction.operand
        else:
            address = self.regs[instruction.rs]

        return self._address(address, DMEM_SIZE)

    def _read_operand(self, instruction: DecodedInstruction) -> int:
        """Returns operand for instruction"""
        if instruction.mode == MODE_REGISTER:
            return self._word(self.regs[instruction.rs])

        if instruction.mode == MODE_IMMEDIATE:
            return instruction.operand

        return self._word(self.dmem[self._memory_address(instruction)])

    def step(self) -> DecodedInstruction | None:
        """Executes one instruction"""
        if self.halted:
            return None

        ins = self.decode()
        name = ins.mnemonic
        rd = ins.rd
        next_pc = self.pc + ins.length
        result = None
        high = None
        store_address = None
        zf = self.ZF
        cf = self.CF
        sf = self.SF

        if name in JUMP_OPCODES:
            conditions = {
                "JMP": True,
                "JZ": self.ZF,
                "JNZ": not self.ZF,
                "JC": self.CF,
                "JNC": not self.CF,
                "JS": self.SF,
                "JNS": not self.SF,
                "HALT": False,
            }

            if conditions[name]:
                next_pc = ins.operand

        elif name == "STORE":
            store_address = self._memory_address(ins)
            store_value = self._word(self.regs[rd])

        elif name in {"MOV", "LOAD"}:
            result = self._read_operand(ins)

        else:
            a = self._word(self.regs[rd])
            b = None if name in SINGLE_OPERAND else self._read_operand(ins)

            if name in {"ADD", "ADC", "INC"}:
                raw = a + (1 if name == "INC" else b)

                if name == "ADC":
                    raw += int(cf)

                result = raw & WORD_MASK
                cf = raw > WORD_MASK

            elif name in {"SUB", "SBB", "CMP", "DEC"}:
                raw = a - (1 if name == "DEC" else b)

                if name == "SBB":
                    raw -= int(cf)

                result = raw & WORD_MASK
                cf = raw < 0

            elif name == "MUL":
                raw = a * b
                result, high = raw & WORD_MASK, raw >> 16

            elif name == "DIV":
                if b == 0:
                    raise ZeroDivisionError(f"DIV by zero at PC=0x{self.pc:03X}")

                result, cf = a // b, False

            else:
                if name == "AND":
                    result = a & b

                elif name == "OR":
                    result = a | b

                elif name == "XOR":
                    result = a ^ b

                elif name == "NOT":
                    result = (~a) & WORD_MASK

                else:
                    raise CPUError(f"Unsupported instruction {name}")

                cf = False

            zf = (raw == 0) if name == "MUL" else result == 0
            sf = bool((high if name == "MUL" else result) & 0x8000)

        if store_address is not None:
            self.dmem[store_address] = store_value

        if result is not None and name != "CMP":
            self.regs[rd] = result

        if high is not None:
            self.regs[rd + 1] = high

        self.ZF = zf
        self.CF = cf
        self.SF = sf
        self.pc = next_pc
        self.ir = ins.word
        self.halted = name == "HALT"
        self.last_instruction = ins

        return ins

    def run(self, limit: int = 10_000) -> int:
        """Executes instructions till halt or limit"""
        if type(limit) is not int or limit < 0:
            raise CPUError("Run limit must be a non-negative integer")

        steps = 0
        while not self.halted and steps < limit:
            self.step()
            steps += 1

        return steps

    def load_mem_file(self, file_path: str) -> None:
        """Parse and load memory file"""
        data = {}
        try:
            with open(file_path, "r") as f:
                for raw_line in f:
                    line = raw_line.split(";", 1)[0].strip()
                    if not line or ":" not in line:
                        continue

                    addr_str, val_str = line.split(":", 1)
                    address = int(addr_str.strip(), 0)

                    val_clean = val_str.strip()
                    if not val_clean:
                        continue

                    if (
                        val_clean.startswith("'")
                        and val_clean.endswith("'")
                        and len(val_clean) == 3
                    ):
                        value = ord(val_clean[1])
                    else:
                        value = int(val_clean.split()[0], 0)

                    data[address] = value

        except (ValueError, OSError) as error:
            raise CPUError(f"Failed to load .mem file {file_path}: {error}")

        for address, value in data.items():
            if not (0 <= address < len(self.dmem)):
                raise CPUError(f"Address {address} exceeds memory size")

            self.dmem[address] = value

        return len(data)
