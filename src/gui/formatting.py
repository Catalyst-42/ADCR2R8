"""formatting.py — small display helpers for the GUI."""


def to_hex(value: int, width: int = 4) -> str:
    """Format an integer as a fixed-width hex string, e.g. 0x0F2A."""
    return f"0x{value & (16 ** width - 1):0{width}X}"
