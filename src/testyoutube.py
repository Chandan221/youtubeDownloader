import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pytubefix import YouTube


def resource_path(relative_path):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


class Themes:
    DARK = {
        "bg": "#0f0f1a",
        "card": "#18182b",
        "card_hover": "#1f1f38",
        "input": "#232340",
        "input_focus": "#2a2a50",
        "primary": "#7c5cfc",
        "primary_hover": "#9175ff",
        "secondary": "#00d4aa",
        "success": "#00d4aa",
        "text": "#eeeff6",
        "text_secondary": "#8888aa",
        "text_muted": "#55557a",
        "border": "#2a2a4a",
        "border_focus": "#7c5cfc",
        "progress_bg": "#232340",
        "progress_fill": "#7c5cfc",
        "toggle_bg": "#232340",
        "toggle_active": "#7c5cfc",
        "toggle_knob": "#eeeff6",
    }
    LIGHT = {
        "bg": "#f0f2f7",
        "card": "#ffffff",
        "card_hover": "#f8f9ff",
        "input": "#e8eaef",
        "input_focus": "#dddff0",
        "primary": "#7c5cfc",
        "primary_hover": "#6a4de6",
        "secondary": "#00b894",
        "success": "#00b894",
        "text": "#1a1a2e",
        "text_secondary": "#6b6b8a",
        "text_muted": "#9999b3",
        "border": "#d8dae5",
        "border_focus": "#7c5cfc",
        "progress_bg": "#e8eaef",
        "progress_fill": "#7c5cfc",
        "toggle_bg": "#d8dae5",
        "toggle_active": "#7c5cfc",
        "toggle_knob": "#ffffff",
    }
    @classmethod
    def get(cls, name):
        return cls.DARK if name == "dark" else cls.LIGHT


FONT = "Segoe UI"
FONT_MONO = "Consolas"


def font_spec(size=10, weight="normal"):
    return (FONT, size, weight)


