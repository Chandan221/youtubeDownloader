import sys
import subprocess
import shutil
import importlib.util
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
from io import BytesIO

try:
    from PIL import Image, ImageTk
    _has_pil = True
except ImportError:
    _has_pil = False


def resource_path(relative_path):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def install_package(package_name):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None


def is_ffmpeg_installed():
    return get_ffmpeg_path() is not None


def get_ffmpeg_path():
    path = shutil.which("ffmpeg")
    if path:
        return path
    winget_base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.isdir(winget_base):
        for entry in os.listdir(winget_base):
            if "FFmpeg" in entry or "ffmpeg" in entry:
                for p in [os.path.join(winget_base, entry, "bin", "ffmpeg.exe"),
                          os.path.join(winget_base, entry, "ffmpeg.exe")]:
                    if os.path.isfile(p):
                        return p
    return None


def install_ffmpeg_windows():
    try:
        subprocess.check_call(["winget", "install", "--id", "Gyan.FFmpeg",
            "-e", "--accept-source-agreements", "--accept-package-agreements"])
        return True
    except Exception:
        return False


def check_and_install_requirements():
    root = tk.Tk()
    root.withdraw()
    if not is_package_installed("pytubefix"):
        messagebox.showinfo("Installing Requirement", "pytubefix is not installed.\n\nThe app will install it now.")
        try:
            install_package("pytubefix")
        except Exception as e:
            messagebox.showerror("Installation Failed", f"Could not install pytubefix.\n\nError:\n{e}")
            sys.exit(1)
    if not is_ffmpeg_installed():
        messagebox.showinfo("Installing Requirement", "FFmpeg is not installed.\n\nThe app will install FFmpeg now using winget.")
        success = install_ffmpeg_windows()
        if not success:
            messagebox.showerror("FFmpeg Installation Failed",
                "Could not install FFmpeg automatically.\n\nPlease install it manually using:\n\nwinget install Gyan.FFmpeg")
            sys.exit(1)
        messagebox.showinfo("Restart Required", "FFmpeg was installed successfully.\n\nPlease close and reopen this app.")
        sys.exit(0)
    root.destroy()


check_and_install_requirements()

from pytubefix import YouTube, Playlist


def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


class Themes:
    DARK = {
        "bg": "#1c1b1f",
        "card": "#2b2930",
        "card_hover": "#333138",
        "input": "#38353e",
        "input_focus": "#423f4a",
        "primary": "#d0bcff",
        "primary_hover": "#dccaff",
        "secondary": "#00d4aa",
        "tertiary": "#efb8c8",
        "success": "#00d4aa",
        "text": "#e6e1e5",
        "text_secondary": "#cac4d0",
        "text_muted": "#938f99",
        "border": "#4a4458",
        "border_focus": "#d0bcff",
        "progress_bg": "#38353e",
        "progress_fill": "#d0bcff",
        "toggle_bg": "#4a4458",
        "toggle_active": "#d0bcff",
        "toggle_knob": "#e6e1e5",
    }
    LIGHT = {
        "bg": "#fdf8fd",
        "card": "#f3edf7",
        "card_hover": "#e8e2ed",
        "input": "#e7e0ec",
        "input_focus": "#ddd6e6",
        "primary": "#6750a4",
        "primary_hover": "#7c64b8",
        "secondary": "#00b894",
        "tertiary": "#7d5260",
        "success": "#00b894",
        "text": "#1d1b20",
        "text_secondary": "#49454f",
        "text_muted": "#79747e",
        "border": "#cac4d0",
        "border_focus": "#6750a4",
        "progress_bg": "#e7e0ec",
        "progress_fill": "#6750a4",
        "toggle_bg": "#cac4d0",
        "toggle_active": "#6750a4",
        "toggle_knob": "#ffffff",
    }
    @classmethod
    def get(cls, name):
        return cls.DARK if name == "dark" else cls.LIGHT


