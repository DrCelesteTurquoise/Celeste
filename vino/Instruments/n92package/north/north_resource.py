import logging
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional
import glm
from dataclasses import dataclass


class Mate:
    MATE_TYPE = "mate_type"
    OFFSET = "offset"
    INV_ATTACH_LOGIC = "invert_attach_logic"
    TRIGGER_CHANNEL_IDX = "trigger_channel_idx"  # should be called "trigger_axis_num"

    MATE_TYPE_DIGITAL_OUTPUT = "digital_output"  # attach/detach based on a toggling a digital output
    MATE_TYPE_PIPETTE = "pipette"  # attach based on z-axis moving up/down on a keyframe
    MATE_TYPE_RM_PIPETTE = "rm_pipette"  # detach pipette based on z-axis moving up/down on a keyframe
    MATE_TYPE_TOOL_PROXY = "tool_proxy"  # on tool rack module that attaches and detaches mvs to the tool tform

    def __init__(self, mate_type: str, offset: glm.vec3, invert_attach_logic: bool, trigger_channel_idx: int):
        """
        Data about a moveable mate point positioned relative to a poseable link
        :param str mate_type: selects which mating logic the joint will use
        :param glm.vec3 offset: the [x, y, z] offset from the link transform to the mate point
        :param bool invert_attach_logic: True: mvabl mates on logic level high, False: mvabl mates on logic level low
        :param int trigger_channel_idx: the idx of the module channel list that triggers mate/unmate
        """

        self._mate_type = mate_type
        self._offset = glm.vec3(offset)  # cast here in case passed in as List[float], i.e. load_from_dict
        self._invert_attach_logic = invert_attach_logic
        self._trigger_channel_idx = trigger_channel_idx   # should be called "trigger_axis_num" or similar

    @property
    def mate_type(self):
        return self._mate_type

    @property
    def offset(self):
        return self._offset

    @property
    def invert_attach_logic(self):
        return self._invert_attach_logic

    @property
    def trigger_channel_idx(self):
        return self._trigger_channel_idx

    def as_dict(self):
        return {
            "mate_type": self.mate_type,
            "offset": self.offset.to_list(),  # [x, y, z]
            "invert_attach_logic": self.invert_attach_logic,  # bool
            "trigger_channel_idx": self.trigger_channel_idx  # int
        }


