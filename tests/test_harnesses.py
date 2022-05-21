import os.path
import pathlib
import unittest
from subprocess import Popen, PIPE

BASE_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = BASE_PATH / "test_resources"


class HarnessTestCase(unittest.TestCase):
    def _compile_script_bytes(self, lsl_bytes):
        p = Popen(['lummao', '-', '-'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        output = p.communicate(input=lsl_bytes)[0]
        self.assertEqual(0, p.returncode)
        new_globals = globals().copy()
        exec(output, new_globals)
        return new_globals["Script"]()

    def _compile_script_filename(self, lsl_filename):
        with open(RESOURCES_PATH / lsl_filename, "rb") as f:
            return self._compile_script_bytes(f.read())

    def test_globals(self):
        script = self._compile_script_filename("lsl_conformance.lsl")
        script.callOrderFunc(1)
        script.callOrderFunc(2)
        self.assertListEqual([1, 2], script.gCallOrder)

    def test_run_conformance_suite(self):
        script = self._compile_script_filename("lsl_conformance.lsl")
        # If it doesn't raise then we count that as a success.
        script.edefaultstate_entry()
        self.assertEqual(182, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    def test_run_execute_loop_with_state_changes(self):
        script = self._compile_script_filename("lsl_conformance2.lsl")
        # Handles the internal state changes and whatnot
        script.execute()
        self.assertEqual(69, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    def test_jump_out_of_while_true(self):
        # Make sure Python's code optimization didn't break our
        # ability to jump out of a `while True` loop
        script = self._compile_script_filename("jump_out_of_while_true.lsl")
        script.edefaultstate_entry()

    def test_declaration_hoisting(self):
        script = self._compile_script_filename("hoist_decl_unstructured_jump.lsl")
        script.edefaultstate_entry()

    def test_continue_like_jump_with_ret(self):
        script = self._compile_script_filename("continue_like_jump_with_ret.lsl")
        script.edefaultstate_entry()

    def test_builtin_builtin_function_mocking(self):
        script = self._compile_script_filename("function_mocking.lsl")

        def _mutate_global(some_str):
            # Doesn't say anything, just fiddles with a global
            script.gFoo += 1
        script.builtin_funcs["llOwnerSay"] = _mutate_global
        script.edefaultstate_entry()
        self.assertEqual(script.gFoo, 1)


if __name__ == '__main__':
    unittest.main()
