#!/usr/bin/env python3
"""Patch the decoded legacy activity and question renderer."""
from pathlib import Path
import sys

root = Path(sys.argv[1])

# AAPT2 rejects six framework-generated drawable names beginning with '$'.
invalid_names = [
    "$avd_hide_password__0", "$avd_hide_password__1", "$avd_hide_password__2",
    "$avd_show_password__0", "$avd_show_password__1", "$avd_show_password__2",
]
for path in list(root.rglob("*")):
    if path.is_file() and path.suffix.lower() in {".xml", ".smali", ".txt", ".json"}:
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = original
        for old in invalid_names:
            updated = updated.replace(old, old[1:])
        if updated != original:
            path.write_text(updated, encoding="utf-8")
for path in list(root.rglob("*")):
    if path.is_file() and path.name in {name + ".xml" for name in invalid_names}:
        path.rename(path.with_name(path.name[1:]))
print("Normalized six invalid $avd drawable resource names for AAPT2")

def method_bounds(lines, prefix):
    start = next((i for i, line in enumerate(lines) if line.startswith(".method") and prefix in line), None)
    if start is None:
        raise SystemExit("Method not found: " + prefix)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == ".end method"), None)
    if end is None:
        raise SystemExit("Unterminated method: " + prefix)
    return start, end

# Patch the question editor.
matches = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/EnterOneActivity.smali"))
if len(matches) != 1:
    raise SystemExit("Expected exactly one EnterOneActivity.smali; found %d" % len(matches))
p = matches[0]
lines = p.read_text().splitlines()
if not any("GalleryImages;->attach" in line for line in lines):
    start, end = method_bounds(lines, "onCreate(")
    target = next((i for i in range(start + 1, end) if lines[i].strip() == "return-void"), None)
    if target is None:
        raise SystemExit("Could not find onCreate return")
    lines.insert(target, "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->attach(Landroid/app/Activity;)V")
start, end = method_bounds(lines, "_saveT()V")
if not any("GalleryImages;->apply" in line for line in lines[start:end]):
    target = next((i for i in range(start + 1, end) if "->saveX:Landroid/content/SharedPreferences;" in lines[i]), None)
    if target is None:
        raise SystemExit("Could not find saveX access inside _saveT")
    lines.insert(target, "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->apply(Landroid/app/Activity;)V")
if not any(line.startswith(".method protected onActivityResult(IILandroid/content/Intent;)V") for line in lines):
    lines.extend([
        "", ".method protected onActivityResult(IILandroid/content/Intent;)V", "    .locals 0",
        "    invoke-super {p0, p1, p2, p3}, Landroidx/appcompat/app/AppCompatActivity;->onActivityResult(IILandroid/content/Intent;)V",
        "    invoke-static {p0, p1, p2, p3}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V",
        "    return-void", ".end method",
    ])
p.write_text("\n".join(lines) + "\n")

# Patch the adapter that supplies question rows to the template and PDF.
adapters = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$Listview1Adapter.smali"))
if len(adapters) != 1:
    raise SystemExit("Expected exactly one Listview1Adapter.smali; found %d" % len(adapters))
ap = adapters[0]
alines = ap.read_text().splitlines()
start, end = method_bounds(alines, "getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;")
if not any("GalleryImages;->renderQuestion" in line for line in alines[start:end]):
    target = next((i for i in range(start + 1, end) if alines[i].strip() == "return-object p2"), None)
    if target is None:
        raise SystemExit("Could not find getView return-object p2")
    alines[target:target] = [
        "    iget-object v0, p0, Lcom/nasa/edateor/exsam/A11/ExzamVActivity$Listview1Adapter;->this$0:Lcom/nasa/edateor/exsam/A11/ExzamVActivity;",
        "    iget-object v1, p0, Lcom/nasa/edateor/exsam/A11/ExzamVActivity$Listview1Adapter;->_data:Ljava/util/ArrayList;",
        "    invoke-virtual {v1, p1}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;",
        "    move-result-object v1",
        "    check-cast v1, Ljava/util/HashMap;",
        "    invoke-static {v0, p2, v1}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->renderQuestion(Landroid/app/Activity;Landroid/view/View;Ljava/util/HashMap;)V",
    ]
ap.write_text("\n".join(alines) + "\n")

# Patch the continuation-page adapter too; PDF generation draws both page layouts.
adapters_5 = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$Listview1_5Adapter.smali"))
if len(adapters_5) != 1:
    raise SystemExit("Expected exactly one Listview1_5Adapter.smali; found %d" % len(adapters_5))
ap5 = adapters_5[0]
a5lines = ap5.read_text().splitlines()
start, end = method_bounds(a5lines, "getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;")
if not any("GalleryImages;->renderQuestion" in line for line in a5lines[start:end]):
    target = next((i for i in range(start + 1, end) if a5lines[i].strip().startswith("return-object ")), None)
    if target is None:
        raise SystemExit("Could not find getView return in continuation adapter")
    a5lines[target:target] = [
        "    iget-object v0, p0, Lcom/nasa/edateor/exsam/A11/ExzamVActivity$Listview1_5Adapter;->this$0:Lcom/nasa/edateor/exsam/A11/ExzamVActivity;",
        "    iget-object v1, p0, Lcom/nasa/edateor/exsam/A11/ExzamVActivity$Listview1_5Adapter;->_data:Ljava/util/ArrayList;",
        "    invoke-virtual {v1, p1}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;",
        "    move-result-object v1",
        "    check-cast v1, Ljava/util/HashMap;",
        "    invoke-static {v0, p2, v1}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->renderQuestion(Landroid/app/Activity;Landroid/view/View;Ljava/util/HashMap;)V",
    ]
ap5.write_text("\n".join(a5lines) + "\n")
print("Patched question editor and both question-template/PDF page adapters")
