import os.path
import pathlib
from subprocess import Popen, PIPE
import unittest

import lummao

BASE_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = BASE_PATH / "test_resources"


class ConformanceTestCase(unittest.TestCase):
    def _assert_output_matches(self, lsl_file: str, py_file: str):
        actual_py = lummao.convert_script_file(RESOURCES_PATH / lsl_file)
        with open(RESOURCES_PATH / py_file, "rb") as f:
            expected_py = f.read()
        self.assertSequenceEqual(expected_py.decode("utf8"), actual_py.decode("utf8"))

    def test_lsl_conformance_matches(self):
        self._assert_output_matches("lsl_conformance.lsl", "lsl_conformance.py")

    def test_lsl_conformance2_matches(self):
        self._assert_output_matches("lsl_conformance2.lsl", "lsl_conformance2.py")

    def test_statements_matches(self):
        self._assert_output_matches("statements.lsl", "statements.py")


if __name__ == '__main__':
    unittest.main()
