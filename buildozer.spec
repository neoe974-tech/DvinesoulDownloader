[app]
title = Dvinesoul Downloader
package.name = dvinesouldownloader
package.domain = com.dvinesoul
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = bin,.buildozer,venv,.venv,__pycache__,tests
version = 0.2.0
requirements = python3,kivy,yt-dlp
orientation = portrait
fullscreen = 0

# The app stores its own downloads in Android app-specific external storage.
# This avoids broad filesystem access and MANAGE_EXTERNAL_STORAGE.
android.permissions = android.permission.INTERNET
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
android.accept_sdk_license = True
