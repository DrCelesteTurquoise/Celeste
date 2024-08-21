from .north_UVC import UVCControl

import logging
import cv2
import mmap
import struct
import socket
import threading
from time import sleep

# https://github.com/off99555/python-mmap-ipc
# TODO check this https://numpy.org/doc/stable/reference/generated/numpy.memmap.html

# older socket server code https://github.com/mfrzr/north_ide/commit/ee414e24c5a8d8e300b564f9833aaf77400d21c8

"""
This should act as an independent server process.
Accepted requests should be register/unregister, shutdown, and maybe some 'alive?' request.
Registered feeds should be constantly polled and placed directly in memory-mapped files.
No image manipulation should occur in this class. Therefore, the mmaps must have a header,
which should include image width, height, and possibly # of channels.
Need some 'ping' test which simply indicates if the server is alive or not... since
we will want to check on north initialization whether the IDE has already created one.
"""


def send_cmd(cmd, data=None, verbose=False) -> (bytes, bytes):
    """
    :param bytes cmd:
    :param bytes data:
    :param bool verbose:
    :return: A response from the data broker.
    """
    assert len(cmd) == 4
    data = data if data else b''
    assembled_cmd = cmd + data
    assert NorthServer.BUF_LEN >= len(assembled_cmd) >= 4

    try:
        if verbose:
            msg = f'send_cmd(): Sending command {assembled_cmd}'
            print(msg)
            logging.info(msg)
        with socket.socket() as sock:
            # connect to NorthServer
            sock.connect(('localhost', 42435))
            sock.send(assembled_cmd)
            ret = sock.recv(NorthServer.BUF_LEN)
        retcode = ret[:4]
        retdata = ret[4:]
        if verbose:
            msg = f'send_cmd(): Received response {retcode}, {retdata}'
            print(msg)
            logging.info(msg)
        return retcode, retdata
    except ConnectionRefusedError:
        if verbose:
            logging.error(f'send_cmd(): NorthServer is not accepting connections.')
        return b'FAIL', b'CON_REFUSED'
    except ConnectionResetError:
        if verbose:
            logging.error(f'send_cmd(): Lost an existing connection to NorthServer.')
        return b'FAIL', b'CON_RESET'
    except Exception:
        if verbose:
            logging.exception(f'send_cmd(): Fatal exception.')
        return b'FAIL', b'DEFAULTEXCEPT'


def try_IDE_import():
    try:
        import northIDE
        return True
    except ModuleNotFoundError:
        return False


def launch_north_server(verbose=False):
    """

    :param verbose:
    :return: True if server is operating, false otherwise.
    """
    assert isinstance(verbose, bool)
    try:
        import socket
        import struct
        with socket.socket() as sock:
            sock.connect(('localhost', 42435))  # check data server exists?
            # sock.send(struct.pack('4si', b'TEST', 0))
        if verbose:
            logging.warning('launch_north_server(): '
                            'Tried to launch NorthServer and got respose from existing server; no server init.')
        return True
    except ConnectionRefusedError:  # data server does not exist; initialize it
        try:
            NorthServer(verbose=verbose)
            if verbose:
                logging.info('launch_north_server(): '
                             'Launched NorthServer.')
            return True
        except Exception:
            if verbose:
                logging.exception('launch_north_server(): '
                                  'Fatal error inializing NorthServer')
            return False
    except Exception:
        if verbose:
            logging.exception('launch_north_server(): '
                              'Fatal error checking NorthServer connection.')
        return False


def kill_north_server(verbose=False):
    assert isinstance(verbose, bool)
    retcode, retdata = send_cmd(b'KILL')
    if retcode == b'FAIL':
        if verbose:
            if retdata == b'CON_REFUSED':
                logging.error(f'kill_north_server():'
                              f'Could not kill NorthServer, doesn\'t exist (connection refused).')
            else:
                logging.error(f'kill_north_server():'
                              f'Unrecognized failure reason: {retdata}')
        return False
    return True


