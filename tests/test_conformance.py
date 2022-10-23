import os.path
import pathlib
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

    def test_one_error_raised(self):
        with self.assertRaises(lummao.CompileError) as e:
            lummao.convert_script_file(RESOURCES_PATH / "one_error.lsl")
        expected = (
            "ERROR:: (  3,  9): [E10015] `string foo' assigned a integer value.",
        )
        self.assertSequenceEqual(expected, e.exception.err_msgs)

    def test_two_errors_raised(self):
        with self.assertRaises(lummao.CompileError) as e:
            lummao.convert_script_file(RESOURCES_PATH / "two_errors.lsl")
        expected = (
            "ERROR:: (  3,  9): [E10015] `string foo' assigned a integer value.",
            "ERROR:: (  4,  9): [E10015] `string baz' assigned a integer value."
        )
        self.assertSequenceEqual(expected, e.exception.err_msgs)


if __name__ == '__main__':
    unittest.main()
