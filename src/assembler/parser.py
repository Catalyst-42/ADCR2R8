from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass

from src.assembler.errors import AsmError
from src.cpu.constants import (
    ADDR12_MASK,
    CONTROL_TAG,
    DATA_OPCODES,
    IMEM_SIZE,
    JUMP_OPCODES,
    MODE_DIRECT,
    MODE_IMMEDIATE,
    MODE_INDIRECT,
    MODE_REGISTER,
    REVERSED_OPERANDS,
    SINGLE_OPERAND,
    WORD_MASK,
)

REG_RE = re.compile(r"^[Rr](1[0-5]|[0-9])$")
LABEL_DEF_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
LABEL_REF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class Operand:
    kind: str  # 'reg' | 'imm' | 'direct' | 'indirect'
    value: int | str  # register number, immediate value, address, or label name


@dataclass
class Instruction:
    line_no: int
    mnemonic: str
    operands: list[Operand]
    address: int = 0  # word address assigned during pass 1
    length: int = 1  # 1 or 2 words


def strip_comment(line: str) -> str:
    """Removes comments from line"""
    return line.partition(";")[0].strip()


def parse_number(tok: str, line_no: int) -> int:
    """Parses hexadecimal or decimal signed number"""
    tok = tok.strip()
    neg = tok.startswith("-")

    if neg:
        tok = tok[1:]

    try:
        if tok.lower().startswith("0x"):
            val = int(tok, 16)
        else:
            val = int(tok, 10)

    except ValueError:
        raise AsmError(f"invalid number '{tok}'", line_no)

    if neg:
        val = -val

    return val & WORD_MASK


def parse_register(tok: str, line_no: int) -> int:
    """Parses register commands"""
    tok = tok.strip()
    m = REG_RE.match(tok)

    if not m:
        raise AsmError(f"expected register (R0-R15), got '{tok}'", line_no)

    reg = int(m.group(1))
    if not (0 <= reg <= 15):
        raise AsmError(f"register out of range: '{tok}'", line_no)

    return reg


def classify_operand(tok: str, line_no: int) -> Operand:
    """Parses token to operand"""
    tok = tok.strip()
    if not tok:
        raise AsmError("empty operand", line_no)

    # Registers
    if REG_RE.match(tok):
        return Operand("reg", parse_register(tok, line_no))

    # Immediates
    if tok.startswith("#"):
        num_tok = tok[1:]
        if LABEL_REF_RE.match(num_tok):
            return Operand("imm", num_tok)

        return Operand("imm", parse_number(num_tok, line_no))

    # Memory reference
    if tok.startswith("[") and tok.endswith("]"):
        inner = tok[1:-1].strip()

        if REG_RE.match(inner):
            return Operand("indirect", parse_register(inner, line_no))
        if LABEL_REF_RE.match(inner):
            return Operand("direct", inner)  # Unresolved label

        return Operand("direct", parse_number(inner, line_no))

    # Label or number
    if LABEL_REF_RE.match(tok):
        return Operand("imm", tok)

    try:
        return Operand("imm", parse_number(tok, line_no))
    except AsmError:
        pass

    raise AsmError(f"unrecognized operand '{tok}'", line_no)


def split_operands(rest: str, line_no: int) -> list[str]:
    """Returns operands from line"""
    if not rest.strip():
        return []

    return [p.strip() for p in rest.split(",") if p.strip() != ""]


def tokenize_line(raw_line: str, line_no: int):
    """Parse line on tokens"""
    line = strip_comment(raw_line)
    if not line:
        return None, None, []

    label = None
    m = LABEL_DEF_RE.match(line)
    if m:
        label = m.group(1)
        line = m.group(2).strip()

        if not line:
            return label, None, []

    parts = line.split(None, 1)
    mnemonic = parts[0].upper()
    rest = parts[1] if len(parts) > 1 else ""
    operand_tokens = split_operands(rest, line_no)

    return label, mnemonic, operand_tokens


