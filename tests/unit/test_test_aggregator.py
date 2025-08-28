import unittest
import tempfile
from pathlib import Path
from src.utils.test_aggregator import TestFileAggregator

class TestTestFileAggregator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.aggregator = TestFileAggregator()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_creates_new_file_if_not_exists(self):
        target_file = Path(self.test_dir.name) / "test_new.cpp"
        content = "#include <gtest/gtest.h>\nTEST(MyTest, Case1) {}"
        
        self.aggregator.aggregate(str(target_file), content)
        
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text().strip(), content.strip())

    def test_appends_new_test_case(self):
        target_file = Path(self.test_dir.name) / "test_append.cpp"
        existing_content = (
            '#include <gtest/gtest.h>\n'
            'TEST(OldTest, Case1) {}\n\n'
            'int main(int argc, char **argv) { return 0; }'
        )
        target_file.write_text(existing_content)

        new_content = "TEST(NewTest, Case2) { ASSERT_TRUE(1); }"
        self.aggregator.aggregate(str(target_file), new_content)

        final_content = target_file.read_text()
        self.assertIn("TEST(OldTest, Case1)", final_content)
        self.assertIn("TEST(NewTest, Case2)", final_content)
        self.assertIn("int main", final_content)

    def test_merges_and_deduplicates_includes(self):
        target_file = Path(self.test_dir.name) / "test_includes.cpp"
        existing_content = '#include "a.h"\n#include "b.h"'
        target_file.write_text(existing_content)

        new_content = '#include "b.h"\n#include "c.h"'
        self.aggregator.aggregate(str(target_file), new_content)

        final_content = target_file.read_text()
        self.assertEqual(final_content.count('#include "b.h"'), 1)
        self.assertIn('#include "a.h"', final_content)
        self.assertIn('#include "c.h"', final_content)

    def test_preserves_main_function_at_end(self):
        target_file = Path(self.test_dir.name) / "test_main.cpp"
        main_func = "int main(int argc, char **argv) { ::testing::InitGoogleTest(&argc, argv); return RUN_ALL_TESTS(); }"
        existing_content = f"TEST(T1, C1) {{}}\n\n{main_func}"
        target_file.write_text(existing_content)

        new_content = "TEST(T2, C2) {}"
        self.aggregator.aggregate(str(target_file), new_content)

        final_content = target_file.read_text()
        self.assertIn("TEST(T1, C1)", final_content)
        self.assertIn("TEST(T2, C2)", final_content)
        self.assertTrue(final_content.strip().endswith("}"))
        self.assertIn(main_func, final_content)

    def test_merges_multiple_new_test_cases(self):
        target_file = Path(self.test_dir.name) / "test_multi.cpp"
        target_file.write_text("TEST(T1, C1) {}")

        new_content = "TEST(T2, C2) {}\n\nTEST_F(MyFixture, C3) {}"
        self.aggregator.aggregate(str(target_file), new_content)

        final_content = target_file.read_text()
        self.assertIn("TEST(T1, C1)", final_content)
        self.assertIn("TEST(T2, C2)", final_content)
        self.assertIn("TEST_F(MyFixture, C3)", final_content)

if __name__ == "__main__":
    unittest.main()
