import sys
import re
import os

def modify_scheduler_for_links(filepath="scheduler/tasks.py"):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist. Cannot modify.")
        sys.exit(1)

    with open(filepath, 'r') as f:
        content = f.read()

    # Target for insertion: inside the "post": { ... } dictionary within transformed_post
    # We want to ensure "extracted_links" is present.
    # Let's find the line with "permalink": item.get("permalink"), and add after it.

    # This regex looks for the "permalink": ... line within the "post": { ... } block
    # and adds the "extracted_links" line after it, ensuring a comma is correctly placed.
    # It also handles the case where "extracted_urls" might exist from a previous version.

    # Step 1: Remove any old "extracted_urls" line to avoid duplication or conflict
    content = re.sub(r'\s*"extracted_urls":\s*item\.get\("extracted_urls_from_text",\s*\[\]\),?\s*',
                     '\n', # Replace with a newline, comma will be handled by next step or was already there
                     content)

    # Step 2: Add "extracted_links" after "permalink"
    # Pattern to find: "permalink": item.get("permalink"),
    # Add after this: "extracted_links": item.get("extracted_links", []),

    # This regex looks for the "permalink": item.get("permalink"), line
    # It captures the line and the comma if it exists.
    # Then it adds the "extracted_links" line, ensuring a comma is added if needed.

    # A simpler approach: ensure the "post" dictionary assignment includes the field.
    # This is safer than complex regex over multiple lines.
    # Find: "permalink": item.get("permalink"),
    # Replace with: "permalink": item.get("permalink"),
    #                "extracted_links": item.get("extracted_links", []),

    # Let's try to replace the entire 'post' dictionary content for robustness
    # This assumes the structure of other fields (id, text, timestamp_str, permalink) is stable.

    new_post_dict_content = '''\
"id": item.get("post_id", f"scraped_{page_url.split('/')[-1]}_{idx}_{int(time.time())}"),
                                "text": item.get("text"),
                                "timestamp_str": item.get("timestamp_str"),
                                "permalink": item.get("permalink"),
                                "extracted_links": item.get("extracted_links", [])''' # New field added

    # Regex to find the "post": { ... } block and replace its contents
    # It captures the opening ("post": {) and closing (})
    # and replaces everything in between.
    # Need to be careful with indentation if new_post_dict_content is multi-line.
    # So, ensure new_post_dict_content has appropriate leading spaces for each line.

    indented_new_post_dict_content = "\n".join(["                                " + line for line in new_post_dict_content.splitlines()])

    content, num_subs = re.subn(r'("post":\s*\{)([^}]*?)(\s*\})',
                                rf'\1{indented_new_post_dict_content}\3',
                                content,
                                flags=re.DOTALL,
                                count=1) # Apply only to the first match (should be only one in this context)

    if num_subs == 0:
        print(f"Error: Could not find the 'post' dictionary structure in {filepath} to inject 'extracted_links'. File not modified.")
        # sys.exit(1) # Don't exit, let subsequent steps run to see full status

    with open(filepath, 'w') as f:
        f.write(content)

    if num_subs > 0:
        print(f"Modified {filepath} to include 'extracted_links' in data transformation (replaced 'post' dict content).")

if __name__ == "__main__":
    try:
        modify_scheduler_for_links()
    except Exception as e:
        print(f"Error modifying scheduler/tasks.py: {e}")
        # sys.exit(1) # Allow script to finish to see all outputs