def instruction_length(mnemonic: str, operands: list[Operand], line_no: int) -> int:
    """Calculates instruction length"""

    if mnemonic in JUMP_OPCODES:
        return 1 if mnemonic == "HALT" else 2

    if mnemonic not in DATA_OPCODES:
        raise AsmError(f"unknown mnemonic '{mnemonic}'", line_no)

    if mnemonic in SINGLE_OPERAND:
        return 1

    if len(operands) != 2:
        raise AsmError(f"'{mnemonic}' expects 2 operands, got {len(operands)}", line_no)

    mode_operand = operands[0] if mnemonic in REVERSED_OPERANDS else operands[1]
    if mode_operand.kind in ("imm", "direct"):
        return 2

    # 'reg' and 'indirect'
    return 1


def pass1(lines: list[str]):
    """Calculates tokens in first approach"""
    instructions: list[Instruction] = []
    labels: dict[str, int] = {}
    address = 0

    for i, raw in enumerate(lines, start=1):
        label, mnemonic, operand_tokens = tokenize_line(raw, i)

        if label is not None:
            if label in labels:
                raise AsmError(f"duplicate label '{label}'", i)
            labels[label] = address

        if mnemonic is None:
            continue

        operands = [classify_operand(tok, i) for tok in operand_tokens]
        length = instruction_length(mnemonic, operands, i)

        instr = Instruction(
            line_no=i,
            mnemonic=mnemonic,
            operands=operands,
            address=address,
            length=length,
        )
        instructions.append(instr)
        address += length

    return instructions, labels


def resolve(value, labels: dict[str, int], line_no: int) -> int:
    """Get label or number"""
    if isinstance(value, str):
        if value not in labels:
            raise AsmError(f"undefined label '{value}'", line_no)

        return labels[value]

    return value & WORD_MASK


def encode_jump(instr: Instruction, labels: dict[str, int]) -> list[int]:
    """Encoder for jump operations"""
    opcode = JUMP_OPCODES[instr.mnemonic]

    if instr.mnemonic == "HALT":
        if instr.operands:
            raise AsmError("HALT expects no operands", instr.line_no)

        return [CONTROL_TAG | (opcode << 4)]

    else:
        if len(instr.operands) != 1:
            raise AsmError(
                f"'{instr.mnemonic}' expects 1 operand (label/address)",
                instr.line_no,
            )

        op = instr.operands[0]
        if op.kind not in ("direct", "imm"):
            raise AsmError(
                f"'{instr.mnemonic}' target must be a label or address",
                instr.line_no,
            )

        addr = resolve(op.value, labels, instr.line_no)

    if addr > ADDR12_MASK:
        raise AsmError(f"jump target 0x{addr:X} does not fit in 12 bits", instr.line_no)

    return [CONTROL_TAG | (opcode << 4), addr]


def encode_data(instr: Instruction, labels: dict[str, int]) -> list[int]:
    """Encoder for data instructions"""
    opcode = DATA_OPCODES[instr.mnemonic]

    if instr.mnemonic in SINGLE_OPERAND:
        if len(instr.operands) != 1:
            raise AsmError(f"'{instr.mnemonic}' expects 1 operand", instr.line_no)

        rd = _require_reg(instr.operands[0], instr.line_no, instr.mnemonic)
        word = (opcode << 12) | (rd << 8) | (0 << 4) | MODE_REGISTER
        return [word & WORD_MASK]

    if len(instr.operands) != 2:
        raise AsmError(
            f"'{instr.mnemonic}' expects 2 operands, got {len(instr.operands)}",
            instr.line_no,
        )

    if instr.mnemonic == "MUL" and instr.operands[0].value == 15:
        raise AsmError("MUL R15 has no high-result register R16", instr.line_no)

    memory_operand = (
        instr.operands[0] if instr.mnemonic == "STORE" else instr.operands[1]
    )

    if instr.mnemonic in {"LOAD", "STORE"} and memory_operand.kind not in {
        "direct",
        "indirect",
    }:
        raise AsmError(f"{instr.mnemonic} requires memory addressing", instr.line_no)

    if instr.mnemonic in REVERSED_OPERANDS:
        mem_op, reg_op = instr.operands[0], instr.operands[1]
        rd = _require_reg(reg_op, instr.line_no, instr.mnemonic)
        return _encode_with_mode(opcode, rd, mem_op, labels, instr.line_no)

    dst_op, src_op = instr.operands[0], instr.operands[1]
    rd = _require_reg(dst_op, instr.line_no, instr.mnemonic)
    return _encode_with_mode(opcode, rd, src_op, labels, instr.line_no)


