import cv2
import logging
from enum import Enum


class UVCControl:
    """
    This class provides methods to change UVC controls of the device
    """

    UVC_CONTROLS = {
        cv2.CAP_PROP_BRIGHTNESS: "Brightness",
        cv2.CAP_PROP_CONTRAST: "Contrast",
        cv2.CAP_PROP_SATURATION: "Saturation",
        cv2.CAP_PROP_HUE: "Hue",
        cv2.CAP_PROP_GAIN: "Gain",
        cv2.CAP_PROP_EXPOSURE: "Exposure",
        cv2.CAP_PROP_WHITE_BALANCE_BLUE_U: "White Balance",
        cv2.CAP_PROP_SHARPNESS: "Sharpness",
        cv2.CAP_PROP_GAMMA: "Gamma",
        cv2.CAP_PROP_ZOOM: "Zoom",
        cv2.CAP_PROP_FOCUS: "Focus",
        cv2.CAP_PROP_BACKLIGHT: "BackLight",
        cv2.CAP_PROP_PAN: "Pan",
        cv2.CAP_PROP_TILT: "Tilt",
    }
    minimum = -1
    maximum = -1
    stepping_delta = -1
    supported_mode = -1
    current_value = -1
    current_mode = -1
    default_value = -1

    names = ['minimum', 'maximum',
             'stepping_delta', 'supported_mode', 'current_value',
             'current_mode', 'default_value']
    modes = Enum('MODES', 'AUTO MANUAL AUTO_AND_MANUAL')

    def __init__(self, cap):
        """
        this init method is called when the object of the class is created.
        :param cv2.VideoCapture cap: object of VideoCapture class in opencv
        """
        self.cap = cap
        # self.display1 = display.Display()

    def describe(self, ctrl_id):
        assert ctrl_id in self.UVC_CONTROLS
        ret, minimum, maximum, stepping_delta, supported_mode, current_value, current_mode, default_value = \
            self.cap.get(ctrl_id, self.minimum, self.maximum, self.stepping_delta, self.supported_mode,
                         self.current_value, self.current_mode, self.default_value)
        if not ret:
            logging.error("Get control Values failed!!")
            return None
        else:
            return f"Camera {self.UVC_CONTROLS[ctrl_id]} Control Values:\n" \
                   f"\tMinimum Value: {minimum}\n" \
                   f"\tMaximum Value: {maximum}\n" \
                   f"\tDefault Value: {default_value}\n" \
                   f"\tStep Value: {stepping_delta}\n" \
                   f"\tCurrent Value: {current_value}\n" \
                   f"\tSupported Mode: {self.modes(supported_mode).name}\n" \
                   f"\tCurrent Mode: {self.modes(current_mode).name}\n"

    def get(self, ctrl_id, setting=None):
        """

        :param int ctrl_id: (such as cv2.CAP_PROP_BRIGHTNESS, etc.)
        :param str setting: If none, returns all settings.
        :return:
        """
        assert ctrl_id in self.UVC_CONTROLS
        control_name = self.UVC_CONTROLS[ctrl_id]
        ret, minimum, maximum, stepping_delta, supported_mode, current_value, current_mode, default_value = \
            self.cap.get(ctrl_id, self.minimum, self.maximum, self.stepping_delta, self.supported_mode,
                         self.current_value, self.current_mode, self.default_value)
        if not ret:
            raise KeyError(f'Get UVC control {ctrl_id} ({control_name}) settings failed.')
        elif isinstance(setting, str):
            assert setting in self.names
            return eval(setting)
        elif setting is None:
            return minimum, maximum, stepping_delta, supported_mode, current_value, current_mode, default_value
        else:
            raise TypeError(f'{setting} ({type(setting)}) is not a str or None; invalid.')

    def set(self, ctrl_id, value):
        assert ctrl_id in self.UVC_CONTROLS
        control_name = self.UVC_CONTROLS[ctrl_id]
        _, _, _, supported_mode, current_value, current_mode, default_value = self.get(ctrl_id)
        set_mode = current_mode if supported_mode != self.modes.AUTO_AND_MANUAL.value \
            else self.modes.MANUAL.value
        ret = self.cap.set(ctrl_id, value, set_mode)
        if not ret:
            raise ValueError(f'set(): Setting {control_name} value to {value} failed.')

    def auto(self, ctrl_id, auto=True):
        assert ctrl_id in self.UVC_CONTROLS
        control_name = self.UVC_CONTROLS[ctrl_id]
        _, _, _, supported_mode, current_value, current_mode, _ = self.get(ctrl_id)
        set_mode = self.modes.AUTO.value if auto else self.modes.MANUAL.value
        if set_mode != supported_mode and supported_mode != self.modes.AUTO_AND_MANUAL.value:
            set_mode = supported_mode
        ret = self.cap.set(ctrl_id, current_value, set_mode)
        if not ret:
            raise ValueError(f'auto(): Setting {control_name} mode to {set_mode} failed.')
