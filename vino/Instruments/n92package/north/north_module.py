from north.north_resource import NorthResource, Mate

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict
import math
import glm  # for module positions and mate point transforms


# TODO: can this class be combined with ControllerConnection somehow?
# TODO: should rename this to ModuleAxis or similar based on the convention that axes are actuated parts of a module
#       and channels are numbered subdivisions of a controller: i.e. the rotary AXIS of the carousel gets a signal from
#       the third CHANNEL of the controller. Since this is representing data about an axis on the module side of the
#       connection, it shouldn't be called channel. Note that in the context of default channels in resources the name
#       "channel" is actually correct since it refers to the controller channel the joint/axis should connect to by
#       default, hence the confusion.
@dataclass
class Channel:
    axis_name: str
    controller_id: int
    channel_n: int

    def to_dict(self):
        return {
            'axis_name': self.axis_name,
            'controller_id': self.controller_id,
            'channel_n': self.channel_n
        }


# TODO I think all NorthModules should have a grid as defined below, but unless they're racks they'll probably only have
#  the origin property, this should be enough to indicate where a tool or single slide etc. should be placed and racks
#  will be expected to have all 3 properties as part of their designation as a rack (something storing multiple [thing])
@dataclass
class Grid:
    ORIGIN = 'origin'
    COUNT = 'count'
    PITCH = 'pitch'

    _origin = [0.0, 0.0, 0.0]
    _counts = None
    _pitch = None

    @property
    def origin(self):
        assert isinstance(self._origin, list)
        return tuple(self._origin)

    @property
    def counts(self):
        if self._counts is None:
            return None
        else:
            assert isinstance(self._counts, list)
            return tuple(self._counts)

    @property
    def pitch(self):
        if self._pitch is None:
            return None
        else:
            assert isinstance(self._pitch, list)
            return tuple(self._pitch)

    @origin.setter
    def origin(self, values: list):
        try:
            assert len(values) == 3
            self._origin = list(values)
        except Exception as e:
            logging.exception(e)

    @counts.setter
    def counts(self, values: list):
        if values is None:
            self._counts = None
            return
        try:
            assert len(values) == 3
            self._counts = list(values)
        except Exception as e:
            logging.exception(e)

    @pitch.setter
    def pitch(self, values: list):
        if values is None:
            self._pitch = None
            return
        try:
            assert len(values) == 3
            self._pitch = list(values)
        except Exception as e:
            logging.exception(e)

    def from_dict(self, grid_dict: dict):
        try:
            assert isinstance(grid_dict, dict)
            assert self.ORIGIN in grid_dict
        except AssertionError as e:
            logging.exception(e)
            return None
        self.origin = grid_dict[self.ORIGIN]
        self.counts = grid_dict[self.COUNT] if self.COUNT in grid_dict else None
        self.pitch = grid_dict[self.PITCH] if self.PITCH in grid_dict else None
        return self

    def as_dict(self):
        d = {self.ORIGIN: self.origin}
        if self._counts is not None:
            d[self.COUNT] = self.counts
        if self._pitch is not None:
            d[self.PITCH] = self.pitch
        return d