def _require_reg(op: Operand, line_no: int, mnemonic: str) -> int:
    """Checks and gets register for operation"""
    if op.kind != "reg":
        raise AsmError(
            f"'{mnemonic}' requires a register operand, got '{op.kind}'", line_no
        )

    return op.value


def _encode_with_mode(
    opcode: int, rd: int, mode_op: Operand, labels: dict[str, int], line_no: int
) -> list[int]:
    """Encodes instruction"""
    if mode_op.kind == "reg":
        rs = mode_op.value
        word = (opcode << 12) | (rd << 8) | (rs << 4) | MODE_REGISTER
        return [word & WORD_MASK]

    if mode_op.kind == "indirect":
        rs = mode_op.value
        word = (opcode << 12) | (rd << 8) | (rs << 4) | MODE_INDIRECT
        return [word & WORD_MASK]

    if mode_op.kind == "imm":
        value = resolve(mode_op.value, labels, line_no)
        word1 = (opcode << 12) | (rd << 8) | (0 << 4) | MODE_IMMEDIATE
        return [word1 & WORD_MASK, value & WORD_MASK]

    if mode_op.kind == "direct":
        addr = resolve(mode_op.value, labels, line_no)
        if addr > ADDR12_MASK:
            raise AsmError("data address exceeds 4095", line_no)
        word1 = (opcode << 12) | (rd << 8) | (0 << 4) | MODE_DIRECT
        return [word1 & WORD_MASK, addr & WORD_MASK]

    raise AsmError(f"unsupported operand kind '{mode_op.kind}'", line_no)


def pass2(instructions: list[Instruction], labels: dict[str, int]) -> list[int]:
    """Resolve last tokens once again"""
    words: list[int] = []

    for instr in instructions:
        if instr.mnemonic in JUMP_OPCODES:
            encoded = encode_jump(instr, labels)
        else:
            encoded = encode_data(instr, labels)

        if len(encoded) != instr.length:
            raise AsmError(
                f"internal error: length mismatch for '{instr.mnemonic}' "
                f"(pass1={instr.length}, pass2={len(encoded)})",
                instr.line_no,
            )
        words.extend(encoded)

    return words


def assemble_source(source: str, mem_size: int | None = None) -> list[int]:
    """Assemble source text into a list of 16 bit words"""
    lines = source.splitlines()
    instructions, labels = pass1(lines)
    words = pass2(instructions, labels)

    if mem_size is not None:
        if len(words) > mem_size:
            raise AsmError(
                f"program too large: {len(words)} words > imem size {mem_size}"
            )

        words = words + [0] * (mem_size - len(words))

    return words


def assemble_file(path: str, mem_size: int | None = IMEM_SIZE) -> list[int]:
    """Assemble source text from a file input"""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    return assemble_source(source, mem_size=mem_size)


def main(argv=None):
    ap = argparse.ArgumentParser(description="ADCR2R8 assembler / parser")
    ap.add_argument("input", help="path to .asm source file")
    ap.add_argument(
        "-o",
        "--output",
        help="write hex words to this file " "(default: print to stdout)",
    )
    ap.add_argument(
        "--size",
        type=int,
        default=IMEM_SIZE,
        help=f"imem size to pad to (default {IMEM_SIZE}, use 0 to disable)",
    )
    args = ap.parse_args(argv)

    mem_size = args.size if args.size > 0 else None

    try:
        words = assemble_file(args.input, mem_size=mem_size)
    except AsmError as e:
        print(f"Assembly error: {e}", file=sys.stderr)
        return 1

    lines_out = [f"0x{w:04X}" for w in words]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(lines_out) + "\n")
        print(f"Wrote {len(words)} words to {args.output}")
    else:
        for w in lines_out:
            print(w)

    return 0


if __name__ == "__main__":
    sys.exit(main())
