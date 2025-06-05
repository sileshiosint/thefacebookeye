import sys
import re
import os

def modify_scheduler_for_links_v2(filepath="scheduler/tasks.py"):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist. Cannot modify.")
        sys.exit(1) # Ok to exit in modifier script, not in main bash script for tool

    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_content_lines = []
    modified = False

    # Pattern to find the permalink line and ensure it's within the 'post' dictionary context
    # This is still a bit heuristic, relying on typical indentation.
    # A more robust parser would be an AST modification, but regex is used here.
    permalink_pattern = re.compile(r'(\s*"permalink":\s*item\.get\("permalink"\),?)')
    # Pattern to find and remove old "extracted_urls" (if it exists)
    old_extracted_urls_pattern = re.compile(r'\s*"extracted_urls":\s*item\.get\("extracted_urls_from_text",\s*\[\]\),?\s*')

    inside_post_dict = False
    transformed_post_block_found = False

    for line in lines:
        # First, remove any old "extracted_urls" line
        line_after_removal = old_extracted_urls_pattern.sub('', line)

        # Heuristic to detect if we are roughly within the `transformed_post`'s `post` sub-dictionary
        if "transformed_post = {" in line:
            transformed_post_block_found = True
        if transformed_post_block_found and "\"post\": {" in line:
            inside_post_dict = True

        if inside_post_dict and permalink_pattern.search(line_after_removal):
            # Add comma to permalink line if not present, then add extracted_links line
            # Ensure permalink line ends with a comma
            stripped_line = line_after_removal.rstrip()
            if not stripped_line.endswith(','):
                line_after_removal = stripped_line + ',\n'
            else:
                line_after_removal = stripped_line + '\n' # Already has comma, just ensure newline

            indentation = re.match(r"(\s*)", line_after_removal).group(1) if re.match(r"(\s*)", line_after_removal) else '                                    ' # Default indent
            new_link_line = indentation + "\"extracted_links\": item.get(\"extracted_links\", []),\n"

            new_content_lines.append(line_after_removal)
            new_content_lines.append(new_link_line)
            modified = True
            inside_post_dict = False # Assume we're done with this specific 'post' dict modification
            transformed_post_block_found = False # Reset for safety if multiple such blocks (unlikely here)
        else:
            new_content_lines.append(line_after_removal) # Keep line as is (or after old_url removal)

        # Reset flags if we leave the block where transformed_post is defined (e.g., on a '}' that closes it)
        if transformed_post_block_found and line.strip() == "}": # This is a simplification
            transformed_post_block_found = False
            inside_post_dict = False


    if not modified:
        print(f"Warning: 'permalink' line not found in the expected context in {filepath}. 'extracted_links' might not have been added.")

    with open(filepath, 'w') as f:
        f.writelines(new_content_lines)

    print(f"Attempted modification of {filepath} for 'extracted_links'. Modified: {modified}")

if __name__ == "__main__":
    try:
        modify_scheduler_for_links_v2()
    except Exception as e:
        print(f"Error modifying scheduler/tasks.py: {e}")
        sys.exit(1)