FONT = "Segoe UI Variable Display, Segoe UI"
FONT_MONO = "Cascadia Code, Consolas"


def font_spec(size=10, weight="normal"):
    return (FONT, size, weight)


class ThemeToggle(tk.Frame):
    def __init__(self, parent, on_toggle, initial_theme="dark"):
        super().__init__(parent, cursor="hand2")
        self.on_toggle = on_toggle
        self.theme_name = initial_theme
        self.track_w = 44
        self.track_h = 24
        self.knob_r = 9
        self.configure(width=self.track_w, height=self.track_h)
        self.canvas = tk.Canvas(self, width=self.track_w, height=self.track_h,
            highlightthickness=0, bd=0)
        self.canvas.bind("<Button-1>", self._click)
        self.bind("<Button-1>", self._click)
        self.canvas.pack()

    def _click(self, event=None):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.render()
        self.on_toggle(self.theme_name)

    def render(self):
        t = Themes.get(self.theme_name)
        is_dark = self.theme_name == "dark"
        bg = t["toggle_active"] if is_dark else t["toggle_bg"]
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, self.track_w, self.track_h,
            fill=bg, outline=bg, width=0)
        kx = self.track_w - self.knob_r * 2 - 3 if is_dark else 3
        self.canvas.create_oval(kx, 3, kx + self.knob_r * 2, 3 + self.knob_r * 2,
            fill=t["toggle_knob"], outline=t["toggle_knob"], width=0)


