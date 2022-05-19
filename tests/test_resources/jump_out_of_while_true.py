from lummao import *


class Script(BaseLSLScript):

    def __init__(self):
        super().__init__()

    @with_goto
    def edefaultstate_entry(self) -> None:
        while cond(1) == True:
            goto .foo
        label .foo

