import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import unittest
from unittest.mock import MagicMock, patch, call


import ids_camview as main_module
import load_config as config_module


class TestIDSCamViewFunctions(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

        self.textConfig = """
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


        [view.testView]
        scale = 0.15
        x_position = 0
        y_position = 0

        """
        with open(self.temp_file_path, "w") as f:
            f.write(self.textConfig)

        self.loaded_config = config_module.load_ini(self.temp_file_path)

    def tearDown(self):
        os.remove(self.temp_file_path)

    @patch("ids_camview.save_ini")
    @patch("ids_camview.MainGui")
    @patch("ids_camview.IDSCam")
    def test_save_config_file(
        self,
        MockIDSCam,
        MockMainGui,
        mock_save_ini,
    ):
        # Setup mock objects
        mock_config = MagicMock(wraps=self.loaded_config)
        mock_cam = MockIDSCam()
        mock_mainWindows = MockMainGui()

        # Set return values for mock methods
        mock_cam.get_scale_factor.return_value = 1.0
        mock_mainWindows.get_scroll_position.return_value = (10, 20)

        # Inject mock objects into the global namespace
        main_module.cam = mock_cam
        main_module.mainWindows = mock_mainWindows
        main_module.config = mock_config
        main_module.config_path = self.temp_file_path
        main_module.typeView = "view.testView"

        # Call the function
        main_module.save_config_file()

        # Verifica delle chiamate
        print(f"Calls to save_ini: {mock_save_ini.call_args_list}")
        print(f"Exception messages: {mock_mainWindows.set_new_message.call_args_list}")
        # Verify that config.set was called with the correct arguments
        mock_config.set.assert_has_calls(
            [
                call("view.testView", "scale", "1.0"),
                call("view.testView", "x_position", "10"),
                call("view.testView", "y_position", "20"),
            ]
        )

        # Verify that save_ini was called with the correct arguments
        mock_save_ini.assert_called_once_with(mock_config, self.temp_file_path)
        # Verify that set_new_message was called with the correct arguments
        mock_mainWindows.set_new_message.assert_called_once_with(
            "Info", "Saving completed"
        )

    @patch("ids_camview.MainGui")
    @patch("ids_camview.IDSCam")
    @patch("ids_camview.save_ini")
    def test_save_config_file_failure(self, mock_save_ini, MockIDSCam, MockMainGui):
        # Setup mock objects
        mock_config = MagicMock()
        mock_cam = MockIDSCam()
        mock_mainWindows = MockMainGui()

        # Set return values for mock methods
        mock_cam.get_scale_factor.return_value = 1.0
        mock_mainWindows.get_scroll_position.return_value = 10

        # Inject mock objects into the global namespace
        main_module.cam = mock_cam
        main_module.mainWindows = mock_mainWindows
        main_module.config = mock_config
        main_module.config_path = "config.cfg"
        main_module.typeView = "view.testView"

        main_module.save_config_file()

        mock_mainWindows.set_new_message.assert_called_once_with("Error", "Save failed")

    @patch("ids_camview.mainWindows")
    @patch("ids_camview.cam")
    def test_zoom_in_out(self, MockIDSCam, MockMainGui):
        # Setup mock objects
        mock_cam = MockIDSCam()
        mock_mainWindows = MockMainGui()

        # Inject mock objects into the global namespace
        main_module.cam = mock_cam
        main_module.mainWindows = mock_mainWindows

        # Set the return value for get_scale_factor
        mock_cam.get_scale_factor.return_value = 0.10
        main_module.zoom_in_out("in")
        mock_cam.set_scale_factor.assert_called_once_with(0.15)

        # Test for the zoom_in_out function with zoom in at the upper limit
        mock_cam.set_scale_factor.reset_mock()
        mock_mainWindows.update_label_zoom.reset_mock()
        mock_cam.get_scale_factor.return_value = 2.5
        main_module.zoom_in_out("in")
        mock_cam.set_scale_factor.assert_not_called()
        mock_mainWindows.update_label_zoom.assert_not_called()

        # Call the function to zoom out
        mock_cam.set_scale_factor.reset_mock()
        mock_mainWindows.update_label_zoom.reset_mock()
        mock_cam.get_scale_factor.return_value = 0.10
        main_module.zoom_in_out("out")
        mock_cam.set_scale_factor.assert_called_once_with(0.07)

        # Test for zoom_in_out function with zoom out at lower limit
        mock_cam.set_scale_factor.reset_mock()
        mock_mainWindows.update_label_zoom.reset_mock()

        mock_cam.get_scale_factor.return_value = 0.01
        main_module.zoom_in_out("out")
        mock_cam.set_scale_factor.assert_not_called()
        mock_mainWindows.update_label_zoom.assert_not_called()

    @patch("ids_camview.MainGui")
    @patch("ids_camview.IDSCam")
    @patch("ids_camview.load_ini")
    def test_setMainWindows(self, mock_load_ini, MockIDSCam, MockMainGui):
        # Setup mock objects
        mock_config = MagicMock()
        mock_mainWindows = MockMainGui()

        # Inject mock objects into the global namespace
        main_module.config = mock_config
        main_module.mainWindows = mock_mainWindows

        # Call the function
        main_module.setMainWindows(800, 600)

        # Verify that set_windows was called with the correct arguments
        mock_mainWindows.set_windows.assert_called_once_with(
            800,
            600,
            mock_config["PrintingView.ViewAreaCorners"].getint("x"),
            mock_config["PrintingView.ViewAreaCorners"].getint("y"),
        )
        # Verify that run was called
        mock_mainWindows.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