class ThemeToggle(tk.Frame):
    def __init__(self, parent, on_toggle, initial_theme="dark"):
        super().__init__(parent, cursor="hand2")
        self.on_toggle = on_toggle
        self.theme_name = initial_theme
        self.track_w = 40
        self.track_h = 20
        self.knob_r = 7
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


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("650x480")
        self.root.resizable(False, False)

        self.theme_name = "dark"
        self.colors = Themes.get(self.theme_name)

        self.yt = None
        self.streams = []
        self.download_path = os.getcwd()

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
                child.configure(bg=self.colors["card"] if role == "card" else self.colors["bg"])

            elif cls == "Label":
                label_role = getattr(child, "_label_role", "normal")
                if label_role == "heading":
                    child.configure(bg=self.colors["bg"], fg=self.colors["text"])
                elif label_role == "secondary":
                    child.configure(bg=self.colors["card"], fg=self.colors["text_secondary"])
                elif label_role == "percent":
                    child.configure(bg=self.colors["card"], fg=self.colors["primary"])
                else:
                    p_bg = self.colors["card"] if getattr(child.master, "_bg_role", None) == "card" else self.colors["bg"]
                    child.configure(bg=p_bg, fg=self.colors["text"])

            elif cls == "Button":
                btn_role = getattr(child, "_btn_role", "primary")
                if btn_role == "primary":
                    child.configure(bg=self.colors["primary"], fg="#ffffff",
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
                try:
                    parent_role = getattr(child.master, "_bg_role", None)
                    child.configure(bg=self.colors["card"] if parent_role == "card" else self.colors["bg"])
                except Exception:
                    pass

            elif cls == "Checkbutton":
                child.configure(bg=self.colors["card"], fg=self.colors["text"],
                    selectcolor=self.colors["input"],
                    activebackground=self.colors["card"],
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
            borderwidth=0, thickness=8)

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
        self.apply_theme()

    def build_header(self):
        header = self._make_bg(self.root)
        header.pack(fill="x", padx=28, pady=(22, 8))

        left = self._make_bg(header)
        left.pack(side="left")

        self._label(left, "\U0001F3AC YouTube Video Downloader", "heading",
            font=font_spec(18, "bold")).pack(anchor="w")

        self._label(left, "Download videos in progressive format", "secondary",
            font=font_spec(10)).pack(anchor="w")

        right = self._make_bg(header)
        right.pack(side="right")

        self.theme_toggle = ThemeToggle(right, self.on_theme_toggle, self.theme_name)
        self.theme_toggle.pack(side="right", padx=(0, 6))

        self.theme_label = self._label(right, "Dark", "secondary",
            font=font_spec(10))
        self.theme_label.pack(side="right", padx=(0, 6))

    def on_theme_toggle(self, theme_name):
        self.theme_name = theme_name
        self.theme_label.config(text="Dark" if theme_name == "dark" else "Light")
        self.apply_theme()

    def build_section_card(self, parent, padding=16):
        card = self._make_card(parent,
            highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(fill="x", padx=28, pady=(0, 8), ipady=padding)
        return card

    def build_main_card(self):
        card = self.build_section_card(self.root, padding=14)

        self._build_url_row(card)
        self._build_quality_row(card)
        self._build_folder_row(card)
        self._build_download_btn(card)

    def _build_url_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(10, 2))

        self._label(row, "YouTube URL", "normal",
            font=font_spec(11, "bold")).pack(anchor="w", pady=(0, 4))

        input_frame = self._make_card(row)
        input_frame.pack(fill="x")

        self.url_entry = tk.Entry(input_frame,
            font=font_spec(12),
            bg=self.colors["input"], fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            relief="flat", bd=0,
            highlightthickness=2,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["border_focus"])
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=10, ipadx=14)
        self.url_entry.bind("<FocusIn>", lambda e: self.url_entry.configure(highlightbackground=self.colors["border_focus"]))
        self.url_entry.bind("<FocusOut>", lambda e: self.url_entry.configure(highlightbackground=self.colors["border"]))

        fetch_btn = self._btn(input_frame, "Fetch Qualities", "secondary",
            command=self.fetch_qualities,
            font=font_spec(10, "bold"),
            relief="flat", bd=0, padx=22, pady=10, cursor="hand2")
        fetch_btn.pack(side="right", padx=(10, 0))

    def _build_quality_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(8, 4))

        self._label(row, "Quality", "normal",
            font=font_spec(11, "bold")).pack(side="left")

        self.quality_combo = ttk.Combobox(row,
            width=55, state="readonly", font=font_spec(10))
        self.quality_combo.pack(side="right", fill="x", expand=True, padx=(12, 0))

    def _build_folder_row(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(8, 4))

        self._label(row, "\U0001F4C2 Download Folder", "normal",
            font=font_spec(11, "bold")).pack(side="left")

        folder_btn = self._btn(row, "\U0001F4C2  Browse", "browse",
            command=self.select_folder,
            font=font_spec(10, "bold"),
            relief="flat", bd=0, padx=16, pady=6, cursor="hand2")
        folder_btn.pack(side="right")

        self.path_label = self._label(row, self._shorten_path(self.download_path, 50),
            "secondary", font=font_spec(10), anchor="e", padx=10)
        self.path_label.pack(side="right", fill="x", expand=True)

    def _build_download_btn(self, parent):
        row = self._make_card(parent)
        row.pack(fill="x", padx=20, pady=(10, 6))

        self.download_button = self._btn(row, "\u25BC  Download Video", "primary",
            command=self.start_download,
            font=font_spec(13, "bold"),
            relief="flat", bd=0, padx=30, pady=14, cursor="hand2")
        self.download_button.pack(fill="x")

    def build_progress_card(self):
        card = self.build_section_card(self.root, padding=10)

        self.progress = ttk.Progressbar(card, orient="horizontal",
            length=550, mode="determinate", style="TProgressbar")
        self.progress.pack(padx=20, pady=(10, 4), fill="x")

        status_frame = self._make_card(card)
        status_frame.pack(fill="x", padx=20)

        self.status_label = self._label(status_frame, "Ready", "secondary",
            font=font_spec(10), anchor="w")
        self.status_label.pack(side="left")

        self.percent_label = self._label(status_frame, "", "percent",
            font=font_spec(10, "bold"), anchor="e")
        self.percent_label.pack(side="right")

    def _shorten_path(self, path, max_len):
        if len(path) <= max_len:
            return path
        parts = path.split(os.sep)
        if len(parts) > 2:
            return parts[0] + os.sep + "..." + os.sep + parts[-1]
        return path

    def set_status(self, text, success=False):
        self.status_label.config(text=text,
            fg=self.colors["success"] if success else self.colors["text_secondary"])
        self.root.update_idletasks()

    def set_percent(self, value):
        self.percent_label.config(text=f"{value}%" if value > 0 else "")

    def fetch_qualities(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        try:
            self.set_status("Fetching video details...")
            self.yt = YouTube(url, on_progress_callback=self.on_progress)
            self.streams = (self.yt.streams
                .filter(progressive=True, file_extension="mp4")
                .order_by("resolution").desc())
            if not self.streams:
                messagebox.showerror("Error", "No downloadable streams found.")
                return
            options = []
            for s in self.streams:
                options.append(f"{s.resolution} | {s.mime_type} | {round(s.filesize / (1024 * 1024), 2)} MB")
            self.quality_combo["values"] = options
            self.quality_combo.current(0)
            self.set_status(f"Loaded - {self.yt.title}", True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch video:\n{e}")
            self.set_status("Error")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_label.config(text=self._shorten_path(folder, 50))

    def start_download(self):
        if not self.yt or not self.streams:
            messagebox.showerror("Error", "Please fetch video qualities first.")
            return
        idx = self.quality_combo.current()
        if idx == -1:
            messagebox.showerror("Error", "Please select a quality.")
            return
        thread = threading.Thread(target=self.download_video, args=(idx,), daemon=True)
        thread.start()

    def download_video(self, selected_index):
        try:
            self.download_button.config(state="disabled",
                bg=self.colors["text_muted"], text="\u23F3  Downloading...")
            self.progress["value"] = 0
            self.set_percent(0)
            stream = self.streams[selected_index]
            self.set_status(f"Downloading {stream.resolution}...")
            stream.download(output_path=self.download_path)
            self.progress["value"] = 100
            self.set_percent(100)
            self.set_status("Download completed!", True)
            messagebox.showinfo("Success", f"Video downloaded to:\n{self.download_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")
            self.set_status("Download failed")
        finally:
            self.download_button.config(state="normal",
                bg=self.colors["primary"], text="\u25BC  Download Video")

    def on_progress(self, stream, chunk, bytes_remaining):
        try:
            total = stream.filesize
            done = total - bytes_remaining
            pct = int((done / total) * 100)
            self.progress["value"] = pct
            self.set_percent(pct)
            self.root.update_idletasks()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
