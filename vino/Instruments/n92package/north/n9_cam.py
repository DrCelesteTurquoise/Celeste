from north.north_project import Project
from north.n9_server import send_cmd
from north.north_util import VideoUtils, get_current_timestamp
from north.north_UVC import UVCControl

import logging
import struct
import mmap
import os
import numpy as np
import cv2

from typing import Callable
from PIL import Image, ImageTk
from pathlib import Path
from time import sleep


class NorthCamera:
    def __init__(self, source=None, pane=None):
        """
        :param int source:
        :param int pane:
        """
        if not isinstance(source, int) and not isinstance(pane, int):
            raise ValueError("Must specify either a source or pane (int) to initialize a camera.")

        # TODO get project path when not in IDE
        self._proj_path = Path(os.getcwd())
        self._settings = None

        cfg = None
        if isinstance(pane, int):
            proj = Project(self._proj_path)
            source = proj.get_visionpane(pane)['src']
            cfg = proj.get_visionpane(pane)['cfg']
        self._source_id = source
        self._config_id = cfg
        self._pane_id = pane

        # register the camera feed with video provider
        from north.n9_server import launch_north_server
        launch_north_server()  # creates data broker iff it doesn't exist
        register_cam(self._source_id)

    def __del__(self):
        # unregister the camera feed
        unregister_cam(self._source_id)

    def capture(self):
        """
        :return: The captured image (numpy.ndarray).
        """
        try:
            headsize = struct.calcsize('ii')
            imgsize = 0
            shape = (0, 0, 3)
            # while camera is booting up the image size will be zero
            while imgsize == 0:
                head = mmap.mmap(-1, headsize, f"CAMERAFEED-{self._source_id}")
                head.seek(0)
                w, h = struct.unpack('ii', head.read(headsize))
                head.close()
                shape = (h, w, 3)
                imgsize = np.prod(shape)
                if imgsize == 0:  # don't poll too often..
                    sleep(0.01)
            # we have ensured camera is up, now..
            # get the current image from mmap
            mm = mmap.mmap(-1, headsize + imgsize, f"CAMERAFEED-{self._source_id}")
            mm.seek(headsize)
            buf = mm.read(imgsize)
            src_frame = np.frombuffer(buf, dtype=np.uint8).reshape(shape)
            mm.close()
            
            try:  # apply any crop if necessary
                if self._config_id is not None:
                    settings = Project(self._proj_path).get_visioncfg(self._config_id)['settings']
                    if settings is not None and settings['crop']['enabled']:
                        crop_set = settings['crop']
                        # numpy arrays are height-first and width-second
                        cropped = src_frame[
                                  crop_set['start_y']:crop_set['end_y'],
                                  crop_set['start_x']:crop_set['end_x']
                                  ]
                        if cropped.shape[0] < 1 or cropped.shape[1] < 1:  # empty crop
                            logging.warning("Cropping settings resulted in empty crop. Capturing full image.")
                            return src_frame
                        else:
                            return cropped
                # if no config or no crop, just return now
                return src_frame
            except FileNotFoundError:  # no project exists
                return src_frame
        except Exception as e:
            logging.error("Error in NorthCamera.capture():")
            logging.exception(e)

    def filter(self, image=None, func=None, pane=None):
        """
        :param np.ndarray image:
        :param Callable func:
        :param int pane:
        :return: The filtered image.
        """
        if not isinstance(image, np.ndarray):
            image = self.capture()
        if isinstance(func, Callable):
            output = func(image)
            if isinstance(output, np.ndarray):
                return output
            else:
                logging.error(f'filter(): Supplied function must return numpy ndarray')
                logging.error('filter(): Returning unprocessed image...')
                return image
        else:
            if not isinstance(pane, int):
                if self._pane_id is not None:
                    pane = self._pane_id
                else:
                    logging.error(f'filter(): Cannot filter without supplied func, cfg_id parameter, or a preset pane.')
                    logging.error('filter(): Returning unprocessed image...')
                    return image
            proj = Project(self._proj_path)
            cfg = proj.get_visioncfg(pane)
            settings = cfg['settings']
            settings['filter'] = cfg['filter']  # TODO this is a hack
            try:
                return VideoUtils.get_output_frame(settings, image)
            except Exception as e:
                logging.error('filter(): Encountered exception during filtering:')
                logging.exception(e)
                logging.error('filter(): Returning unprocessed image...')
                return image

    def save(self, image, filename=None):
        """
        :param np.ndarray image: Image to save.
        :param filename:
        :return: Filepath of the saved image.
        """
        if not filename:
            filename = f'capture_{get_current_timestamp()}'
        return save_capture(image, filename, proj_path=self._proj_path)

    def display(self):
        show_image(self.capture())


