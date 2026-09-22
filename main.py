from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager

from yt_dlp import YoutubeDL

import os
import threading


class SplashScreen(Screen):
    pass


class HomeScreen(Screen):

    def open_browser(self):
        self.manager.current = "browser"

    def open_downloads(self):
        self.manager.current = "downloads"

    def open_settings(self):
        self.manager.current = "settings"


class BrowserScreen(Screen):

    selected_video_url = ""
    selected_video_title = ""

    def search_youtube(self):
        query = self.ids.search_input.text.strip()

        if not query:
            self.ids.search_status.text = "Enter something to search."
            return

        self.ids.search_status.text = "Searching YouTube..."
        self.ids.results_box.clear_widgets()

        threading.Thread(
            target=self._search_worker,
            args=(query,),
            daemon=True
        ).start()

    def _search_worker(self, query):
        try:
            options = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }

            search_query = f"ytsearch8:{query}"

            with YoutubeDL(options) as ydl:
                result = ydl.extract_info(
                    search_query,
                    download=False
                )

            entries = result.get("entries", [])

            results = []

            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get("id")
                thumbnail = entry.get("thumbnail", "")

                if not thumbnail and video_id:
                    thumbnail = (
                        f"https://i.ytimg.com/vi/"
                        f"{video_id}/hqdefault.jpg"
                    )

                results.append({
                    "title": entry.get("title", "Unknown video"),
                    "url": entry.get("webpage_url")
                    or entry.get("url"),
                    "channel": entry.get("channel")
                    or entry.get("uploader")
                    or "YouTube",
                    "duration": entry.get("duration"),
                    "thumbnail": thumbnail,
                })

            Clock.schedule_once(
                lambda dt: self._search_success(results)
            )

        except Exception as error:
            message = str(error)

            if len(message) > 300:
                message = message[:300] + "..."

            Clock.schedule_once(
                lambda dt: self._search_error(message)
            )

    def _search_success(self, results):
        self.results = results

        if not results:
            self.ids.search_status.text = "No videos found."
            return

        self.ids.search_status.text = (
            f"Found {len(results)} video(s)"
        )

        for index, item in enumerate(results):
            self._add_result_card(index, item)

    def _search_error(self, message):
        self.ids.search_status.text = (
            f"Search failed: {message}"
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
            height=dp(115),
            spacing=dp(8),
            padding=dp(6),
        )

        thumbnail = AsyncImage(
            source=item.get("thumbnail", ""),
            size_hint_x=None,
            width=dp(145),
            allow_stretch=True,
            keep_ratio=True,
        )

        info_box = BoxLayout(
            orientation="vertical",
            spacing=dp(2),
        )

        title = Label(
            text=item.get("title", "Unknown video"),
            font_size=dp(14),
            bold=True,
            color=(0.65, 1, 0.05, 1),
            halign="left",
            valign="middle",
            text_size=(None, dp(45)),
        )

        channel = Label(
            text=item.get("channel", "YouTube"),
            font_size=dp(11),
            color=(0.75, 0.75, 0.75, 1),
            halign="left",
            valign="middle",
            text_size=(None, dp(22)),
        )

        duration = item.get("duration")

        if duration:
            try:
                seconds = int(duration)
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)

                if hours:
                    duration_text = (
                        f"{hours}:{minutes:02d}:{seconds:02d}"
                    )
                else:
                    duration_text = f"{minutes}:{seconds:02d}"

            except (ValueError, TypeError):
                duration_text = "Duration unavailable"
        else:
            duration_text = "Duration unavailable"

        duration_label = Label(
            text=duration_text,
            font_size=dp(10),
            color=(0.55, 0.55, 0.55, 1),
            halign="left",
            valign="middle",
            text_size=(None, dp(18)),
        )

        info_box.add_widget(title)
        info_box.add_widget(channel)
        info_box.add_widget(duration_label)

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
            on_release=lambda instance, i=index:
            self.select_video(i)
        )

        card.add_widget(thumbnail)
        card.add_widget(info_box)
        card.add_widget(button)

        self.ids.results_box.add_widget(card)

    def select_video(self, index):
        item = self.results[index]

        self.selected_video_url = item["url"]
        self.selected_video_title = item["title"]

        self.ids.selected_title.text = item["title"]

        self.ids.download_panel.opacity = 1
        self.ids.download_panel.disabled = False

        self.ids.search_status.text = (
            "Video selected. Choose MP4 or MP3."
        )

    def choose_mp4(self):
        self.ids.format_mp4.state = "down"
        self.ids.format_mp3.state = "normal"

        self.ids.format_status.text = "MP4 selected"

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
        url = self.selected_video_url

        if not url:
            return

        self.ids.format_status.text = (
            "Reading available video qualities..."
        )

        threading.Thread(
            target=self._quality_worker,
            args=(url,),
            daemon=True
        ).start()

    def _quality_worker(self, url):
        try:
            options = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    url,
                    download=False
                )

            formats = info.get("formats", [])

            heights = set()

            for fmt in formats:
                height = fmt.get("height")

                if height and height >= 144:
                    heights.add(height)

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
                lambda dt: self._quality_success(qualities)
            )

        except Exception as error:
            message = str(error)

            if len(message) > 250:
                message = message[:250] + "..."

            Clock.schedule_once(
                lambda dt: self._quality_error(message)
            )

    def _quality_success(self, qualities):
        self.ids.quality.values = qualities
        self.ids.quality.text = qualities[0]

        self.ids.format_status.text = (
            f"{len(qualities)} quality option(s) available"
        )

    def _quality_error(self, message):
        self.ids.format_status.text = (
            f"Could not read qualities: {message}"
        )

    def start_download(self):
        url = self.selected_video_url

        if not url:
            self.ids.download_status.text = (
                "Select a video first."
            )
            return

        if self.ids.format_mp3.state == "down":
            format_type = "mp3"
        else:
            format_type = "mp4"

        quality = self.ids.quality.text

        if format_type == "mp4":
            height = self._get_height(quality)

            if height:
                selector = (
                    f"bestvideo[height<={height}]"
                    f"+bestaudio/best[height<={height}]"
                )
            else:
                selector = "bestvideo+bestaudio/best"

        else:
            selector = "bestaudio/best"

        self.ids.download_status.text = (
            f"Starting {format_type.upper()} download..."
        )

        threading.Thread(
            target=self._download_worker,
            args=(url, format_type, selector),
            daemon=True
        ).start()

    def _get_height(self, quality):
        try:
            return int(quality.split("p")[0])
        except (ValueError, IndexError):
            return None

    def _download_worker(self, url, format_type, selector):
        try:
            download_path = os.path.expanduser(
                "~/Downloads"
            )

            os.makedirs(download_path, exist_ok=True)

            options = {
                "format": selector,
                "outtmpl": os.path.join(
                    download_path,
                    "%(title)s.%(ext)s"
                ),
                "quiet": True,
                "no_warnings": True,
                "noprogress": False,
                "progress_hooks": [
                    self._download_progress
                ],
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
                info = ydl.extract_info(
                    url,
                    download=True
                )

            title = info.get(
                "title",
                "Video"
            )

            Clock.schedule_once(
                lambda dt: self._download_success(
                    title,
                    format_type
                )
            )

        except Exception as error:
            message = str(error)

            if len(message) > 300:
                message = message[:300] + "..."

            Clock.schedule_once(
                lambda dt: self._download_error(message)
            )

    def _download_progress(self, progress):
        if progress.get("status") == "downloading":
            downloaded = progress.get(
                "downloaded_bytes",
                0
            )

            total = (
                progress.get("total_bytes")
                or progress.get("total_bytes_estimate")
            )

            if total:
                percent = downloaded / total * 100

                Clock.schedule_once(
                    lambda dt:
                    self._update_progress(percent)
                )

    def _update_progress(self, percent):
        self.ids.download_status.text = (
            f"Downloading... {percent:.1f}%"
        )

    def _download_success(self, title, format_type):
        self.ids.download_status.text = (
            f"{format_type.upper()} complete: {title}"
        )

    def _download_error(self, message):
        self.ids.download_status.text = (
            f"Download failed: {message}"
        )


class DownloadsScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class DvinesoulScreenManager(ScreenManager):
    pass


class DvinesoulDownloaderApp(App):

    title = "Dvinesoul Downloader"

    def build(self):
        Builder.load_file("main.kv")
        return DvinesoulScreenManager()

    def start_app(self):
        self.root.current = "home"


if __name__ == "__main__":
    DvinesoulDownloaderApp().run()