class Joint:
    TYPE_FIXED = 0
    TYPE_PRISMATIC = 1
    TYPE_REVOLUTE = 2

    CHAIN_SERIAL = 0
    CHAIN_PRIMARY_PARALLEL = 1  # The first link in a list of parallel links
    CHAIN_SECONDARY_PARALLEL = 2  # Any subsequent link  in a list of parallel links

    BASE_JOINT = 'base'

    def __init__(self, name: str, model=None):
        self._name = name
        self._model = model

        self._min = 0.0
        self._max = 1.0
        self._type = self.TYPE_FIXED
        self._chain = self.CHAIN_SERIAL
        self._dh = None  # optional if tform included
        self._init_tform = glm.mat4(*model.loc_transform) if model else glm.mat4()  # 4x4 identity

        # Follower joints are secondary parallel joints that always move in direct opposition to a primary parallel
        # joint. They do not have defaults/kinematics given.
        self._follower = False

        self._defaults = {
            "counts": 0,
            "channel": 0,
        }
        self._kinematics = {
            "slope": 0.00001,
            "y_int": 0.0,
        }

    def init_from_dict(self, jointdict: dict):
        try:
            self._name = jointdict['name']
            self._min = jointdict['min']
            self._max = jointdict['max']
            self._type = jointdict['type']
            tform = jointdict['tform']
            if len(tform) == 0:
                self._init_tform = glm.mat4()
            else:
                if len(tform) != 16:
                    logging.warning(f'Initializing joint {self._name} from dict with irregular tform len({len(tform)})')
                self._init_tform = glm.mat4(*tform)
            self._dh = jointdict['dh']
            self._chain = jointdict['chain']
            if 'defaults' in jointdict and 'kinematics' in jointdict:
                self._defaults = jointdict['defaults']
                self._kinematics = jointdict['kinematics']
            else:
                if self._chain == self.CHAIN_SECONDARY_PARALLEL:
                    self._follower = True
                self._defaults = None
                self._kinematics = None
        except KeyError as e:
            logging.exception(e)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        assert isinstance(value, str)
        self._name = value

    @property
    def joint_type(self) -> int:
        return self._type

    @property
    def chain_config(self) -> int:
        return self._chain

    @property
    def min(self) -> float:
        return self._min

    @property
    def max(self) -> float:
        return self._max

    @property
    def _tform(self) -> glm.mat4:
        # right now, prefer a current (modelled) tform but revert to initial if no current one exists.
        # initial tform is either loaded from file or the identity matrix if no file tform
        if self._model is not None:
            return glm.mat4(*np.array(self._model.loc_transform).flatten())
        else:
            return glm.mat4(*np.array(self._init_tform).flatten())

    @property
    def defaults(self):
        return self._defaults

    @property
    def default_counts(self):
        return self._defaults['counts']

    @property
    def default_channel(self):
        return self._defaults['channel']

    @property
    def kinematics(self):
        return self._kinematics

    @property
    def kin_slope(self):
        return self._kinematics['slope']

    @property
    def kin_yint(self):
        return self._kinematics['y_int']

    @property
    def is_follower(self):
        return self._follower

    def as_dict(self):
        return {
            "name": self._name,
            "max": self._max,  # what units?
            "min": self._min,
            "type": self._type,
            "tform": list(map(float, np.array(self._tform).flatten())),
            "dh": self._dh,
            "chain": self._chain,
            "follower": self._follower,
            "defaults": self._defaults,
            "kinematics": self._kinematics
        }

    def configure(self, joint_type=None, chain_config=None, dh_params: list = None):
        if joint_type is not None:
            self._type = joint_type
        if chain_config is not None:
            self._chain = chain_config
        if dh_params is not None:
            self._dh = dh_params

    def set_init_tform(self, tform: glm.mat4):
        self._init_tform = tform

    def set_minmax(self, min_val: float = None, max_val: float = None):
        if type(min_val) in [int, float]:
            self._min = float(min_val)
        if type(max_val) in [int, float]:
            self._max = float(max_val)

    def set_defaults(self, counts=None, channel=None):
        if counts is not None:
            assert isinstance(counts, int)
            self._defaults['counts'] = counts
        if channel is not None:
            assert isinstance(channel, int)
            self._defaults['channel'] = channel
        if counts is None and channel is None:
            logging.warning(f'{self.__class__.__name__}.set_defaults(): '
                            f'both counts and channel are None.')

    def set_kinematics(self, slope: float = None, y_intercept: float = None):
        if slope is not None:
            self._kinematics['slope'] = slope
        if y_intercept is not None:
            self._kinematics['y_int'] = y_intercept


class Link:
    JOINT_SETTINGS = "joint_settings"
    MATES = "mates"

    def __init__(self, name: str, filepath: Path, model=None, create_joint=True):
        self._name = name
        self._filepath = filepath
        self._model = model
        self._mates = []
        self._joint = Joint(name, model) if create_joint else None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        assert isinstance(value, str)
        self._name = value

    @property
    def file(self) -> str:
        return self._filepath.name

    @property
    def path(self) -> Path:
        return self._filepath

    @path.setter
    def path(self, value: Path):
        self._filepath = value

    @property
    def joint(self):
        return self._joint

    @property
    def is_base_link(self):
        return self._joint is None

    @property
    def is_controllable(self):
        return (not self.is_base_link) and not self.joint.is_follower and not self.joint.joint_type == Joint.TYPE_FIXED

    @property
    def has_model(self):
        return self._model is not None

    @property
    def model(self):
        return self._model

    @property
    def mates(self):
        return self._mates

    def as_dict(self):
        return {  # TODO rename some of these?
            "obj_name": self.file,
            "joint_settings": self.joint.as_dict() if isinstance(self.joint, Joint) else Joint.BASE_JOINT,
            "mates": [mate.as_dict for mate in self._mates]
        }

    def init_model(self, overwrite=False):
        # TODO create model from self.file and return it
        # return _model_(self.file)
        raise NotImplementedError()

    def add_mate(self, mate: Mate):
        self._mates.append(mate)


