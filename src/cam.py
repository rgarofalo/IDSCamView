# The `IDSCam` class is a Python class that initializes a peak library for device management and image
# acquisition, with methods for setting frame rate, callbacks, scale factor, capturing images,
# managing device connections, and controlling the camera's region of interest (ROI).
from ids_peak import ids_peak
from ids_peak_ipl import ids_peak_ipl
from ids_peak import ids_peak_ipl_extension
from PIL import Image, ImageTk
from utils import set_callback
from typing import Optional
import queue
import threading
import time

FPS_LIMIT = 10


class IDSCam:
    def __init__(self, frame_rate=FPS_LIMIT):
        """
        The function initializes a peak library and sets up variables for device management and image
        acquisition.

        :param frame_rate: The `frame_rate` parameter in the `__init__` method is used to specify the
        frame rate for the video capture. It is set to a default value `FPS_LIMIT` if no value is
        provided when initializing the object
        """

        # initialize peak library
        ids_peak.Library.Initialize()

        self.__device: Optional[ids_peak.Device] = None
        self.__device_manager: ids_peak.DeviceManager = (
            ids_peak.DeviceManager.Instance()
        )

        self.__device_connected = False
        self.__nodemap_remote_device: Optional[ids_peak.NodeMap] = None
        self.__datastream: Optional[ids_peak.DataStream] = None

        self.__frame_rate = frame_rate

        self.__resolution: tuple[int, int] = None
        self.__ids_scale_factor = ids_peak_ipl.ScaleFactor().New(1.0, 1.0)
        self.__scale_factor = 1.0

        self.__acquisition_timer = threading.Thread(target=self.on_acquisition_timer)
        self.__acquisition_running = False
        self.__capture_image = queue.Queue(30)

        self.__callback_message = None

        self.__restart_event = threading.Event()
        self.thread = threading.Thread(target=self.__restart_acquisition)
        self.thread.daemon = True  # Assicurati che il thread termini quando il programma principale termina
        self.thread.start()

    def __del__(self):
        self.__destroy_all()

    def set_frame_rate(self, frame_rate):
        """
        The function `set_frame_rate` sets the frame rate for a given object.

        :param frame_rate: The `frame_rate` parameter represents the number of frames displayed per
        second in a video or animation.
        """
        self.__frame_rate = frame_rate

    def set_callback_message(self, fun):
        """
        The `set_callback_message` function sets a callback function with optional arguments for a
        specified object.

        :param fun: The `fun` parameter is expected to be a function or method that you want to set
        as the callback function. This function will be called when you whant diplay message on gui

        """
        set_callback(self, "_IDSCam__callback_message", fun, None)

    def set_scale_factor_size_screen(self, newSize: tuple[int, int]):
        """
        The function `set_scale_factor_size_screen` calculates the scale factor based on the new size and
        updates the scale factor attribute.

        :param newSize: The `newSize` parameter is a tuple containing two integers representing the new
        size of the screen or display. The first integer in the tuple represents the width, and the
        second integer represents the height of the screen
        :type newSize: tuple[int, int]
        """

        if self.__resolution is None:
            raise Exception(
                "Error, it is not possible to set the scaling factor because the cam is not started. Please start the cam with run() method"
            )

        self.__scale_factor = min(
            newSize[0] / self.__resolution[0], newSize[1] / self.__resolution[1]
        )

        self.__ids_scale_factor = ids_peak_ipl.ScaleFactor().New(
            self.__scale_factor, self.__scale_factor
        )

    def set_scale_factor(self, scale_factor: float):
        """
        The function `set_scale_factor` sets a scale factor and creates a new scale factor object with
        the given value.

        :param scale_factor: The `scale_factor` parameter is a floating-point number that represents the
        scaling factor to be set for a particular object or component.
        """
        self.__scale_factor = scale_factor
        self.__ids_scale_factor = ids_peak_ipl.ScaleFactor().New(
            scale_factor, scale_factor
        )

    def get_scale_factor(self):
        return self.__scale_factor

    def get_capture_image(self):
        return self.__capture_image.get_nowait()

    def get_resolution(self):
        return self.__resolution

    def get_device_temperature(self):
        if self.__nodemap_remote_device is not None and self.__device_connected:
            return self.__nodemap_remote_device.FindNode("DeviceTemperature").Value()
        else:
            return "---"

    def __device_found(self, device: ids_peak.DeviceDescriptor):
        """
        The 'found' event is triggered if a new device is found upon calling
        `DeviceManager.Update()`
        """
        print(f"Found-Device-Callback: Key={device.Key()}")
        self.__device_connected = True

    @staticmethod
    def __device_lost(key: str):
        """
        The 'lost' event is only called for this application's opened devices if
        a device is closed explicitly or if connection is lost while the reconnect is disabled,
        otherwise the 'disconnected' event is triggered.
        Other devices that were not opened or were opened by someone else still trigger
        a 'lost' event.
        """
        print(f"Lost-Device-Callback: Key={key}")
        # self.__device_connected = False

    def __device_disconnected(self, device: ids_peak.DeviceDescriptor):
        """
        Only called if the reconnect is enabled and if the device was previously opened by this
        application instance.
        """
        # print(f"Disconnected-Callback: Key={device.Key()}")
        self.__callback_message("Error", "Cam Disconnected")
        self.__device_connected = False

    def __ensure_compatible_buffers_and_restart_acquisition(
        self, reconnect_information: ids_peak.DeviceReconnectInformation
    ):
        """
        After a reconnect the PayloadSize might have changed, e.g. due to
        a reboot and the last parameter state not being saved in the
        starting UserSet. Here we check the PayloadSize and
        reallocate the buffers if we encounter a mismatch.

        We also start the local and remote acquistion if necessary.
        """
        payload_size = self.__nodemap_remote_device.FindNode("PayloadSize").Value()

        has_payload_size_mismatch = (
            payload_size != self.__datastream.AnnouncedBuffers()[0].Size()
        )

        # The payload size might have changed. In this case it's required to reallocate the buffers.
        if has_payload_size_mismatch:
            print("PayloadSize has changed. Reallocating buffers...")

            is_data_stream_running = self.__datastream.IsGrabbing()
            if is_data_stream_running:
                self.__datastream.StopAcquisition()

            self.__revoke_buffers()

            # Allocate and queue the buffers using the new "PayloadSize".
            self.__alloc_buffers()

            if is_data_stream_running:
                self.__datastream.StartAcquisition()

        if not reconnect_information.IsRemoteDeviceAcquisitionRunning():
            self.__nodemap_remote_device.FindNode("AcquisitionStart").Execute()

    def __restart_acquisition(self):

        while True:
            print("Thread in attesa dell'evento...")
            self.__restart_event.wait()  # Il thread rimane in attesa che l'evento venga impostato
            print("Thread in start ")
            self.__device_connected = False
            self.__destroy_all()

            # initialize peak library
            ids_peak.Library.Initialize()

            self.__device_manager = ids_peak.DeviceManager.Instance()
            self.__acquisition_timer = threading.Thread(
                target=self.on_acquisition_timer
            )

            self.run()

            self.__restart_event.clear()  # Ripristina l'evento per la prossima attesa

    def __device_reconnected(
        self,
        device: ids_peak.Device,
        reconnect_information: ids_peak.DeviceReconnectInformation,
    ):
        """
        When a device that was opened by the same application instance regains connection
        after a previous disconnect the 'Reconnected' event is triggered.
        """
        print(
            (
                "Device-Reconnected-Callback:\n"
                f"Key={device.Key()}\n"
                f"ReconnectSuccessful: {reconnect_information.IsSuccessful()}\n"
                f"RemoteDeviceAcquisitionRunning: {reconnect_information.IsRemoteDeviceAcquisitionRunning()}\n"
                f"RemoteDeviceConfigurationRestored: {reconnect_information.IsRemoteDeviceConfigurationRestored()}"
            )
        )

        self.__callback_message("Info", "Cam Reconnected")
        self.__device_connected = True

        # Using the `reconnectInformation` the user can tell whether they need to take actions
        # in order to resume the image acquisition.
        if reconnect_information.IsSuccessful():
            # Device was reconnected successfully, nothing to do.

            return

        self.__ensure_compatible_buffers_and_restart_acquisition(reconnect_information)

    def __register_callbacks(self):
        """
        Register the Devicemanager callbacks.

        Note: We have to store the callbacks, otherwise the callbacks will be unregistered because their
        lifetime is shorter than the device manager instance.
        """
        # ids_peak provides several events that you can subscribe to in order
        # to be notified when the connection status of a device changes.
        self.device_found_callback = self.__device_manager.DeviceFoundCallback(
            self.__device_found
        )
        self.device_found_callback_handle = (
            self.__device_manager.RegisterDeviceFoundCallback(
                self.device_found_callback
            )
        )

        self.device_lost_callback = self.__device_manager.DeviceLostCallback(
            self.__device_lost
        )
        self.device_lost_callback_handle = (
            self.__device_manager.RegisterDeviceLostCallback(self.device_lost_callback)
        )

        self.device_reconnected_callback = (
            self.__device_manager.DeviceReconnectedCallback(self.__device_reconnected)
        )
        self.device_reconnected_callback_handle = (
            self.__device_manager.RegisterDeviceReconnectedCallback(
                self.device_reconnected_callback
            )
        )

        self.device_disconnected_callback = (
            self.__device_manager.DeviceDisconnectedCallback(self.__device_disconnected)
        )
        self.device_disconnected_callback_handle = (
            self.__device_manager.RegisterDeviceDisconnectedCallback(
                self.device_disconnected_callback
            )
        )

    def __unregister_callbacks(self):
        """
        Unregister the registered callbacks inside the Devicemanager
        """
        self.__device_manager.UnregisterDeviceFoundCallback(
            self.device_found_callback_handle
        )
        self.__device_manager.UnregisterDeviceLostCallback(
            self.device_lost_callback_handle
        )
        self.__device_manager.UnregisterDeviceReconnectedCallback(
            self.device_reconnected_callback_handle
        )
        self.__device_manager.UnregisterDeviceDisconnectedCallback(
            self.device_disconnected_callback_handle
        )

    def __open_device(self):
        try:

            # Return if no device was found
            if self.__device_manager.Devices().empty():
                self.__callback_message("Error", "No device found! Restart View")
                return False

            # Open the first openable device in the managers device list
            for device in self.__device_manager.Devices():
                if device.IsOpenable():
                    self.__device = device.OpenDevice(ids_peak.DeviceAccessType_Control)
                    break

            # Return if no device could be opened
            if self.__device is None:
                self.__callback_message("Error", "Device could not be opened!")
                return False

            self.__nodemap_remote_device = self.__device.RemoteDevice().NodeMaps()[0]

            device_infos = (
                device.ModelName()
                + " ("
                + device.ParentInterface().DisplayName()
                + "; "
                + device.ParentInterface().ParentSystem().DisplayName()
                + " v."
                + device.ParentInterface().ParentSystem().Version()
                + ") SerialNumber "
                + device.SerialNumber()
            )

            self.__callback_message("Info", "CAM Found: " + device_infos)

            try:
                self.__resolution = [
                    self.__nodemap_remote_device.FindNode("WidthMax").Value(),
                    self.__nodemap_remote_device.FindNode("HeightMax").Value(),
                ]

            except ids_peak.Exception as e:
                print("Max. resolution (w x h): (unknown)")
                print(e)
                pass

            # To prepare for untriggered continuous image acquisition, load the default user set if available and
            # wait until execution is finished
            try:
                self.__nodemap_remote_device.FindNode(
                    "UserSetSelector"
                ).SetCurrentEntry("Default")
                self.__nodemap_remote_device.FindNode("UserSetLoad").Execute()
                self.__nodemap_remote_device.FindNode("UserSetLoad").WaitUntilDone()
            except ids_peak.Exception:
                # Userset is not available
                pass

            return True
        except ids_peak.Exception as e:
            self.__callback_message("Critical", "Exception __open_device " + str(e))

        return False

    def __enable_reconnect(self):
        """
        We enable the reconnect by writing to the `ReconnectEnable` node
        in the `NodeMap` of the `System` that our device is connected to.
        """

        system_node_map = self.__device.ParentInterface().ParentSystem().NodeMaps()[0]

        if not system_node_map.HasNode("ReconnectEnable"):
            self.__callback_message("Error", "No ReconnectEnable Node found!")
            return False

        reconnect_enable_node = system_node_map.FindNode("ReconnectEnable")
        reconnect_enable_access_status = reconnect_enable_node.AccessStatus()

        if reconnect_enable_access_status == ids_peak.NodeAccessStatus_ReadWrite:
            reconnect_enable_node.SetValue(True)
            return

        if reconnect_enable_access_status == ids_peak.NodeAccessStatus_ReadOnly:
            if reconnect_enable_node.Value():
                return

        self.__callback_message("Error", "ReconnectEnable cannot be set to true!")

    def __prepare_acquisition(self):
        try:
            data_streams = self.__device.DataStreams()
            if data_streams.empty():
                self.__callback_message("Error", "Device has no DataStream!")
                self.__device = None
                return False

            try:
                self.__datastream = data_streams[0].OpenedDataStream()
                return True
            except ids_peak.BadAccessException:
                pass

            self.__datastream = data_streams[0].OpenDataStream()

            return True
        except Exception as e:
            self.__callback_message("Error", str(e))

        return False

    def __alloc_buffers(self):
        try:
            if self.__datastream:
                # Flush queue and prepare all buffers for revoking
                self.__datastream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)

                # Clear all old buffers
                for buffer in self.__datastream.AnnouncedBuffers():
                    self.__datastream.RevokeBuffer(buffer)

                # Get the payload size for correct buffer allocation
                payload_size = self.__nodemap_remote_device.FindNode(
                    "PayloadSize"
                ).Value()

                # Get number of minimum required buffers
                buffer_count_max = self.__datastream.NumBuffersAnnouncedMinRequired()

                # Allocate and announce image buffers and queue them
                for count in range(buffer_count_max):
                    buffer = self.__datastream.AllocAndAnnounceBuffer(payload_size)
                    self.__datastream.QueueBuffer(buffer)

                return True
        except Exception as e:
            self.__callback_message("Critical", str(e))

        return False

    def __revoke_buffers(self):
        # Remove buffers from any associated queue
        if self.__datastream is not None:
            self.__datastream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)

            for buffer in self.__datastream.AnnouncedBuffers():
                # Remove buffer from the transport layer
                self.__datastream.RevokeBuffer(buffer)

    def __destroy_all(self):
        """
        The function `__destroy_all` stops acquisition, unregisters callbacks, closes the device, and
        closes the peak library.
        """
        # Close device and peak library
        self.__close_device()
        ids_peak.Library.Close()

    def __close_device(self):
        """
        Stop acquisition if still running and close datastream and nodemap of the device
        """

        # Stop Acquisition in case it is still running
        self.__unregister_callbacks()
        self.__stop_acquisition()

    def __start_acquisition(self):
        """
        Start Acquisition on camera and start the acquisition timer to receive and display images

        :return: True/False if acquisition start was successful
        """
        # Check that a device is opened and that the acquisition is NOT running. If not, return.
        if self.__device is None:
            return False
        if self.__acquisition_running is True:
            return True

        # Get the maximum framerate possible, limit it to the configured FPS_LIMIT. If the limit can't be reached, set
        # acquisition interval to the maximum possible framerate
        try:
            max_fps = self.__nodemap_remote_device.FindNode(
                "AcquisitionFrameRate"
            ).Maximum()

            target_fps = min(max_fps, self.__frame_rate)
            self.__nodemap_remote_device.FindNode("AcquisitionFrameRate").SetValue(
                target_fps
            )
        except ids_peak.Exception:
            # AcquisitionFrameRate is not available. Unable to limit fps. Print warning and continue on.
            self.__callback_message(
                "warning",
                "Unable to limit fps, since the AcquisitionFrameRate Node is"
                " not supported by the connected camera. Program will continue without limit.",
            )

        # Setup acquisition timer accordingly
        # self.__acquisition_timer.set_interval((1 / target_fps) * 1000)
        # self.__acquisition_timer.set_execute(self.on_acquisition_timer)

        try:
            # Lock critical features to prevent them from changing during acquisition
            self.__nodemap_remote_device.FindNode("TLParamsLocked").SetValue(1)

            # Start acquisition on camera
            self.__datastream.StartAcquisition()
            self.__nodemap_remote_device.FindNode("AcquisitionStart").Execute()
            self.__nodemap_remote_device.FindNode("AcquisitionStart").WaitUntilDone()
        except Exception as e:
            print("Exception: " + str(e))
            return False

        # Start acquisition timer
        self.__acquisition_running = True
        self.__acquisition_timer.start()

        return True

    def __stop_acquisition(self):
        """
        Stop acquisition timer and stop acquisition on camera
        :return:
        """
        # Check that a device is opened and that the acquisition is running. If not, return.
        if self.__device is None or self.__acquisition_running is False:
            return

        self.__acquisition_running = False
        # self.__acquisition_timer.join()
        # Otherwise try to stop acquisition
        try:
            remote_nodemap = self.__device.RemoteDevice().NodeMaps()[0]
            remote_nodemap.FindNode("AcquisitionStop").Execute()

            # Stop and flush datastream
            self.__datastream.KillWait()
            self.__datastream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)

            self.__revoke_buffers()

            # Unlock parameters after acquisition stop
            if self.__nodemap_remote_device is not None:
                try:
                    self.__nodemap_remote_device.FindNode("TLParamsLocked").SetValue(0)
                except Exception as e:
                    self.__callback_message("Error", "Exception " + str(e))

        except Exception as e:
            self.__callback_message("Error", "Exception " + str(e))

    def on_acquisition_timer(self):
        """
        This function gets called on every timeout of the acquisition timer
        """

        # ids_peak_ipl.ImageConverter.
        conv = ids_peak_ipl.ImageConverter()
        conv.SetConversionMode(ids_peak_ipl.ConversionMode_Fast)
        while self.__acquisition_running:
            try:
                # Get buffer from device's datastream
                buffer = self.__datastream.WaitForFinishedBuffer(5000)

                # Create IDS peak IPL image for debayering and convert it to RGBa8 format
                ipl_image: ids_peak_ipl.Image = ids_peak_ipl_extension.BufferToImage(
                    buffer
                )
                converted_ipl_image = conv.Convert(
                    ipl_image, ids_peak_ipl.PixelFormatName_RGB8
                ).Scale(self.__ids_scale_factor)

              
                # # Get raw image data from converted image
                image_np_array = converted_ipl_image.get_numpy_3D()

                # Converti l'array numpy in un'immagine PIL
                image = Image.fromarray(image_np_array)

                imgtk = ImageTk.PhotoImage(image=image)

                self.__capture_image.put(imgtk)

                self.__datastream.QueueBuffer(buffer)
                # if count > 100:
                #     self.__restart_event.set()
                #     count = 0
                # else:
                #     count += 1
            except ids_peak.TimeoutException:
                if self.__device_connected:
                    self.__restart_event.set()
                print("Timeout Error")
            except ids_peak.Exception as e:
                print("Exception: " + str(e))
            except Exception as e:
                print("Generic Exception: " + str(e))

    def run(self):
        if self.__callback_message is None:
            return False

        self.__register_callbacks()
        self.__device_manager.Update()

        if self.__open_device():

            # Enable reconnect
            self.__enable_reconnect()

            try:
                if not self.__prepare_acquisition():
                    return False

                if not self.__alloc_buffers():
                    return False

                if not self.__start_acquisition():
                    self.__callback_message("Critical", "Unable to start acquisition!")
                else:
                    return True
            except Exception as e:
                self.__callback_message("Critical", "Exception Run Function:" + str(e))

        else:
            # self.__destroy_all()
            return False

        return True

   