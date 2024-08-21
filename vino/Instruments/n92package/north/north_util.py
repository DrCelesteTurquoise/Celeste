import logging
from datetime import date, datetime

shell_print_available = False
try:
    from thonny import get_shell
    shell_print_available = True
except Exception as e:
    pass


def clamp(value, floor, ceil):
    """

    :param float value: The value to be clamped.
    :param float floor: The minimal allowed value.
    :param float ceil: The maximal allowed value.
    :return: Value clamped to range [floor, ceil]
    """
    return min(max(value, floor), ceil)


def next_pow_2(num):
    """ If num isn't a power of 2, will return the next higher power of two """
    rval = 1
    while rval < num:
        rval <<= 1
    return rval


def parse_range_str(input):
    if input is None:
        return

    if input == 'None' or input == 'null':
        return

    range_list = []
    input = input.replace(' ', '')
    terms = input.split(',')
    for term in terms:
        try:
            range_list.append(int(term))
        except Exception:
            sub_terms = term.split('-')
            range_list += range(int(sub_terms[0]), int(sub_terms[1]) + 1)
    return set(range_list)


def make_file(fp):
    f = open(fp, 'w')
    f.close()


def shell_print(to_write):
    if not shell_print_available:
        return

    try:
        get_shell().print_error(str(to_write))
        # move to new shell line after error msg
        get_shell().submit_magic_command("")
    except AttributeError:  # in case get_shell() returns NoneType
        pass


def get_current_timestamp() -> str:
    return '{0}_{1}-{2}-{3}'.format(
        date.today(),
        datetime.now().hour,
        datetime.now().minute,
        datetime.now().second
    )


import cv2 as cv
import numpy as np
from PIL import Image
from PIL import ImageTk


class VideoUtils:
    FILTERS = {
        'None': {},
        'Edges': {},
        'Binarized': {},
        'Adapt.Thresh': {},
        'Lines': {
            # identifier: (Name, default)
            'threshold': ('Threshold', 15),
            'minLineLength': ('Min. Line Length', 10),
            'maxLineGap': ('Max. Line Gap', 20)
        },
        'Colors': {
            'numColors': ('Number of Colors', 5)
        },
        'Top Color': {},
        'Avg. Color': {}
    }

    @staticmethod
    def get_ms_frame_delay(target_fps):
        return int((1.0 / target_fps) * 1000)

    @staticmethod
    def list_vid_ports():
        # https://stackoverflow.com/questions/57577445/list-available-cameras-opencv-python
        ports = []
        index = 0
        while True:
            cam = cv.VideoCapture(index)
            if not cam.isOpened():  # break the loop on first non-cam port
                break
            else:
                ports.append(index)
            index += 1
        return ports

    @staticmethod
    def get_source_list():
        return ['None', 'Image'] + [f"Camera {i}" for i in VideoUtils.list_vid_ports()]

    @staticmethod
    def filter_names():
        return list(VideoUtils.FILTERS.keys())

    @staticmethod
    def filter_settings(filter_name) -> dict:
        return VideoUtils.FILTERS[filter_name]

    @staticmethod
    def filter_setting_default(filter_name, setting_name):
        return VideoUtils.FILTERS[filter_name][setting_name][1]

    @staticmethod
    def get_output_frame(flt: dict, src) -> np.ndarray:
        """
        :param dict flt:
        :param np.ndarray src:
        :return: Filtered image in numpy array format.
        """
        assert isinstance(flt, dict)
        assert isinstance(src, np.ndarray)
        filter_name = flt['filter']
        if filter_name == 'None':
            return src
        else:  # must apply some filter
            try:
                if filter_name == 'Edges':
                    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
                    edged = cv.Canny(gray, 50, 100)
                    return cv.cvtColor(edged, cv.COLOR_GRAY2RGB)
                elif filter_name == 'Binarized':
                    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
                    _, binned = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)
                    return cv.cvtColor(binned, cv.COLOR_GRAY2RGB)
                elif filter_name == 'Adapt.Thresh':
                    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
                    threshed = cv.adaptiveThreshold(gray, 255,
                                                    cv.ADAPTIVE_THRESH_MEAN_C,
                                                    cv.THRESH_BINARY, 11, 2)
                    return cv.cvtColor(threshed, cv.COLOR_GRAY2RGB)
                elif filter_name == 'Lines':
                    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
                    # blurred = cv.GaussianBlur(gray, ksize=(5, 5), sigmaX=0)
                    # _, binned = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)
                    edged = cv.Canny(gray, 50, 200)
                    lines = cv.HoughLinesP(edged, rho=1, theta=np.pi / 180,
                                           threshold=flt["threshold"],
                                           minLineLength=flt["minLineLength"],
                                           maxLineGap=flt["maxLineGap"])
                    if isinstance(lines, np.ndarray):
                        lined = np.copy(src)
                        for line in lines:
                            x1, y1, x2, y2 = line[0]
                            cv.line(lined, (x1, y1), (x2, y2), (0, 0, 255), 1)
                        return lined
                    else:  # lines will be None if none are detected (wish it were just empty array...)
                        return src
                elif filter_name == 'Colors':
                    # determine dominant colors
                    pix = np.float32(src.reshape(-1, 3))  # flatten 2D to 1D array (of triples)
                    n_colors = flt['numColors']
                    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 200, 0.1)
                    flags = cv.KMEANS_RANDOM_CENTERS
                    _, labels, palette = cv.kmeans(pix, n_colors, None, criteria, 10, flags)
                    _, counts = np.unique(labels, return_counts=True)
                    # construct representation of dominant colors
                    indices = np.argsort(counts)[::-1]
                    freqs = np.cumsum(np.hstack(
                        [[0], counts[indices] / float(counts.sum())]
                    ))
                    rows = np.int_(src.shape[0] * freqs)
                    dominant_img = np.zeros(shape=src.shape, dtype=np.uint8)
                    for i in range(len(rows) - 1):
                        dominant_img[rows[i]:rows[i + 1], :, :] += np.uint8(palette[indices[i]])
                    return dominant_img
                elif filter_name == 'Top Color':
                    pix = np.float32(src.reshape(-1, 3))  # flatten 2D to 1D array (of triples)
                    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 200, 0.1)
                    flags = cv.KMEANS_RANDOM_CENTERS
                    _, labels, palette = cv.kmeans(pix, 1, None, criteria, 10, flags)
                    _, counts = np.unique(labels, return_counts=True)
                    indices = np.argsort(counts)[::-1]
                    top_color = np.uint8(palette[indices[0]])
                    return np.tile(top_color, reps=(src.shape[0], src.shape[1], 1))  # returns a monochromatic image
                elif filter_name == 'Avg. Color':
                    avg = np.array(src.mean(axis=0).mean(axis=0), dtype=np.uint8)  # array looks like [B, G, R]
                    return np.tile(avg, reps=(src.shape[0], src.shape[1], 1))  # returns a monochromatic image
                else:
                    raise ValueError(f"Unrecognized filter: {filter_name}")
            except cv.error as e:
                logging.error(f'encountered openCV error:')
                logging.exception(e)

    @staticmethod
    def np_img_to_tk(src):
        """
        :param np.ndarray src: Source image (numpy array)
        :return: Converted Tkinter image
        """
        try:
            return ImageTk.PhotoImage(Image.fromarray(cv.cvtColor(src, cv.COLOR_BGR2RGB)))
        except cv.error:
            return None
