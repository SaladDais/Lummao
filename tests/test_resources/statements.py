from lummao import *


class Script(BaseLSLScript):

    def __init__(self):
        super().__init__()

    async def edefaultstate_entry(self) -> None:
        if cond(1):
            await self.builtin_funcs.llOwnerSay("if")
        elif cond(2):
            await self.builtin_funcs.llOwnerSay("else if")

