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
        if type(value) is not int or not 0 <= value <= WORD_MASK:
            raise CPUError(f"Expected a 16-bit unsigned integer, got {value!r}")
        return value

    @staticmethod
    def _address(value: int, size: int) -> int:
        if type(value) is not int or not 0 <= value < size:
            raise CPUError(f"Address {value!r} outside memory of {size} words")
        return value

    def load_program(self, words: Iterable[int]) -> None:
        """Validate, copy, clear unused imem and reset execution state (retain dmem)."""
        words = list(words)
        if len(words) > IMEM_SIZE:
            raise CPUError(f"Program exceeds {IMEM_SIZE} words")
        for word in words:
            self._word(word)
        self.imem[:] = words + [0] * (IMEM_SIZE - len(words))
        # Reset execution state but preserve program and data memory
        self.regs[:] = [0] * NUM_REGISTERS
        self.pc = self.ir = 0
        self.ZF = self.CF = self.SF = False
        self.halted = False
        self.last_instruction = None

    def load_data(self, address: int, values: Iterable[int]) -> None:
        """Validate the entire block before writing to data memory."""
        self._address(address, DMEM_SIZE)
        values = list(values)
        if address + len(values) > DMEM_SIZE:
            raise CPUError("Data exceeds memory")
        for value in values:
            self._word(value)
        self.dmem[address : address + len(values)] = values

    def snapshot(self):
        """Dump copy of a CPU"""
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
        """Decode without executing. Addresses and lengths are in 16-bit words."""
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
        if instruction.mode == MODE_DIRECT:
            address = instruction.operand
        else:
            address = self.regs[instruction.rs]
        return self._address(address, DMEM_SIZE)

    def _read_operand(self, instruction: DecodedInstruction) -> int:
        if instruction.mode == MODE_REGISTER:
            return self._word(self.regs[instruction.rs])
        if instruction.mode == MODE_IMMEDIATE:
            return instruction.operand
        return self._word(self.dmem[self._memory_address(instruction)])

    def step(self) -> DecodedInstruction | None:
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

        # Commit only after every fallible operation has completed.
        if store_address is not None:
            self.dmem[store_address] = store_value
        if result is not None and name != "CMP":
            self.regs[rd] = result
        if high is not None:
            self.regs[rd + 1] = high
        self.ZF, self.CF, self.SF = zf, cf, sf
        self.pc, self.ir = next_pc, ins.word
        self.halted = name == "HALT"
        self.last_instruction = ins
        return ins

    def run(self, limit: int = 10000) -> int:
        """Run at most limit instructions; return count. Resume with another call."""
        if type(limit) is not int or limit < 0:
            raise CPUError("Run limit must be a non-negative integer")
        steps = 0
        while not self.halted and steps < limit:
            self.step()
            steps += 1
        return steps

    def load_mem_file(self, file_path: str) -> None:
        """Load memory data from a .mem file.

        Format: address:value pairs (supports hex/decimal/quoted characters, ignores ; comments)
        Characters must be in single quotes: 'A', ' ', '!'
        Numbers can be hex (0x1234) or decimal (1234)
        Example:
        0x0001:6
        0x0002:10    ; comment
        0x0003:20
        0x0004:'A'    ; character in quotes converted to ord()
        0x0005:' '    ; space character
        """
        data = {}
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(";"):
                        # Remove comments after ;
                        if ";" in line:
                            line = line.split(";")[0].strip()

                        # Parse address:value format
                        if ":" in line:
                            addr_str, val_str = line.split(":", 1)
                            address = int(addr_str.strip(), 0)  # Handle 0x prefix
                            # Clean value string (remove remaining comments and spaces)
                            val_clean = val_str.strip()

                            if val_clean:
                                # Check if it's a quoted character
                                if (
                                    val_clean.startswith("'")
                                    and val_clean.endswith("'")
                                    and len(val_clean) == 3
                                ):
                                    # Convert quoted character to ord() value
                                    char = val_clean[1]  # Get character between quotes
                                    value = ord(char)
                                else:
                                    # Parse as regular number (hex or decimal)
                                    val_num = (
                                        val_clean.split()[0]
                                        if " " in val_clean
                                        else val_clean
                                    )
                                    value = int(val_num, 0)
                                data[address] = value

            # Load data into CPU memory
            for address, value in data.items():
                if 0 <= address < len(self.dmem):
                    self.dmem[address] = value
                else:
                    raise CPUError(f"Address {address} exceeds memory size")

        except (ValueError, OSError) as error:
            raise CPUError(f"Failed to load .mem file {file_path}: {error}")

        return len(data)
