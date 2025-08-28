
import unittest
import tempfile
import os
from pathlib import Path
from src.utils.fixture_finder import FixtureFinder

class TestFixtureFinder(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for test files."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.search_path = self.test_dir.name
        self.finder = FixtureFinder()

    def tearDown(self):
        """Clean up the temporary directory."""
        self.test_dir.cleanup()

    def _write_file(self, path_segments, content):
        """Helper to write content to a file within the temp directory."""
        filepath = Path(self.search_path).joinpath(*path_segments)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

    def test_finds_fixture_in_root(self):
        fixture_code = """
class MyFixtureTest : public ::testing::Test {
protected:
    void SetUp() override {
        // setup code
    }
};
"""
        self._write_file(["test_A.cpp"], f"// Some other code\n{fixture_code}\n// More code")
        result = self.finder.find_fixture_definition("MyFixtureTest", self.search_path)
        self.assertEqual(result.strip(), fixture_code.strip())

    def test_finds_fixture_in_subdir(self):
        fixture_code = """
class DeepFixtureTest:public ::testing::Test {
protected:
    int value;
};
"""
        self._write_file(["deep", "nested", "test_B.h"], fixture_code)
        result = self.finder.find_fixture_definition("DeepFixtureTest", self.search_path)
        self.assertEqual(result.strip(), fixture_code.strip())

    def test_returns_none_if_not_found(self):
        self._write_file(["test_C.cpp"], "class OtherFixture {};")
        result = self.finder.find_fixture_definition("NonExistentFixture", self.search_path)
        self.assertIsNone(result)

    def test_returns_none_for_invalid_path(self):
        result = self.finder.find_fixture_definition("AnyFixture", "/invalid/path/that/does/not/exist")
        self.assertIsNone(result)

    def test_returns_none_for_empty_directory(self):
        result = self.finder.find_fixture_definition("AnyFixture", self.search_path)
        self.assertIsNone(result)

    def test_matches_correct_fixture_among_many(self):
        fixture1_code = "class FixtureOne : public ::testing::Test { };"
        fixture2_code = "class FixtureTwo : public ::testing::Test { int x; };"
        self._write_file(["test_D.cpp"], f"{fixture1_code}\n{fixture2_code}")
        result = self.finder.find_fixture_definition("FixtureTwo", self.search_path)
        self.assertEqual(result.strip(), fixture2_code.strip())

    def test_handles_various_formatting(self):
        fixture_code = """
class   WeirdFormatFixture
  :
    public   ::testing::Test
{
    // comments
};
"""
        self._write_file(["test_E.hpp"], fixture_code)
        result = self.finder.find_fixture_definition("WeirdFormatFixture", self.search_path)
        self.assertEqual(result.strip(), fixture_code.strip())

if __name__ == "__main__":
    unittest.main()
