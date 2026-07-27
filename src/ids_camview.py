from gui import MainGui
from cam import IDSCam

import queue
from load_config import load_ini, load_config_default, save_ini


target_fps = 20
loaded_config_default = False
config = None
config_path = None
typeView = None

mainWindows: MainGui = None
cam: IDSCam = None

list_factor = [0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.33, 0.50, 0.67, 1.0, 1.5, 2.0]


def save_config_file():
    global config, cam, mainWindows

    if typeView is None:
        mainWindows.set_new_message("Error", "Save failed")
        return

    try:
        config.set("view."+typeView, "scale", str(cam.get_scale_factor()))
        config.set("view."+typeView, "x_position", str(mainWindows.get_scroll_position()[0]))
        config.set("view."+typeView, "y_position", str(mainWindows.get_scroll_position()[1]))

        save_ini(config, config_path)
        mainWindows.set_new_message("Info", "Saving completed")
    except Exception as e:
        print(str(e))
        mainWindows.set_new_message("Error", "Save failed")


def zoom_in_out(zoom):
    sc_fac = cam.get_scale_factor()
    # Calcolare la differenza assoluta tra ciascun valore della lista e il target
    differenze = [abs(x - sc_fac) for x in list_factor]

    # Trovare l'indice del valore minimo nelle differenze
    indice_minimo = differenze.index(min(differenze))

    if zoom == "out" and indice_minimo - 1 >= 0:
        sc_fac = list_factor[indice_minimo - 1]
    elif zoom == "in" and indice_minimo < len(list_factor) - 1:
        sc_fac = list_factor[indice_minimo + 1]
    else:
        return

    cam.set_scale_factor(sc_fac)
    mainWindows.command_bar.update_label_zoom(sc_fac)


def setMainWindows(width, height):
    global mainWindows, loaded_config_default, config_path

    mainWindows.set_windows(
        width,
        height,
        config["PrintingView.ViewAreaCorners"].getint("x"),
        config["PrintingView.ViewAreaCorners"].getint("y"),
    )

    mainWindows.run()

    if loaded_config_default:
        mainWindows.set_new_message(
            "Error",
            f'Error: The config file in "{config_path}" is incorrect. The default configuration has been loaded',
        )


def setCommandBar():
    global mainWindows, loaded_config_default

    width = min(config["PrintingView.CommandAreaCorners"].getint("width"), 1080)
    height = min(config["PrintingView.CommandAreaCorners"].getint("heigth"), 1920)
    mainWindows.set_command_bar()
    mainWindows.command_bar.set_windows(
        width,
        height,
        config["PrintingView.CommandAreaCorners"].getint("x"),
        config["PrintingView.CommandAreaCorners"].getint("y"),
        2,
    )

    mainWindows.command_bar.set_zoom_event(zoom_in_out)
    mainWindows.command_bar.set_callback_save(save_config_file)
    mainWindows.command_bar.set_callback_scroll(mainWindows._scroll_canvas_video)


def idsCamView(args=None):
    global cam, mainWindows, loaded_config_default, config, config_path, typeView

    # parser = argparse.ArgumentParser(description="")
    # parser.add_argument("--configPath", type=str, required=False, default="config.cfg")
    # parser.add_argument("--typeView", type=str, required=False, default="Default")

    # args = parser.parse_args()

    config_path = args.configPath
    config = load_ini(config_path)

    if config is None:
        config = load_config_default()
        loaded_config_default = True

    width_windows = config["PrintingView.ViewAreaCorners"].getint("width")
    height_windows = config["PrintingView.ViewAreaCorners"].getint("heigth")

    mainWindows = MainGui()
    setMainWindows(width_windows, height_windows)
    setCommandBar()

    cam = IDSCam(target_fps)
    cam.set_callback_message(mainWindows.set_new_message)

    if cam.run():

        if "view." + args.typeView in config:
            typeView = args.typeView
        elif loaded_config_default:
            typeView = "Default"
            mainWindows.command_bar.disable_save_button()

        if typeView is not None:
            cam.set_scale_factor(config["view." + typeView].getfloat("scale"))

            mainWindows.set_scroll_position(
                config["view." + typeView].getfloat("x_position"),
                config["view." + typeView].getfloat("y_position"),
            )

            mainWindows.command_bar.set_label_config(typeView)

        else:
            cam.set_scale_factor_size_screen((width_windows, height_windows))
            mainWindows.command_bar.set_label_config("bad config file")
            mainWindows.command_bar.disable_save_button()

        mainWindows.command_bar.update_label_zoom(cam.get_scale_factor())

        def capture_video():
            try:
                while True:
                    image = cam.get_capture_image()
                    mainWindows.update_video(image)
            except queue.Empty:
                pass

            mainWindows.set_refresh_video(target_fps + 5, capture_video)

        capture_video()

        def update_temperature():
            t = cam.get_device_temperature()
            mainWindows.command_bar.set_update_temperature(update_temperature, t)

        update_temperature()
    # else:
    #     mainWindows.command_bar.disable_save_button()

    mainWindows.mainloop()


# if __name__ == "__main__":
#     main()
