class AsmError(Exception):
    """Raised for any assembly/syntax error, with line number context."""

    def __init__(self, message: str, line_no: int | None = None, text: str = ""):
        self.line_no = line_no
        self.text = text
        if line_no is not None:
            message = f"line {line_no}: {message}" + (f"  ({text!r})" if text else "")
        super().__init__(message)
