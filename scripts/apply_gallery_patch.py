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

# Flatten PDF pages to bitmap before embedding; this preserves fallback emoji glyphs on printers.
activity = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity.smali"))
if len(activity) != 1:
    raise SystemExit("Expected exactly one ExzamVActivity.smali; found %d" % len(activity))
vp = activity[0]
vlines = vp.read_text().splitlines()
start, end = method_bounds(vlines, "PD(Landroid/graphics/pdf/PdfDocument;)V")
pdf_method = vlines[start:end]
import re

# Match the actual Smali register names instead of assuming a fixed pair
# (the original APK uses different registers across build variants).
draw_pattern = re.compile(
    r"^(\\s*)invoke-virtual\\s+\\{([^}]+)\\},\\s*"
    r"Landroid/widget/LinearLayout;->draw\\(Landroid/graphics/Canvas;\\)V\\s*$"
)
patched_draws = 0
for index, line in enumerate(pdf_method):
    match = draw_pattern.match(line)
    if match:
        registers = match.group(2)
        if len([part.strip() for part in registers.split(",")]) != 2:
            continue
        pdf_method[index] = (
            f"{match.group(1)}invoke-static {{{registers}}}, "
            "Lcom/nasa/edateor/exsam/A11/GalleryImages;->"
            "drawPdfRaster(Landroid/view/View;Landroid/graphics/Canvas;)V"
        )
        patched_draws += 1

if patched_draws == 0 and not any("GalleryImages;->drawPdfRaster" in line for line in pdf_method):
    candidates = [line.strip() for line in pdf_method if "->draw(Landroid/graphics/Canvas;)V" in line]
    raise SystemExit(
        "Could not patch PDF page drawing calls; draw() candidates: "
        + repr(candidates)
    )
vlines[start:end] = pdf_method
vp.write_text("\n".join(vlines) + "\n")
print("Patched both PDF question adapters and rasterized PDF page drawing")

