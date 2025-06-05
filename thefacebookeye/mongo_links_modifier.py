import sys
import re
import os

def modify_mongo_handler_for_links(filepath="database/mongo_handler.py"):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist. Cannot modify.")
        sys.exit(1)

    with open(filepath, 'r') as f:
        content = f.read()

    # Add 'extracted_links' to the 'post' sub-document in dummy_post_data example
    # Target: after "permalink": "http://example.com/post/001",
    # We need to be careful about the comma.

    # Regex to find the permalink line and add extracted_links after it.
    # It looks for a line ending with "permalink": "...", (optional comma)
    # and inserts the new field, ensuring comma correctness.

    # Simpler: find the permalink line, capture it, and add the new field after it.
    # "permalink": "http://example.com/post/001",
    #                "extracted_links": ["http://link1", "http://link2"] # new line

    # This pattern finds the permalink line, assuming it ends with a comma.
    pattern = r'("permalink":\s*"[^"]*",\s*)'
    replacement = r'\1\n                "extracted_links": ["http://example.com/link1", "http://another.org/article"],'

    content, num_subs = re.subn(pattern, replacement, content, count=1)

    if num_subs == 0:
        # Fallback if permalink line does not end with a comma (e.g. it's the last item)
        pattern_no_comma = r'("permalink":\s*"[^"]*"\s*)'
        replacement_no_comma = r'\1,\n                "extracted_links": ["http://example.com/link1", "http://another.org/article"]'
        content, num_subs = re.subn(pattern_no_comma, replacement_no_comma, content, count=1)

    if num_subs == 0:
        print(f"Error: Could not find 'permalink' key in dummy_post_data in {filepath} to inject 'extracted_links'. File not modified.")
    else:
        print(f"Modified {filepath} to include 'extracted_links' in dummy schema example.")

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    try:
        modify_mongo_handler_for_links()
    except Exception as e:
        print(f"Error modifying database/mongo_handler.py: {e}")
        # sys.exit(1)
