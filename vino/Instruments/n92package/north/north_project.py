from north.north_module import NorthModule, PosableModule, RackModule, PumpModule, build_module_from_res
from north.north_resource import NorthResource
from north.north_paths import get_default_proj_path
from north.north_util import parse_range_str, make_file, shell_print

import json
import math
import glm  # TODO:for ModuleMatePoint -- remove if this code is moved, see TODOS for that class
import shutil
import logging
from os import mkdir, walk
from dataclasses import dataclass
from ast import literal_eval
from io import IOBase
from pathlib import Path
from copy import deepcopy
from sortedcontainers import SortedList
from typing import Any, Union, Optional, List, Dict, Tuple

"""
03/19/2023
Updated VERSION to 0.3 
Reason for change:
--- Removal of "pumps" from .nproj file
--- Only saving mutable module properties.
"""
VERSION = 0.3
DEFAULTPROJ = None

AnyModule = Union[NorthModule, PosableModule, RackModule, PumpModule]
PathOrStr = Union[str, Path]


def get_default_proj() -> dict:
    # Note: this uses a pretty hacky Python trick - we are assigning an attribute to ~this function~! #
    # https://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
    if not hasattr(get_default_proj, "default_proj"):
        with open(Path(__file__).absolute().parent.joinpath('default_proj.nproj'), 'r') as default_proj_file:
            get_default_proj.default_proj = import_json_proj(default_proj_file)
    return get_default_proj.default_proj


def get_default_values(key: str) -> dict:
    proj = get_default_proj()
    if key in proj:
        return proj[key]
    else:
        shell_print(f'Attempted to retrieve a default value for [{key}] which is not in default project.')


def import_json_proj(proj_file: IOBase) -> dict:
    try:
        return json.load(proj_file)
    except json.decoder.JSONDecodeError:
        raise LegacyProjectError("File not properly JSON formatted.")
    except KeyError as e:
        raise LegacyProjectError(str(e))


# todo: support projects that are missing some of these fields
def import_legacy_proj(proj_file: IOBase):
    proj_contents = proj_file.read()
    if proj_contents == '':
        raise RuntimeError("Blank project file!")
    return literal_eval(proj_contents)


def default_vision_settings():
    return {
        'image_source': None,
        'crop': {
            'enabled': False,
            'start_x': 0,
            'start_y': 0,
            'end_x': 1,
            'end_y': 1
        }
    }


class LegacyProjectError(ValueError):
    pass


# TODO: will eventually need to subclass this based on products, for now they're all C9s
class Controller:
    """
    Represents a controller included in a North Project
    Store an address and settings so as to mirror a physical C9, C2, etc.
    Keeps a record of which modules are connected to which channels
    """

    # channels:
    GRIPPER = 0
    ELBOW = 1
    SHOULDER = 2
    Z_AXIS = 3

    N_MOTORS = HVO_CHANNELS = GRIPPER_FINGERS_HVO = 8  # Start of digital outputs, relays, pneumatics (high voltage outputs)
    CLAMP_HVO = 9

    N_OUTPUTS = 16
    PUMPS = N_OUTPUTS + N_MOTORS
    N_PUMPS = 15
    LAST_PUMP_AXIS = PUMPS + 2 * N_PUMPS - 1
    # LINE_NUM = LAST_PUMP_AXIS + 1
    # N_AXES = LINE_NUM + 1
    N_AXES = LAST_PUMP_AXIS + 1

    def __init__(self, c_id, name=None, address: int = 65):
        self.id = c_id
        self._name = name
        self.address = address if isinstance(address, int) else ord(address)
        self.reset_connections_list()
        self.axis_map = {}

    def __repr__(self):
        return self.name

    def _make_empty_connection_list(self):
        return SortedList(key=lambda c: c.channel)

    def reset_connections_list(self):
        self.connections = self._make_empty_connection_list()

    @property
    def name(self):
        return self._name if self._name is not None else f'Controller_{self.id}'

    @name.setter
    def name(self, new_name):
        self._name = new_name

    def generate_name(self, nameset, init_n=2):
        """
        :param List[str] nameset: List of names which are illegal to use.
        :param int init_n: First n to start with. Could be anything, but prefer 'name', 'name_2' by default.
        """
        assert isinstance(init_n, int)
        cur_name = init_name = self.name
        while cur_name in nameset:
            cur_name = f"{init_name}_{init_n}"
            init_n += 1
        self.name = cur_name

    def add_connection(self, channel_n: int, module: NorthModule, module_axis: int):
        self.connections.add(ControllerConnection(self.id, channel_n, module, module_axis))

    def remove_all_module_connections(self, m_id_to_remove: int):
        new_connections = self._make_empty_connection_list()
        for connection in self.connections:
            if connection.module.id != m_id_to_remove:
                new_connections.add(connection)
        self.connections = new_connections

    def remove_connection(self, m_id: int, module_axis: int):
        idx_to_remove = None
        for i, c in enumerate(self.connections):
            if c.module.id == m_id and c.module_axis == module_axis:
                idx_to_remove = i
                break
        else:  # no break
            return
        del self.connections[i]

    def get_save_dict(self):
        """
        Generate a dictionary that serializes the class for saving in json file
        Note, connections, axis_map are not saved, as they are generated based on Module info at load-time
        :return: dictionary of class data
        """

        return {'id': self.id,
                'name': self.name,
                'address': self.address
                }


