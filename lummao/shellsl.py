#!/usr/bin/env python
import asyncio
import sys
import uuid
from subprocess import Popen, PIPE

import lummao
from lummao import ScriptExtender, BaseLSLScript, TimerScriptExtender, DateTimeScriptExtender
from lummao.http import HTTPRequestScriptExtender

# All on one line so that we don't mess up line numbers for script errors
LSL_HEADER = rb"""
integer argc;
list argv;
integer cashquery; /* $? in bash */

system(string command) {}
string exec(list command_parts) {return "";}
""".replace(b"\n", b" ")


class ShelLSLExtender(ScriptExtender):
    script: lummao.BaseLSLScript

    def __init__(self, new_argv):
        super().__init__()
        self.argv = new_argv

    def extend_script(self, script: BaseLSLScript):
        super().extend_script(script)
        script.builtin_funcs["llOwnerSay"] = print
        script.builtin_funcs["llGetOwner"] = lambda: uuid.UUID(int=1)
        script.builtin_funcs["llLoadURL"] = lambda user, text, url: print("llLoadURL:", text, url)
        script.builtin_funcs["llResetScript"] = lambda: sys.exit(0)
        script.exec = self._exec_wrapper
        script.system = self._system_wrapper
        script.argc = len(self.argv)
        script.argv = self.argv

    async def _system_wrapper(self, command: str):
        p = Popen(command, shell=True)
        p.wait()
        self.script.cashquery = p.returncode

    async def _exec_wrapper(self, command: list):
        p = Popen(command, stdout=PIPE, stdin=PIPE)
        stdout, stderr = p.communicate()
        if stderr:
            print(stderr.decode("utf8"), file=sys.stderr)
        self.script.cashquery = p.returncode
        return stdout.decode("utf8").rstrip("\n")


def shellsl_main():
    with open(sys.argv[1], "rb") as f:
        lsl_bytes = f.read()
    # replace shebang line if present
    if lsl_bytes.startswith(b"#!"):
        lsl_bytes = b"\n" + b"\n".join(lsl_bytes.split(b"\n")[1:])
    script = lummao.compile_script(LSL_HEADER + lsl_bytes)

    # Enhance our script env with real HTTP, timer and shell support.
    shell_extender = ShelLSLExtender(sys.argv[1:])
    shell_extender.extend_script(script)
    http_extender = HTTPRequestScriptExtender()
    http_extender.extend_script(script)
    timer_extender = TimerScriptExtender()
    timer_extender.extend_script(script)
    datetime_extender = DateTimeScriptExtender()
    datetime_extender.extend_script(script)

    asyncio.run(script.execute_until_complete())


if __name__ == "__main__":
    shellsl_main()
