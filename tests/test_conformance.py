import os.path
import pathlib
from subprocess import Popen, PIPE
import unittest

BASE_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = BASE_PATH / "test_resources"


class ConformanceTestCase(unittest.TestCase):
    def _run_lummao(self, lsl_str: str):
        p = Popen(['lummao', '-', '-'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        output = p.communicate(input=lsl_str.encode("utf8"))[0]
        self.assertEqual(0, p.returncode)
        return output

    def _assert_output_matches(self, lsl_file: str, py_file: str):
        with open(RESOURCES_PATH / lsl_file, "rb") as f:
            lsl_str = f.read()
        with open(RESOURCES_PATH / py_file, "rb") as f:
            expected_py = f.read()
        actual_py = self._run_lummao(lsl_str.decode("utf8"))
        self.assertSequenceEqual(expected_py.decode("utf8"), actual_py.decode("utf8"))

    def test_lsl_conformance_matches(self):
        self._assert_output_matches("lsl_conformance.lsl", "lsl_conformance.py")

    def test_lsl_conformance2_matches(self):
        self._assert_output_matches("lsl_conformance2.lsl", "lsl_conformance2.py")


if __name__ == '__main__':
    unittest.main()
