from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1])
editor_files = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/EnterOneActivity.smali"))
assert len(editor_files) == 1
editor = editor_files[0].read_text()
for token in (
    "GalleryImages;->attach(Landroid/app/Activity;)V",
    "GalleryImages;->apply(Landroid/app/Activity;)V",
    "GalleryImages;->finishSave(Landroid/app/Activity;Z)V",
    "GalleryImages;->discard(Landroid/app/Activity;)V",
    "GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V",
):
    assert token in editor, token
save_start = editor.index(".method public _saveT()V")
save_end = editor.index(".end method", save_start)
save = editor[save_start:save_end]
assert save.index("GalleryImages;->apply") < save.index("SharedPreferences$Editor;->commit()Z")
assert save.index("SharedPreferences$Editor;->commit()Z") < save.index("GalleryImages;->finishSave")
assert "move-result v0" in save[save.index("SharedPreferences$Editor;->commit()Z"):save.index("GalleryImages;->finishSave")]
back_start = editor.index(".method public _bacef()V")
back_end = editor.index(".end method", back_start)
assert "GalleryImages;->discard" in editor[back_start:back_end]

for adapter_name in ("Listview1Adapter", "Listview1_5Adapter"):
    adapters = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$" + adapter_name + ".smali"))
    assert len(adapters) == 1
    source = adapters[0].read_text()
    start = source.index(".method public getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;")
    end = source.index(".end method", start)
    assert "GalleryImages;->renderQuestion(Landroid/app/Activity;Landroid/view/View;Ljava/util/HashMap;)V" in source[start:end]
    assert source[start:end].count("GalleryImages;->renderQuestion") == 1

activity_files = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity.smali"))
assert len(activity_files) == 1
activity = activity_files[0].read_text()
start = activity.index("PD(Landroid/graphics/pdf/PdfDocument;)V")
start = activity.rfind(".method", 0, start)
end = activity.index(".end method", start)
pdf = activity[start:end]
assert pdf.count("GalleryImages;->drawPdfRaster(Landroid/view/View;Landroid/graphics/Canvas;)V") == 2

manifest = (root / "AndroidManifest.xml").read_text()
assert 'android:name="androidx.core.content.FileProvider"' in manifest
assert 'android:authorities="com.nasa.edateor.exsam.A11.provider"' in manifest
assert 'android:name="android.support.FILE_PROVIDER_PATHS"' in manifest
provider_paths = root / "res/xml/provider_paths.xml"
assert provider_paths.is_file()
provider_xml = provider_paths.read_text()
assert 'external-files-path' in provider_xml and 'path="Pictures/"' in provider_xml
assert '<external-path' not in provider_xml, "FileProvider must not expose the whole shared storage"

helper = Path("src/com/nasa/edateor/exsam/A11/GalleryImages.java").read_text()
for token in (
    "Intent.ACTION_OPEN_DOCUMENT", "MediaStore.ACTION_IMAGE_CAPTURE",
    'Class.forName("androidx.core.content.FileProvider")', "getUriForFile",
    "MediaStore.EXTRA_OUTPUT", "Intent.FLAG_GRANT_WRITE_URI_PERMISSION",
    "ClipData.newRawUri", "QUESTION_IMAGES_TAG", 'question.get("images")',
    "CAMERA_PENDING_PREFIX", "cameraPendingKey", "restoreCameraFile",
    "getCanonicalPath", "Cannot persist camera output path",
    "private static void releaseBitmaps(View view)", "bitmap.recycle()",
):
    assert token in helper, token
assert "new ArrayList<>(s.paths)" in helper or "new ArrayList<>(current.paths)" in helper
assert "import androidx.core.content.FileProvider;" not in helper, "helper must compile against android.jar without an extra AndroidX jar"
assert "s.applied = true" in helper or "current.applied = true" in helper
assert "if (!s.applied)" in helper or "if (!current.applied)" in helper
render_start = helper.index("public static void renderQuestion(")
render_end = helper.index("public static void drawPdfRaster", render_start)
render = helper[render_start:render_end]
assert "HorizontalScrollView" not in render, "PDF images must not be clipped by a horizontal scroller"
assert "grid.setOrientation(LinearLayout.VERTICAL)" in render
assert "inRow == 2" in render, "question images should flow into two-column rows"
assert "root.addView(grid" in render
assert "while(root.getChildCount()>1)" not in helper
preview_start = helper.index("private static void renderPreview(")
preview_end = helper.index("public static void apply(", preview_start)
assert ".delete()" not in helper[preview_start:preview_end], "preview deletion must be deferred until save succeeds"
assert "if (!s.paths.contains(old))" in helper or "if (!current.paths.contains(oldPath))" in helper
assert "if (!s.originalPaths.contains(selected))" in helper or "if (!current.originalPaths.contains(selected))" in helper
assert "created.cameraFile = restoreCameraFile(a)" in helper
assert ".putString(cameraPendingKey(a), s.cameraFile.getAbsolutePath()).commit()" in helper
assert "remove(cameraPendingKey(a)).apply()" in helper
assert helper.index("releaseBitmaps(previous)") < helper.index("removeView(previous)")
preview_start = helper.index("private static void renderPreview(")
preview_end = helper.index("public static void apply(", preview_start)
preview = helper[preview_start:preview_end]
assert "releaseBitmaps(s.preview.getChildAt(i))" in preview
assert preview.index("releaseBitmaps(s.preview.getChildAt(i))") < preview.index("s.preview.removeAllViews()")

layout_path = root / "res/layout/custam_v1.xml"
assert layout_path.is_file()
layout = ET.parse(layout_path).getroot()
android_ns = "{http://schemas.android.com/apk/res/android}"
assert layout.attrib.get(android_ns + "orientation") == "vertical"
linear1 = next((child for child in layout if child.attrib.get(android_ns + "id") == "@id/linear1"), None)
assert linear1 is not None and linear1.attrib.get(android_ns + "orientation") == "horizontal"
for adapter_name in ("Listview1Adapter", "Listview1_5Adapter"):
    adapters = list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$" + adapter_name + ".smali"))
    assert len(adapters) == 1
    adapter_source = adapters[0].read_text()
    assert "invoke-static {v0, p2, v1}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->renderQuestion" in adapter_source

print("Gallery/camera, process-recovery, restricted FileProvider, save transaction, cancel cleanup, vertical row layout, bitmap release, both adapters, and both PDF pages passed static checks")
