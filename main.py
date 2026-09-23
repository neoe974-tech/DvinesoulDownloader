from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from yt_dlp import YoutubeDL
import os
import threading
import sys


APP_VERSION = "0.2.0"


def android_download_dir():
    if "android" not in sys.platform:
        return os.path.expanduser("~/Downloads")

    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Environment = autoclass("android.os.Environment")
        context = PythonActivity.mActivity
        directory = context.getExternalFilesDir(
            Environment.DIRECTORY_DOWNLOADS
        )
        if directory:
            path = directory.getAbsolutePath()
            os.makedirs(path, exist_ok=True)
            return path
    except Exception:
        pass

    return os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    )


class SplashScreen(Screen):
    pass


class BrowserScreen(Screen):
    selected_video_url = ""
    selected_video_title = ""
    results = []
    download_active = False

    def go(self, screen):
        self.manager.current = screen

    def search_youtube(self):
        query = self.ids.search_input.text.strip()
        if not query:
            self.ids.search_status.text = "Enter something to search."
            return

        self.ids.search_status.text = "Searching YouTube..."
        self.ids.results_box.clear_widgets()

        threading.Thread(
            target=self._search_worker, args=(query,), daemon=True
        ).start()

    def _search_worker(self, query):
        try:
            options = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }
            with YoutubeDL(options) as ydl:
                result = ydl.extract_info(
                    f"ytsearch8:{query}", download=False
                )

            results = []
            for entry in result.get("entries", []) or []:
                if not entry:
                    continue
                video_id = entry.get("id")
                thumbnail = entry.get("thumbnail", "")
                if not thumbnail and video_id:
                    thumbnail = (
                        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    )
                results.append({
                    "title": entry.get("title", "Unknown video"),
                    "url": entry.get("webpage_url") or entry.get("url"),
                    "channel": entry.get("channel")
                    or entry.get("uploader")
                    or "YouTube",
                    "duration": entry.get("duration"),
                    "thumbnail": thumbnail,
                })

            Clock.schedule_once(
                lambda dt, data=results: self._search_success(data)
            )
        except Exception as error:
            self._schedule_error(self._search_error, "Search failed", error)

    def _search_success(self, results):
        self.results = results
        if not results:
            self.ids.search_status.text = "No videos found."
            return

        self.ids.search_status.text = f"Found {len(results)} video(s)"
        for index, item in enumerate(results):
            self._add_result_card(index, item)

    def _search_error(self, message):
        self.ids.search_status.text = f"Search failed: {message}"

    def _schedule_error(self, callback, prefix, error, limit=300):
        message = str(error).replace("\n", " ")
        if len(message) > limit:
            message = message[:limit] + "..."
        Clock.schedule_once(
            lambda dt, msg=message: callback(msg)
        )

    def _add_result_card(self, index, item):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.image import AsyncImage
        from kivy.metrics import dp

        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(112),
            spacing=dp(8),
            padding=dp(6),
        )

        card.add_widget(AsyncImage(
            source=item.get("thumbnail", ""),
            size_hint_x=None,
            width=dp(140),
            allow_stretch=True,
            keep_ratio=True,
        ))

        info = BoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(Label(
            text=item.get("title", "Unknown video"),
            font_size=dp(13),
            bold=True,
            color=(0.65, 1, 0.05, 1),
            halign="left",
            valign="middle",
            text_size=(None, dp(48)),
        ))
        info.add_widget(Label(
            text=item.get("channel", "YouTube"),
            font_size=dp(11),
            color=(0.75, 0.75, 0.75, 1),
            halign="left",
            valign="middle",
            text_size=(None, dp(22)),
        ))

        duration = item.get("duration")
        duration_text = "Duration unavailable"
        try:
            if duration is not None:
                seconds = int(duration)
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                duration_text = (
                    f"{hours}:{minutes:02d}:{seconds:02d}"
                    if hours else f"{minutes}:{seconds:02d}"
                )
        except (ValueError, TypeError):
            pass

        info.add_widget(Label(
            text=duration_text,
            font_size=dp(10),
            color=(0.55, 0.55, 0.55, 1),
            halign="left",
            valign="middle",
            text_size=(None, dp(18)),
        ))

        button = Button(
            text="DOWNLOAD",
            size_hint_x=None,
            width=dp(105),
            background_normal="",
            background_color=(0.85, 0.05, 0.08, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        button.bind(
            on_release=lambda instance, i=index: self.select_video(i)
        )

        card.add_widget(info)
        card.add_widget(button)
        self.ids.results_box.add_widget(card)

    def select_video(self, index):
        try:
            item = self.results[index]
        except (IndexError, TypeError):
            self.ids.search_status.text = "That result is no longer available."
            return

        self.selected_video_url = item.get("url") or ""
        self.selected_video_title = item.get("title", "Video")
        if not self.selected_video_url:
            self.ids.search_status.text = "This video has no usable URL."
            return

        self.ids.selected_title.text = self.selected_video_title
        self.ids.download_panel.opacity = 1
        self.ids.download_panel.disabled = False
        self.ids.search_status.text = "Video selected. Choose MP4 or MP3."

    def choose_mp4(self):
        if not self.selected_video_url:
            return
        self.ids.format_mp4.state = "down"
        self.ids.format_mp3.state = "normal"
        self.ids.format_status.text = "MP4 selected — reading qualities..."
        self.ids.quality.disabled = False
        self.extract_selected_formats()

    def choose_mp3(self):
        self.ids.format_mp3.state = "down"
        self.ids.format_mp4.state = "normal"
        self.ids.format_status.text = "MP3 selected"
        self.ids.quality.disabled = True
        self.ids.quality.values = ["Best audio"]
        self.ids.quality.text = "Best audio"

    def extract_selected_formats(self):
        if not self.selected_video_url:
            return
        threading.Thread(
            target=self._quality_worker,
            args=(self.selected_video_url,),
            daemon=True,
        ).start()

    def _quality_worker(self, url):
        try:
            with YoutubeDL({
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }) as ydl:
                info = ydl.extract_info(url, download=False)

            heights = {
                fmt.get("height")
                for fmt in info.get("formats", []) or []
                if fmt.get("height") and fmt.get("height") >= 144
            }

            qualities = []
            for height in sorted(heights, reverse=True):
                if height >= 2160:
                    label = f"{height}p — 4K"
                elif height >= 1440:
                    label = f"{height}p — 2K"
                elif height >= 1080:
                    label = f"{height}p — Full HD"
                elif height >= 720:
                    label = f"{height}p — HD"
                else:
                    label = f"{height}p"
                qualities.append(label)

            if not qualities:
                qualities = ["Best available"]

            Clock.schedule_once(
                lambda dt, q=qualities: self._quality_success(q)
            )
        except Exception as error:
            self._schedule_error(
                self._quality_error, "Quality error", error, 250
            )

    def _quality_success(self, qualities):
        self.ids.quality.values = qualities
        self.ids.quality.text = qualities[0]
        self.ids.format_status.text = (
            f"{len(qualities)} quality option(s) available"
        )

    def _quality_error(self, message):
        self.ids.format_status.text = f"Could not read qualities: {message}"

    def start_download(self):
        if self.download_active:
            self.ids.download_status.text = "A download is already running."
            return

        url = self.selected_video_url
        if not url:
            self.ids.download_status.text = "Select a video first."
            return

        format_type = (
            "mp3"
            if self.ids.format_mp3.state == "down"
            else "mp4"
        )

        if format_type == "mp4":
            height = self._get_height(self.ids.quality.text)
            selector = (
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]"
                if height else "bestvideo+bestaudio/best"
            )
        else:
            selector = "bestaudio/best"

        self.download_active = True
        self.ids.download_button.disabled = True
        self.ids.download_status.text = (
            f"Starting {format_type.upper()} download..."
        )

        threading.Thread(
            target=self._download_worker,
            args=(url, format_type, selector),
            daemon=True,
        ).start()

    @staticmethod
    def _get_height(quality):
        try:
            return int(quality.split("p", 1)[0])
        except (ValueError, IndexError, AttributeError):
            return None

    def _download_worker(self, url, format_type, selector):
        try:
            download_path = android_download_dir()
            os.makedirs(download_path, exist_ok=True)

            options = {
                "format": selector,
                "outtmpl": os.path.join(
                    download_path, "%(title)s.%(ext)s"
                ),
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._download_progress],
                "noprogress": False,
            }

            if format_type == "mp3":
                options["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            else:
                options["merge_output_format"] = "mp4"

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)

            title = info.get("title", "Video")
            Clock.schedule_once(
                lambda dt, t=title, f=format_type, p=download_path:
                self._download_success(t, f, p)
            )
        except Exception as error:
            self._schedule_error(
                self._download_error, "Download failed", error, 300
            )

    def _download_progress(self, progress):
        if progress.get("status") != "downloading":
            return

        downloaded = progress.get("downloaded_bytes", 0)
        total = (
            progress.get("total_bytes")
            or progress.get("total_bytes_estimate")
        )
        if total:
            percent = max(0, min(100, downloaded / total * 100))
            Clock.schedule_once(
                lambda dt, p=percent: self._update_progress(p)
            )

    def _update_progress(self, percent):
        self.ids.download_status.text = f"Downloading... {percent:.1f}%"

    def _download_success(self, title, format_type, path):
        self.download_active = False
        self.ids.download_button.disabled = False
        self.ids.download_status.text = (
            f"{format_type.upper()} complete: {title}"
        )

        downloads = self.manager.get_screen("downloads")
        downloads.set_download_path(path)
        Clock.schedule_once(
            lambda dt: downloads.refresh_downloads(), 0.2
        )

    def _download_error(self, message):
        self.download_active = False
        self.ids.download_button.disabled = False
        self.ids.download_status.text = f"Download failed: {message}"


