import os
import re

class TestFileAggregator:
    """Aggregates GTest test cases into a single file."""

    def __init__(self):
        self.include_pattern = re.compile(r'#include\s*[<\"].*?[>\"]')
        self.test_case_pattern = re.compile(
            r"(^{TEST(_[FP])?\(.*\)\s*\{[\s\S]*?^\})", re.MULTILINE
        )
        self.main_pattern = re.compile(
            r"(int\s+main\(int\s+argc,\s*char\s*\*\*\s*argv\)\s*\{[\s\S]*?^\})",
            re.MULTILINE,
        )

    def _extract_parts(self, content: str):
        includes = self.include_pattern.findall(content)
        main_match = self.main_pattern.search(content)
        main_block = main_match.group(1) if main_match else None

        # To get the body, remove includes and main
        body_content = content
        if main_block:
            body_content = body_content.replace(main_block, "")
        for inc in includes:
            body_content = body_content.replace(inc, "")
        
        return sorted(list(set(includes))), body_content.strip(), main_block

    def aggregate(self, target_filepath: str, new_content: str):
        """
        Merges new test content into a target test file.

        If the file doesn't exist, it's created with the new content.
        If it exists, includes are merged and test cases are appended.
        """
        if not os.path.exists(target_filepath):
            with open(target_filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            return

        with open(target_filepath, "r", encoding="utf-8") as f:
            existing_content = f.read()

        existing_includes, existing_body, existing_main = self._extract_parts(
            existing_content
        )
        new_includes, new_body, _ = self._extract_parts(new_content)

        # Combine and deduplicate includes
        all_includes = sorted(list(set(existing_includes + new_includes)))

        # Combine test bodies
        combined_body = existing_body
        if new_body:
            combined_body += "\n\n" + new_body

        # Reconstruct the file
        final_content = "\n".join(all_includes) + "\n\n" + combined_body
        if existing_main:
            final_content += "\n\n" + existing_main
        else: # If original file had no main, maybe new one does.
            _, _, new_main = self._extract_parts(new_content)
            if new_main:
                final_content += "\n\n" + new_main

        with open(target_filepath, "w", encoding="utf-8") as f:
            f.write(final_content.strip() + "\n")
