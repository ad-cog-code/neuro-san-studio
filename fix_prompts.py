"""Fix Section 7 -> Section 6 in all sub-agent prompt files."""
import os
import glob

prompt_dir = r"dealcraft\prompts\v2"
files = glob.glob(os.path.join(prompt_dir, "*-v2.md"))

# Read one file to see exactly what the text looks like
sample = files[0]
with open(sample, "r", encoding="utf-8") as f:
    content = f.read()

# Find the step 4 line
for line in content.splitlines():
    if "Step 4" in line:
        print(f"Sample line: {repr(line)}")
        break

replacements = [
    # Format 1: already fixed bid-qualification (skip)
    # Format 2: the short format used by most agents
    (
        "**Step 4**: write_file to path in Section 7.",
        "**Step 4**: write_file to ONLY YOUR OWN path in Section 6. Do NOT write files for other agents.",
    ),
    # Format 3: long format (in case any remain)
    (
        "**Step 4**: Write output to the path in **Section 7** using `write_file`.",
        "**Step 4**: Write output to ONLY YOUR OWN path in **Section 6** using `write_file`. Do NOT write files assigned to other agents.",
    ),
]

count = 0
for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    changed = False
    for old_text, new_text in replacements:
        if old_text in content:
            content = content.replace(old_text, new_text)
            changed = True
    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
        print(f"Fixed: {os.path.basename(fpath)}")
    else:
        print(f"No match: {os.path.basename(fpath)}")

print(f"\nTotal: {count}/{len(files)} files fixed")