class NorthServer:
    BUF_LEN = 64
    """
    North Server
    """

    def __init__(self, host="localhost", port=42435, verbose=False):
        assert isinstance(host, str)
        assert isinstance(port, int)
        assert isinstance(verbose, bool)

        self._host = host
        self._port = port
        self._verbose = verbose
        self._server_thread = None
        self._terminate = False

        """
        ~~ Initialize Exchange Objects ~~
        
        if we have an IDE:
        - initialize DataBroker
        - initialize JoystickBroker
        no matter what:
        - initialize VideoProvider
        - begin serving
        """
        if try_IDE_import():
            self._has_IDE = True
            self._data_broker = DataBroker(verbose=verbose)
            self._js_broker = JoystickBroker(verbose=verbose)
            if self._verbose:
                msg = f'NorthServer: IDE may exist. Running all exchanges.'
                logging.info(msg); print(msg)  # TODO create some utility for this
        else:
            self._has_IDE = False
            if self._verbose:
                msg = f'NorthServer: No IDE exists. Running VideoProvider only.'
                logging.info(msg); print(msg)
        self._vid_provider = VideoProvider(verbose=verbose)
        # with exchange objects initialized we can begin serving
        self._start()

    def _start(self):
        assert self._server_thread is None
        if self._verbose:
            logging.info(f'NorthServer: Booting up.')
        self._server_thread = threading.Thread(target=self._serve, daemon=False)
        self._server_thread.start()
        self._vid_provider.start()

    def _serve(self):
        # initialize socket #
        try:
            self._sock = socket.socket()
            self._sock.bind(("", self._port))
            if self._verbose:
                logging.info(f'NorthServer: Bound socket to port {self._port}.')
            self._sock.listen(5)
            if self._verbose:
                logging.info('NorthServer: Listening for connections...')
        except Exception:
            if self._verbose:
                logging.exception('NorthServer: Failed to initialize socket.')
        assert not self._terminate
        # accept connections loop #
        while not self._terminate:
            conn, addr = self._sock.accept()
            if self._verbose:
                logging.info(f'NorthServer: Received connection from {addr}.')
            # server loop #
            retcode = b''
            retdata = b''
            try:
                # receive a command
                buffer = conn.recv(self.BUF_LEN)
                if buffer == b'':
                    continue
                # get cmd arguments from data
                cmd = buffer[:4].decode('ascii')
                data = buffer[4:]
                if self._verbose:
                    logging.info(f'NorthServer: Received cmd {cmd} with data {data}.')

                # perform some action based on command #
                if cmd == 'KILL':
                    self._vid_provider.stop()
                    retcode = b'OKAY'
                    retdata = b''
                    self._terminate = True

                # simple ping
                elif cmd == 'TEST':
                    retcode = b'OKAY'
                    retdata = b''

                # video provider commands #
                elif cmd.startswith('V'):
                    retcode, retdata = self._vid_provider.handle_cmd(cmd, data)

                # data table commands
                elif cmd.startswith('D'):
                    if self._has_IDE:
                        retcode, retdata = self._data_broker.handle_cmd(cmd, data)
                    elif self._verbose:  # We have no attached IDE and cannot handle Data command
                        logging.warning(f'NorthServer: Received data command when no IDE exists.')

                # joystick commands
                elif cmd.startswith('J'):
                    if self._has_IDE:
                        retcode, retdata = self._js_broker.handle_cmd(cmd, data)
                    elif self._verbose:
                        logging.warning(f'NorthServer: Received joystick command when no IDE exists.')
                else:
                    if self._verbose:
                        logging.error(f'NorthServer: Unrecognized command type {cmd[0]} (in {cmd}).')
                    retcode = b'FAIL'
                    retdata = b'BADCMD'
            except Exception:
                if self._verbose:
                    logging.exception(f'NorthServer: While receiving command:')
                retcode = b'FAIL'
                retdata = b'SRVERR'
            try:
                # send a reply
                assert isinstance(retcode, bytes)
                assert isinstance(retdata, bytes)
                conn.send(retcode + retdata)
            except Exception:
                if self._verbose:
                    logging.exception(f'NorthServer: While sending response:')
            # end of server loop #
            conn.close()
            if self._verbose:
                logging.info(f'NorthServer: Disconnected from {addr}.')
            # end of subscription cleanup #
        # end of connections loop #
        del self._sock
        if self._verbose:
            logging.warning(f'NorthServer: Main loop terminated. Server shut down.')


class DataBroker:
    def __init__(self, verbose=False):
        assert isinstance(verbose, bool)
        self._verbose = verbose

    def handle_cmd(self, cmd, data=None):
        filename = data.decode('ascii')
        if cmd == 'DOPE':
            return self._open_file(filename)
        elif cmd == 'DREF':
            return DataBroker._refresh(filename)
        else:
            if self._verbose:
                logging.error(f'DataBroker: Unrecognized command {cmd}.')
            return b'FAIL', b'BADCMD'

    def _open_file(self, filename):
        from northIDE import MVC
        filepath = MVC.project().current_proj.path.joinpath(filename)
        if not MVC.data().open(filepath):
            if self._verbose:
                logging.error(f'DataBroker: Could not open {filepath}.')
            return b'FAIL', b'BADPATH'
        else:
            MVC.refresh_file_view()  # might be a new file
            return b'OKAY', b''

    @staticmethod
    def _refresh(filename):
        from northIDE import MVC
        MVC.data().refresh(filename)
        return b'OKAY', b''


