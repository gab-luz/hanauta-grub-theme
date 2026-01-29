import os
import re

THEME_DIR = "grub-theme"
THEME_FILE = os.path.join(THEME_DIR, "theme.txt")

def verify():
    if not os.path.exists(THEME_FILE):
        print("FAIL: theme.txt missing")
        return False

    with open(THEME_FILE, 'r') as f:
        content = f.read()

    # Find file references
    # Pattern: property = "filename" or "path/filename"
    # Also ignore special values

    # Simple regex to find quoted strings that look like filenames
    # This is heuristic.
    # Exclude strings with *, which are patterns
    quoted = re.findall(r'"([^*"]+\.(?:png|jpg|jpeg|tga|pf2|ttf))"', content)

    # Also look for patterns like selection_*.png
    patterns = re.findall(r'"([^"]+\*\.[a-z]+)"', content)

    missing = []

    for filename in quoted:
        path = os.path.join(THEME_DIR, filename)
        if not os.path.exists(path):
            # Check if it's in a subdirectory referenced in the file
            # If the filename in theme.txt is "icons/foo.png", path is "grub-theme/icons/foo.png" which is correct.
            missing.append(filename)

    for pattern in patterns:
        # Check if any file matches the pattern
        # e.g. selection_*.png
        # We assume the * matches any string.
        # Check directory
        dirname = os.path.dirname(pattern)
        basename = os.path.basename(pattern)

        search_dir = os.path.join(THEME_DIR, dirname)
        if not os.path.exists(search_dir):
            missing.append(pattern + " (dir missing)")
            continue

        # Convert glob to regex
        # escape dots
        regex = basename.replace('.', r'\.').replace('*', '.*')

        found = False
        for f in os.listdir(search_dir):
            # print(f"Checking {f} against {regex}")
            if re.match(regex, f):
                found = True
                break
        if not found:
            print(f"Pattern {pattern} (regex {regex}) not found in {search_dir}")
            missing.append(pattern)

    if missing:
        print("FAIL: Missing referenced files:")
        for m in missing:
            print(f"  - {m}")
        return False

    print("PASS: theme.txt references valid files (heuristic).")
    return True

if __name__ == "__main__":
    if verify():
        exit(0)
    else:
        exit(1)
