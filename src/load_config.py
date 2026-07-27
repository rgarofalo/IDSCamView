import configparser
import os

CONFIG_MAP = {
    "PrintingView.ViewAreaCorners": {
        "width": {"type": int, "min": 100, "max": 1080},
        "heigth": {"type": int, "min": 100, "max": 1920},
        "x": {"type": int, "min": 0, "max": 1080},
        "y": {"type": int, "min": 0, "max": 1920},
    },
    "PrintingView.CommandAreaCorners": {
        "width": {"type": int, "min": 100, "max": 1080},
        "heigth": {"type": int, "min": 50, "max": 50},
        "x": {"type": int, "min": 0, "max": 1080},
        "y": {"type": int, "min": 0, "max": 1920},
    },
    "view": {
        "scale": {"type": float, "min": 0.03, "max": 2.0},
        "x_position": {"type": float, "min": -4000, "max": 4000},
        "y_position": {"type": float, "min": -3000, "max": 3000},
    },
}

CONFIG_DEFAULT = """
[PrintingView.ViewAreaCorners]
width = 700
heigth = 500
x = 500
y = 200

[PrintingView.CommandAreaCorners]
width = 700
heigth = 50
x = 500
y = 800


[view.Default]
scale = 0.15
x_position = 0
y_position = 0
"""


def load_ini(file_path):
    try:
        config = configparser.ConfigParser()
        if os.path.exists(file_path):
            config.read(file_path)

            if _verifica_config(config):
                return config

        return None
    except configparser.Error as e:
        return None


def save_ini(config, file_path):

    try:
        if _verifica_config(config):
            with open(file_path, "w") as configfile:
                config.write(configfile)
            return True
    except Exception as e:
        print(str(e))

    return False


def load_config_default():
    global CONFIG_DEFAULT
    config = configparser.ConfigParser()
    config.read_string(CONFIG_DEFAULT)
    return config


def _verifica_tipo_valore(value, expected_type):
    try:
        if expected_type["type"] == int:
            value = int(value)
        elif expected_type["type"] == float:
            value = float(value)
        elif expected_type["type"] == str:
            value = str(value)
        else:
            return False

        # Check limits
        if "min" in expected_type and value < expected_type["min"]:
            print(f"Value too low: {value}, minimum: {expected_type['min']}")
            return False
        if "max" in expected_type and value > expected_type["max"]:
            print(f"Value too high: {value}, maximum: {expected_type['max']}")
            return False

        return True
    except ValueError:
        return False


def _verifica_config(config):
    global CONFIG_MAP

    is_exist_view_section = False
    # Verifica che tutte le sezioni richieste esistano
    for required_section in CONFIG_MAP.keys():
        if not config.has_section(required_section) and required_section != "view":
            print(f"Missing section: {required_section}")
            return False

    for section in config.sections():
        if section in CONFIG_MAP:
            options = CONFIG_MAP[section]
        elif section.startswith("view."):
            options = CONFIG_MAP["view"]
            is_exist_view_section = True
        else:
            print(f"Unrecognized section: {section}")
            continue

        for option, value_option in options.items():
            if not config.has_option(section, option):
                print(f"Missing option: [{section}] {option}")
                return False

            value = config.get(section, option)
            if not _verifica_tipo_valore(value, value_option):
                print(
                    f"Wrong type for [{section}] {option}: expected '{value_option['type'].__name__}', found '{value}'"
                )
                return False


def _verifica_config(config):
    global CONFIG_MAP

    is_exist_view_section = False
    # Verifica che tutte le sezioni richieste esistano
    for required_section in CONFIG_MAP.keys():
        if not config.has_section(required_section) and required_section != "view":
            print(f"Missing section: {required_section}")
            return False

    for section in config.sections():
        if section in CONFIG_MAP:
            options = CONFIG_MAP[section]
        elif section.startswith("view."):
            options = CONFIG_MAP["view"]
            is_exist_view_section = True
        else:
            print(f"Unrecognized section: {section}")
            continue

        for option, value_option in options.items():
            if not config.has_option(section, option):
                print(f"Missing option: [{section}] {option}")
                return False

            value = config.get(section, option)
            if not _verifica_tipo_valore(value, value_option):
                print(
                    f"Wrong type for [{section}] {option}: expected '{value_option['type'].__name__}', found '{value}'"
                )
                return False

    if not is_exist_view_section:
        print("Missing section: view")
        return False

    return True
