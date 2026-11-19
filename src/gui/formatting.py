def to_hex(value: int, width: int = 4) -> str:
    return f"0x{value & (16 ** width - 1):0{width}X}"