@dataclass
class ControllerConnection:
    """Data relating to a single channel's connection on a Controller"""
    controller_id: int
    channel: int
    module: NorthModule
    module_axis: int

    def __repr__(self):
        return f'module {self.module.name}, axis {self.module_axis} ==>' \
               f' controller {self.controller_id}, channel {self.channel}'

    def module_string(self):
        return f'{self.module.name} axis {self.module_axis}'

@dataclass
class Moveable:
    """Data for a single moveable"""
    # TODO: should this somehow link to its MoveableEventList?
    module_id: int  # ID of the module in which it populates
    moveable_res_id: str  # The resource ID for this moveable's type, e.g.: "vial_8ml.2021_03_20"
    transform: glm.mat4  # The transformation matrix of the initial position/rotation relative to the global origin


@dataclass
class CoordSys:
    name: str
    module: Optional[NorthModule]

    def get_offset(self):
        if self.module is None:
            return [0.0, 0.0, 0.0, 0.0]
        return [self.module.x, self.module.y, self.module.z, self.module.rotation]


class Project:
    CONTROLLERS = 'controllers'
    MODULES = 'modules'
    LOCATIONS = 'locations'
    SIM_INPUTS = 'sim_inputs'

    # module parameters that are mutable and may be specified as default by the resource
    # module_default_params = ['x', 'y', 'z', 'rot', 'moveable_res_id', 'moveable_name', 'fill_range']

    # module parameters that are copied from the resource and are immutable
    # module_shared_params = ['res_id', 'name', 'py_name', 'type', 'subtype', 'grid', 'tool', 'moveable_type', 'kinematics']

    def __init__(self, proj_dir: PathOrStr, new=False, res_paths=None):
        """
        :param proj_dir: The path to the project directory.
        :param bool new: Whether the project is new (created at path), or loaded from path.
        :param tuple res_paths: Resource paths outside the project directory which should be searched iff res_ids from
        project cannot be matched with resource in project dir.
        """
        res_paths = () if res_paths is None else res_paths
        assert isinstance(proj_dir, Path) or isinstance(proj_dir, str)
        assert isinstance(new, bool)
        assert isinstance(res_paths, tuple)
        try:
            self._dir = Path(proj_dir)
        except ValueError as e:
            logging.error(f'{self.__class__.__name__}.__init__(): '
                          f'"proj_dir" argument ({type(proj_dir)}) could not be converted to Path() object.')
            raise e
        self._auxiliary_res_paths = res_paths

        # todo: modules in form {m_id: module_dict, }, could easily be [module_dict,] since m_id in module_dict?
        #   alternatively: take m_id out of module_dict? same data should not live in two places.
        self._modules: Dict[int, AnyModule] = {}
        self._controllers: Dict[int, Controller] = {}
        self._moveables: List[Moveable] = []
        self._locations = {}
        self._sim_inputs = {}
        self._vision_cfgs = {}  # TODO better way to conceptualize vision configurations??
        self._vision_panes = {}

        self._sim_axis_lookup = {}  # a list of every ControllerConnection that needs simulating in the project
        self._n_sim_axes = 0

        self._csv_data = None
        self._csv_cols = None

        if new:
            # initialize the Project directory
            shutil.copyfile(get_default_proj_path(), self.nproj_file)
            make_file(self.locator_py)
            mkdir(self.res_dir)
            mkdir(self.modules_dir)
            mkdir(self.moveables_dir)
            self._load_from_dict(get_default_proj())
        else:
            self.load_from(self._dir)

    @property
    def name(self):
        return self.dir.stem

    @property
    def controllers(self) -> Tuple[Controller]:
        return tuple(self._controllers.values())

    @property
    def any_controllers(self):
        return len(self._controllers) > 0

    @property
    def modules(self) -> Tuple[AnyModule]:
        return tuple(self._modules.values())

    @property
    def modules_dict(self):
        return {m.id: m for m in self.modules}

    @property
    def poseables(self) -> Tuple[PosableModule]:
        return tuple(filter(lambda m: m.type == NorthResource.TYPE_POSEABLE, self.modules))

    @property
    def decks(self) -> Tuple[NorthModule]:
        return tuple(filter(lambda m: m.subtype == NorthResource.SUBTYPE_DECK, self.modules))

    @property
    def n9s(self) -> Tuple[PosableModule]:
        return tuple(filter(lambda m:m.subtype == NorthResource.SUBTYPE_N9, self.modules))

    @property
    def pumps(self) -> Tuple[PumpModule]:
        return tuple(filter(lambda m: m.subtype == NorthResource.SUBTYPE_PUMP, self.modules))

    @property
    def peri_pumps(self) -> Tuple[NorthModule]:
        return tuple(filter(lambda m: m.subtype == NorthResource.SUBTYPE_PERI_PUMP, self.modules))

    @property
    def moveables(self) -> Tuple[Moveable]:
        return tuple(self._moveables)

    @property
    def locations(self):  # TODO don't want to return dict (mutable), would prefer to return a tuple of locations
        return self._locations

    @locations.setter
    def locations(self, values):
        assert isinstance(values, dict)
        # TODO further validate values
        self._locations = values

    @property
    def sim_inputs(self):
        return self._sim_inputs

    @sim_inputs.setter
    def sim_inputs(self, values):
        assert isinstance(values, dict)
        # TODO further validate values
        self._sim_inputs = values

    @property
    def module_names(self) -> Tuple[str]:
        return tuple(map(lambda m: m.name, self.modules))

    @property
    def pump_names(self):
        return [p.name for p in self.pumps]

    @property
    def num_axes(self):
        return self._n_sim_axes

    @property
    def axis_lookup(self) -> Dict[int, Dict]:
        return self._sim_axis_lookup

    # directory properties #
    @property
    def dir(self):
        return self._dir

    @property
    def res_dir(self):
        return self.dir.joinpath('res')

    @property
    def modules_dir(self):
        return self.res_dir.joinpath('modules')

    @property
    def moveables_dir(self):
        return self.res_dir.joinpath('moveables')

    # file path properties #
    @property
    def nproj_file(self):
        return self.dir.joinpath(f'{self.name}.nproj')

    @property
    def main_py(self):
        return self.dir.joinpath(f'{self.name}.py')

    @property
    def locator_py(self):
        return self.dir.joinpath('Locator.py')

    @property
    def exp_log(self):
        return self.dir.joinpath('experiment_log.txt')

    @property
    def exp_csv(self):
        return self.dir.joinpath('experiment_data.csv')

    # TODO: Would like Project to be totally in charge of "available resources" and maintain 3 sets:
    #  project resources: Those found in the project directory (could be empty)
    #  builtin resources: Those found in the IDE folder (if running IDE, if not will be empty!!) so we also add...
    #  auxiliary resources: Those pointed to by the user. This is done at runtime as a param of Project, and allows us
    #                       to add a feature to IDE whereby users can "watch" a res folder (on their desktop / whatever)

    def get_save_dict(self) -> Dict[str, Any]:
        return {
            "controllers": [c.get_save_dict() for c in self.controllers],
            "modules": {m.id: m.get_save_dict() for m in self.modules},
            "locations": self.locations,
            "sim_inputs": self.sim_inputs,
            "visionconfigs": self._vision_cfgs,
            "visionpanes": self._vision_panes,
            "version": VERSION,
        }

    # File I/O #
    def reload(self):
        self.load_from(self.dir)

    def save(self):
        self.save_to(self.dir)

    def load_from(self, proj_dir: Union[str, Path], redirect_project=True):
        """
        :param proj_dir: The directory to load from. Should contain a same-name .nproj file.
        :param redirect_project: If True, will set Project._filepath to path. (see reload() and save())
        """
        try:
            proj_dir = Path(proj_dir)
        except ValueError:
            logging.error(f'{self.__class__.__name__}.load_from(): '
                          f'"proj_dir" argument ({type(proj_dir)}) could not be converted to Path() object.')
            return

        proj_filepath = proj_dir.joinpath(f'{proj_dir.stem}.nproj')
        try:
            with open(proj_filepath, 'r') as proj_file:
                try:
                    proj_dict = import_json_proj(proj_file)
                except LegacyProjectError:
                    proj_dict = import_legacy_proj(proj_file)
                    shell_print(f'"{self.name}" is a Legacy project, will be converted to modern format on next save.')
        except FileNotFoundError as e:
            shell_print(f'Could not open {proj_filepath}: File not found.')
            raise e

        self._load_from_dict(proj_dict)
        logging.info(f'Loaded project with {len(self._controllers)} controllers and {len(self._modules)} modules.')

        if redirect_project:
            self._dir = proj_dir

        self.refresh_axis_lookup()  # sync modules and controller axis assignments

    def _get_project_resources(self):
        return (self._get_resources_in_dir(self.modules_dir),
                self._get_resources_in_dir(self.moveables_dir))

    def _get_resources_in_dir(self, dir_path: PathOrStr):
        res_dict = {}
        dir_path = Path(dir_path)
        if dir_path.exists():
            _, dirs, _ = next(walk(dir_path))  # gets only the first result from walk() generator.
            for res_dir in map(lambda d: dir_path.joinpath(d), dirs):
                res_path = res_dir.joinpath(f'{res_dir.name}.nres')
                if not res_path.exists():
                    logging.error(f'{self.__class__.__name__}._get_project_resources(): '
                                  f'{res_dir} does not contain a file named {res_dir.name}.nres')
                    continue
                res = NorthResource(filepath=res_path)
                if res.id is None:  # TODO does this need to be here?
                    logging.error(f'NONE RESID FOR {res_dir.name}')
                res_dict[res.id] = res
        else:
            logging.error(f'{self.__class__.__name__}._get_resources_in_dir(): '
                          f'Received path {dir_path} which does not exist.')
        return res_dict

    def _load_from_dict(self, proj_dict: dict):
        # Fill-in missing project fields #
        for key in [self.CONTROLLERS, self.MODULES, self.LOCATIONS, self.SIM_INPUTS,
                    "version", "visionconfigs", "visionpanes"]:
            proj_dict.setdefault(key, get_default_values(key))

        # Get project resources #
        modules_res, moveables_res = self._get_project_resources()

        # Combines current project resources with auxiliary (probably built-in) resources
        # (preferring project resource paths in case of conflict)
        for res_dir in self._auxiliary_res_paths:
            aux_res = self._get_resources_in_dir(res_dir)
            if res_dir.stem == "modules" or res_dir.stem == "user":  # TODO hard-checking this doesn't seem right..
                modules_res = {**aux_res, **modules_res}
            else:
                assert res_dir.stem == "moveables"  # TODO
                moveables_res = {**aux_res, **moveables_res}

        # Load controllers #
        self._controllers = {c['id']: Controller(c['id'], c['name'], c['address']) for c in proj_dict[self.CONTROLLERS]}

        # Load modules #
        self._modules = {}
        for module_id, m_dict in proj_dict[self.MODULES].items():
            module_id_i = int(module_id)
            res_id = m_dict[NorthResource.RES_ID]
            if res_id not in modules_res:
                # TODO access built-in resources somehow..
                logging.error(f'{self.__class__.__name__}._load_from_dict(): '
                              f'/[project]/res/modules/ does not contain {res_id}, nor do auxiliary filepaths')
                continue
            res = modules_res[res_id]

            # Determine module type/subtype from resource #
            if res.type == NorthResource.TYPE_POSEABLE:
                m_type = PumpModule if res.subtype == NorthResource.SUBTYPE_PUMP else PosableModule
            else:  # static modules
                assert res.type == NorthResource.TYPE_STATIC
                m_type = RackModule if res.subtype == NorthResource.SUBTYPE_RACK else NorthModule

            # Loads module values from resource then over-writes defaults with mutable values in m_dict #
            module = m_type(module_id_i).load_from_res(res).load_from_dict(m_dict)
            if isinstance(module, RackModule):
                if RackModule.MOVEABLE_RES_ID in m_dict:
                    mv_res_id = m_dict[RackModule.MOVEABLE_RES_ID]
                elif RackModule.MOVEABLE_NAME in m_dict:
                    logging.warning(f'Out-of-date project moveable name key; will be replaced on save.')
                    mv_res_id = m_dict[RackModule.MOVEABLE_NAME]
                else:
                    logging.error(f'RackModule dict in project file is missing {RackModule.MOVEABLE_RES_ID} field.')
                    mv_res_id = 'NO_RES_ID'
                if mv_res_id is None:
                    pass  # None is a valid mv_res_id
                elif mv_res_id in moveables_res:
                    module.set_movable(moveables_res[mv_res_id])
                else:
                    logging.error(f'moveables_res dict does not contain the key "{mv_res_id}" ({type(mv_res_id)})')
                # logging.warning(f'mv_res ({type(mv_res)}) id {mv_res.id} name {mv_res.name}')
            self._modules[module_id_i] = module
        # end of modules loading #
        if proj_dict['version'] < 0.3:  # Add N9/Deck to out-of-date-project, but only if they are lacking one
            logging.warning(f"Out-of-date project file ({self.name}): adding deck and N9 by default.")
            n9_res = modules_res["n9.2023_04_17"]  # TODO hardcoded value..
            deck_res = modules_res["deck.2023_04_17"]  # TODO hardcoded value..
            if not any(filter(lambda m: m.res_id == n9_res.id, self._modules.values())):
                self.add_module(n9_res).enable()
            if not any(filter(lambda m: m.res_id == deck_res.id, self._modules.values())):
                self.add_module(deck_res).enable()

        # if not any(map(lambda m: m.subtype == NorthResource.SUBTYPE_DECK, self._modules)):
        #     deck_res = modules_res["deck.2023_04_17"]  # TODO hardcoded value..
        #     logging.warning(f"No deck in project file ({self.name}): adding one by default.")
        #     self.add_module(deck_res).enable()

        self._locations = proj_dict[self.LOCATIONS]
        # logging.warning(f'self._locations ({type(self._locations)}) {self._locations}')
        self._sim_inputs = proj_dict[self.SIM_INPUTS]
        # replace any legacy keys in the sim_inputs (should be str not int) TODO still necessary??
        # logging.warning(f'(PRE CHANNEL MATCH) self._sim_inputs ({type(self._sim_inputs)}) {self._sim_inputs}')
        for k in self._sim_inputs:
            try:
                channel_dict: dict = deepcopy(self._sim_inputs[k]['channels'])
                # iterate on local copy of 'channels' dict
                for i in channel_dict.keys():
                    if type(i) == int:
                        del self._sim_inputs[k]['channels'][i]  # delete the integer-keyed entry
                        self._sim_inputs[k]['channels'][str(i)] = channel_dict[i]  # add string-keyed entry
            except KeyError:
                continue
        # logging.warning(f'(POST CHANNEL MATCH) self._sim_inputs ({type(self._sim_inputs)}) {self._sim_inputs}')

        self._vision_cfgs = proj_dict['visionconfigs']
        self._vision_panes = proj_dict['visionpanes']

        self.update_moveables_list()

    def save_to(self, proj_dir: PathOrStr, redirect_project=False):
        """
        :param proj_dir: The path to save to.
        :param redirect_project: If True, will set Project._filepath to path. (see reload() and save())
        """
        self.refresh_axis_lookup()
        try:
            proj_dir = Path(proj_dir)
        except ValueError:
            logging.error(f'{self.__class__.__name__}.save_to(): '
                          f'"proj_dir" argument ({type(proj_dir)}) could not be converted to Path() object.')
            return
        save_dict = self.get_save_dict()
        # Check save_dict to ensure it's JSON serializable -before- we try writing it (avoids butchering .nproj files) #
        try:
            json.dumps(save_dict)
            can_save = True
        except (TypeError, OverflowError) as e:
            logging.warning(f'{self.__class__.__name__}.save_to(): Could not serialize Project, see exception below.')
            logging.exception(e)
            can_save = False
        if can_save:
            proj_filepath = proj_dir.joinpath(f'{proj_dir.stem}.nproj')
            with open(proj_filepath, 'w') as proj_file:
                json.dump(save_dict, proj_file, indent="  ")
        if redirect_project:
            self._dir = proj_dir

    # Collections management #
    def get_next_m_id(self):
        if len(self.modules) > 0:
            return max(map(lambda m: m.id, self.modules)) + 1
        else:
            return 1

    def get_next_c_id(self):
        if len(self.controllers) > 0:
            return max(map(lambda c: c.id, self.controllers)) + 1
        else:
            return 1

    def add_module(self, resource: NorthResource, m_id: Optional[int] = None) -> NorthModule:
        """
        :param NorthResource resource: The resource that the module should instantiate.
        :param m_id: The ID to give the new module. Will generate one if None.
        :return: The added module.
        """
        assert isinstance(resource, NorthResource)
        m_id = self.get_next_m_id() if m_id is None else m_id
        # TODO? also add the resource if it is not already in ProjectController.available_res
        assert isinstance(m_id, int)
        module = build_module_from_res(m_id, resource)
        assert isinstance(module, NorthModule) and module.initialized
        module.generate_name(self.module_names)
        module.disable()

        # By default attaches channels to the "first" controller...
        # TODO !! this is not obvious to the user and could result in controller mixups !!
        if self.any_controllers and module.any_channels:
            default_controller = self.controllers[0]
            for axis_n, channel in enumerate(module.channels):
                channel.controller_id = default_controller.id
                default_controller.add_connection(channel.channel_n, module, axis_n)
            self.refresh_axis_lookup(remake_connection_list=False)

        assert isinstance(module.id, int)
        self._modules[module.id] = module
        return module

    def has_module(self, m_id: int):
        assert isinstance(m_id, int)
        return m_id in self._modules

    def get_module(self, m_id: int):
        assert isinstance(m_id, int)
        try:
            return self._modules[m_id]
        except KeyError:
            return None

    def remove_module(self, m_id: int):
        assert isinstance(m_id, int)
        try:
            # unlink channels
            controllers_to_unlink = []
            if hasattr(self._modules[m_id], 'channels'):
                for channel in self._modules[m_id].channels:
                    # the key error will also be thrown if the controller id is not in _controllers dict
                    if channel.controller_id != None:
                        controllers_to_unlink.append(self._controllers[channel.controller_id])
            for c in controllers_to_unlink:
                c.remove_all_module_connections(m_id)
            del self._modules[m_id]
        except KeyError:  # doesn't exist anyhow, nothing to do
            logging.error(f"{self.__class__.__name__}.remove_module(): "
                          f"Tried to remove module {m_id} ({type(m_id)}) from project; either not present or contained a channel with a bad controller id.")

    def add_controller(self, c_id: Optional[int] = None):
        c_id = self.get_next_c_id() if c_id is None else c_id
        if c_id in self.controllers:
            logging.error(f"ID conflict when adding controller, {c_id} is already taken")
        addr = max([c.address for c in self.controllers]) + 1 if len(self.controllers) > 0 else 65
        controller = Controller(c_id, name="New_Controller", address=addr)
        controller.generate_name([c.name for c in self.controllers])
        self._controllers[c_id] = controller
        self.refresh_axis_lookup()

    def has_controller(self, c_id: int):
        return c_id in self._controllers

    def get_controller(self, c_id: int):
        assert isinstance(c_id, int)
        try:
            return self._controllers[c_id]
        except KeyError:
            return None

    def remove_controller(self, c_id: int):
        if not self.has_controller(c_id):
            logging.warning(f'Tried to remove controller with id {c_id}, which does not exist')
        del self._controllers[c_id]
        self.refresh_axis_lookup()

    def update_moveables_list(self):
        self._moveables: List[Moveable] = []
        for module in filter(lambda m: isinstance(m, RackModule), self.modules):
            if not module.enabled:
                continue
            if module.fill_range is None or module.fill_range == 'None':
                continue
            if module.movable_res is None:
                continue

            cos_r = math.cos(module.rotation)
            sin_r = math.sin(module.rotation)
            origin = module.grid['origin']
            x_n, y_n, z_n = module.grid['count']
            total_count = x_n * y_n * z_n
            pitch = module.grid['pitch']
            grid_indices = parse_range_str(module.fill_range)
            for i in grid_indices:
                if i < 0 or i >= total_count:
                    continue
                coord_i = (int(i / (y_n * z_n)), int((i % (y_n * z_n)) / z_n), i % z_n)
                pos = [origin[j] + pitch[j] * coord_i[j] for j in range(3)]
                x_ = pos[0] * cos_r - pos[1] * sin_r
                y_ = pos[0] * sin_r + pos[1] * cos_r
                pos[0] = x_
                pos[1] = y_
                pos = [module.position[j] + pos[j] for j in range(3)]
                self._moveables.append(Moveable(module_id=module.id,
                                                moveable_res_id=module.movable_id,
                                                transform=glm.rotate(glm.translate(glm.mat4(), glm.vec3(pos)),
                                                                     module.rotation,
                                                                     glm.vec3(0, 0, 1))
                                                )
                                       )

    def refresh_axis_lookup(self, remake_connection_list=True):
        if remake_connection_list:
            # reset controller connection lists
            for controller in self.controllers:
                controller.reset_connections_list()

            # rebuild controller connection lists based off of current module dict
            for module in self.modules:
                for axis, channel in enumerate(module.channels):
                    c_id: int = channel.controller_id
                    if self.has_controller(c_id) and channel is not None:
                        self._controllers[c_id].add_connection(channel.channel_n, module, axis)
                    else:
                        channel.controller_id = None
                        channel.channel_n = None

        axis_cnt = 0
        self._sim_axis_lookup = {}
        for c_id, controller in self._controllers.items():
            axis_map = {}
            for channel in {cxn.channel for cxn in controller.connections}:
                axis_map[channel] = axis_cnt
                axis_cnt += 1
            self._sim_axis_lookup[c_id] = axis_map
            controller.axis_map = axis_map
        self._n_sim_axes = axis_cnt

    # Vision config management
    def add_visioncfg(self):
        i = 0
        while str(i) in self._vision_cfgs:
            i = i + 1
        # got a unique id
        cfg_id = str(i)
        self._vision_cfgs[cfg_id] = {
            'filter': None,
            'settings': default_vision_settings()
        }
        return cfg_id

    def get_visioncfg(self, cfg_id):
        cfg_id = str(cfg_id)
        assert cfg_id in self._vision_cfgs
        cfg = self._vision_cfgs[cfg_id]
        assert 'filter' in cfg
        assert 'settings' in cfg
        return cfg

    def update_visioncfg(self, cfg_id, filter=None, settings=None):
        cfg_id = str(cfg_id)
        assert cfg_id in self._vision_cfgs
        if filter is not None:
            self._vision_cfgs[cfg_id]['filter'] = filter
        if isinstance(settings, dict):
            self._vision_cfgs[cfg_id]['settings'] = settings
        elif settings is not None:
            logging.warning(f'Project: Attempted to update_visioncfg with non-dict settings object ({type(settings)}.')

    def remove_visioncfg(self, cfg_id):
        cfg_id = str(cfg_id)
        assert cfg_id in self._vision_cfgs
        del self._vision_cfgs[cfg_id]

    # Vision pane management
    def add_visionpane(self, pane_id):
        pane_id = str(pane_id)
        self._vision_panes[pane_id] = {
            'src': None,
            'cfg': None
        }

    def get_visionpanes(self):
        return self._vision_panes

    def get_visionpane(self, pane_id):
        pane_id = str(pane_id)
        assert pane_id in self._vision_panes
        return self._vision_panes[pane_id]

    def update_visionpane(self, pane_id, src_id=None, cfg_id=None):
        pane_id = str(pane_id)
        assert pane_id in self._vision_panes
        if src_id is not None:
            self._vision_panes[pane_id]['src'] = src_id
        if cfg_id is not None:
            self._vision_panes[pane_id]['cfg'] = cfg_id

    def remove_visionpane(self, pane_id):
        pane_id = str(pane_id)
        assert pane_id in self._vision_panes

        # TODO messy, honestly panes <-> cfgs should be 1:1 probably
        # Remove unused cfgs #
        used_cfgs = [str(pane['cfg']) for pane in self._vision_panes.values()]
        unused_cfgs = list(filter(lambda id: id not in used_cfgs, self._vision_cfgs))
        for cfg in unused_cfgs:
            self.remove_visioncfg(cfg)

        del self._vision_panes[pane_id]

    def export_csv(self):
        # experiement log to csv
        # format
        DIR = 0
        TIME = 1
        ADDR = 2
        CMD = 3
        ARGS = 4

        def _parse_scale(args):
            neg = bool(args[0])
            pre_dec = int(args[1])
            post_dec = float(args[2])
            post_dec_len = int(args[3])
            for i in range(post_dec_len):
                post_dec /= 10
            weight = pre_dec + post_dec
            if neg:
                weight *= -1
            return weight

        try:
            with open(self.exp_log) as f:
                lines = [line.rstrip() for line in f]
        except FileNotFoundError:
            logging.warning(f'Could not export CSV: {self.exp_log} does not exist')
            return

        cmds = []
        # get list of cmds
        for line in lines:
            msg = line.split(' ')
            cmd = msg[CMD]
            if cmd not in cmds:
                cmds.append(cmd)

        self._csv_cols = ['time']

        col_names = {'time': 'time',
                     'TAG': 'tag',
                     'INFO': 'fw',
                     'RDSC': 'mass',
                     'BUFF': 'barcode',
                     'GETA': 'analog'}

        col_order = ['TAG', 'INFO', 'RDSC', 'BUFF', 'GETA']

        self._csv_cols += [col_names[c] for c in col_order if c in cmds]
        col_nums = {c: i for i, c in enumerate(self._csv_cols)}

        self._csv_data = [['0' for _ in self._csv_cols]]

        def _next_csv_row(t, n, d):
            self._csv_data.append([self._csv_data[-1][c] for c in range(len(self._csv_cols))])
            self._csv_data[-1][0] = str(t)
            self._csv_data[-1][n] = str(d)

        for line in lines:
            msg = line.split(' ')
            dir = msg[DIR]
            if dir != 'R':
                continue

            time = float(msg[TIME])
            addr = ord(msg[ADDR])
            cmd = msg[CMD]
            raw_args = msg[ARGS:]
            if cmd == 'BUFF':
                args = [''.join(raw_args)]
            else:
                args = [int(a) for a in raw_args]

            if cmd == 'INFO':
                _next_csv_row(time, col_nums[col_names['INFO']], args[0])
            elif cmd == 'RDSC':
                _next_csv_row(time, col_nums[col_names['RDSC']], _parse_scale(args[1:]))
            elif cmd == 'BUFF':
                _next_csv_row(time, col_nums[col_names['BUFF']], args[0])
            elif cmd == 'GETA':
                _next_csv_row(time, col_nums[col_names['GETA']], args[0])
            elif cmd == 'TAG':
                _next_csv_row(time, col_nums[col_names['TAG']], '_'.join([str(a) for a in args]))

        # write csv
        csv = open(self.exp_csv, 'w')
        csv.write(', '.join(self._csv_cols) + '\n')
        for line in self._csv_data:
            csv.write(', '.join(line) + '\n')
        csv.close()
