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
    'Class.forName("com.nasa.edateor.exsam.A11.FileUtil")',
    'getMethod("getJpegRotate", String.class)',
    "private static int jpegRotation(File file)", "Matrix transform = new Matrix()",
    "transform.postRotate(rotation)",
    "WeakReference<LinearLayout> preview",
    "s.preview = new WeakReference<>(preview)",
    "CREATED_PENDING_PREFIX",
    "final ArrayList<String> createdPaths",
    "private static String createdPendingKey(Activity a)",
    "pendingCreatedPaths",
    "s.createdPaths.add(copied)",
    "LinearLayout preview = s.preview == null ? null : s.preview.get()",
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
assert "if (imageRow != null && inRow == 1)" in render, "a lone image in the last row must use full width"
assert "params.width = ViewGroup.LayoutParams.MATCH_PARENT" in render
assert "params.weight = 0f" in render
assert 'if (!(value instanceof List<?>)) return; // Old questions without images are unchanged.' in render
assert "root.addView(grid" in render
assert "while(root.getChildCount()>1)" not in helper
decode_start = helper.index("private static Bitmap decode(")
decode_end = helper.index("/** Release detached", decode_start)
decode = helper[decode_start:decode_end]
assert "int rotation = jpegRotation(file)" in decode
assert "Bitmap.createBitmap(decoded, 0, 0," in decode
assert "decoded.recycle()" in decode
assert "return decoded;" in decode, "orientation failures must preserve the original decoded bitmap"

preview_start = helper.index("private static void renderPreview(")
preview_end = helper.index("public static void apply(", preview_start)
assert ".delete()" not in helper[preview_start:preview_end], "preview deletion must be deferred until save succeeds"
assert "if (!s.paths.contains(old))" in helper or "if (!current.paths.contains(oldPath))" in helper
assert "for (String item : selected) if (!original.contains(item)) out.add(item)" in helper, "legacy pending recovery must exclude original question images"
assert "restored.cameraFile = restoreCameraFile(a)" in helper
assert ".putString(cameraPendingKey(a), s.cameraFile.getAbsolutePath()).commit()" in helper
assert "remove(cameraPendingKey(a)).apply()" in helper
assert helper.index("releaseBitmaps(previous)") < helper.index("removeView(previous)")
preview_start = helper.index("private static void renderPreview(")
preview_end = helper.index("public static void apply(", preview_start)
preview = helper[preview_start:preview_end]
assert "releaseBitmaps(preview.getChildAt(i))" in preview
assert preview.index("releaseBitmaps(preview.getChildAt(i))") < preview.index("preview.removeAllViews()")

pending_signature = ("private static boolean savePending(" if "private static boolean savePending(" in helper else "private static void savePending(")
pending_start = helper.index(pending_signature)
pending_end = helper.index("private static int dp(", pending_start)
pending = helper[pending_start:pending_end]
assert ".putString(createdKey, created.toString()).commit()" in pending
assert "for (String path : s.createdPaths)" in pending
if "private static boolean savePending(" in helper:
    assert "boolean saved = prefs.edit().putString(selectedKey, selected.toString())" in pending
    assert ".putString(createdKey, created.toString()).commit()" in pending
    assert "return saved;" in pending and "return false;" in pending
    assert "snapshotReady = true;" in pending
    assert "restorePending(prefs, selectedKey, createdKey" in pending
    assert "if (!saved) {" in pending
    assert "if (snapshotReady)" in pending
    rollback_start = helper.index("private static void restorePending(")
    rollback_end = helper.index("private static boolean savePending(", rollback_start)
    rollback = helper[rollback_start:rollback_end]
    assert "if (hadSelected) editor.putString(selectedKey, oldSelected)" in rollback
    assert "if (hadCreated) editor.putString(createdKey, oldCreated)" in rollback
    assert "editor.apply()" in rollback
