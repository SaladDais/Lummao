from typing import Sequence


class CompileError(Exception):
    def __init__(self, err_msgs: Sequence[str]):
        self.err_msgs = err_msgs

    def __str__(self):
        msgs_str = "Compile Errors\n"
        for msg in self.err_msgs:
            msgs_str += f"  {msg}\n"
        return msgs_str

    def __repr__(self):
        return f"{self.__class__.__name__}({self.err_msgs!r})"
