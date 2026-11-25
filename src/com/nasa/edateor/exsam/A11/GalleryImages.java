package com.nasa.edateor.exsam.A11;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.drawable.BitmapDrawable;
import android.net.Uri;
import android.os.Environment;
import android.provider.MediaStore;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Toast;
import java.io.*;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.*;

public final class GalleryImages {
    private static final int GALLERY_REQUEST = 27125;
    private static final int CAMERA_REQUEST = 27126;
    private static final String PREFS = "exam25_gallery_pending";
    private static final String CAMERA_PENDING_PREFIX = "exam25_camera_pending_";
    private static final String CREATED_PENDING_PREFIX = "exam25_created_pending_";
    private static final String QUESTION_IMAGES_TAG = "exam25_question_images";
    private static final Map<Activity, State> STATES = new WeakHashMap<>();

    private static final class State {
        WeakReference<LinearLayout> preview;
        final ArrayList<String> paths;
        ArrayList<String> originalPaths;
        final ArrayList<String> createdPaths;
        File cameraFile;
        boolean applied;
        State(ArrayList<String> selected, ArrayList<String> original, ArrayList<String> created) {
            paths = selected;
            originalPaths = original;
            createdPaths = created;
        }
    }

    private GalleryImages() { }

    private static Object field(Object object, String name) throws Exception {
        Field f = object.getClass().getDeclaredField(name);
        f.setAccessible(true);
        return f.get(object);
    }

    private static int position(Activity a) throws Exception {
        return (int) ((Double) field(a, "Position")).doubleValue();
    }

    private static String key(Activity a) throws Exception {
        return String.valueOf(field(a, "ID")) + "_" + String.valueOf(field(a, "pppp"))
                + "_" + String.valueOf(field(a, "Tipee")) + "_" + position(a);
    }

    private static String safeKey(Activity a) {
        try { return key(a); } catch (Exception ignored) { return "invalid-question"; }
    }

    private static String cameraPendingKey(Activity a) {
        return CAMERA_PENDING_PREFIX + safeKey(a);
    }

    private static String createdPendingKey(Activity a) {
        return CREATED_PENDING_PREFIX + safeKey(a);
    }

    private static File cameraDirectory(Activity a) throws IOException {
        File dir = a.getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        if (dir == null) throw new IOException("Pictures directory unavailable");
        return dir.getCanonicalFile();
    }

