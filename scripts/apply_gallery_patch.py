#!/usr/bin/env python3
"""Patch the decoded legacy activity without relying on JADX formatting."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
matches = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/EnterOneActivity.smali"))
if len(matches) != 1:
    raise SystemExit("Expected exactly one EnterOneActivity.smali; found %d" % len(matches))
p = matches[0]
lines = p.read_text().splitlines()

def method_bounds(prefix):
    start = next((i for i, line in enumerate(lines) if line.startswith(".method") and prefix in line), None)
    if start is None:
        raise SystemExit("Method not found: " + prefix)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == ".end method"), None)
    if end is None:
        raise SystemExit("Unterminated method: " + prefix)
    return start, end

# Attach UI after the activity has completed its own view initialization.
if not any("GalleryImages;->attach" in line for line in lines):
    start, end = method_bounds("onCreate(")
    target = next((i for i in range(start + 1, end) if lines[i].strip() == "return-void"), None)
    if target is None:
        raise SystemExit("Could not find onCreate return")
    lines.insert(target, "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->attach(Landroid/app/Activity;)V")

# Apply selected paths at the beginning of the existing save routine.
start, end = method_bounds("_saveT()V")
if not any("GalleryImages;->apply" in line for line in lines[start:end]):
    target = next((i for i in range(start + 1, end) if "->saveX:Landroid/content/SharedPreferences;" in lines[i]), None)
    if target is None:
        raise SystemExit("Could not find saveX access inside _saveT")
    lines.insert(target, "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->apply(Landroid/app/Activity;)V")
    end += 1

# Route the gallery picker result to the helper.
if not any(line.startswith(".method protected onActivityResult(IILandroid/content/Intent;)V") for line in lines):
    lines.extend([
        "",
        ".method protected onActivityResult(IILandroid/content/Intent;)V",
        "    .locals 0",
        "    invoke-super {p0, p1, p2, p3}, Landroidx/appcompat/app/AppCompatActivity;->onActivityResult(IILandroid/content/Intent;)V",
        "    invoke-static {p0, p1, p2, p3}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V",
        "    return-void",
        ".end method",
    ])

p.write_text("\n".join(lines) + "\n")
print("Patched", p)
