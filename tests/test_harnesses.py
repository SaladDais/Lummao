import asyncio
import json
import os.path
import pathlib
import unittest
from unittest import mock

import pytest_httpbin

import lummao
from lummao import DetectedDetails, TimerScriptExtender
from lummao.http import HTTPRequestScriptExtender

BASE_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = BASE_PATH / "test_resources"


def _compile_script_filename(lsl_filename):
    return lummao.compile_script_file(RESOURCES_PATH / lsl_filename)


class HarnessTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_globals(self):
        script = _compile_script_filename("lsl_conformance.lsl")
        await script.callOrderFunc(1)
        await script.callOrderFunc(2)
        self.assertListEqual([1, 2], script.gCallOrder)

    async def test_run_conformance_suite(self):
        script = _compile_script_filename("lsl_conformance.lsl")
        # If it doesn't raise then we count that as a success.
        await script.edefaultstate_entry()
        self.assertEqual(187, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    async def test_run_execute_loop_with_state_changes(self):
        script = _compile_script_filename("lsl_conformance2.lsl")
        # Handles the internal state changes and whatnot
        await script.execute()
        self.assertEqual(69, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    async def test_jump_out_of_while_true(self):
        # Make sure Python's code optimization didn't break our
        # ability to jump out of a `while True` loop
        script = _compile_script_filename("jump_out_of_while_true.lsl")
        await script.edefaultstate_entry()

    async def test_declaration_hoisting(self):
        script = _compile_script_filename("hoist_decl_unstructured_jump.lsl")
        await script.edefaultstate_entry()

    async def test_continue_like_jump_with_ret(self):
        script = _compile_script_filename("continue_like_jump_with_ret.lsl")
        await script.edefaultstate_entry()

    async def test_builtin_builtin_function_mocking(self):
        script = _compile_script_filename("function_mocking.lsl")

        def _mutate_global(some_str):
            # Doesn't say anything, just fiddles with a global
            script.gFoo += 1
        script.builtin_funcs["llOwnerSay"] = _mutate_global
        await script.edefaultstate_entry()
        self.assertEqual(script.gFoo, 1)

    async def testuncleared_locals(self):
        script = _compile_script_filename("uncleared_locals.lsl")
        ownersay_mock = mock.MagicMock()
        script.builtin_funcs["llOwnerSay"] = ownersay_mock
        await script.edefaultstate_entry()
        self.assertListEqual(
            [mock.call("quux"), mock.call("quux")],
            ownersay_mock.mock_calls,
        )

    async def test_detected_function_wrappers(self):
        script = _compile_script_filename("detected_touch.lsl")
        logged_names = []

        script.builtin_funcs["llOwnerSay"] = logged_names.append
        script.queue_event("touch_start", (1,), [DetectedDetails(Name="foobar")])
        await script.execute()
        self.assertListEqual(["foobar", ""], logged_names)


class ScriptExtenderTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_timers(self):
        script = _compile_script_filename("timers.lsl")
        extender = TimerScriptExtender()
        extender.extend_script(script)

        await script.execute_until_complete()
        self.assertEqual(3, script.gCount)


@pytest_httpbin.use_class_based_httpbin
class HTTPRequestScriptExtenderTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.script = _compile_script_filename("http_request.lsl")
        extender = HTTPRequestScriptExtender()
        extender.extend_script(self.script)

    async def test_request_invalid_url(self):
        await self.script.makeRequest("badscheme://invalid.local/example")
        await self.script.execute_until_complete()
        self.assertTrue(self.script.gTriggered)
        self.assertTrue("Internal exception" in self.script.gResp)

    async def test_custom_headers_sent(self):
        await self.script.makeRequest(self.httpbin.url + "/headers")
        await self.script.execute_until_complete()
        self.assertTrue(self.script.gTriggered)
        headers = json.loads(self.script.gResp)["headers"]
        self.assertEqual("Bar", headers["Foo"])


if __name__ == '__main__':
    unittest.main()
