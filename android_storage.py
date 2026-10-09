"""Android-compatible public Downloads publishing for Dvinesoul Downloader.

Modern Android uses MediaStore so files are visible in the system Downloads
collection without requesting broad storage access. Older Android versions use
the public Downloads directory and legacy storage permission.
"""
import os
import shutil
import sys
import mimetypes


def is_android():
    return "android" in sys.platform


def android_api_level():
    if not is_android():
        return 0
    from jnius import autoclass
    BuildVersion = autoclass("android.os.Build$VERSION")
    return int(BuildVersion.SDK_INT)


def app_staging_dir():
    """Private app-owned staging directory; no storage permission required."""
    if not is_android():
        path = os.path.join(os.path.expanduser("~"), "Downloads", "Dvinesoul-Staging")
        os.makedirs(path, exist_ok=True)
        return path
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Environment = autoclass("android.os.Environment")
    directory = PythonActivity.mActivity.getExternalFilesDir(
        Environment.DIRECTORY_DOWNLOADS
    )
    if directory is None:
        raise OSError("Android did not provide an app download directory")
    path = directory.getAbsolutePath()
    os.makedirs(path, exist_ok=True)
    return path


def _safe_display_name(path):
    name = os.path.basename(path).replace("/", "_").replace("\\x00", "")
    return name or "download"


def publish_to_public_downloads(source_path):
    """Publish a completed staging file into the public Downloads collection."""
    if not os.path.isfile(source_path):
        raise FileNotFoundError(source_path)

    if not is_android():
        public_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(public_dir, exist_ok=True)
        destination = os.path.join(public_dir, _safe_display_name(source_path))
        if os.path.abspath(source_path) != os.path.abspath(destination):
            shutil.copy2(source_path, destination)
        return destination

    api = android_api_level()
    if api >= 29:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ContentValues = autoclass("android.content.ContentValues")
        Integer = autoclass("java.lang.Integer")
        MediaStoreDownloads = autoclass("android.provider.MediaStore$Downloads")
        Environment = autoclass("android.os.Environment")

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        display_name = _safe_display_name(source_path)
        mime_type = mimetypes.guess_type(display_name)[0] or "application/octet-stream"

        values = ContentValues()
        values.put("_display_name", display_name)
        values.put("mime_type", mime_type)
        values.put("relative_path", Environment.DIRECTORY_DOWNLOADS + "/Dvinesoul Downloader/")
        values.put("is_pending", Integer.valueOf(1))

        uri = resolver.insert(MediaStoreDownloads.EXTERNAL_CONTENT_URI, values)
        if uri is None:
            raise OSError("Android could not create a Downloads entry")

        try:
            output_stream = resolver.openOutputStream(uri)
            if output_stream is None:
                raise OSError("Android could not open the Downloads output stream")
            try:
                with open(source_path, "rb") as source:
                    buffer = bytearray(1024 * 128)
                    while True:
                        chunk = source.read(len(buffer))
                        if not chunk:
                            break
                        output_stream.write(chunk)
                output_stream.flush()
            finally:
                output_stream.close()

            complete = ContentValues()
            complete.put("is_pending", Integer.valueOf(0))
            resolver.update(uri, complete, None, None)
        except Exception:
            try:
                resolver.delete(uri, None, None)
            except Exception:
                pass
            raise

        try:
            os.remove(source_path)
        except OSError:
            pass
        return str(uri.toString())

    # Android 9 and older: public directory is available with legacy write permission.
    from jnius import autoclass
    Environment = autoclass("android.os.Environment")
    public_dir = Environment.getExternalStoragePublicDirectory(
        Environment.DIRECTORY_DOWNLOADS
    ).getAbsolutePath()
    public_dir = os.path.join(public_dir, "Dvinesoul Downloader")
    os.makedirs(public_dir, exist_ok=True)
    destination = os.path.join(public_dir, _safe_display_name(source_path))
    shutil.move(source_path, destination)
    return destination


def list_public_downloads():
    """Return this app's published downloads for the in-app Downloads screen."""
    if not is_android():
        path = os.path.join(os.path.expanduser("~"), "Downloads")
        items = []
        try:
            for entry in os.scandir(path):
                if entry.is_file(follow_symlinks=False) and os.path.splitext(entry.name)[1].lower() in (".mp3", ".mp4", ".m4a", ".webm"):
                    stat = entry.stat(follow_symlinks=False)
                    items.append({"name": entry.name, "size": stat.st_size, "mtime": stat.st_mtime})
        except OSError:
            pass
        return sorted(items, key=lambda item: item["mtime"], reverse=True)

    api = android_api_level()
    if api >= 29:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        MediaStoreDownloads = autoclass("android.provider.MediaStore$Downloads")
        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        # Passing a null projection avoids Java String[] conversion issues in PyJNIus.
        cursor = resolver.query(
            MediaStoreDownloads.EXTERNAL_CONTENT_URI,
            None, None, None, "date_added DESC"
        )
        items = []
        if cursor is None:
            return items
        try:
            name_i = cursor.getColumnIndex("_display_name")
            size_i = cursor.getColumnIndex("_size")
            date_i = cursor.getColumnIndex("date_added")
            path_i = cursor.getColumnIndex("relative_path")
            while cursor.moveToNext():
                name = cursor.getString(name_i) if name_i >= 0 else ""
                relpath = cursor.getString(path_i) if path_i >= 0 else ""
                if not name or not (relpath or "").startswith("Download/Dvinesoul Downloader/"):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in (".mp3", ".mp4", ".m4a", ".webm"):
                    continue
                items.append({
                    "name": name,
                    "size": int(cursor.getLong(size_i)) if size_i >= 0 else 0,
                    "mtime": int(cursor.getLong(date_i)) if date_i >= 0 else 0,
                })
        finally:
            cursor.close()
        return items

    # Legacy Android: enumerate only this app's subdirectory.
    from jnius import autoclass
    Environment = autoclass("android.os.Environment")
    path = os.path.join(
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath(),
        "Dvinesoul Downloader",
    )
    items = []
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False) and os.path.splitext(entry.name)[1].lower() in (".mp3", ".mp4", ".m4a", ".webm"):
                    stat = entry.stat(follow_symlinks=False)
                    items.append({"name": entry.name, "size": stat.st_size, "mtime": stat.st_mtime})
    except OSError:
        pass
    return sorted(items, key=lambda item: item["mtime"], reverse=True)
