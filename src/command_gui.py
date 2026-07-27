import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from decorator import disabled
from utils import get_monitor, set_callback, resource_path


class CommandGui(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self._command_zoom = None
        self._command_save = None
        self._command_scroll = None

        self.overrideredirect(True)

        # Disabilita il trascinamento della finestra
        self._is_dragging = False
        self._drag_position = None

        # self.configure(bg="white")

        # Imposta l'app come topmost dopo l'avvio
        self.after(100, self.set_topmost)

    def set_topmost(self):
        self.attributes("-topmost", True)

    def set_windows(
        self,
        width: int,
        height: int,
        x_top_left: int,
        y_top_left: int,
        display: int = 1,
    ):
        screen = get_monitor(display)

        windows_width = min(screen.height, width)
        windows_height = min(screen.width, height)

        self.geometry(f"{windows_width}x{windows_height }+{x_top_left}+{y_top_left}")
        self.overrideredirect(True)

        self._setup_menu_bar()

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

    def _add_menu_button(self, parent, icon_path, command):
        button = self._create_button_image(resource_path(icon_path), parent, command)
        button.pack(side=tk.LEFT, padx=5)
        return button

    def _create_button_image(self, icon_path, parent, command):
        image = Image.open(icon_path)
        image = image.resize((30, 30), Image.LANCZOS)
        icon = ImageTk.PhotoImage(image)

        button = ttk.Button(parent, image=icon, command=command)
        button.image = icon  # Keep a reference to avoid garbage collection

        return button

    def _setup_menu_bar(self):
        # Create a frame at the bottom for additional buttons

        self._add_menu_button(
            self,
            "img/delete_min_icon.png",
            lambda: self._command_zoom("out"),
        )

        self._label_zoom = ttk.Label(self, text="x1.0", font=("Helvetica", 12))
        self._label_zoom.pack(side=tk.LEFT, padx=5)

        self._add_menu_button(
            self, "img/add_plus_icon.png", lambda: self._command_zoom("in")
        )

        self._add_menu_button(
            self,
            "img/left-button.png",
            lambda: self._command_scroll("left"),
        )
        self._add_menu_button(
            self, "img/up-button.png", lambda: self._command_scroll("up")
        )
        self._add_menu_button(
            self,
            "img/down-button.png",
            lambda: self._command_scroll("down"),
        )
        self._add_menu_button(
            self,
            "img/right-button.png",
            lambda: self._command_scroll("right"),
        )

        self._label_config = ttk.Label(self)
        self._label_config.pack(side=tk.LEFT, padx=25)

        self.save_button = ttk.Button(
            self, text="Save", command=lambda: self._command_save()
        )
        self.save_button.pack(side=tk.RIGHT, padx=5)

        self._label_temperature = ttk.Label(self, text="-1", font=("Helvetica", 12))
        self._label_temperature.pack(side=tk.RIGHT, padx=5)

    def set_update_temperature(self, fun, temperature):
        if temperature == "---":
            self._label_temperature.config(text="--- °C")
        else:
            self._label_temperature.config(text="{:.2f} °C".format(temperature))

        self._label_temperature.after(1000, fun)

    def set_label_config(self, config_name):
        self._label_config.config(text=config_name)

    def update_label_zoom(self, zoom):
        self._label_zoom.config(text="x{:.2f}".format(zoom))

    def set_zoom_event(self, fun):
        set_callback(self, "_command_zoom", fun)

    def set_callback_save(self, fun, args=None):
        set_callback(self, "_command_save", fun, args)

    def set_callback_scroll(self, fun, args=None):
        set_callback(self, "_command_scroll", fun, args)

    def disable_save_button(self):
        self.save_button.config(state=tk.DISABLED)