class RoundedCard(tk.Frame):
    def __init__(self, parent, radius=16, bg_color="#2b2930", parent_bg="#1c1b1f", **kwargs):
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self._radius = radius
        self._bg_color = bg_color
        self._parent_bg = parent_bg

        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=parent_bg)
        self._canvas._is_rounding_canvas = True
        self._canvas.pack(fill="both", expand=True)

        self.bind("<Configure>", self._redraw)
        self._redraw()

    def recolor(self, bg_color, parent_bg):
        self._bg_color = bg_color
        self._parent_bg = parent_bg
        self.configure(bg=parent_bg)
        self._canvas.configure(bg=parent_bg)
        self._redraw()

    def _redraw(self, event=None):
        self._canvas.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 1 or h < 1:
            return
        r = min(self._radius, w // 4, h // 4)
        self._draw_rounded_rect(0, 0, w, h, r, fill=self._bg_color, outline="")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        kwargs.setdefault('width', 0)
        c = self._canvas
        c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, **kwargs)
        c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, **kwargs)
        c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, **kwargs)
        c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, **kwargs)
        c.create_rectangle(x1 + r, y1, x2 - r, y1 + 2 * r, **kwargs)
        c.create_rectangle(x1 + r, y2 - 2 * r, x2 - r, y2, **kwargs)
        c.create_rectangle(x1, y1 + r, x1 + 2 * r, y2 - r, **kwargs)
        c.create_rectangle(x2 - 2 * r, y1 + r, x2, y2 - r, **kwargs)
        c.create_rectangle(x1 + r, y1 + r, x2 - r, y2 - r, **kwargs)


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("860x740")
        self.root.resizable(False, False)

        self.theme_name = "dark"
        self.colors = Themes.get(self.theme_name)

        self.download_path = os.getcwd()
        self.yt = None
        self.video_streams = []
        self.is_playlist = tk.BooleanVar(value=False)
        self.audio_only = tk.BooleanVar(value=False)
        self.thumb_photo = None

        self.root.configure(bg=self.colors["bg"])
        self.set_icon()
        self.setup_style()
        self.create_widgets()

    def set_icon(self):
        try:
            png_path = resource_path("ytd-icon.png")
            if os.path.exists(png_path):
                icon = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, icon)
        except Exception:
            pass

    def setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def apply_theme(self):
        self.colors = Themes.get(self.theme_name)
        self.root.configure(bg=self.colors["bg"])
        self._recolor_all(self.root)
        self.theme_toggle.render()
        self.style_config()

    def _recolor_all(self, parent):
        for child in parent.winfo_children():
            role = getattr(child, "_bg_role", None)
            cls = child.winfo_class()

            if cls == "Frame":
                if role == "rounded_card":
                    child.recolor(self.colors["card"], self.colors["bg"])
                elif role == "card":
                    child.configure(bg=self.colors["card"])
                else:
                    child.configure(bg=self.colors["bg"])

            elif cls == "Label":
                label_role = getattr(child, "_label_role", "normal")
                if label_role == "heading":
                    child.configure(bg=self.colors["bg"], fg=self.colors["text"])
                elif label_role == "secondary":
                    child.configure(bg=self.colors["card"], fg=self.colors["text_secondary"])
                elif label_role == "percent":
                    child.configure(bg=self.colors["card"], fg=self.colors["primary"])
                elif label_role == "title":
                    child.configure(bg=self.colors["card"], fg=self.colors["text"])
                else:
                    p_bg = self.colors["card"] if getattr(child.master, "_bg_role", None) in ("card", "rounded_card") else self.colors["bg"]
                    child.configure(bg=p_bg, fg=self.colors["text"])

            elif cls == "Button":
                btn_role = getattr(child, "_btn_role", "primary")
                if btn_role == "primary":
                    child.configure(bg=self.colors["primary"], fg="#1c1b1f",
                        activebackground=self.colors["primary_hover"])
                elif btn_role == "secondary":
                    child.configure(bg=self.colors["secondary"], fg=self.colors["bg"],
                        activebackground="#00ecc0", activeforeground=self.colors["bg"])
                elif btn_role == "browse":
                    child.configure(bg=self.colors["input"], fg=self.colors["text"],
                        activebackground=self.colors["border"], activeforeground=self.colors["text"])
                elif btn_role == "clear":
                    child.configure(bg=self.colors["input"], fg=self.colors["text_secondary"],
                        activebackground=self.colors["border"], activeforeground=self.colors["text"])

            elif cls == "Entry":
                child.configure(bg=self.colors["input"], fg=self.colors["text"],
                    insertbackground=self.colors["primary"],
                    highlightbackground=self.colors["border"],
                    highlightcolor=self.colors["border_focus"])

            elif cls == "Text":
                child.configure(bg=self.colors["input"], fg=self.colors["text"],
                    insertbackground=self.colors["primary"],
                    highlightbackground=self.colors["border"])

            elif cls == "Canvas":
                if not getattr(child, "_is_rounding_canvas", False):
                    try:
                        parent_role = getattr(child.master, "_bg_role", None)
                        child.configure(bg=self.colors["card"] if parent_role == "card" else self.colors["bg"])
                    except Exception:
                        pass

            elif cls == "Checkbutton":
                p_role = getattr(child.master, "_bg_role", None)
                p_bg = self.colors["card"] if p_role in ("card", "rounded_card") else self.colors["bg"]
                child.configure(bg=p_bg, fg=self.colors["text"],
                    selectcolor=self.colors["input"],
                    activebackground=p_bg,
                    activeforeground=self.colors["text"])

            self._recolor_all(child)

    def style_config(self):
        c = self.colors
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["text"])
        self.style.configure("TEntry",
            fieldbackground=c["input"], foreground=c["text"],
            insertcolor=c["primary"], borderwidth=0)
        self.style.configure("TCombobox",
            fieldbackground=c["input"], foreground=c["text"],
            selectbackground=c["primary"], selectforeground=c["text"],
            arrowcolor=c["text_secondary"], borderwidth=0)
        self.style.map("TCombobox",
            fieldbackground=[("focus", c["input_focus"])])
        self.style.configure("TProgressbar",
            background=c["progress_fill"], troughcolor=c["progress_bg"],
            borderwidth=0, thickness=10)

    def _make_card(self, parent, **kwargs):
        f = tk.Frame(parent, **kwargs)
        f._bg_role = "card"
        return f

    def _make_bg(self, parent, **kwargs):
        f = tk.Frame(parent, **kwargs)
        f._bg_role = "bg"
        return f

    def _label(self, parent, text, role="normal", **kwargs):
        lbl = tk.Label(parent, text=text, **kwargs)
        lbl._label_role = role
        return lbl

    def _btn(self, parent, text, role="primary", **kwargs):
        btn = tk.Button(parent, text=text, **kwargs)
        btn._btn_role = role
        return btn

    def create_widgets(self):
        self.build_header()
        self.build_main_card()
        self.build_progress_card()
        self.build_log_card()
        self.apply_theme()

    def build_header(self):
        header = self._make_bg(self.root)
        header.pack(fill="x", padx=28, pady=(24, 12))

        left = self._make_bg(header)
        left.pack(side="left")

        self._label(left, "\U0001F3AC YouTube Downloader", "heading",
            font=font_spec(22, "bold")).pack(anchor="w")

        self._label(left, "Download videos, playlists & audio", "secondary",
            font=font_spec(12)).pack(anchor="w")

        right = self._make_bg(header)
        right.pack(side="right", pady=(4, 0))

        self.theme_toggle = ThemeToggle(right, self.on_theme_toggle, self.theme_name)
        self.theme_toggle.pack(side="right", padx=(0, 6))

        self.theme_label = self._label(right, "Dark", "secondary",
            font=font_spec(11))
        self.theme_label.pack(side="right", padx=(0, 6))

    def on_theme_toggle(self, theme_name):
        self.theme_name = theme_name
        self.theme_label.config(text="Dark" if theme_name == "dark" else "Light")
        self.apply_theme()

    def _on_audio_only_toggle(self):
        if self.audio_only.get():
            self.quality_combo.set("Audio Only")
            self.quality_combo.configure(state="disabled")
        else:
            self.quality_combo.configure(state="readonly")
            self.quality_combo.set("")

    def build_section_card(self, parent, padding=16):
        card = RoundedCard(parent, radius=18,
            bg_color=self.colors["card"], parent_bg=self.colors["bg"])
        card._bg_role = "rounded_card"
        card.pack(fill="x", padx=28, pady=(0, 12), ipady=padding)
        return card

    def build_main_card(self):
        card = self.build_section_card(self.root, padding=10)

        self.build_url_row(card)
        self.thumb_row = self._make_card(card)
        self.thumb_row.pack(fill="x", padx=20, pady=(6, 0))
        self.thumb_row.pack_forget()

        self.build_checkbox_row(card)
        self.build_quality_row(card)
        self.build_folder_row(card)
        self.build_download_btn(card)

    def build_url_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(12, 2))

        self._label(row, "YouTube URL", "normal",
            font=font_spec(12, "bold")).pack(anchor="w", pady=(0, 6))

        input_frame = self._make_card(row)
        input_frame.pack(fill="x")

        self.url_entry = tk.Entry(input_frame,
            font=font_spec(13),
            bg=self.colors["input"], fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            relief="flat", bd=0,
            highlightthickness=2,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["border_focus"])
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=12, ipadx=16)
        self.url_entry.bind("<FocusIn>", lambda e: self.url_entry.configure(highlightbackground=self.colors["border_focus"]))
        self.url_entry.bind("<FocusOut>", lambda e: self.url_entry.configure(highlightbackground=self.colors["border"]))

        fetch_btn = self._btn(input_frame, "Fetch", "secondary",
            command=self.fetch_qualities,
            font=font_spec(11, "bold"),
            relief="flat", bd=0, padx=26, pady=12, cursor="hand2")
        fetch_btn.pack(side="right", padx=(12, 0))

    def _clear_thumbnail(self):
        for w in self.thumb_row.winfo_children():
            w.destroy()
        self.thumb_row.pack_forget()
        self.thumb_photo = None

    def _load_thumbnail(self, yt):
        self._clear_thumbnail()
        try:
            url = yt.thumbnail_url
            if not url:
                return

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()

            if not _has_pil:
                return

            img = Image.open(BytesIO(data))
            max_w = 160
            w, h = img.size
            if w > max_w:
                ratio = max_w / w
                img = img.resize((max_w, int(h * ratio)), Image.LANCZOS)

            self.thumb_photo = ImageTk.PhotoImage(img)

            thumb_label = tk.Label(self.thumb_row, image=self.thumb_photo,
                bg=self.colors["card"], relief="flat", bd=0)
            thumb_label._label_role = "normal"
            thumb_label.pack(side="left", padx=(0, 14))

            info_frame = self._make_card(self.thumb_row)
            info_frame.pack(side="left", fill="x", expand=True)

            title = yt.title or ""
            if len(title) > 80:
                title = title[:77] + "..."

            title_lbl = self._label(info_frame, title, "title",
                font=font_spec(12, "bold"), anchor="w", wraplength=500)
            title_lbl.pack(fill="x", pady=(0, 2))

            meta_parts = []
            try:
                if yt.author:
                    meta_parts.append(yt.author)
            except Exception:
                pass
            try:
                if yt.length:
                    mins, secs = divmod(int(yt.length), 60)
                    meta_parts.append(f"{mins}:{secs:02d}")
            except Exception:
                pass
            try:
                if yt.views:
                    meta_parts.append(f"{yt.views:,} views")
            except Exception:
                pass

            if meta_parts:
                meta_lbl = self._label(info_frame, "  |  ".join(meta_parts), "secondary",
                    font=font_spec(10))
                meta_lbl.pack(fill="x")

            self.thumb_row.pack(fill="x", padx=20, pady=(6, 2))

        except Exception:
            pass

    def build_checkbox_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(4, 2))

        self.playlist_cb = tk.Checkbutton(row,
            text="This URL is a playlist", variable=self.is_playlist,
            font=font_spec(12),
            bg=self.colors["card"], fg=self.colors["text"],
            selectcolor=self.colors["input"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["text"],
            relief="flat", bd=0, cursor="hand2",
            padx=8, pady=8)
        self.playlist_cb.pack(side="left")

        self.audio_cb = tk.Checkbutton(row,
            text="Audio only (MP3)", variable=self.audio_only,
            command=self._on_audio_only_toggle,
            font=font_spec(12),
            bg=self.colors["card"], fg=self.colors["text"],
            selectcolor=self.colors["input"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["text"],
            relief="flat", bd=0, cursor="hand2",
            padx=8, pady=8)
        self.audio_cb.pack(side="left", padx=(14, 0))

    def build_quality_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(8, 4))

        self._label(row, "Quality", "normal",
            font=font_spec(12, "bold")).pack(side="left")

        self.quality_combo = ttk.Combobox(row,
            width=52, state="readonly", font=font_spec(12))
        self.quality_combo.pack(side="right", fill="x", expand=True, padx=(16, 0))

    def build_folder_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(8, 4))

        self._label(row, "Save to", "normal",
            font=font_spec(12, "bold")).pack(side="left")

        folder_btn = self._btn(row, "\U0001F4C2  Browse", "browse",
            command=self.select_folder,
            font=font_spec(11, "bold"),
            relief="flat", bd=0, padx=18, pady=8, cursor="hand2")
        folder_btn.pack(side="right")

        self.path_label = self._label(row, self._shorten_path(self.download_path, 55),
            "secondary", font=font_spec(11), anchor="e", padx=12)
        self.path_label.pack(side="right", fill="x", expand=True)

    def build_download_btn(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(10, 8))

        self.download_button = self._btn(row, "\u25BC  Download Now", "primary",
            command=self.start_download,
            font=font_spec(14, "bold"),
            relief="flat", bd=0, padx=30, pady=16, cursor="hand2")
        self.download_button.pack(fill="x")

    def build_progress_card(self):
        card = self.build_section_card(self.root, padding=10)

        self.progress = ttk.Progressbar(card, orient="horizontal",
            length=800, mode="determinate", style="TProgressbar")
        self.progress.pack(padx=20, pady=(12, 6), fill="x")

        status_frame = self._make_card(card)
        status_frame.pack(fill="x", padx=20)

        self.status_label = self._label(status_frame, "Ready", "secondary",
            font=font_spec(11), anchor="w")
        self.status_label.pack(side="left")

        self.percent_label = self._label(status_frame, "", "percent",
            font=font_spec(14, "bold"), anchor="e")
        self.percent_label.pack(side="right")

    def build_log_card(self):
        card = RoundedCard(self.root, radius=18,
            bg_color=self.colors["card"], parent_bg=self.colors["bg"])
        card._bg_role = "rounded_card"
        card.pack(fill="both", expand=True, padx=28, pady=(0, 28), ipady=4)

        header = self._make_card(card)
        header.pack(fill="x", padx=20, pady=(12, 0))

        self._label(header, "Activity Log", "normal",
            font=font_spec(12, "bold")).pack(side="left")

        self.clear_btn = self._btn(header, "Clear", "clear",
            command=self.clear_log,
            font=font_spec(10, "bold"),
            relief="flat", bd=0, padx=14, pady=4, cursor="hand2")
        self.clear_btn.pack(side="right")

        self.log_box = tk.Text(card, height=7,
            font=(FONT_MONO, 10),
            bg=self.colors["input"], fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            relief="flat", bd=0, highlightthickness=2,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["border_focus"],
            padx=16, pady=12)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(8, 16))

    def _shorten_path(self, path, max_len):
        if len(path) <= max_len:
            return path
        parts = path.split(os.sep)
        if len(parts) > 2:
            return parts[0] + os.sep + "..." + os.sep + parts[-1]
        return path

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, text, is_success=False):
        self.status_label.config(text=text,
            fg=self.colors["success"] if is_success else self.colors["text_secondary"])
        self.root.update_idletasks()

    def set_percent(self, value, size_text=""):
        text = ""
        if value > 0:
            text = f"{value}%"
            if size_text:
                text = f"{size_text}  ({value}%)"
        elif value == 0 and size_text:
            text = size_text
        self.percent_label.config(text=text)

    def fetch_qualities(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        try:
            self.set_status("Fetching information...")
            self.set_percent(0)
            self.progress["value"] = 0
            self._clear_thumbnail()

            if self.is_playlist.get():
                playlist = Playlist(url)
                if not playlist.video_urls:
                    messagebox.showerror("Error", "No videos found in playlist.")
                    return
                self.yt = YouTube(playlist.video_urls[0], on_progress_callback=self.on_progress)
            else:
                self.yt = YouTube(url, on_progress_callback=self.on_progress)

            if self.audio_only.get():
                audio_stream = (self.yt.streams
                    .filter(only_audio=True)
                    .order_by("abr").desc().first())
                if audio_stream is None:
                    messagebox.showerror("Error", "No audio stream found.")
                    return
                size_mb = round(audio_stream.filesize / (1024 * 1024), 2)
                self.quality_combo.set(f"Audio Only | {audio_stream.abr} | {size_mb} MB")
                self.quality_combo.configure(state="disabled")
                self._load_thumbnail(self.yt)
                self.set_status(f"Audio info loaded for: {self.yt.title}", True)
                return

            self.video_streams = (self.yt.streams
                .filter(adaptive=True, only_video=True, file_extension="mp4")
                .order_by("resolution").desc())

            if not self.video_streams:
                messagebox.showerror("Error", "No video streams found.")
                return

            quality_options = []
            seen = set()
            for stream in self.video_streams:
                if stream.resolution in seen:
                    continue
                seen.add(stream.resolution)
                size_mb = round(stream.filesize / (1024 * 1024), 2)
                quality_options.append(f"{stream.resolution} | {stream.fps}fps | {size_mb} MB")

            self.quality_combo["values"] = quality_options
            self.quality_combo.current(0)
            self.quality_combo.configure(state="readonly")
            self._load_thumbnail(self.yt)
            self.set_status(f"Loaded {len(quality_options)} quality options for: {self.yt.title}", True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch qualities:\n{e}")
            self.set_status("Failed to fetch qualities")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_label.config(text=self._shorten_path(folder, 55))

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        selected_quality = self.get_selected_resolution()
        if not self.audio_only.get() and not selected_quality:
            messagebox.showerror("Error", "Please select a quality.")
            return
        thread = threading.Thread(target=self.download_task, args=(url, selected_quality), daemon=True)
        thread.start()

    def get_selected_resolution(self):
        selected = self.quality_combo.get()
        return selected.split("|")[0].strip() if selected else None

    def download_task(self, url, selected_quality):
        self.download_button.config(state="disabled",
            bg=self.colors["text_muted"], text="\u23F3  Downloading...")
        self.progress["value"] = 0
        self.set_percent(0)
        try:
            if self.audio_only.get():
                if self.is_playlist.get():
                    self.download_playlist_audio(url)
                else:
                    self.download_single_audio(url)
            elif self.is_playlist.get():
                self.download_playlist(url, selected_quality)
            else:
                self.download_single_video(url, selected_quality)
            self.set_status("Download completed successfully!", True)
            messagebox.showinfo("Success", "Download completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")
            self.set_status("Download failed")
        finally:
            self.download_button.config(state="normal",
                bg=self.colors["primary"], fg="#1c1b1f", text="\u25BC  Download Now")

    def download_playlist(self, playlist_url, selected_quality):
        playlist = Playlist(playlist_url)
        playlist_title = clean_filename(playlist.title or "YouTube_Playlist")
        playlist_folder = os.path.join(self.download_path, playlist_title)
        os.makedirs(playlist_folder, exist_ok=True)
        total_videos = len(playlist.video_urls)
        self.log(f"Playlist: {playlist_title}")
        self.log(f"Total videos: {total_videos}")
        self.log(f"Selected quality: {selected_quality}")
        for index, video_url in enumerate(playlist.video_urls, start=1):
            try:
                self.set_status(f"Downloading {index}/{total_videos}")
                self.log(f"Downloading {index}/{total_videos}: {video_url}")
                yt = YouTube(video_url, on_progress_callback=self.on_progress)
                self.download_video_by_quality(yt, selected_quality, playlist_folder, prefix=f"{index:02d}_")
                self.log(f"Done: {yt.title}")
            except Exception as e:
                self.log(f"Failed: {video_url}")
                self.log(f"Reason: {e}")
        self.progress["value"] = 100
        self.set_percent(100)

    def download_single_video(self, video_url, selected_quality):
        yt = YouTube(video_url, on_progress_callback=self.on_progress)
        self.log(f"Video: {yt.title}")
        self.log(f"Selected quality: {selected_quality}")
        self.download_video_by_quality(yt, selected_quality, self.download_path)
        self.progress["value"] = 100
        self.set_percent(100)

    def download_video_by_quality(self, yt, selected_quality, output_folder, prefix=""):
        video_stream = (yt.streams
            .filter(adaptive=True, only_video=True, file_extension="mp4", res=selected_quality)
            .order_by("fps").desc().first())
        if video_stream is None:
            self.log(f"{selected_quality} not available for {yt.title}. Downloading best available quality instead.")
            video_stream = (yt.streams
                .filter(adaptive=True, only_video=True, file_extension="mp4")
                .order_by("resolution").desc().first())
        audio_stream = (yt.streams
            .filter(adaptive=True, only_audio=True, file_extension="mp4")
            .order_by("abr").desc().first())
        if audio_stream is None:
            raise Exception("No audio stream found.")
        title = clean_filename(yt.title)
        temp_video = os.path.join(output_folder, f"{prefix}temp_video.mp4")
        temp_audio = os.path.join(output_folder, f"{prefix}temp_audio.mp4")
        output_file = os.path.join(output_folder, f"{prefix}{title}_{video_stream.resolution}.mp4")
        self.set_status(f"Downloading video... ({video_stream.resolution})")
        video_stream.download(output_path=output_folder, filename=f"{prefix}temp_video.mp4")
        self.set_status("Downloading audio...")
        audio_stream.download(output_path=output_folder, filename=f"{prefix}temp_audio.mp4")
        self.set_status("Merging with FFmpeg...")
        self.root.update_idletasks()
        ffmpeg_bin = get_ffmpeg_path() or "ffmpeg"
        subprocess.run([ffmpeg_bin, "-y",
            "-i", temp_video, "-i", temp_audio,
            "-c:v", "copy", "-c:a", "aac", output_file],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        for f in [temp_video, temp_audio]:
            if os.path.exists(f):
                os.remove(f)

    def download_single_audio(self, video_url):
        yt = YouTube(video_url, on_progress_callback=self.on_progress)
        self.log(f"Video: {yt.title}")
        self.log("Mode: Audio only")
        self._download_audio(yt, self.download_path)
        self.progress["value"] = 100
        self.set_percent(100)

    def download_playlist_audio(self, playlist_url):
        playlist = Playlist(playlist_url)
        playlist_title = clean_filename(playlist.title or "YouTube_Playlist")
        playlist_folder = os.path.join(self.download_path, playlist_title)
        os.makedirs(playlist_folder, exist_ok=True)
        total_videos = len(playlist.video_urls)
        self.log(f"Playlist: {playlist_title}")
        self.log(f"Total videos: {total_videos}")
        self.log("Mode: Audio only")
        for index, video_url in enumerate(playlist.video_urls, start=1):
            try:
                self.set_status(f"Downloading audio {index}/{total_videos}")
                self.log(f"Downloading {index}/{total_videos}: {video_url}")
                yt = YouTube(video_url, on_progress_callback=self.on_progress)
                self._download_audio(yt, playlist_folder, prefix=f"{index:02d}_")
                self.log(f"Done: {yt.title}")
            except Exception as e:
                self.log(f"Failed: {video_url}")
                self.log(f"Reason: {e}")
        self.progress["value"] = 100
        self.set_percent(100)

    def _download_audio(self, yt, output_folder, prefix=""):
        audio_stream = (yt.streams
            .filter(only_audio=True)
            .order_by("abr").desc().first())
        if audio_stream is None:
            raise Exception("No audio stream found.")
        title = clean_filename(yt.title)
        temp_audio = os.path.join(output_folder, f"{prefix}temp_audio.mp4")
        output_file = os.path.join(output_folder, f"{prefix}{title}.mp3")
        self.set_status("Downloading audio...")
        audio_stream.download(output_path=output_folder, filename=f"{prefix}temp_audio.mp4")
        self.set_status("Converting to MP3...")
        self.root.update_idletasks()
        ffmpeg_bin = get_ffmpeg_path() or "ffmpeg"
        subprocess.run([ffmpeg_bin, "-y",
            "-i", temp_audio,
            "-codec:a", "libmp3lame", "-qscale:a", "2", output_file],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

    def on_progress(self, stream, chunk, bytes_remaining):
        try:
            total_size = getattr(stream, 'filesize', None)
            if total_size and total_size > 0:
                downloaded = total_size - bytes_remaining
                percentage = int((downloaded / total_size) * 100)
                self.progress["value"] = percentage
                dl_mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                self.set_percent(percentage, f"{dl_mb:.1f} MB / {total_mb:.1f} MB")
            else:
                percentage = 50
                self.progress["value"] = percentage
                self.set_percent(percentage, "Downloading...")
            self.root.update_idletasks()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