class NorthModule:
    NAME = 'name'
    PYNAME = 'pyname'
    ENABLED = 'enabled'
    X = 'x'
    Y = 'y'
    Z = 'z'
    ROTATION = 'rot'
    COORD_SYS = 'coord_sys'
    CHANNELS = 'channels'

    def __init__(self, m_id: int):
        assert isinstance(m_id, int)
        # module parameters that are not derived from the resource
        self._id = m_id
        self._enabled = True
        self._model = None
        self._initialized = False
        # module['channels'] = resource.default_channels
        # module['init_counts'] = resource.default_counts

        # mutable parameters that are initialized from the resource/dictionary
        self._name = self._pyname = 'BASE_MODULE_NAME'
        self._res_id = None
        self._coord_sys = -1  # -1 represents global coord sys, otherwise this is an int of an N9Deck id for local coord
        self._position = [0.0, 0.0, 0.0]
        self._rotation = 0.0

        # immutable parameters which are specified by the resource/dictionary
        self._type = None
        self._subtype = None
        self._tool = None
        self._grid = None

        self._channels: List[Channel] = []

        self._mate_points = {}

    @property
    def initialized(self):
        return self._initialized

    @property
    def id(self) -> int:
        return self._id

    @property
    def enabled(self):
        return self._enabled

    @property
    def name(self) -> str:
        assert isinstance(self._name, str)
        return self._name

    @property
    def pyname(self):
        return self._pyname

    @property
    def model(self):
        return self._model

    @property
    def coord_sys(self) -> int:
        return self._coord_sys
    
    @coord_sys.setter
    def coord_sys(self, value):
        try:
            self._coord_sys = int(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def position(self):
        return self._position

    @property
    def x(self):
        return self._position[0]

    @x.setter
    def x(self, value):
        try:
            self._position[0] = float(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def y(self):
        return self._position[1]

    @y.setter
    def y(self, value):
        try:
            self._position[1] = float(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def z(self):
        return self._position[2]

    @z.setter
    def z(self, value):
        try:
            self._position[2] = float(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        try:
            self._rotation = float(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def res_id(self):
        return self._res_id

    @property
    def type(self) -> str:
        return self._type

    @property
    def subtype(self) -> Optional[str]:
        return self._subtype

    @property
    def tool(self):
        return self._tool

    @property
    def grid(self):
        return self._grid

    @property
    def mates(self):
        return self._mate_points

    @property
    def mate_list(self):
        return [mate.to_dict() for mate in self._mate_points.values()]

    @property
    def pipette_mates(self):  # -> List[ModuleMatePoint]  (typing issue, TODO: give ModuleMatePoint its own file)
        return [mate for mate in self.mates.values() if mate.mate_type == Mate.MATE_TYPE_PIPETTE]

    @property
    def pipette_unmates(self):  # -> List[ModuleMatePoint]  (typing issue, TODO: give ModuleMatePoint its own file)
        return [mate for mate in self.mates.values() if mate.mate_type == Mate.MATE_TYPE_RM_PIPETTE]

    @property
    def channels(self) -> List[Channel]:
        return self._channels

    @property
    def channel_names(self):
        return list(map(lambda c: c.axis_name, self._channels))

    @property
    def any_channels(self):
        return len(self._channels) > 0

    @property
    def named_channels(self) -> Dict[str, int]:
        assert len(self.channel_names) == len(self.channels)
        return list(zip(self.channel_names, self.channels))

    def as_dict(self):
        return {
            "m_id": self.id,
            NorthResource.RES_ID: self.res_id,
            NorthModule.NAME: self.name,
            NorthModule.PYNAME: self.pyname,
            NorthModule.ENABLED: self.enabled,
            NorthResource.TYPE: self.type,
            NorthResource.SUBTYPE: self.subtype,
            NorthResource.TOOL: self.tool,
            NorthResource.GRID: self.grid,
            NorthModule.COORD_SYS: self.coord_sys,
            NorthModule.X: self.x,
            NorthModule.Y: self.y,
            NorthModule.Z: self.z,
            NorthModule.ROTATION: self.rotation,
            NorthResource.MATES: self.mate_list,
            NorthModule.CHANNELS: [ch.to_dict() for ch in self._channels]
        }

    def get_save_dict(self):
        return {
            # 'res_id' is the only NorthResource (immutable) property saved in project module dict.
            # All other immutable properties can be accessed in the resource.
            NorthResource.RES_ID: self.res_id,

            NorthModule.NAME: self.name,
            NorthModule.PYNAME: self.pyname,
            NorthModule.ENABLED: self.enabled,
            NorthModule.COORD_SYS: self.coord_sys,
            NorthModule.X: self.x,  # TODO I would rather have "position": self.position, personally
            NorthModule.Y: self.y,
            NorthModule.Z: self.z,
            NorthModule.ROTATION: self.rotation,
            NorthModule.CHANNELS: [ch.to_dict() for ch in self._channels]
        }

    # TODO we need to make some decision between this and load_from_properties_model() -- right now they are basically
    #  both used in similar ways, that is to change a module's mutable values after being instanced from a resource(?).
    def load_from_dict(self, dictionary: Dict):
        assert isinstance(dictionary, dict)
        try:
            assert NorthModule.NAME in dictionary
            assert NorthModule.X in dictionary
            assert NorthModule.Y in dictionary
            assert NorthModule.Z in dictionary
            assert NorthModule.ROTATION in dictionary
            assert NorthModule.ENABLED in dictionary

            assert NorthResource.RES_ID in dictionary
            # assert NorthModule.COORD_SYS in dictionary
            # assert NorthModule.CHANNELS in dictionary
            # assert NorthResource.TYPE in dictionary
            # assert NorthResource.SUBTYPE in dictionary
            # assert NorthResource.TOOL in dictionary
            # assert NorthResource.GRID in dictionary
            # assert NorthResource.MATES in dictionary
        except AssertionError as e:
            logging.exception(e)

        # mutable parameters that are to be specified as default by the dictionary
        self.rename(dictionary.setdefault(NorthModule.NAME, self._name))
        self._coord_sys = dictionary.setdefault(NorthModule.COORD_SYS, self._coord_sys)
        self._position = [
            dictionary.setdefault(NorthModule.X, self.x),
            dictionary.setdefault(NorthModule.Y, self.y),
            dictionary.setdefault(NorthModule.Z, self.z),
        ]
        self._rotation = dictionary.setdefault(NorthModule.ROTATION, self.rotation)
        self.enable(dictionary.setdefault(NorthModule.ENABLED, self.enabled))
        # immutable parameters which must be loaded from the dictionary
        self._res_id = dictionary.setdefault(NorthResource.RES_ID, self.res_id)
        self._type = dictionary.setdefault(NorthResource.TYPE, self.type)
        self._subtype = dictionary.setdefault(NorthResource.SUBTYPE, self.subtype)
        self._tool = dictionary.setdefault(NorthResource.TOOL, self.tool)
        self._grid = dictionary.setdefault(NorthResource.GRID, self.grid)
        grid = dictionary[NorthResource.GRID]
        if grid == "None":  # for backwards compatibility
            grid = None
        elif isinstance(grid, dict):
            grid.setdefault(NorthResource.GRID_ORIGIN, (0.0, 0.0, 0.0, 0.0))
            grid.setdefault(NorthResource.GRID_COUNT, (1, 1, 1))
            grid.setdefault(NorthResource.GRID_PITCH, (0.005, 0.005, 0.005))
        try:
            assert isinstance(grid, dict) or grid is None
            self._grid = grid
        except AssertionError as e:
            logging.warning(f'dictionary has invalid grid type ({type(grid)}): {grid}')
            logging.exception(e)
            self._grid = None

        channels = dictionary.setdefault(PosableModule.CHANNELS, [])  # TODO an actual default?
        if all(map(lambda c: isinstance(c, int), channels)):  # Out-of-date (< v0.3) channels list
            # logging.warning(f'load_from_dict(): Loading from out-of-date channels list: '
                            # f'list elements should be dicts with keys "axis_name", "controller_id", "channel_n"')
            self._channels = [Channel(axis_name=f"unknown axis {i}",
                                      controller_id=None,
                                      channel_n=channel) for i, channel in enumerate(channels)]
        elif all(map(lambda c: isinstance(c, dict), channels)):
            try:
                self._channels = [Channel(axis_name=channel['axis_name'],
                                          controller_id=channel['controller_id'],
                                          channel_n=channel['channel_n'])
                                  for channel in channels]
            except Exception as e:
                logging.exception(e)
                self._channels = []
        else:
            logging.error(f"load_from_dict(): Unrecognized or mixed channel {type(channels)} {channels}")

        self._initialized = True
        return self

    def load_from_properties_model(self, model):
        self.rename(model.name)
        self._enabled = model.is_enabled
        if model.position:
            self._coord_sys = model.position.coord
            self.reposition(
                [float(model.position.x / 1000), float(model.position.y / 1000), float(model.position.z / 1000)],
                math.radians(float(model.position.rot)))

    def load_from_res(self, resource: NorthResource):
        assert isinstance(resource, NorthResource)
        # mutable parameters that are to be specified as default by the resource
        self.rename(resource.pyname)
        self._position = [resource.defaults[axis] for axis in [NorthModule.X, NorthModule.Y, NorthModule.Z]]
        self._rotation = resource.defaults[NorthModule.ROTATION]
        # immutable parameters which must be loaded from the resource
        self._res_id = resource.id
        self._type = resource.type
        self._subtype = resource.subtype
        self._tool = resource.tool
        self._grid = resource.grid
        self._mate_points = {mate.trigger_channel_idx: self._mate_point_factory(link_num=i, mate=mate)
                             for i, mate_list in enumerate(resource.mates) for mate in mate_list}
        self._channels = [Channel(axis_name=name, controller_id=None, channel_n=channel_n)
                          for name, channel_n in zip(resource.axis_names, resource.default_channels)]
        logging.info(f'load_from_res(): {self.name} loaded {len(self._channels)} channels = {self._channels}')
        self._initialized = True
        return self

    def load_from_module(self, module):
        assert isinstance(module, NorthModule)
        # mutable parameters that are to be specified as default by the resource
        self.rename(module.name)
        self._position = module.position
        self._rotation = module.rotation
        self.enable(module.enabled)
        # immutable parameters which must be loaded from the resource
        self._res_id = module.res_id
        self._type = module.type
        self._subtype = module.subtype
        self._tool = module.tool
        self._channels = module.channels
        self._initialized = True
        return self

    def generate_name(self, nameset, init_n=2):
        """

        :param List[str] nameset: List of names which are illegal to use.
        :param int init_n: First n to start with. Could be anything, but prefer 'name', 'name_2' by default.
        """
        assert isinstance(init_n, int)
        cur_name = init_name = self._name
        while cur_name in nameset:
            cur_name = f"{init_name}_{init_n}"
            init_n += 1
        self._name = cur_name

    def enable(self, enabled=True):
        self._enabled = enabled

    def disable(self):
        self.enable(False)

    def rename(self, new_name: str):
        assert isinstance(new_name, str)
        self._name = new_name
        self._pyname = self._name  # TODO

    def reposition(self, position=None, rotation=None):
        if position is not None:
            self._position = list(position)
        if rotation is not None:
            self._rotation = float(rotation)

    def configure_channel(self, index: int, controller_id: int, channel_n: int):
        self._channels[index].controller_id = controller_id
        self._channels[index].channel_n = channel_n

    def set_channel(self, index: int, value):
        assert isinstance(value, int) or value is None
        raise NotImplementedError()

    def _mate_point_factory(self, link_num: int, mate: Mate):
        if mate.mate_type == Mate.MATE_TYPE_TOOL_PROXY:
            return ToolProxyModuleMatePoint(link_num=link_num, mate=mate, module=self)
        elif not isinstance(self, PosableModule):
            return StaticModuleMatePoint(link_num=link_num, mate=mate, module=self)
        return ModuleMatePoint(link_num=link_num, mate=mate, module=self)


# TODO: do we actually want to collapse these subclasses into NorthModule and base different behavior on type and
#  subtype, and have properties that only return under the correct conditions otherwise "None" and log a warning??
#  Could use dataclasses in order to bundle the settings that are particular to a typeset?
#  On the other hand, Modules shouldn't ever really change type. Only Resources have type/subtype mutable...
class PosableModule(NorthModule):
    KINEMATICS = 'kinematics'
    INIT_COUNTS = 'init_counts'

    def __init__(self, m_id: int):
        super().__init__(m_id)
        self._kinematics = []
        self._init_counts = []

        self._robot_model = None

    def load_from_dict(self, dictionary: Dict):
        super().load_from_dict(dictionary)
        # try:
        #     # assert PosableModule.KINEMATICS in dictionary
        #     # assert PosableModule.INIT_COUNTS in dictionary
        #
        # except AssertionError as e:
        #     logging.exception(e)

        self._kinematics = dictionary.setdefault(PosableModule.KINEMATICS, self.kinematics)
        self._init_counts = dictionary.setdefault(PosableModule.INIT_COUNTS, self.init_counts)
        if self._kinematics is None:
            logging.warning(f'{self.__class__.__name__}.load_from_dict(): null kinematics in dict. Replacing with [].')
            self._kinematics = []
        if len(self._init_counts) != len(self._kinematics):
            logging.warning(f'{self.__class__.__name__}.load_from_dict(): Mismatched lengths: '
                            f'len(self._init_counts) {len(self._init_counts)} '
                            f'len(self._kinematics) {len(self._kinematics)}')
        return self

    def load_from_res(self, resource: NorthResource):
        super().load_from_res(resource)
        self._kinematics = resource.kinematics
        logging.info(f'load_from_res(): {self.name} loaded {len(self._kinematics)} kinematics = {self._kinematics}')
        self._init_counts = resource.default_counts
        if len(self._init_counts) != len(self._kinematics):
            logging.warning(f'{self.__class__.__name__}.load_from_dict(): Mismatched lengths: '
                            f'len(self._init_counts) {len(self._init_counts)} '
                            f'len(self._kinematics) {len(self._kinematics)}')
        return self

    def load_from_module(self, module):
        assert isinstance(module, NorthModule)
        super().load_from_module(module)
        if isinstance(module, PosableModule):
            self._kinematics = module.kinematics
            self._init_counts = module.init_counts
        if len(self._init_counts) != len(self._kinematics):
            logging.warning(f'{self.__class__.__name__}.load_from_dict(): Mismatched lengths: '
                            f'len(self._init_counts) {len(self._init_counts)} '
                            f'len(self._kinematics) {len(self._kinematics)}')
        return self

    @property
    def kinematics(self):
        return self._kinematics

    @property
    def init_counts(self):
        return self._init_counts

    @property
    def robot_model(self):
        return self._robot_model

    @robot_model.setter
    def robot_model(self, new_robot_model):
        self._robot_model = new_robot_model
        # update mates

    def as_dict(self):
        d = super().as_dict()
        d[PosableModule.KINEMATICS] = self.kinematics
        d[PosableModule.INIT_COUNTS] = self.init_counts
        return d

    def pose_from_counts(self, counts):
        assert len(counts) == len(self.kinematics)
        pose = []
        for axis_counts, channel, k in zip(counts,
                                           self.channels[:len(self.kinematics)],
                                           self.kinematics):
            if channel.controller_id is None or channel.channel_n is None:
                pose.append(k['y_int'])  # counts = 0
            else:
                pose.append(k['slope'] * axis_counts + k['y_int'])
        return pose


class PumpModule(PosableModule):
    VOLUME = 'volume'
    DIAL = 'dial'
    ADDRESS = 'address'

    def __init__(self, p_id: int):
        super().__init__(p_id)
        self._volume = 1.0
        self._dial_pos = 0
        self._address = 0

    def load_from_dict(self, dictionary: dict):
        super().load_from_dict(dictionary)
        try:
            assert PumpModule.VOLUME in dictionary
            assert PumpModule.ADDRESS in dictionary
        except AssertionError as e:
            logging.exception(e)
        self._volume = dictionary.setdefault(PumpModule.VOLUME, self.volume)
        self._dial_pos = dictionary.setdefault(PumpModule.DIAL, self.dial)
        self._address = dictionary.setdefault(PumpModule.ADDRESS, self.address)
        return self

    def load_from_res(self, resource: NorthResource):
        super().load_from_res(resource)
        # TODO these are 'pump only' resource properties ... perhaps a PumpResource to match RackModule would be good
        self._volume = resource.as_dict()[PumpModule.VOLUME]
        self._address = resource.defaults[PumpModule.ADDRESS]
        return self

    def load_from_module(self, module):
        assert isinstance(module, NorthModule)
        super().load_from_module(module)
        if isinstance(module, PumpModule):
            self._volume = module.volume
            self._dial_pos = module.dial
            self._address = module.address
        return self

    def load_from_properties_model(self, model):
        super().load_from_properties_model(model)
        self._volume = model.pump_volume
        self._address = model.pump_address
        return self

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        try:
            self._volume = float(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def dial(self):
        return self._dial_pos

    @dial.setter
    def dial(self, value: float):
        try:
            self._dial_pos = float(value)
        except ValueError as e:
            logging.exception(e)

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value: int):
        try:
            self._address = int(value)
        except ValueError as e:
            logging.exception(e)


    def as_dict(self):
        d = super().as_dict()
        d[PumpModule.VOLUME] = self.volume
        d[PumpModule.ADDRESS] = self.address
        return d

    def get_save_dict(self):
        return self.as_dict()  # TODO temp, eventually one or the other?


class RackModule(NorthModule):
    FILL_RANGE = 'fill_range'
    MOVEABLE_TYPE = 'moveable_type'
    MOVEABLE_NAME = 'moveable_name'  # TODO deprecated
    MOVEABLE_RES_ID = 'moveable_res_id'

    def __init__(self, m_id: int):
        super().__init__(m_id)
        self._movable_type = None
        self._movable_resource: Optional[NorthResource] = None
        self._fillrange = None

    def load_from_dict(self, dictionary: dict):
        super().load_from_dict(dictionary)
        try:
            assert RackModule.FILL_RANGE in dictionary
            # assert RackModule.MOVEABLE_TYPE in dictionary
            assert RackModule.MOVEABLE_RES_ID in dictionary or RackModule.MOVEABLE_NAME in dictionary
            # assert RackModule.MOVEABLE_ID in dictionary
        except AssertionError as e:
            logging.exception(e)
        self._fillrange = dictionary.setdefault(RackModule.FILL_RANGE, self.fill_range)
        self._movable_type = dictionary.setdefault(RackModule.MOVEABLE_TYPE, self.movable_type)
        return self

    # this should just be temporary until north_module and ModuleSettingsModel merge...
    def load_from_properties_model(self, model, res=None):
        super().load_from_properties_model(model)
        # self.set_movable(model.fill_with.fill_selection, model.fill_with.fill_selection) # cannot change movable id from PropertiesModel only
        self.fill(model.fill_with.fill_range)
        self.set_movable(res)

    def load_from_res(self, resource: NorthResource):
        super().load_from_res(resource)
        # TODO these are 'racksonly' resource properties ... perhaps a RackResource to match RackModule would be good
        rd = resource.as_dict()
        self._movable_type = rd[RackModule.MOVEABLE_TYPE]
        self._fillrange = rd[NorthResource.DEFAULTS][RackModule.FILL_RANGE]
        return self

    def load_from_module(self, module):
        assert isinstance(module, NorthModule)
        super().load_from_module(module)
        if isinstance(module, RackModule):
            self._grid = module.grid
            self._movable_type = module.movable_type
            self._fillrange = module.fill_range
            self._movable_resource = module.movable_res
        return self

    def fill(self, fill_range):
        self._fillrange = fill_range

    def set_movable(self, mv_res: NorthResource):
        assert isinstance(mv_res, NorthResource) or mv_res is None
        self._movable_resource = mv_res

    @property
    def movable_type(self):
        return self._movable_type

    @property
    def has_movable(self):
        return isinstance(self._movable_resource, NorthResource)

    @property
    def movable_res(self):
        return self._movable_resource

    # Mutable properties below #
    @property
    def fill_range(self):
        return self._fillrange

    @property
    def movable_name(self):
        if self.has_movable:
            return self.movable_res.name
        else:
            logging.warning(f'{self.__class__.__name__}.movable_name: '
                            f'Requested movable name but no resource is attached !!!!')
            return None

    @property
    def movable_id(self):
        if self.has_movable:
            return self.movable_res.id
        else:
            logging.warning(f'{self.__class__.__name__}.movable_id: '
                            f'Requested movable id but no resource is attached !!!!')
            return None

    def as_dict(self):
        d = super().as_dict()
        d[RackModule.MOVEABLE_TYPE] = self.movable_type
        d[RackModule.FILL_RANGE] = self.fill_range
        d[RackModule.MOVEABLE_RES_ID] = self.movable_id
        return d

    def get_save_dict(self):
        d = super().get_save_dict()
        d[RackModule.FILL_RANGE] = self.fill_range
        d[RackModule.MOVEABLE_RES_ID] = self.movable_id
        return d


class ModuleMatePoint:
    LINK_NUM = 'link_num'
    MATE_DATA = 'mate_data'

    def __init__(self, link_num: int, mate: Mate, module: NorthModule):
        self._link_num = link_num
        self._mate = mate
        self._module: NorthModule = module
        self.child = None

    @property
    def mate_type(self):
        return self._mate.mate_type

    @property
    def offset(self):
        return self._mate.offset

    @property
    def invert_attach_logic(self):
        return self._mate.invert_attach_logic

    @property
    def trigger_channel_idx(self):
        return self._mate.trigger_channel_idx

    @property
    def module(self):
        return self._module

    @property
    def transform(self):
        """
        Called while SimController is replaying the sim, returns the transform for the pose the robot_model is actually
        in
        """
        assert isinstance(self._module, PosableModule)
        return glm.translate(self._module.robot_model.links[self._link_num].transform, self.offset)

    def to_dict(self):
        return {self.LINK_NUM: self._link_num, self.MATE_DATA: self._mate.as_dict()}

    def get_tform_in_pose(self, module_pose: list = None):
        """
        Called while SimController is building the sim, returns the transform for the pose the robot_model is
        hypothetically in given module_pose
        """
        assert module_pose is not None
        assert isinstance(self._module, PosableModule)
        assert len(module_pose) == len(self._module.kinematics)
        return glm.translate(self._module.robot_model.get_tform(module_pose, last_link=self._link_num), self.offset)


class StaticModuleMatePoint(ModuleMatePoint):
    @property
    def transform(self):
        return self.get_tform_in_pose(None)

    def get_tform_in_pose(self, module_pose: list = None):
        tform = glm.rotate(glm.mat4(), self._module.rotation, glm.vec3(0, 0, 1))
        tform = glm.translate(tform, glm.vec3(self._module.position))
        return glm.translate(tform, glm.vec3(self.offset))


class ToolProxyModuleMatePoint(ModuleMatePoint):

    def __init__(self, link_num: int, mate: Mate, module: NorthModule):
        super().__init__(link_num, mate, module)
        self.tool_moveable = None
        self.tool_model = None
        self._mate._offset = glm.vec3([0, -0.07, -0.01])  # TODO: generalize tool offsets in .NRES file

    @property
    def transform(self):
        return glm.translate(self.tool_model.transform, self.offset)


def build_module_from_res(module_id: int, resource: NorthResource) -> NorthModule:
    """
    :param int module_id: Identifier for the new module
    :param NorthResource resource: The resource to be instanced.
    :returns: The constructed module.
    """
    try:
        assert isinstance(module_id, int)
        assert isinstance(resource, NorthResource)
    except AssertionError as e:
        logging.exception(e)
        logging.info(f'module_id ({type(module_id)}) {module_id} resource {type(resource)}')
    if resource.type == NorthResource.TYPE_POSEABLE:
        if resource.subtype == NorthResource.SUBTYPE_PUMP:
            return PumpModule(module_id).load_from_res(resource)
        else:
            return PosableModule(module_id).load_from_res(resource)
    else:  # static modules
        assert resource.type == NorthResource.TYPE_STATIC
        if resource.subtype == NorthResource.SUBTYPE_RACK:
            return RackModule(module_id).load_from_res(resource)
        else:
            return NorthModule(module_id).load_from_res(resource)
