# Dvinesoul Downloader

Dvinesoul Downloader is an Android app built with Python, Kivy, and yt-dlp. It lets you search YouTube from inside the app, select a video, choose MP4 video or MP3 audio, and track the download status.

## Current features

- Search YouTube from inside the app and display video results.
- Select a result and choose MP4 or MP3.
- For MP4, read available video heights and select a quality.
- Download video/audio using yt-dlp.
- Extract MP3 audio at 192 kbps using yt-dlp's FFmpeg postprocessor.
- View downloaded media in the Downloads screen and refresh the list.
- Run downloads and scan files on worker threads while keeping Android path/JNI access on the UI thread to avoid background-thread JNI failures.

## Download the Android APK

1. Open the [GitHub Actions build](https://github.com/neoe974-tech/DvinesoulDownloader/actions/workflows/android.yml).
2. Select the latest successful run on the `stable-sep23-passing-build` branch.
3. Under **Artifacts**, download **Dvinesoul-Downloader-APK**.
4. Extract the artifact ZIP and install the included APK on your Android device.

The APK is built by GitHub Actions for `arm64-v8a` and `armeabi-v7a`.

## Download location and permissions

- Completed media is published to the phone's public **Downloads/Dvinesoul Downloader** folder.
- Android 10 and newer use the **MediaStore Downloads API** and scoped storage. This avoids requesting broad storage access just to save files created by the app.
- Android 9 and older use the public Downloads directory and request legacy read/write storage permission at runtime. Those legacy permissions are capped at API 28 in the manifest.
- Android 13 and newer declare and request `POST_NOTIFICATIONS`. Denying notification permission should not block downloads.
- The app does not request `READ_MEDIA_AUDIO` or `READ_MEDIA_VIDEO` because it only needs to publish and list media it creates itself; those permissions would grant broader access to the user's other media and are not required for this flow.
- The in-app Downloads screen queries MediaStore on Android 10+ and lists this app's published items.

## Build

The Android APK is built in GitHub Actions using Buildozer and a pinned, patched python-for-android checkout. The workflow verifies that the optional `requests` and `charset-normalizer` dependencies are excluded from the Android dependency resolution before building the APK.

## Notes

- YouTube extraction can change when YouTube changes its services; keep yt-dlp updated if searches or downloads stop working.
- MP3 conversion requires FFmpeg to be available in the Android build.
- A successful CI build confirms that the APK was produced; it does not replace testing installation, downloads, and the Refresh button on a physical device.
- Only download content you have permission to save and use.
