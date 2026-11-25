"""Tests for scripts/convert-times.py. Run: python3 -m unittest discover -s tests"""

import importlib.util
import json
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("convert_times", ROOT / "scripts" / "convert-times.py")
convert_times = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_times)


class ConvertTimesTest(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "tests" / "fixtures" / "results", self.dir, dirs_exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def load(self, name):
        return json.loads((self.dir / name).read_text(encoding="utf-8"))

    def test_converts_seconds_to_milliseconds(self):
        convert_times.main(str(self.dir))
        execution = self.load("php.json")["execution"]
        self.assertAlmostEqual(execution["start_time"], 1795611663184.21, places=1)
        self.assertAlmostEqual(execution["end_time"], 1795611663197.793, places=1)
        # The difference is the duration that qasectl recomputes (milliseconds)
        self.assertEqual(int(execution["end_time"] - execution["start_time"]), 13)

    def test_keeps_other_fields(self):
        before = self.load("playwright.json")
        convert_times.main(str(self.dir))
        after = self.load("playwright.json")
        self.assertEqual(after["execution"]["duration"], before["execution"]["duration"])
        self.assertEqual(after["title"], before["title"])
        self.assertEqual(after["signature"], before["signature"])

    def test_leaves_missing_times_alone(self):
        path = self.dir / "no-times.json"
        path.write_text(json.dumps({"execution": {"status": "passed", "start_time": None, "duration": 5}}), encoding="utf-8")
        convert_times.main(str(self.dir))
        execution = json.loads(path.read_text(encoding="utf-8"))["execution"]
        self.assertIsNone(execution["start_time"])
        self.assertNotIn("end_time", execution)


if __name__ == "__main__":
    unittest.main()
