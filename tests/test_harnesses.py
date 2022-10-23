import os.path
import pathlib
import unittest

import lummao
from lummao import DetectedDetails

BASE_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = BASE_PATH / "test_resources"


class HarnessTestCase(unittest.IsolatedAsyncioTestCase):
    def _compile_script_filename(self, lsl_filename):
        return lummao.compile_script_file(RESOURCES_PATH / lsl_filename)

    async def test_globals(self):
        script = self._compile_script_filename("lsl_conformance.lsl")
        await script.callOrderFunc(1)
        await script.callOrderFunc(2)
        self.assertListEqual([1, 2], script.gCallOrder)

    async def test_run_conformance_suite(self):
        script = self._compile_script_filename("lsl_conformance.lsl")
        # If it doesn't raise then we count that as a success.
        await script.edefaultstate_entry()
        self.assertEqual(187, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    async def test_run_execute_loop_with_state_changes(self):
        script = self._compile_script_filename("lsl_conformance2.lsl")
        # Handles the internal state changes and whatnot
        await script.execute()
        self.assertEqual(69, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    async def test_jump_out_of_while_true(self):
        # Make sure Python's code optimization didn't break our
        # ability to jump out of a `while True` loop
        script = self._compile_script_filename("jump_out_of_while_true.lsl")
        await script.edefaultstate_entry()

    async def test_declaration_hoisting(self):
        script = self._compile_script_filename("hoist_decl_unstructured_jump.lsl")
        await script.edefaultstate_entry()

    async def test_continue_like_jump_with_ret(self):
        script = self._compile_script_filename("continue_like_jump_with_ret.lsl")
        await script.edefaultstate_entry()

    async def test_builtin_builtin_function_mocking(self):
        script = self._compile_script_filename("function_mocking.lsl")

        def _mutate_global(some_str):
            # Doesn't say anything, just fiddles with a global
            script.gFoo += 1
        script.builtin_funcs["llOwnerSay"] = _mutate_global
        await script.edefaultstate_entry()
        self.assertEqual(script.gFoo, 1)

    async def test_detected_function_wrappers(self):
        script = self._compile_script_filename("detected_touch.lsl")
        logged_names = []

        script.builtin_funcs["llOwnerSay"] = logged_names.append
        script.queue_event("touch_start", (1,), [DetectedDetails(Name="foobar")])
        await script.execute()
        self.assertListEqual(["foobar", ""], logged_names)


if __name__ == '__main__':
    unittest.main()
