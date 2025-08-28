
import os
import re
from typing import Optional

class FixtureFinder:
    """
    Scans a directory to find the definition of a C++ GTest fixture class.
    """

    def find_fixture_definition(
        self, suite_name: str, search_path: str
    ) -> Optional[str]:
        """
        Recursively searches for a GTest fixture class definition in a given directory.

        Args:
            suite_name: The name of the fixture class to find (e.g., "MyTestFixture").
            search_path: The absolute path to the directory to start searching from.

        Returns:
            The full string definition of the class if found, otherwise None.
        """
        if not os.path.isdir(search_path):
            return None

        # Regex to find the class definition. It handles various formatting issues.
        # It looks for "class [suite_name] : public ::testing::Test {"
        # and captures everything until the closing brace and semicolon "};"
        # MODIFIED: Removed '^' anchor to allow single-line fixture definitions.
        pattern = re.compile(
            r"class\s+"
            + re.escape(suite_name)
            + r"\s*:\s*public\s+::testing::Test\s*\{[\s\S]*?};",
            re.MULTILINE,
        )

        for root, _, files in os.walk(search_path):
            for filename in files:
                if filename.endswith((".h", ".hpp", ".cpp", ".cc")):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            match = pattern.search(content)
                            if match:
                                return match.group(0)
                    except (IOError, UnicodeDecodeError):
                        # Ignore files that can't be read
                        continue
        return None