    /** Restore the output file after Android recreates the Activity while the camera is open. */
    private static File restoreCameraFile(Activity a) {
        SharedPreferences prefs = a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE);
        String prefKey = cameraPendingKey(a);
        String path = prefs.getString(prefKey, null);
        if (path == null || path.isEmpty()) return null;
        try {
            File directory = cameraDirectory(a);
            File candidate = new File(path).getCanonicalFile();
            String allowedPrefix = directory.getCanonicalPath() + File.separator;
            if (!candidate.getCanonicalPath().startsWith(allowedPrefix) || !candidate.isFile()) {
                prefs.edit().remove(prefKey).apply();
                return null;
            }
            return candidate;
        } catch (Exception ignored) {
            prefs.edit().remove(prefKey).apply();
            return null;
        }
    }

    @SuppressWarnings("unchecked")
    private static HashMap<String, Object> question(Activity a) throws Exception {
        if ("A".equals(field(a, "Tipee"))) return (HashMap<String, Object>) field(a, "mmmo");
        ArrayList<HashMap<String, Object>> list =
                (ArrayList<HashMap<String, Object>>) field(a, "list_allQ");
        return list.get(position(a));
    }

    private static boolean managed(String path) {
        return path != null && path.startsWith("question_images/") && !path.contains("..");
    }

    private static File internalFile(Activity a, String path) {
        return managed(path) ? new File(a.getFilesDir(), path) : null;
    }

    private static ArrayList<String> originalPaths(Activity a) {
        ArrayList<String> out = new ArrayList<>();
        try {
            Object value = question(a).get("images");
            if (value instanceof List<?>) {
                for (Object item : (List<?>) value)
                    if (item != null && managed(item.toString())) out.add(item.toString());
            }
        } catch (Exception ignored) { }
        return out;
    }

    private static ArrayList<String> pendingPaths(Activity a) {
        ArrayList<String> out = new ArrayList<>();
        try {
            String raw = a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE)
                    .getString(key(a), null);
            if (raw != null && !raw.isEmpty())
                for (String item : raw.split("\\n")) if (managed(item)) out.add(item);
        } catch (Exception ignored) { }
        return out;
    }

    private static boolean savePending(Activity a, State s) {
        try {
            StringBuilder selected = new StringBuilder();
            for (String path : s.paths) {
                if (!managed(path)) continue;
                if (selected.length() > 0) selected.append('\n');
                selected.append(path);
            }
            StringBuilder created = new StringBuilder();
            for (String path : s.createdPaths) {
                if (!managed(path)) continue;
                if (created.length() > 0) created.append('\n');
                created.append(path);
            }
            boolean saved = a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit()
                    .putString(key(a), selected.toString())
                    .putString(createdPendingKey(a), created.toString()).commit();
            if (!saved) Toast.makeText(a, "تعذر حفظ حالة الصور المؤقتة؛ أُلغيت آخر عملية", Toast.LENGTH_LONG).show();
            return saved;
        } catch (Exception e) {
            Toast.makeText(a, "تعذر حفظ حالة الصور المؤقتة؛ أُلغيت آخر عملية", Toast.LENGTH_LONG).show();
            return false;
        }
    }

    private static ArrayList<String> pendingCreatedPaths(Activity a, ArrayList<String> selected,
            ArrayList<String> original) {
        ArrayList<String> out = new ArrayList<>();
        try {
            SharedPreferences prefs = a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE);
            String raw = prefs.getString(createdPendingKey(a), null);
            if (raw != null) {
                for (String item : raw.split("\\n")) if (managed(item)) out.add(item);
            } else {
                // Recover pending sessions created by older builds without an explicit created-file list.
                for (String item : selected) if (!original.contains(item)) out.add(item);
            }
        } catch (Exception ignored) { }
        return out;
    }

    private static State state(Activity a) {
        State existing = STATES.get(a);
        if (existing != null) return existing;
        ArrayList<String> original = originalPaths(a);
        SharedPreferences prefs = a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE);
        ArrayList<String> selected = prefs.contains(safeKey(a))
                ? pendingPaths(a) : new ArrayList<>(original);
        ArrayList<String> created = pendingCreatedPaths(a, selected, original);
        State restored = new State(selected, original, created);
        restored.cameraFile = restoreCameraFile(a);
        STATES.put(a, restored);
        return restored;
    }

    private static int dp(Activity a, int value) {
        return (int) (value * a.getResources().getDisplayMetrics().density + 0.5f);
    }

    public static void attach(final Activity a) {
        try {
            LinearLayout parent = (LinearLayout) field(a, "linear1");
            State s = state(a);
            LinearLayout controls = new LinearLayout(a);
            controls.setOrientation(LinearLayout.HORIZONTAL);

            Button gallery = new Button(a);
            gallery.setText("إضافة صور من المعرض");
            gallery.setOnClickListener(v -> openGallery(a));
            controls.addView(gallery, new LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            Button camera = new Button(a);
            camera.setText("التقاط صورة بالكاميرا");
            camera.setOnClickListener(v -> openCamera(a, s));
            controls.addView(camera, new LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            LinearLayout block = new LinearLayout(a);
            block.setOrientation(LinearLayout.VERTICAL);
            block.addView(controls);
            android.widget.HorizontalScrollView scroll = new android.widget.HorizontalScrollView(a);
            LinearLayout preview = new LinearLayout(a);
            preview.setOrientation(LinearLayout.HORIZONTAL);
            scroll.addView(preview);
            block.addView(scroll);
            s.preview = new WeakReference<>(preview);
            parent.addView(block, Math.max(0, parent.getChildCount() - 1));
            renderPreview(a, s);
        } catch (Exception e) {
            Toast.makeText(a, "تعذر تهيئة إرفاق الصور", Toast.LENGTH_LONG).show();
        }
    }

    private static void openGallery(Activity a) {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("image/*");
        i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        a.startActivityForResult(i, GALLERY_REQUEST);
    }

    private static void openCamera(Activity a, State s) {
        try {
            File dir = cameraDirectory(a);
            if (!dir.exists() && !dir.mkdirs()) throw new IOException("Cannot create directory");
            s.cameraFile = File.createTempFile("exam25_", ".jpg", dir);
            boolean persisted = a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit()
                    .putString(cameraPendingKey(a), s.cameraFile.getAbsolutePath()).commit();
            if (!persisted) throw new IOException("Cannot persist camera output path");
            Class<?> provider = Class.forName("androidx.core.content.FileProvider");
            Method getUri = provider.getMethod("getUriForFile", android.content.Context.class, String.class, File.class);
            Uri uri = (Uri) getUri.invoke(null, a, a.getPackageName() + ".provider", s.cameraFile);
            Intent i = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            i.putExtra(MediaStore.EXTRA_OUTPUT, uri);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            i.setClipData(ClipData.newRawUri("Exam Editor photo", uri));
            a.startActivityForResult(i, CAMERA_REQUEST);
        } catch (Exception e) {
            deleteCameraFile(a, s);
            Toast.makeText(a, "تعذر تشغيل الكاميرا على هذا الجهاز", Toast.LENGTH_LONG).show();
        }
    }

    private static void deleteCameraFile(Activity a, State s) {
        if (s.cameraFile != null) s.cameraFile.delete();
        s.cameraFile = null;
        a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit()
                .remove(cameraPendingKey(a)).apply();
    }

    public static void onActivityResult(Activity a, int request, int result, Intent data) {
        if (request != GALLERY_REQUEST && request != CAMERA_REQUEST) return;
        State s = state(a);
        if (request == CAMERA_REQUEST) {
            try {
                if (result == Activity.RESULT_OK && s.cameraFile != null
                        && s.cameraFile.isFile() && s.cameraFile.length() > 0) {
                    String copied = copyFile(a, s.cameraFile);
                    s.createdPaths.add(copied);
                    s.paths.add(copied);
                    if (!savePending(a, s)) {
                        s.paths.remove(copied);
                        s.createdPaths.remove(copied);
                        File imported = internalFile(a, copied);
                        if (imported != null) imported.delete();
                    }
                    renderPreview(a, s);
                } else if (result == Activity.RESULT_OK) {
                    Toast.makeText(a, "لم تُنتج الكاميرا صورة صالحة", Toast.LENGTH_LONG).show();
                }
            } catch (Exception e) {
                Toast.makeText(a, "تعذر حفظ الصورة الملتقطة", Toast.LENGTH_LONG).show();
            } finally {
                deleteCameraFile(a, s);
            }
            return;
        }
        if (result != Activity.RESULT_OK || data == null) return;
        int imported = 0, failed = 0;
        ArrayList<String> importedPaths = new ArrayList<>();
        if (data.getClipData() != null) {
            for (int n = 0; n < data.getClipData().getItemCount(); n++) {
                Uri uri = data.getClipData().getItemAt(n).getUri();
                if (uri == null) continue;
                try {
                    String copied = copyUri(a, uri);
                    s.createdPaths.add(copied);
                    s.paths.add(copied);
                    importedPaths.add(copied);
                    imported++;
                } catch (Exception e) { failed++; }
            }
        } else if (data.getData() != null) {
            try {
                String copied = copyUri(a, data.getData());
                s.createdPaths.add(copied);
                s.paths.add(copied);
                importedPaths.add(copied);
                imported++;
            } catch (Exception e) { failed++; }
        }
        if (imported > 0 && !savePending(a, s)) {
            for (String copied : importedPaths) {
                s.paths.remove(copied);
                s.createdPaths.remove(copied);
                File importedFile = internalFile(a, copied);
                if (importedFile != null) importedFile.delete();
            }
            failed += imported;
            imported = 0;
        }
        renderPreview(a, s);
        if (imported > 0) Toast.makeText(a, "تمت إضافة " + imported + " صورة", Toast.LENGTH_SHORT).show();
        if (failed > 0) Toast.makeText(a, "تعذر استيراد " + failed + " صورة", Toast.LENGTH_LONG).show();
    }

    private static String copyUri(Activity a, Uri uri) throws IOException {
        InputStream in = a.getContentResolver().openInputStream(uri);
        if (in == null) throw new IOException("Cannot open image URI");
        try { return copyStream(a, in); } finally { in.close(); }
    }

    private static String copyFile(Activity a, File source) throws IOException {
        InputStream in = new FileInputStream(source);
        try { return copyStream(a, in); } finally { in.close(); }
    }

    private static String copyStream(Activity a, InputStream in) throws IOException {
        File dir = new File(a.getFilesDir(), "question_images");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Cannot create image directory");
        String relative = "question_images/" + UUID.randomUUID() + ".img";
        File destination = internalFile(a, relative);
        if (destination == null) throw new IOException("Invalid image destination");
        FileOutputStream out = new FileOutputStream(destination);
        boolean complete = false;
        try {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            out.flush();
            complete = destination.length() > 0;
        } finally {
            out.close();
            if (!complete) destination.delete();
        }
        if (!complete) throw new IOException("Empty image");
        return relative;
    }

    /** Read the legacy app's EXIF rotation helper without adding a new runtime dependency. */
    private static int jpegRotation(File file) {
        if (file == null) return 0;
        try {
            Class<?> utility = Class.forName("com.nasa.edateor.exsam.A11.FileUtil");
            Method method = utility.getMethod("getJpegRotate", String.class);
            Object value = method.invoke(null, file.getAbsolutePath());
            return value instanceof Integer ? ((Integer) value).intValue() : 0;
        } catch (Throwable ignored) {
            return 0;
        }
    }

    private static Bitmap decode(File file, int targetWidth, int targetHeight) {
        if (file == null || !file.isFile()) return null;
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(file.getAbsolutePath(), bounds);
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null;
        int sample = 1;
        while (bounds.outWidth / (sample * 2) > targetWidth * 2
                || bounds.outHeight / (sample * 2) > targetHeight * 2) sample *= 2;
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inSampleSize = sample;
        options.inPreferredConfig = Bitmap.Config.ARGB_8888;
        Bitmap decoded = BitmapFactory.decodeFile(file.getAbsolutePath(), options);
        if (decoded == null) return null;
        int rotation = jpegRotation(file);
        if (rotation == 0) return decoded;
        try {
            Matrix transform = new Matrix();
            transform.postRotate(rotation);
            Bitmap oriented = Bitmap.createBitmap(decoded, 0, 0,
                    decoded.getWidth(), decoded.getHeight(), transform, true);
            if (oriented != decoded) decoded.recycle();
            return oriented;
        } catch (Throwable ignored) {
            return decoded;
        }
    }

    /** Release detached preview/row bitmaps promptly when ListView recycles its views. */
    private static void releaseBitmaps(View view) {
        if (view == null) return;
        if (view instanceof ImageView) {
            ImageView image = (ImageView) view;
            android.graphics.drawable.Drawable drawable = image.getDrawable();
            image.setImageDrawable(null);
            if (drawable instanceof BitmapDrawable) {
                Bitmap bitmap = ((BitmapDrawable) drawable).getBitmap();
                if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
            }
            return;
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++)
                releaseBitmaps(group.getChildAt(i));
        }
    }

    private static void renderPreview(Activity a, State s) {
        // Do not let the static WeakHashMap retain an Activity through its view hierarchy.
        LinearLayout preview = s.preview == null ? null : s.preview.get();
        if (preview == null) return;
        for (int i = 0; i < preview.getChildCount(); i++)
            releaseBitmaps(preview.getChildAt(i));
        preview.removeAllViews();
        for (String path : new ArrayList<>(s.paths)) {
            Bitmap bitmap = decode(internalFile(a, path), dp(a, 88), dp(a, 88));
            if (bitmap == null) continue;
            LinearLayout item = new LinearLayout(a);
            item.setOrientation(LinearLayout.VERTICAL);
            ImageView image = new ImageView(a);
            image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            image.setImageBitmap(bitmap);
            item.addView(image, new LinearLayout.LayoutParams(dp(a, 88), dp(a, 88)));
            Button remove = new Button(a);
            remove.setText("حذف");
            remove.setOnClickListener(v -> {
                int index = s.paths.indexOf(path);
                if (index < 0) return;
                s.paths.remove(index); // File deletion is deferred until the question commit succeeds.
                if (!savePending(a, s)) s.paths.add(Math.min(index, s.paths.size()), path);
                renderPreview(a, s);
            });
            item.addView(remove);
            preview.addView(item);
        }
    }

    public static void apply(Activity a) {
        try {
            State s = state(a);
            question(a).put("images", new ArrayList<>(s.paths));
            s.applied = true;
        } catch (Exception e) {
            Toast.makeText(a, "تعذر تجهيز صور السؤال للحفظ", Toast.LENGTH_LONG).show();
        }
    }

    /** Called immediately after the legacy SharedPreferences.commit() result is obtained. */
    public static void finishSave(Activity a, boolean committed) {
        State s = STATES.get(a);
        if (s == null) return;
        if (!s.applied) {
            Toast.makeText(a, "تعذر ربط الصور بالسؤال؛ لم نحذف أي صورة", Toast.LENGTH_LONG).show();
            return;
        }
        if (!committed) {
            s.applied = false;
            try {
                HashMap<String, Object> q = question(a);
                if (s.originalPaths.isEmpty()) q.remove("images");
                else q.put("images", new ArrayList<>(s.originalPaths));
            } catch (Exception ignored) { }
            Toast.makeText(a, "لم يكتمل حفظ السؤال؛ احتفظنا بالصور للمحاولة مجدداً", Toast.LENGTH_LONG).show();
            return;
        }
        for (String old : s.originalPaths) {
            if (!s.paths.contains(old)) {
                File file = internalFile(a, old);
                if (file != null) file.delete();
            }
        }
        for (String created : s.createdPaths) {
            if (!s.paths.contains(created)) {
                File file = internalFile(a, created);
                if (file != null) file.delete();
            }
        }
        s.originalPaths = new ArrayList<>(s.paths);
        s.createdPaths.clear();
        s.applied = false;
        a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit()
                .remove(safeKey(a)).remove(createdPendingKey(a)).apply();

    }

    /** Discard new, uncommitted files only; original question images remain intact. */
    public static void discard(Activity a) {
        State s = STATES.get(a);
        if (s == null) {
            ArrayList<String> original = originalPaths(a);
            ArrayList<String> selected = pendingPaths(a);
            s = new State(selected, original, pendingCreatedPaths(a, selected, original));
        }
        for (String created : s.createdPaths) {
            // A crash may occur after the question commit but before finishSave clears pending state.
            // If the current question already references this path, it is no longer disposable.
            if (s.originalPaths.contains(created)) continue;
            File file = internalFile(a, created);
            if (file != null) file.delete();
        }
        deleteCameraFile(a, s);
        a.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit()
                .remove(safeKey(a)).remove(createdPendingKey(a)).apply();
        STATES.remove(a);
    }

    /** Add image rows beneath the existing question cells without horizontal clipping. */
    public static void renderQuestion(Activity a, View row, HashMap<String, Object> question) {
        if (!(row instanceof LinearLayout) || question == null) return;
        LinearLayout root = (LinearLayout) row;
        View previous = root.findViewWithTag(QUESTION_IMAGES_TAG);
        if (previous != null) {
            releaseBitmaps(previous);
            if (previous.getParent() instanceof ViewGroup)
                ((ViewGroup) previous.getParent()).removeView(previous);
        }
        Object value = question.get("images");
        if (!(value instanceof List<?>)) return; // Old questions without images are unchanged.

        LinearLayout grid = new LinearLayout(a);
        grid.setOrientation(LinearLayout.VERTICAL);
        grid.setTag(QUESTION_IMAGES_TAG);
        LinearLayout imageRow = null;
        int inRow = 0, rendered = 0;
        for (Object item : (List<?>) value) {
            if (item == null) continue;
            Bitmap bitmap = decode(internalFile(a, item.toString()), dp(a, 320), dp(a, 132));
            if (bitmap == null) continue;
            if (imageRow == null || inRow == 2) {
                imageRow = new LinearLayout(a);
                imageRow.setOrientation(LinearLayout.HORIZONTAL);
                grid.addView(imageRow, new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, dp(a, 136)));
                inRow = 0;
            }
            ImageView image = new ImageView(a);
            image.setAdjustViewBounds(true);
            image.setScaleType(ImageView.ScaleType.FIT_CENTER);
            image.setImageBitmap(bitmap);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(a, 132), 1f);
            lp.setMargins(dp(a, 2), dp(a, 2), dp(a, 2), dp(a, 2));
            imageRow.addView(image, lp);
            inRow++;
            rendered++;
        }
        if (rendered > 0) {
            grid.addView(new View(a), new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(a, 12)));
            root.addView(grid, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        }
    }

    /** Rasterize a complete PDF page so images and fallback glyphs are embedded as pixels. */
    public static void drawPdfRaster(View view, Canvas target) {
        if (view == null || target == null) return;
        int width = view.getWidth(), height = view.getHeight();
        if (width <= 0 || height <= 0) {
            view.draw(target);
            return;
        }
        Bitmap page = null;
        try {
            page = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            view.draw(new Canvas(page));
            target.drawBitmap(page, 0f, 0f, null);
        } catch (Throwable failure) {
            view.draw(target);
        } finally {
            if (page != null && !page.isRecycled()) page.recycle();
        }
    }
}