# functions
def register_cam(cam_id, verbose=False):
    """
    :param int cam_id:
    :param bool verbose:

    Registers a camera feed for mmap updates.
    """
    assert isinstance(cam_id, int)
    assert isinstance(verbose, bool)
    if verbose:
        msg = f'register_cam(): Registering camera feed {cam_id}...'; print(msg); logging.info(msg)
    retcode, retdata = send_cmd(b'VREG', data=struct.pack('i', cam_id))
    if retcode == b'DATA':
        registrations, = struct.unpack('i', retdata)
        return True, registrations
    else:
        if verbose:
            logging.error(f'register_cam(): Registering camera feed {cam_id} failed ({retcode}): {retdata}.')
        return False, None


def unregister_cam(cam_id, verbose=False) -> bool:
    """
    :param int cam_id:
    :param bool verbose:

    Unregisters a camera feed from mmap updates.
    """
    assert isinstance(cam_id, int)
    assert isinstance(verbose, bool)
    if verbose:
        msg = f'unregister_cam(): Unregistering camera feed {cam_id}...'; print(msg); logging.info(msg)
    retcode, retdata = send_cmd(b'VUNR', data=struct.pack('i', cam_id), verbose=verbose)
    if retcode == b'DATA':
        registrations, = struct.unpack('i', retdata)
        return True, registrations
    else:
        if verbose:
            logging.error(f'unregister_cam(): Unregistering camera feed {cam_id} failed: {retcode}, {retdata}.')
        return False, None


def get_cam_control(cam_id, ctrl_id) -> tuple:
    """

    :param int cam_id:
    :param int ctrl_id:
    """
    assert isinstance(cam_id, int)
    assert isinstance(ctrl_id, int)
    ctrl_name = UVCControl.UVC_CONTROLS[ctrl_id]
    retcode, retdata = send_cmd(b'VGET', data=struct.pack('ii', cam_id, ctrl_id))
    if retcode != b'DATA':
        if retdata == b'BADCTRL':
            logging.warning(f'get_cam_control():'
                            f'Failed because ({ctrl_id}){ctrl_name} is not a valid control for cam {cam_id}')
        else:
            logging.error(f'get_cam_control(): '
                          f'Get cam {cam_id} ({ctrl_id}){ctrl_name} controls failed: {retcode}, {retdata}.')
        return None
    return struct.unpack(f'{len(UVCControl.names)}i', retdata)


def set_cam_control(cam_id, ctrl_id, value):
    """

    :param int cam_id:
    :param int ctrl_id:
    :param int value:
    """
    assert isinstance(cam_id, int)
    assert isinstance(ctrl_id, int)
    assert isinstance(value, int)
    retcode, retdata = send_cmd(b'VSET', data=struct.pack('iii', cam_id, ctrl_id, value))
    if retcode != b'OKAY':
        logging.warning(f'set_cam_control(): '
                      f'Setting camera {cam_id} controls failed: {retcode}, {retdata}.')
        return False
    return True


def set_cam_auto(cam_id, ctrl_id, auto=True):
    """

    :param int cam_id:
    :param int ctrl_id:
    :param bool auto:
    """
    assert isinstance(cam_id, int)
    assert isinstance(ctrl_id, int)
    assert isinstance(auto, bool)
    retcode, retdata = send_cmd(b'VAUT', data=struct.pack('ii?', cam_id, ctrl_id, auto))
    if retcode != b'DATA':
        logging.error(f'set_cam_auto(): '
                      f'Setting camera {cam_id} auto failed: {retcode}, {retdata}.')
        return None
    return struct.unpack(f'{len(UVCControl.names)}i', retdata)


def get_captures_path(proj_path=None) -> Path:
    """
    :param Path proj_path: If None, will assume the script is being called in project directory.
    :return: The path where captures are saved.
    """
    if proj_path is None:
        # TODO: default to user_data/captures on None proj_path, in case no project open...
        raise NotImplementedError()
    return proj_path.joinpath('captures')


def show_image(image):
    """
    :param np.ndarray image:
    """
    from matplotlib import pyplot as plt
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.show()


def save_capture(image, filename,
                 proj_path=None,
                 no_duplicates=True,
                 extension='png') -> Path:
    """
    :param image:
    :param str filename:
    :param Path proj_path:
    :param bool no_duplicates:
    :param str extension:
    :return: Filepath of the saved capture, or None if not successfully saved
    """
    assert type(image) in [np.ndarray, ImageTk.PhotoImage]
    # ensure captures directory exists
    if not Path.exists(get_captures_path(proj_path)):
        Path.mkdir(get_captures_path(proj_path))

    filepath = get_captures_path(proj_path).joinpath(f'{filename}.{extension}')

    if no_duplicates:
        i = 2
        while Path.exists(filepath):
            filepath = get_captures_path(proj_path).joinpath(f'{filename}_{i}.{extension}')
            i += 1
    else:
        raise NotImplementedError("TODO: save_capture when no_duplicates == False")

    # save the capture
    if isinstance(image, np.ndarray):
        # cv images are BGR, PIL images are RGB
        img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        assert isinstance(image, ImageTk.PhotoImage)
        img_pil = ImageTk.getimage(image)
    img_pil.save(filepath, format=extension)

    print(f'Saved capture: {filepath}')
    logging.info(f'Saved capture: {filepath}')
    return filepath
