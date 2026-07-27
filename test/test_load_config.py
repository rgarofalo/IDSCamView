import unittest
import tempfile
import os
from configparser import ConfigParser

import src.load_config as config_module


class TestConfigModule(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        os.remove(self.temp_file_path)

    def test_load_config_default(self):
        config = config_module.load_config_default()
        self.assertTrue(config_module._verifica_config(config))

    def test_load_ini(self):
        config = config_module.load_config_default()
        config_module.save_ini(config, self.temp_file_path)

        loaded_config = config_module.load_ini(self.temp_file_path)
        self.assertIsNotNone(loaded_config)
        self.assertTrue(config_module._verifica_config(loaded_config))

    def test_save_ini(self):
        config = config_module.load_config_default()
        config_module.save_ini(config, self.temp_file_path)

        loaded_config = ConfigParser()
        loaded_config.read(self.temp_file_path)
        self.assertTrue(config_module._verifica_config(loaded_config))

    def test_verifica_tipo_valore(self):
        self.assertTrue(
            config_module._verifica_tipo_valore(
                500, {"type": int, "min": 100, "max": 1000}
            )
        )
        self.assertFalse(
            config_module._verifica_tipo_valore(
                50, {"type": int, "min": 100, "max": 1000}
            )
        )
        self.assertFalse(
            config_module._verifica_tipo_valore(
                1500, {"type": int, "min": 100, "max": 1000}
            )
        )
        self.assertFalse(
            config_module._verifica_tipo_valore(
                "invalid", {"type": int, "min": 100, "max": 1000}
            )
        )

        self.assertTrue(
            config_module._verifica_tipo_valore(
                0.5, {"type": float, "min": 0.01, "max": 1.0}
            )
        )
        self.assertFalse(
            config_module._verifica_tipo_valore(
                0.001, {"type": float, "min": 0.01, "max": 1.0}
            )
        )
        self.assertFalse(
            config_module._verifica_tipo_valore(
                1.5, {"type": float, "min": 0.01, "max": 1.0}
            )
        )
        self.assertFalse(
            config_module._verifica_tipo_valore(
                "invalid", {"type": float, "min": 0.01, "max": 1.0}
            )
        )

        self.assertTrue(config_module._verifica_tipo_valore("test", {"type": str}))
        self.assertTrue(config_module._verifica_tipo_valore("", {"type": str}))

        self.assertFalse(config_module._verifica_tipo_valore(500, {"type": bool}))

    def test_verifica_config(self):
        config = config_module.load_config_default()
        self.assertTrue(config_module._verifica_config(config))

    # Test che sono destinati a fallire
    def test_failing_load_ini(self):
        # Configurazione con una sezione mancante
        invalid_config = """
        [PrintingView.ViewAreaCorners]
        width = 2000  # Out of range
        heigth = 500
        x = 500
        y = 200

        [PrintingView.CommandAreaCorners]
        width = 700
        heigth = 50
        x = 500
        y = 200

        [view.zoomTotale]
        scale = 1.5  # Out of range
        x_position = -71
        y_position = 8

        [view.zoomAgo]
        scale = 0.50
        x_position = 150  # Out of range
        y_position = 1202
        """
        with open(self.temp_file_path, "w") as f:
            f.write(invalid_config)

        loaded_config = config_module.load_ini(self.temp_file_path)
        self.assertIsNone(loaded_config)

    def test_not_found_load_ini(self):
        # Configurazione con una sezione mancante
        loaded_config = config_module.load_ini("not_found.cfg")
        self.assertIsNone(loaded_config)

    def test_failing_verifica_config(self):

        import io
        import sys

        # Cattura l'output dello standard output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Rimozione di un'opzione
        config = config_module.load_config_default()
        config.remove_section("PrintingView.ViewAreaCorners")
        self.assertFalse(config_module._verifica_config(config))
        self.assertIn(
            "Missing section: PrintingView.ViewAreaCorners", captured_output.getvalue()
        )
        captured_output = io.StringIO()
        sys.stdout = captured_output

        config = config_module.load_config_default()
        config.remove_section("view.Default")
        self.assertFalse(config_module._verifica_config(config))
        self.assertIn("Missing section: view", captured_output.getvalue())

        captured_output = io.StringIO()
        sys.stdout = captured_output

        config = config_module.load_config_default()
        config.set("view.Default", "scale", "3.0")
        self.assertFalse(config_module._verifica_config(config))
        self.assertIn(
            "Wrong type for [view.Default] scale: expected 'float', found '3.0'",
            captured_output.getvalue(),
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        config.set("view.Default", "scale", "1.0")
        config.set("PrintingView.ViewAreaCorners", "width", "abc")
        self.assertFalse(config_module._verifica_config(config))
        self.assertIn(
            "Wrong type for [PrintingView.ViewAreaCorners] width: expected 'int', found 'abc'",
            captured_output.getvalue(),
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output

        config.remove_option("PrintingView.ViewAreaCorners", "width")
        self.assertFalse(config_module._verifica_config(config))
        self.assertIn(
            "Missing option: [PrintingView.ViewAreaCorners] width",
            captured_output.getvalue(),
        )

        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    unittest.main()
