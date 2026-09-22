import os
import threading

import flet as ft
from yt_dlp import YoutubeDL


LIME = "#B6FF00"
RED = "#FF3030"
BG = "#080808"
CARD = "#151515"
TEXT = "#FFFFFF"
MUTED = "#999999"


def format_duration(value):
    if not value:
        return "Duration unavailable"

    try:
        seconds = int(value)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"

        return f"{minutes}:{seconds:02d}"

    except (ValueError, TypeError):
        return "Duration unavailable"


def quality_label(height):
    if height >= 2160:
        return f"{height}p — 4K"
    if height >= 1440:
        return f"{height}p — 2K"
    if height >= 1080:
        return f"{height}p — Full HD"
    if height >= 720:
        return f"{height}p — HD"
    return f"{height}p"


def main(page: ft.Page):
    page.title = "Dvinesoul Downloader"
    page.bgcolor = BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    state = {
        "selected_url": "",
        "selected_title": "",
        "format": "mp4",
        "quality": "Best available",
        "results": [],
    }

    splash = ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                ft.Text(
                    "X-CORE",
                    size=42,
                    weight=ft.FontWeight.BOLD,
                    color=LIME,
                ),
                ft.Text(
                    "DVINESOUL",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=RED,
                ),
                ft.Text(
                    "DOWNLOADER",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT,
                ),
                ft.Container(height=20),
                ft.Text(
                    "DVINESOUL DOWNLOADER",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=LIME,
                ),
                ft.Text(
                    "Created by Neo Emmanuel",
                    size=14,
                    color=MUTED,
                ),
                ft.Container(height=30),
                ft.Button(
                    content=ft.Text(
                        "START",
                        weight=ft.FontWeight.BOLD,
                    ),
                    width=180,
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor=RED,
                        color=TEXT,
                    ),
                    on_click=lambda e: show_dashboard(),
                ),
                ft.Container(height=18),
                ft.Text(
                    "X-CORE • DVINESOUL",
                    size=12,
                    color="#666666",
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )

    page.add(splash)

    search_input = ft.TextField(
        hint_text="Search YouTube...",
        expand=True,
        height=48,
        border_color="#333333",
        focused_border_color=LIME,
        color=TEXT,
        hint_style=ft.TextStyle(color="#777777"),
    )

    search_status = ft.Text(
        "Search for a video to begin.",
        color=MUTED,
        size=13,
    )

    results_column = ft.Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    selected_title = ft.Text(
        "No video selected",
        color=MUTED,
        size=14,
    )

    format_status = ft.Text(
        "Choose MP4 or MP3 after selecting a video.",
        color=MUTED,
        size=13,
    )

    download_status = ft.Text(
        "Ready.",
        color=MUTED,
        size=13,
    )

    progress_bar = ft.ProgressBar(
        value=0,
        visible=False,
        color=LIME,
        bgcolor="#333333",
    )

    quality_dropdown = ft.Dropdown(
        label="Quality",
        value="Best available",
        options=[
            ft.DropdownOption(
                key="Best available",
                text="Best available",
            )
        ],
        disabled=False,
        width=240,
    )

    format_mp4 = ft.Button(
        content=ft.Text("MP4"),
        style=ft.ButtonStyle(
            bgcolor=LIME,
            color="#000000",
        ),
        on_click=lambda e: choose_mp4(),
    )

    format_mp3 = ft.Button(
        content=ft.Text("MP3"),
        style=ft.ButtonStyle(
            bgcolor="#333333",
            color=TEXT,
        ),
        on_click=lambda e: choose_mp3(),
    )

    def show_dashboard():
        page.clean()

        header = ft.Container(
            padding=ft.Padding(left=18, right=18, top=12, bottom=12),
            bgcolor="#101010",
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "X-CORE",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=LIME,
                            ),
                            ft.Text(
                                "DVINESOUL DOWNLOADER",
                                size=11,
                                color=TEXT,
                            ),
                        ],
                        spacing=0,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        "Neo Emmanuel",
                        size=11,
                        color=MUTED,
                    ),
                ]
            ),
        )

        search_bar = ft.Row(
            [
                search_input,
                ft.Button(
                    content=ft.Text(
                        "SEARCH",
                        weight=ft.FontWeight.BOLD,
                    ),
                    height=48,
                    style=ft.ButtonStyle(
                        bgcolor=LIME,
                        color="#000000",
                    ),
                    on_click=lambda e: search_youtube(),
                ),
            ],
        )

        search_section = ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Text(
                        "YouTube Search",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT,
                    ),
                    search_bar,
                    search_status,
                ],
                spacing=10,
            ),
        )

        results_card = ft.Container(
            expand=True,
            padding=16,
            bgcolor=CARD,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Text(
                        "Search Results",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=LIME,
                    ),
                    results_column,
                ],
                expand=True,
            ),
        )

        selected_card = ft.Container(
            padding=16,
            bgcolor=CARD,
            border_radius=10,
            content=ft.Column(
                [
                    ft.Text(
                        "Download",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=RED,
                    ),
                    selected_title,
                    ft.Row(
                        [
                            format_mp4,
                            format_mp3,
                        ],
                        spacing=10,
                    ),
                    format_status,
                    quality_dropdown,
                    progress_bar,
                    download_status,
                    ft.Button(
                        content=ft.Text(
                            "DOWNLOAD",
                            weight=ft.FontWeight.BOLD,
                        ),
                        width=180,
                        height=48,
                        style=ft.ButtonStyle(
                            bgcolor=RED,
                            color=TEXT,
                        ),
                        on_click=lambda e: start_download(),
                    ),
                ],
                spacing=10,
            ),
        )

        body = ft.Column(
            [
                search_section,
                results_card,
                selected_card,
            ],
            expand=True,
            spacing=10,
        )

        page.add(
            ft.Column(
                [
                    header,
                    body,
                ],
                expand=True,
                spacing=0,
            )
        )

    def search_youtube():
        query = search_input.value.strip()

        if not query:
            search_status.value = "Enter something to search."
            page.update()
            return

        search_status.value = "Searching YouTube..."
        results_column.controls.clear()
        page.update()

        threading.Thread(
            target=search_worker,
            args=(query,),
            daemon=True,
        ).start()

    def search_worker(query):
        try:
            options = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }

            with YoutubeDL(options) as ydl:
                result = ydl.extract_info(
                    f"ytsearch8:{query}",
                    download=False,
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

                results.append(
                    {
                        "title": entry.get(
                            "title",
                            "Unknown video",
                        ),
                        "url": entry.get(
                            "webpage_url"
                        )
                        or entry.get("url"),
                        "channel": entry.get(
                            "channel"
                        )
                        or entry.get("uploader")
                        or "YouTube",
                        "duration": entry.get("duration"),
                        "thumbnail": thumbnail,
                    }
                )

            page.run_thread(
                lambda: search_success(results)
            )

        except Exception as error:
            message = str(error)

            if len(message) > 300:
                message = message[:300] + "..."

            page.run_thread(
                lambda: search_error(message)
            )

    def search_success(results):
        state["results"] = results

        if not results:
            search_status.value = "No videos found."
            page.update()
            return

        search_status.value = f"Found {len(results)} video(s)"

        for index, item in enumerate(results):
            add_result_card(index, item)

        page.update()

    def search_error(message):
        search_status.value = f"Search failed: {message}"
        page.update()

    def add_result_card(index, item):
        thumbnail_url = item.get("thumbnail", "")

        thumbnail = ft.Image(
            src=thumbnail_url,
            width=140,
            height=85,
            fit=ft.ImageFit.COVER,
            border_radius=6,
        )

        title = ft.Text(
            item.get("title", "Unknown video"),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=LIME,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )

        channel = ft.Text(
            item.get("channel", "YouTube"),
            size=11,
            color="#BBBBBB",
        )

        duration = ft.Text(
            format_duration(item.get("duration")),
            size=10,
            color="#777777",
        )

        info = ft.Column(
            [
                title,
                channel,
                duration,
            ],
            expand=True,
            spacing=2,
        )

        button = ft.Button(
            content=ft.Text(
                "DOWNLOAD",
                size=11,
                weight=ft.FontWeight.BOLD,
            ),
            width=110,
            height=40,
            style=ft.ButtonStyle(
                bgcolor=RED,
                color=TEXT,
            ),
            on_click=lambda e, i=index: select_video(i),
        )

        card = ft.Container(
            padding=6,
            bgcolor="#101010",
            border_radius=8,
            content=ft.Row(
                [
                    thumbnail,
                    info,
                    button,
                ],
                spacing=8,
            ),
        )

        results_column.controls.append(card)

    def select_video(index):
        item = state["results"][index]

        state["selected_url"] = item["url"]
        state["selected_title"] = item["title"]

        selected_title.value = item["title"]
        format_status.value = (
            "Video selected. Choose MP4 or MP3."
        )

        page.update()

    def choose_mp4():
        state["format"] = "mp4"

        format_mp4.style = ft.ButtonStyle(
            bgcolor=LIME,
            color="#000000",
        )

        format_mp3.style = ft.ButtonStyle(
            bgcolor="#333333",
            color=TEXT,
        )

        format_status.value = "MP4 selected"
        quality_dropdown.disabled = False

        extract_selected_formats()
        page.update()

    def choose_mp3():
        state["format"] = "mp3"

        format_mp3.style = ft.ButtonStyle(
            bgcolor=LIME,
            color="#000000",
        )

        format_mp4.style = ft.ButtonStyle(
            bgcolor="#333333",
            color=TEXT,
        )

        format_status.value = "MP3 selected"

        quality_dropdown.disabled = True
        quality_dropdown.options = [
            ft.DropdownOption(
                key="Best audio",
                text="Best audio",
            )
        ]
        quality_dropdown.value = "Best audio"

        page.update()

    def extract_selected_formats():
        url = state["selected_url"]

        if not url:
            return

        format_status.value = (
            "Reading available video qualities..."
        )
        page.update()

        threading.Thread(
            target=quality_worker,
            args=(url,),
            daemon=True,
        ).start()

    def quality_worker(url):
        try:
            options = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    url,
                    download=False,
                )

            heights = set()

            for fmt in info.get("formats", []):
                height = fmt.get("height")

                if height and height >= 144:
                    heights.add(height)

            qualities = [
                quality_label(height)
                for height in sorted(
                    heights,
                    reverse=True,
                )
            ]

            if not qualities:
                qualities = ["Best available"]

            page.run_thread(
                lambda: quality_success(qualities)
            )

        except Exception as error:
            message = str(error)

            if len(message) > 250:
                message = message[:250] + "..."

            page.run_thread(
                lambda: quality_error(message)
            )

    def quality_success(qualities):
        quality_dropdown.options = [
            ft.DropdownOption(
                key=q,
                text=q,
            )
            for q in qualities
        ]

        quality_dropdown.value = qualities[0]
        state["quality"] = qualities[0]

        format_status.value = (
            f"{len(qualities)} quality option(s) available"
        )

        page.update()

    def quality_error(message):
        format_status.value = (
            f"Could not read qualities: {message}"
        )
        page.update()

    def start_download():
        url = state["selected_url"]

        if not url:
            download_status.value = "Select a video first."
            page.update()
            return

        format_type = state["format"]
        quality = quality_dropdown.value or "Best available"

        if format_type == "mp4":
            height = get_height(quality)

            if height:
                selector = (
                    f"bestvideo[height<={height}]"
                    f"+bestaudio/best[height<={height}]"
                )
            else:
                selector = "bestvideo+bestaudio/best"

        else:
            selector = "bestaudio/best"

        download_status.value = (
            f"Starting {format_type.upper()} download..."
        )

        progress_bar.visible = True
        progress_bar.value = 0

        page.update()

        threading.Thread(
            target=download_worker,
            args=(url, format_type, selector),
            daemon=True,
        ).start()

    def get_height(quality):
        try:
            return int(quality.split("p")[0])
        except (ValueError, IndexError):
            return None

    def download_worker(url, format_type, selector):
        try:
            download_path = os.path.expanduser(
                "~/Downloads"
            )

            os.makedirs(
                download_path,
                exist_ok=True,
            )

            options = {
                "format": selector,
                "outtmpl": os.path.join(
                    download_path,
                    "%(title)s.%(ext)s",
                ),
                "quiet": True,
                "no_warnings": True,
                "noprogress": False,
                "progress_hooks": [
                    download_progress,
                ],
            }

            if format_type == "mp3":
                options["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
            else:
                options["merge_output_format"] = "mp4"

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True,
                )

            title = info.get("title", "Video")

            page.run_thread(
                lambda: download_success(
                    title,
                    format_type,
                )
            )

        except Exception as error:
            message = str(error)

            if len(message) > 300:
                message = message[:300] + "..."

            page.run_thread(
                lambda: download_error(message)
            )

    def download_progress(progress):
        if progress.get("status") != "downloading":
            return

        downloaded = progress.get(
            "downloaded_bytes",
            0,
        )

        total = (
            progress.get("total_bytes")
            or progress.get("total_bytes_estimate")
        )

        if total:
            percent = downloaded / total * 100

            page.run_thread(
                lambda: update_progress(percent)
            )

    def update_progress(percent):
        progress_bar.value = max(
            0,
            min(1, percent / 100),
        )

        download_status.value = (
            f"Downloading... {percent:.1f}%"
        )

        page.update()

    def download_success(title, format_type):
        progress_bar.value = 1
        download_status.value = (
            f"{format_type.upper()} complete: {title}"
        )
        page.update()

    def download_error(message):
        progress_bar.visible = False
        download_status.value = (
            f"Download failed: {message}"
        )
        page.update()


if __name__ == "__main__":
    ft.run(main)