class DownloadsScreen(Screen):
    download_path = ""

    def on_pre_enter(self):
        self.refresh_downloads()

    def set_download_path(self, path):
        self.download_path = path

    def refresh_downloads(self):
        self.ids.download_status.text = "Refreshing downloads..."
        threading.Thread(
            target=self._scan_worker, daemon=True
        ).start()

    def _scan_worker(self):
        path = self.download_path or android_download_dir()
        items = []
        error_message = ""

        try:
            if not os.path.isdir(path):
                os.makedirs(path, exist_ok=True)

            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext not in (".mp3", ".mp4", ".m4a", ".webm"):
                            continue
                        stat = entry.stat(follow_symlinks=False)
                        items.append({
                            "name": entry.name,
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                        })
                    except (OSError, ValueError):
                        continue

            items.sort(key=lambda x: x["mtime"], reverse=True)
        except (OSError, PermissionError) as error:
            error_message = str(error) or "Storage could not be read."
        except Exception as error:
            error_message = str(error) or "Unexpected storage error."

        Clock.schedule_once(
            lambda dt, data=items, err=error_message:
            self._scan_complete(data, err)
        )

    def _scan_complete(self, items, error_message):
        if error_message:
            self.ids.download_status.text = (
                f"Could not read downloads: {error_message}"
            )
            self.ids.download_list.text = (
                "Downloads unavailable.\n\n"
                "The app will continue running."
            )
            return

        if not items:
            self.ids.download_list.text = (
                "No MP3 or MP4 downloads yet.\n\n"
                "Completed downloads will appear here automatically."
            )
            self.ids.download_status.text = "Downloads refreshed."
            return

        lines = []
        for item in items:
            size = self._format_size(item["size"])
            lines.append(f"{item['name']}\n{size}")

        self.ids.download_list.text = "\n\n".join(lines)
        self.ids.download_status.text = (
            f"{len(items)} download(s) found."
        )

    @staticmethod
    def _format_size(size):
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} GB"

    def go(self, screen):
        self.manager.current = screen


class SettingsScreen(Screen):
    def go(self, screen):
        self.manager.current = screen

    def storage_description(self):
        return android_download_dir()


class DvinesoulScreenManager(ScreenManager):
    pass


class DvinesoulDownloaderApp(App):
    title = "Dvinesoul Downloader"
    version = APP_VERSION

    def build(self):
        Builder.load_file("main.kv")
        return DvinesoulScreenManager()

    def start_app(self):
        self.root.current = "browser"


if __name__ == "__main__":
    DvinesoulDownloaderApp().run()
