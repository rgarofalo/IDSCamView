import sys
import os

import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


from cam import IDSCam, ids_peak, ids_peak_ipl, Image, ImageTk


class TestIDSCam(unittest.TestCase):

    @patch("cam.ids_peak.Library")
    @patch("cam.ids_peak.DeviceManager")
    def setUp(self, MockDeviceManager, MockLibrary):
        self.mock_device_manager = MockDeviceManager.Instance.return_value
        self.mock_library = MockLibrary
        self.cam = IDSCam()

    def test_initialization(self):
        self.mock_library.Initialize.assert_called_once()
        self.assertIsNone(self.cam._IDSCam__device)
        self.assertIsNone(self.cam._IDSCam__nodemap_remote_device)
        self.assertIsNone(self.cam._IDSCam__datastream)
        self.assertFalse(self.cam._IDSCam__acquisition_running)

    def test_set_scale_factor_size_screen(self):
        self.cam._IDSCam__resolution = (1920, 1080)
        new_size = (1280, 720)
        self.cam.set_scale_factor_size_screen(new_size)
        expected_scale_factor = min(new_size[0] / 1920, new_size[1] / 1080)
        self.assertEqual(self.cam._IDSCam__scale_factor, expected_scale_factor)

    def test_set_scale_factor_size_screen_with_none_resolution(self):
        self.cam._IDSCam__resolution = None
        new_size = (1280, 720)
        with self.assertRaises(Exception) as context:
            self.cam.set_scale_factor_size_screen(new_size)
        self.assertEqual(
            str(context.exception),
            "Error, it is not possible to set the scaling factor because the cam is not started. Please start the cam with run() method",
        )


if __name__ == "__main__":
    unittest.main()