class JoystickBroker:
    def __init__(self, verbose=False):
        assert isinstance(verbose, bool)
        self._verbose = verbose

    def handle_cmd(self, cmd, data=None):
        if cmd == 'JBEG':
            return JoystickBroker._begin()
        elif cmd == 'JMOV':
            assert isinstance(data, bytes)
            from northIDE.simulator import Simulator
            js_pos = struct.unpack(f'{len(Simulator.ROBOT_AXES)}i', data)
            return JoystickBroker._move(js_pos)
        elif cmd == 'JEND':
            return JoystickBroker._end()
        else:
            if self._verbose:
                logging.error(f'JoystickBroker: Unrecognized command {cmd}.')
            return b'FAIL', b'BADCMD'

    @staticmethod
    def _begin():
        from northIDE import MVC
        MVC.sim().js_begin()
        return b'OKAY', b''

    @staticmethod
    def _move(data):
        from northIDE import MVC
        MVC.sim().js_move(data)
        return b'OKAY', b''

    @staticmethod
    def _end():
        from northIDE import MVC
        MVC.sim().js_end()
        return b'OKAY', b''


class VideoProvider:
    """
    Video Provider
    """
    VIDEO_LOOP_DELAY = 0.01

    # CAMERA_START_DELAY = 1.5

    def __init__(self, verbose=False):
        assert isinstance(verbose, bool)

        self._verbose = verbose
        self._cam_thread = None

        self._lock = threading.Lock()
        self._terminate = False
        self._registrations = {}  # [cam_id]: int
        self._cameras = {}  # [cam_id] : VideoCapture
        self._uvc = {}  # [cam_id]: UVCControl
        self._mmaps = {}

    ##################
    # Public methods #
    def start(self):
        assert self._cam_thread is None
        if self._verbose:
            logging.info(f'VideoProvider: Booting up.')
        self._terminate = False
        self._cam_thread = threading.Thread(target=self._poll_cams)
        self._cam_thread.start()
        assert isinstance(self._cam_thread, threading.Thread)

    def stop(self):
        assert isinstance(self._cam_thread, threading.Thread)
        if self._verbose:
            logging.info(f'VideoProvider: Shutting down.')
        self._terminate = True
        self._cam_thread.join()
        self._cam_thread = None

    def handle_cmd(self, cmd, data):
        """
        :param str cmd:
        :param bytes data:
        :return: bytes return code
        """
        assert isinstance(data, bytes)
        assert len(data) >= 4
        if cmd == 'VREG':
            cam_id, = struct.unpack('i', data)
            assert isinstance(cam_id, int)
            return self.register(cam_id)
        elif cmd == 'VUNR':
            cam_id, = struct.unpack('i', data)
            assert isinstance(cam_id, int)
            retcode, retdata = self.unregister(cam_id)
            return retcode, retdata
        elif cmd == 'VGET':  # get camera settings
            cam_id, ctrl_id = struct.unpack('ii', data)
            return self.get_camcfg(cam_id, ctrl_id)
        elif cmd == 'VSET':  # configure camera settings
            cam_id, ctrl_id, cfg_val = struct.unpack('iii', data)
            return self.set_camcfg(cam_id, ctrl_id, cfg_val)
        elif cmd == 'VAUT':  # configure camera auto-setting
            cam_id, ctrl_id, cfg_auto = struct.unpack('ii?', data)
            return self.set_camauto(cam_id, ctrl_id, cfg_auto)
        else:
            if self._verbose:
                logging.error(f'VideoProvider: Unrecognized command {cmd}.')
            return b'FAIL', b'BADCMD'

    def register(self, cam_id):
        """
        :param int cam_id:
        """
        self._lock.acquire()
        if cam_id not in self._registrations:
            assert cam_id not in self._cameras
            assert cam_id not in self._uvc
            self._cameras[cam_id] = cv2.VideoCapture(cam_id)
            self._uvc[cam_id] = UVCControl(cap=self._cameras[cam_id])
            self._registrations[cam_id] = 0
        assert cam_id in self._cameras
        assert cam_id in self._uvc
        assert cam_id in self._registrations
        # successful registration is contingent on being able to refresh_src without failure #
        try:
            self._refresh_src(cam_id)
            self._registrations[cam_id] += 1
            retcode = b'DATA'
            retdata = struct.pack('i', self._registrations[cam_id])
        except OSError:
            assert isinstance(self._registrations[cam_id], int)
            if self._verbose:
                logging.error(f'VideoProvider: No camera read while registering cam {cam_id}.')
                logging.info(f'VideoProvider: Camera {cam_id} has {self._registrations[cam_id]} registrations.')
            retcode = b'FAIL'
            retdata = b'NOREAD'
        except Exception:
            if self._verbose:
                logging.exception(f'VideoProvider: Base exception while registering camera {cam_id}.')
            retcode = b'FAIL'
            retdata = b'DEFAULT'
        self._lock.release()
        return retcode, retdata

    def unregister(self, cam_id):
        """
        :param int cam_id:
        """
        self._lock.acquire()
        if cam_id not in self._registrations:
            if self._verbose:
                logging.error("VideoProvider: Tried to unregister pane from unopened source")
            retcode = b'FAIL'
            retdata = b'NOTREG'
        else:
            self._registrations[cam_id] -= 1
            # check whether we should delete this source entirely
            retcode = b'DATA'
            retdata = struct.pack('i', max(self._registrations[cam_id], 0))
            if self._registrations[cam_id] <= 0:
                self._remove_cam(cam_id)
        self._lock.release()
        return retcode, retdata

    def get_camcfg(self, cam_id, ctrl_id) -> (bytes, bytes):
        try:
            uvc = self._uvc[cam_id]
        except KeyError:
            return b'FAIL', b'BADSRC'
        try:
            return b'DATA', struct.pack(f'{len(UVCControl.names)}i', *uvc.get(ctrl_id))
        except KeyError:
            return b'FAIL', b'BADCTRL'
        except Exception:
            if self._verbose:
                logging.exception('VideoProvider: While getting camera config.')
            return b'FAIL', b'DEFAULT'

    def set_camcfg(self, cam_id, ctrl_id, value):
        try:
            uvc = self._uvc[cam_id]
        except KeyError:
            return b'FAIL', b'BADSRC'
        try:
            uvc.set(ctrl_id, value)
            return b'OKAY', b''
        except KeyError:
            return b'FAIL', b'BADCTRL'
        except Exception:
            if self._verbose:
                logging.exception(f'VideoProvider: While setting camera config.')
            return b'FAIL', b'DEFAULT'

    def set_camauto(self, cam_id, ctrl_id, auto):
        try:
            uvc = self._uvc[cam_id]
        except KeyError:
            return b'FAIL', b'BADSRC'
        try:
            uvc.auto(ctrl_id, auto)
            return b'DATA', struct.pack(f'{len(UVCControl.names)}i', *uvc.get(ctrl_id))
        except KeyError:
            return b'FAIL', b'BADCTRL'
        except Exception:
            if self._verbose:
                logging.exception(f'VideoProvider: While setting camera AUTO.')
            return b'FAIL', b'DEFAULT'

    ###################
    # Private methods #
    def _poll_cams(self):
        while not self._terminate:
            self._lock.acquire()
            for cam_id in self._cameras.keys():
                try:
                    self._refresh_src(cam_id)
                except OSError:
                    if self._verbose:
                        logging.warning(f'VideoProvider: Read error on camera {cam_id}')
                        logging.info(f'VideoProvider: Camera {cam_id} has {self._registrations}')
                except Exception:
                    if self._verbose:
                        logging.exception(f'VideoProvider: Unrecognized exception in polling loop for camera {cam_id}.')
            self._lock.release()
            sleep(self.VIDEO_LOOP_DELAY)
        if self._verbose:
            logging.info(f'VideoProvider: Terminated polling loop.')

    def _refresh_src(self, cam_id):
        """
        :param int cam_id:
        """
        ret, img = self._cameras[cam_id].read()
        if not ret:
            raise OSError(f'No camera return value in VideoProvider._refresh_src(cam_id={cam_id}).')

        head = struct.pack('ii', img.shape[1], img.shape[0])
        if cam_id not in self._mmaps:
            channels = 3
            mmap_size = len(head) + (img.size * channels)
            mmap_name = f'CAMERAFEED-{cam_id}'
            self._mmaps[cam_id] = mmap.mmap(-1, mmap_size, mmap_name)
            if self._verbose:
                logging.info(f'VideoProvider: Initialized mmap "{mmap_name}".')
        assert cam_id in self._mmaps
        self._mmaps[cam_id].seek(0)
        self._mmaps[cam_id].write(head)
        self._mmaps[cam_id].write(img.tobytes())
        self._mmaps[cam_id].flush()

    def _remove_cam(self, cam_id):
        """
        :param int cam_id:
        """
        assert cam_id in self._cameras
        assert cam_id in self._uvc
        assert cam_id in self._registrations
        self._cameras[cam_id].release()
        del self._cameras[cam_id]
        del self._uvc[cam_id]

        if cam_id in self._mmaps:
            self._mmaps[cam_id].close()
            del self._mmaps[cam_id]

        if self._verbose and self._registrations[cam_id] > 0:
            logging.warning(f'VideoProvider: Removing a still-registered source ({cam_id})!')
        del self._registrations[cam_id]
        assert cam_id not in self._cameras
        assert cam_id not in self._uvc
        assert cam_id not in self._mmaps
        assert cam_id not in self._registrations
        if self._verbose:
            logging.info(f'VideoProvider: Removed a source ({cam_id}).')
