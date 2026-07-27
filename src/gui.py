import tkinter as tk
from tkinter import ttk
from decorator import disabled

from utils import get_monitor
from command_gui import CommandGui


class MainGui(tk.Tk):
    def __init__(self):
        super().__init__()

        # self._on_resize = None
        self._windows_width = None
        self._windows_height = None

        # Configura la finestra
        self.overrideredirect(True)

        # Make the window always on top
        self.attributes("-topmost", True)

        self._size_canvas_video: tuple[int, int] = [0, 0]
        self._set_canvas_video()

        # Abilita il trascinamento della finestra
        self._is_dragging = False
        self._drag_position = None

    def set_command_bar(self):
        self.command_bar = CommandGui(self)

    def set_windows_by_factor(self, scale_factor=0.8, display=1):
        screen = get_monitor(display)

        self._windows_width = int(screen.width * scale_factor)
        self._windows_height = int(screen.height * scale_factor)

        y = int((screen.height - self._windows_height) / 2)
        x = int((screen.width - self._windows_width) / 2)

        self.set_windows(self._windows_width, self._windows_height, x, y)

    def set_windows(
        self,
        width: int,
        height: int,
        x_top_left: int,
        y_top_left: int,
        display: int = 1,
    ):
        screen = get_monitor(display)

        self._windows_width = min(screen.height, width)
        self._windows_height = min(screen.width, height)

        self.geometry(
            f"{self._windows_width}x{self._windows_height }+{x_top_left}+{y_top_left}"
        )
        self.overrideredirect(1)

    def run(self):
        self.bind("<ButtonPress-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_move)
        self.bind("<ButtonRelease-1>", self.on_drag_stop)

    @disabled
    def on_drag_start(self, event):
        self._is_dragging = True
        self._drag_position = event.x, event.y

    @disabled
    def on_drag_move(self, event):
        if self._is_dragging:
            x, y = self._drag_position
            self.geometry(f"+{event.x_root - x}+{event.y_root - y}")

    @disabled
    def on_drag_stop(self, event):
        self._is_dragging = False
        self._drag_position = None

    def _set_label_message(self, level, msg="prova"):

        color = "Black" if level == "Info" else "Red"
        self._label_message = ttk.Label(
            text=msg,
            background="#ffffff",
            foreground=color,
            font=("Helvetica", 12),
            wraplength=self._windows_width,
            padding=(10, 10),
        )

        self._label_message.place(x=10, y=10)
        self._label_message.after(10000, self._label_message.destroy)

    def set_new_message(self, level, message):
        if (
            not hasattr(self, "_label_message")
            or not self._label_message.winfo_exists()
        ):
            self._set_label_message(level, message)
        else:
            new_msg = self._label_message.cget("text") + " \n\r" + message
            self._label_message.destroy()
            self._set_label_message(level, new_msg)

        print("[" + level + "]: " + message)

    def _set_canvas_video(self):
        # Create a label to display video frames
        self._canvas_video = tk.Canvas(
            self,
            width=self.winfo_width(),
            height=self.winfo_height(),
            highlightthickness=0,
        )

        hbar = tk.Scrollbar(self._canvas_video, orient=tk.HORIZONTAL)
        hbar.config(command=self._canvas_video.xview)

        vbar = tk.Scrollbar(self._canvas_video, orient=tk.VERTICAL)
        vbar.config(command=self._canvas_video.yview)

        self._canvas_video.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self._canvas_video.pack(padx=0, pady=0, expand=True, fill="both")

    def _scroll_canvas_video(self, direction: str):

        if direction == "left":
            self._canvas_video.xview_scroll(1, "units")
        elif direction == "right":
            self._canvas_video.xview_scroll(-1, "units")

        elif direction == "up":
            self._canvas_video.yview_scroll(1, "units")
        elif direction == "down":
            self._canvas_video.yview_scroll(-1, "units")

        self._canvas_video.update_idletasks()

        x = self._canvas_video.canvasx(0)
        y = self._canvas_video.canvasy(0)
        print(f"Canvas coordinates after scroll: x={x}, y={y}")

    def update_video(self, imageCam):
        self._canvas_video.delete("all")

        self._canvas_video.image = (
            imageCam  # Necessario per evitare che l'immagine venga garbage collected
        )
        image_id = self._canvas_video.create_image(0, 0, image=imageCam, anchor=tk.NW)

        # Confronta le dimensioni dell'immagine corrente con quelle precedenti
        if (imageCam.width() != self._size_canvas_video[0]) or (
            imageCam.height() != self._size_canvas_video[1]
        ):
            self._canvas_video.configure(scrollregion=self._canvas_video.bbox(image_id))

            self._size_canvas_video[0] = imageCam.width()
            self._size_canvas_video[1] = imageCam.height()

    def _move_canvas_video(self, x, y):
        scroll_region = self._canvas_video.bbox("all")

        if scroll_region is None:
            self.set_scroll_position(x, y)
            return

        self._canvas_video.xview_moveto(x / scroll_region[2])
        self._canvas_video.yview_moveto(y / scroll_region[3])

    def set_scroll_position(self, x, y):
        self._canvas_video.update_idletasks()
        self._canvas_video.after(400, self._move_canvas_video, x, y)

    def get_scroll_position(self):
        x = self._canvas_video.canvasx(0)
        y = self._canvas_video.canvasy(0)
        return [x, y]

    def set_refresh_video(self, frame_rate, fun):
        self._canvas_video.after(int((1 / frame_rate) * 1000), fun)
