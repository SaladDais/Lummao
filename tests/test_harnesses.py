import unittest

from .test_resources import lsl_conformance, lsl_conformance2


class HarnessTestCase(unittest.TestCase):
    def test_globals(self):
        script = lsl_conformance.Script()
        script.callOrderFunc(1)
        script.callOrderFunc(2)
        self.assertListEqual([1, 2], script.gCallOrder)

    def test_run_conformance_suite(self):
        script = lsl_conformance.Script()
        # If it doesn't raise then we count that as a success.
        script.edefaultstate_entry()
        self.assertEqual(182, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)

    def test_run_execute_loop_with_state_changes(self):
        script = lsl_conformance2.Script()
        # Handles the internal state changes and whatnot
        script.execute()
        self.assertEqual(69, script.gTestsPassed)
        self.assertEqual(0, script.gTestsFailed)


if __name__ == '__main__':
    unittest.main()
