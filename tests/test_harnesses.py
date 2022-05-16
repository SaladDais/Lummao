import unittest

from .test_resources import lsl_conformance


class HarnessTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # Fresh version of the script for each test
        self.script = lsl_conformance.Script()

    def test_globals(self):
        self.script.callOrderFunc(1)
        self.script.callOrderFunc(2)
        self.assertListEqual([1, 2], self.script.gCallOrder)

    def test_run_conformance_suite(self):
        # If it doesn't raise then we count that as a success.
        self.script.edefaultstate_entry()
        self.assertEqual(179, self.script.gTestsPassed)
        self.assertEqual(0, self.script.gTestsFailed)


if __name__ == '__main__':
    unittest.main()
