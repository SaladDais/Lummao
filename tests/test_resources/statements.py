from lummao import *


class Script(BaseLSLScript):

    def __init__(self):
        super().__init__()

    def edefaultstate_entry(self) -> None:
        if cond(1):
            self.builtin_funcs.llOwnerSay("if")
        elif cond(2):
            self.builtin_funcs.llOwnerSay("else if")