class NorthResource:
    RES_ID = 'res_id'
    TYPE = 'type'
    SUBTYPE = 'subtype'
    DISABLE_LINES = 'disable_lines'
    GRID = 'grid'
    TOOL = 'tool'
    MATES = 'mates'
    DEFAULTS = 'defaults'

    TYPE_STATIC = 'static'
    TYPE_POSEABLE = 'poseable'
    TYPE_MOVEABLE = 'moveable'

    SUBTYPE_N9 = 'N9'
    SUBTYPE_RACK = 'rack'
    SUBTYPE_DECK = 'deck'
    SUBTYPE_PUMP = 'pump'
    SUBTYPE_PERI_PUMP = 'peri_pump'

    TOOL_GRIPPER = 'gripper'
    TOOL_PIPETTE = 'pipette'
    TOOL_BERNOULLI = 'bern_gripper'

    GRID_ORIGIN = 'origin'  # TODO replace with Grid.ORIGIN etc. (see above)
    GRID_COUNT = 'count'
    GRID_PITCH = 'pitch'

    def __init__(self, filepath=None):
        self._filepath = filepath

        self._res_id = None
        self._name = None
        self._pyname = None
        self._links = []
        self._type = self.TYPE_STATIC
        self._subtype = None
        self._rackonly = {}  # for storing properties only racks have!
        self._pumponly = {}  # for storing properties only racks have!
        self._grid = {
            self.GRID_ORIGIN: (0.0, 0.0, 0.0, 0.0),
            self.GRID_COUNT: (1, 1, 1),
            self.GRID_PITCH: (0.005, 0.005, 0.005)
        }
        self._tool = None
        self._defaults = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "rot": 0.0,
        }
        self._aux_channels = {}
        self._disable_lines = False

        if filepath is not None:
            self.read()

    @property
    def path(self) -> Path:
        return self._filepath

    @property
    def dir(self) -> Path:
        return self.path.parent

    @property
    def id(self) -> str:
        return self._res_id

    @id.setter
    def id(self, value: str):
        self._res_id = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    # TODO since pyname is derived from name, which is a parameter that is mutated in instanced modules, it doesn't make
    #  much sense to keep it around in resources at all. In fact, even "name" should probably be moved under "defaults".
    @property
    def pyname(self) -> str:
        return self._pyname

    @pyname.setter
    def pyname(self, value: str):
        self._pyname = value

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str):
        self._type = value

    @property
    def subtype(self) -> Optional[str]:
        return self._subtype

    @subtype.setter
    def subtype(self, value: Optional[str]):
        self._subtype = value

    @property
    def grid(self):
        assert isinstance(self._grid, dict) or self._grid is None
        return self._grid

    @grid.setter
    def grid(self, value):
        if value == "None":  # for backwards compatibility
            value = None
        elif isinstance(value, dict):
            value.setdefault(self.GRID_ORIGIN, (0.0, 0.0, 0.0, 0.0))
            value.setdefault(self.GRID_COUNT, (1, 1, 1))
            value.setdefault(self.GRID_PITCH, (0.005, 0.005, 0.005))
        try:
            assert isinstance(value, dict) or value is None
            self._grid = value
        except AssertionError as e:
            logging.exception(e)
            self._grid = None

    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, value):
        self._tool = value

    @property
    def links(self) -> List[Link]:
        return self._links

    @property
    def links_dict(self) -> Dict[str, Link]:
        return {link.name: link.as_dict() for link in self._links}

    @property
    def _posable_links(self):
        return tuple(filter(lambda lnk: not lnk.is_base_link, self.links))

    @property
    def _controlled_links(self):
        return tuple(filter(lambda lnk: lnk.is_controllable, self.links))

    @property
    def staticlink(self) -> Optional[Link]:
        try:
            return self._links[0]
        except IndexError:
            logging.warning(f'NorthResource.staticlink() was called on resource "{self._name}" with no links!')
            logging.error(self.path)
            return None

    @property
    def defaults(self) -> dict:
        return self._defaults

    @property
    def default_channels(self) -> List:
        return [link.joint.default_channel for link in self._controlled_links] + \
               [ac.default_channel for ac in self._aux_channels]

    @property
    def axis_names(self) -> List:
        return [link.joint.name for link in self._controlled_links] + [ac.name for ac in self._aux_channels]

    @property
    def default_counts(self) -> List[int]:
        return [link.joint.default_counts for link in self._controlled_links]

    @property
    def kinematics(self) -> List[Dict]:
        return [link.joint.kinematics for link in self._controlled_links]

    @property
    def mates(self) -> List[List[Mate]]:
        return [link.mates for link in self._links]

    @property
    def lines_disabled(self):
        assert isinstance(self._disable_lines, bool)
        return self._disable_lines

    def as_dict(self):
        return {
            "res_id": self.id,
            "name": self._name,
            "py_name": self._pyname,
            self.TYPE: self._type,
            self.SUBTYPE: self._subtype,
            self.GRID: self.grid,
            self.TOOL: self._tool,
            **self._rackonly,
            **self._pumponly,
            "defaults": self._defaults,
            "links": self.links_dict,
        }

    def add_link(self, link: Link):
        self._links.append(link)

    def set_defaults(self, x=0.0, y=0.0, z=0.0, rot=0.0):
        if x is not None:
            self._defaults['x'] = x
        if y is not None:
            self._defaults['y'] = y
        if z is not None:
            self._defaults['z'] = z
        if rot is not None:
            self._defaults['rot'] = rot

    def set_grid(self, origin=None, counts=None, pitch=None):
        if origin is not None:
            assert len(origin) == 4
            self.grid[NorthResource.GRID_ORIGIN] = origin
        if counts is not None:
            assert len(counts) == 3
            self.grid[NorthResource.GRID_COUNT] = counts
        if pitch is not None:
            assert len(pitch) == 3
            self.grid[NorthResource.GRID_PITCH] = pitch

    def tryopen(self, filepath=None):
        if filepath is None:
            assert self._filepath is not None
            filepath = self._filepath
        try:
            open(filepath, 'w')
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def read(self):
        assert self._filepath is not None
        return self.read_from(self._filepath)

    def read_from(self, filepath: Path):
        try:
            with open(filepath, 'r') as file:
                nres = json.load(file)
        except json.decoder.JSONDecodeError as e:
            logging.warning(f'JSON decoding error reading {filepath}:')
            logging.exception(e)
            return False
        except FileNotFoundError:
            logging.error(f'Tried to read resource from {filepath} which does not exist.')
            return False
        except PermissionError:
            logging.error(f'Tried to read resource from {filepath} but was denied.')
            return False
        allow_overwrite = True
        try:
            self._res_id = nres['res_id']
            self._name = nres['name']
            self._pyname = nres['py_name']
            self._type = nres[self.TYPE]
            self._subtype = nres[self.SUBTYPE]
            del nres['res_id']
            del nres['name']
            del nres['py_name']
            del nres[self.TYPE]
            del nres[self.SUBTYPE]

            if self._type != self.TYPE_MOVEABLE:
                self.grid = nres[self.GRID]  # using setter to check against "None"
                self._tool = nres[self.TOOL]
                self._defaults = nres['defaults']
                del nres[self.GRID]
                del nres[self.TOOL]
                del nres['defaults']

            # TODO: handle rack defaults (moveable type, fill_range, etc.)
            # if self._subtype == 'rack':

            if self.DISABLE_LINES in nres:
                self._disable_lines = nres[self.DISABLE_LINES]
                logging.info(f'{self.name} has {self.DISABLE_LINES} set to {self._disable_lines}')
                del nres[self.DISABLE_LINES]

            if 'moveable_type' in nres:
                if self._subtype != 'rack':
                    logging.warning(f'moveable_type in nonrack module ({self._type}, {self._subtype})')
                self._rackonly['moveable_type'] = nres['moveable_type']
                del nres['moveable_type']

            if 'volume' in nres:
                if self._subtype != self.SUBTYPE_PUMP:
                    logging.warning(f'volume in nonpump module ({self._type}, {self._subtype})')
                self._pumponly['volume'] = nres['volume']
                del nres['volume']
        except KeyError as e:
            logging.error(f'KeyError after reading from {filepath}')
            logging.warning(f'could not find key in nres: {nres}')
            logging.exception(e)
            allow_overwrite = False

        if 'aux_channels' in nres:
            self._aux_channels = [AuxChannel(name=name, default_channel=aux_chan['default'])
                                    for name, aux_chan in nres['aux_channels'].items()]

        self.links.clear()
        if 'links' in nres:  # Current NRES format
            for link_name in nres['links']:
                link_dict = nres['links'][link_name]
                assert isinstance(link_dict, dict)
                link_path = filepath.parent.joinpath(link_dict['obj_name'])
                joint_settings = link_dict[Link.JOINT_SETTINGS]
                is_base_link = link_dict[Link.JOINT_SETTINGS] == Joint.BASE_JOINT
                link = Link(link_name, link_path, create_joint=not is_base_link)
                if not is_base_link:
                    assert isinstance(joint_settings, dict)
                    link.joint.init_from_dict(joint_settings)
                if Link.MATES in link_dict:
                    for mate in link_dict[Link.MATES]:
                        if Mate.MATE_TYPE not in mate:
                            logging.error(f'No mate type in {self.name}, link: {link_name}')
                            continue  # could we set a default?
                        link.add_mate(Mate(mate_type=mate[Mate.MATE_TYPE],
                                           offset=glm.vec3(mate[Mate.OFFSET]),
                                           invert_attach_logic=mate[Mate.INV_ATTACH_LOGIC],
                                           trigger_channel_idx=mate[Mate.TRIGGER_CHANNEL_IDX]))
                self.add_link(link)
        else:  # Outdated NRES format; will be brought up-to-date. #
            assert 'models' in nres
            logging.warning(f'Reading from outdated NRES ({filepath.name}): using "models" instead of "links"')
            # logging.warning(f'{filepath} will be overwritten with the up-to-date format.')
            # Handle outdated models #
            models = nres['models']
            if isinstance(models, str):
                link_path = filepath.parent.joinpath(f'{models}.obj')
                self.add_link(Link(models, link_path))
            else:
                assert type(models) in [dict, list]
                assert self._type in [NorthResource.TYPE_MOVEABLE, NorthResource.TYPE_POSEABLE]
                for model_name in models:
                    link_path = filepath.parent.joinpath(f'{model_name}.obj')
                    link = Link(model_name, link_path)
                    if self._type == NorthResource.TYPE_POSEABLE:
                        assert type(models) is dict
                        link.joint.configure(chain_config=models[model_name]['chain'], dh_params=models[model_name]['dh'])
                    self.add_link(link)
            del nres['models']

            # posable_link_count = sum(map(lambda lnk: 1 if lnk.joint.chain_config in [0, 1] else 0, self._links)) - 1
            posable_link_count = len(self._controlled_links)
            if 'counts' in self._defaults and 'channels' in self._defaults:
                channels = self._defaults['channels']
                counts = self._defaults['counts']
                if len(counts) == len(channels) == posable_link_count:
                    for i, link in enumerate(self._links):
                        if link.is_base_link:
                            continue
                        if link.joint.chain_config == 2:  # SECONDARY PARALLEL
                            continue
                        link.joint.set_defaults(self._defaults['counts'][i], self._defaults['channels'][i])
                else:
                    allow_overwrite = False
                    if len(channels) != posable_link_count:
                        logging.warning(f'NorthResource.read_from(): channels len ({len(channels)})'
                                        f' does not match posable links len ({posable_link_count})')
                    if len(counts) != posable_link_count:
                        logging.warning(f'NorthResource.read_from(): counts len ({len(counts)})'
                                        f' does not match posable links len ({posable_link_count})')
                del self._defaults['channels']
                del self._defaults['counts']

            if 'kinematics' in nres:
                kinematics = nres['kinematics']
                if len(kinematics) != posable_link_count:
                    logging.warning(f'NorthResource.read_from(): kinematics len ({len(kinematics)})'
                                    f' does not match links len ({len(self._links)})')
                    allow_overwrite = False
                else:
                    for i, link in enumerate(
                            self._links[1:]):  # skip first link, assumed to be base link TODO keep this?
                        if link.joint.chain_config == 2:  # SECONDARY PARALLEL
                            continue
                        link.joint.set_kinematics(kinematics[i]['slope'], kinematics[i]['y_int'])
                del nres['kinematics']

            if len(nres) > 0:
                logging.warning(f'{self.__class__.__name__}.read_from(): Unaccounted-for keylist - {list(nres.keys())}')
                allow_overwrite = False

            if allow_overwrite:
                self.write()  # Updates the file this NorthResource shadows to be up-to-date.
                logging.info(f'{self.__class__.__name__}.read_from(): Over-writing {self._filepath}')
            else:
                logging.info(f'Leaving {self._filepath} out-of-date!')
            # TODO: still need to handle moveable_type from old file (create mates)
            # TODO: assign channels from defaults to individual joint defaults
        return True

    def point_to(self, filepath):
        self._filepath = filepath

    def write(self):
        assert self._filepath is not None
        self.write_to(self._filepath)

    def write_to(self, filepath):
        try:
            with open(filepath, 'w') as file:
                json.dump(self.as_dict(), file, indent="  ")
        except Exception as e:
            logging.exception(e)


@dataclass
class AuxChannel:
    name: str
    default_channel: int