#!/usr/bin/env python3
"""Apply the gallery/camera image feature to the decoded legacy APK."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
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
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(".method") and prefix in line), None)
    if start is None:
        raise SystemExit("Method not found: " + prefix)
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip() == ".end method"), None)
    if end is None:
        raise SystemExit("Unterminated method: " + prefix)
    return start, end


editor_matches = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/EnterOneActivity.smali"))
if len(editor_matches) != 1:
    raise SystemExit("Expected exactly one EnterOneActivity.smali; found %d" % len(editor_matches))
editor = editor_matches[0]
lines = editor.read_text().splitlines()

start, end = method_bounds(lines, "onCreate(")
if not any("GalleryImages;->attach" in line for line in lines[start:end]):
    target = next((i for i in range(start + 1, end)
                   if lines[i].strip() == "return-void"), None)
    if target is None:
        raise SystemExit("Could not find onCreate return")
    lines.insert(target,
        "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->attach(Landroid/app/Activity;)V")

start, end = method_bounds(lines, "_saveT()V")
if not any("GalleryImages;->apply" in line for line in lines[start:end]):
    target = next((i for i in range(start + 1, end)
                   if "->saveX:Landroid/content/SharedPreferences;" in lines[i]), None)
    if target is None:
        raise SystemExit("Could not find saveX access inside _saveT")
    lines.insert(target,
        "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->apply(Landroid/app/Activity;)V")

start, end = method_bounds(lines, "_saveT()V")
commit_index = next((i for i in range(start + 1, end)
                     if "Landroid/content/SharedPreferences$Editor;->commit()Z" in lines[i]), None)
if commit_index is None:
    raise SystemExit("Could not find SharedPreferences.commit() in _saveT")
if not any("GalleryImages;->finishSave" in line for line in lines[start:end]):
    lines[commit_index + 1:commit_index + 1] = [
        "    move-result v0",
        "    invoke-static {p0, v0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->finishSave(Landroid/app/Activity;Z)V",
    ]

start, end = method_bounds(lines, "_bacef()V")
if not any("GalleryImages;->discard" in line for line in lines[start:end]):
    target = next((i for i in range(start + 1, end)
                   if lines[i].strip().startswith("new-instance")), None)
    if target is None:
        raise SystemExit("Could not find _bacef start")
    lines.insert(target,
        "    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->discard(Landroid/app/Activity;)V")

if not any(line.startswith(".method protected onActivityResult(IILandroid/content/Intent;)V")
           for line in lines):
    lines.extend([
        "", ".method protected onActivityResult(IILandroid/content/Intent;)V", "    .locals 0",
        "    invoke-super {p0, p1, p2, p3}, Landroidx/appcompat/app/AppCompatActivity;->onActivityResult(IILandroid/content/Intent;)V",
        "    invoke-static {p0, p1, p2, p3}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V",
        "    return-void", ".end method",
    ])
editor.write_text("\n".join(lines) + "\n")

for adapter_name in ("Listview1Adapter", "Listview1_5Adapter"):
    matches = list(root.glob(
        "smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$" + adapter_name + ".smali"))
    if len(matches) != 1:
        raise SystemExit("Expected exactly one %s; found %d" % (adapter_name, len(matches)))
    adapter = matches[0]
    adapter_lines = adapter.read_text().splitlines()
    descriptor = "Lcom/nasa/edateor/exsam/A11/ExzamVActivity$" + adapter_name + ";"
    start, end = method_bounds(adapter_lines,
        "getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;")
    if not any("GalleryImages;->renderQuestion" in line for line in adapter_lines[start:end]):
        target = next((i for i in range(start + 1, end)
                       if adapter_lines[i].strip() == "return-object p2"), None)
        if target is None:
            raise SystemExit("Could not find getView return in " + adapter_name)
        adapter_lines[target:target] = [
            "    iget-object v0, p0, " + descriptor + "->this$0:Lcom/nasa/edateor/exsam/A11/ExzamVActivity;",
            "    iget-object v1, p0, " + descriptor + "->_data:Ljava/util/ArrayList;",
            "    invoke-virtual {v1, p1}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;",
            "    move-result-object v1",
            "    check-cast v1, Ljava/util/HashMap;",
            "    invoke-static {v0, p2, v1}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->renderQuestion(Landroid/app/Activity;Landroid/view/View;Ljava/util/HashMap;)V",
        ]
    adapter.write_text("\n".join(adapter_lines) + "\n")

activity_matches = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity.smali"))
if len(activity_matches) != 1:
    raise SystemExit("Expected exactly one ExzamVActivity.smali; found %d" % len(activity_matches))
activity = activity_matches[0]
activity_lines = activity.read_text().splitlines()
start, end = method_bounds(activity_lines, "PD(Landroid/graphics/pdf/PdfDocument;)V")
pdf_method = activity_lines[start:end]
draw_pattern = re.compile(
    r"^(\s*)invoke-virtual\s+\{([^}]+)\},\s*"
    r"Landroid/widget/LinearLayout;->draw\(Landroid/graphics/Canvas;\)V\s*$"
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
existing_draws = sum("GalleryImages;->drawPdfRaster" in line for line in pdf_method)
if patched_draws + existing_draws < 2:
    raise SystemExit("Expected raster drawing for both PDF pages; found %d" % (patched_draws + existing_draws))
activity_lines[start:end] = pdf_method
activity.write_text("\n".join(activity_lines) + "\n")
provider_paths = root / "res/xml/provider_paths.xml"
if not provider_paths.is_file():
    raise SystemExit("FileProvider paths resource is missing")
provider_xml = provider_paths.read_text(encoding="utf-8")
restricted_provider_path = '<external-files-path name="exam25_camera" path="Pictures/" />'
if restricted_provider_path not in provider_xml:
    provider_xml, replacements = re.subn(
        r'<external-path\s+name="external_files"\s+path="\."\s*/>',
        restricted_provider_path,
        provider_xml,
    )
    if replacements != 1:
        raise SystemExit("Could not safely restrict FileProvider to app Pictures directory")
    provider_paths.write_text(provider_xml, encoding="utf-8")
print("Restricted FileProvider to app-specific Pictures directory")
print("Patched editor save/cancel lifecycle, both question adapters, and both PDF pages")