assert "selected.append('\\n')" in helper
assert "created.append('\\n')" in helper
assert "selected.append('\\\\n')" not in helper
assert "created.append('\\\\n')" not in helper

copy_start = helper.index("private static String copyStream(")
copy_end = helper.index("/** Read the legacy app's EXIF", copy_start)
copy_method = helper[copy_start:copy_end]
assert "try (FileOutputStream out = new FileOutputStream(destination))" in copy_method
assert "out.getFD().sync()" in copy_method
assert "if (!complete) destination.delete()" in copy_method
assert copy_method.index("try (FileOutputStream out = new FileOutputStream(destination))") < copy_method.index("out.flush()")
assert "private static ArrayList<String> pendingCreatedPaths(" in pending
assert "if (raw != null)" in pending
assert "for (String item : selected) if (!original.contains(item)) out.add(item)" in pending
assert helper.count("s.createdPaths.add(copied)") == 3, "camera, multi-select and single-select imports must all be tracked"

original_start = helper.index("private static ArrayList<String> originalPaths(")
original_end = helper.index("private static ArrayList<String> pendingPaths(", original_start)
original_method = helper[original_start:original_end]
assert 'Object value = question(a).get("images");' in original_method
assert 'if ("A".equals(field(a, "Tipee"))) return out;' not in original_method, "new-question recovery must recognize already committed image paths"

activity_result_start = helper.index("public static void onActivityResult(")
activity_result_end = helper.index("private static String copyUri(", activity_result_start)
activity_result = helper[activity_result_start:activity_result_end]
if "private static boolean savePending(" in helper:
    assert "if (!savePending(a, s))" in activity_result, "camera import must roll back if pending state cannot be persisted"
    assert "ArrayList<String> importedPaths = new ArrayList<>()" in activity_result
    assert "if (imported > 0 && !savePending(a, s))" in activity_result, "gallery imports must roll back if pending state cannot be persisted"
    assert "s.createdPaths.remove(copied)" in activity_result
    preview_start = helper.index("private static void renderPreview(")
    preview_end = helper.index("public static void apply(", preview_start)
    preview = helper[preview_start:preview_end]
    assert "int index = s.paths.indexOf(path)" in preview
    assert "if (!savePending(a, s)) s.paths.add(Math.min(index, s.paths.size()), path);" in preview, "failed delete-state persistence must restore the selection"

finish_start = helper.index("public static void finishSave(")
finish_end = helper.index("public static void discard(", finish_start)
finish = helper[finish_start:finish_end]
assert "for (String created : s.createdPaths)" in finish
assert "if (!s.paths.contains(created))" in finish
assert "s.createdPaths.clear()" in finish
assert ".remove(createdPendingKey(a))" in finish
assert finish.index("if (!committed)") < finish.index("for (String created : s.createdPaths)")

discard_start = helper.index("public static void discard(")
discard_end = helper.index("public static void renderQuestion(", discard_start)
discard = helper[discard_start:discard_end]
assert "pendingCreatedPaths(a, selected, original)" in discard
assert "for (String created : s.createdPaths)" in discard
if "private static boolean savePending(" in helper:
    assert "if (s.originalPaths.contains(created)) continue;" in discard, "cancel after a successful question commit must not delete referenced files"
assert "File file = internalFile(a, created)" in discard
assert ".remove(createdPendingKey(a))" in discard
assert "for (String selected : s.paths)" not in discard

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

assert "WeakReference<LinearLayout> preview" in helper
assert "s.preview = new WeakReference<>(preview)" in helper
assert "LinearLayout preview = s.preview == null ? null : s.preview.get()" in helper
assert "s.preview.getChildCount()" not in helper
assert "s.preview.addView(item)" not in helper

print("Gallery/camera, process-recovery, restricted FileProvider, save transaction, cancel cleanup, vertical row layout, bitmap release, weak Activity/view retention, both adapters, and both PDF pages passed static checks")
