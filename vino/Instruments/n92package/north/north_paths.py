import inspect
import shutil
import os

from pathlib import Path


def get_base_path() -> Path:
    return Path(inspect.stack()[0][1]).parents[3]  # \NorthIDE\


def get_user_data_path() -> Path:
    return get_base_path().joinpath('user_data')


def get_northIDE_pkg_path() -> Path:
    return get_base_path().joinpath('Lib\\site-packages\\northIDE')


def get_base_res_path() -> Path:
    return get_northIDE_pkg_path().joinpath('res')


def get_default_proj_path() -> Path:
    return get_northIDE_pkg_path().joinpath('default_proj.nproj')


def get_north_res_path() -> Path:
    return get_base_res_path().joinpath('north')


def get_user_res_path() -> Path:
    return get_base_res_path().joinpath('user')


def get_fonts_path() -> Path:
    return get_north_res_path().joinpath('fonts')


def get_north_modules_path() -> Path:
    return get_north_res_path().joinpath('modules')


def get_n9_path() -> Path:
    return get_north_modules_path().joinpath('n9')


def get_pump_path() -> Path:
    return get_north_modules_path().joinpath('pump')


def get_north_moveables_path() -> Path:
    return get_north_res_path().joinpath('moveables')


def get_proj_res_path() -> Path:
    from northIDE import MVC
    return Path(MVC.project().current_proj.res_dir)


def get_proj_modules_path() -> Path:
    from northIDE import MVC
    return Path(MVC.project().current_proj.modules_dir)


def get_proj_moveables_path() -> Path:
    from northIDE import MVC
    return Path(MVC.project().current_proj.moveables_dir)


def copy_resource(res_path: Path, dest: Path):
    # ensure that the source files actually exist
    if not res_path.is_dir():
        raise FileNotFoundError(f'"{res_path}" does not exist.')
    shutil.copytree(res_path, dest)

    # copy source files to destination (do not overwrite if exists)
    # if not destination.is_file():
    #     shutil.copyfile(obj_src_fp, obj_dst_fp)
    # if not mtl_dst_fp.is_file():
    #     shutil.copyfile(mtl_src_fp, mtl_dst_fp)


def delete_resource(res_path: Path, project_dir: Path):
    if not res_path.is_dir():
        return

    # don't delete something outside project path
    if os.path.abspath(project_dir) != os.path.commonpath([res_path, project_dir]):
        raise RuntimeError(
            "Project error: Attempted to delete directory " + str(res_path) + "that is not in project path")

    # raise RuntimeError(project_dir.name, list(res_path.parents)) if project_dir.name not in res_path.parents: raise
    # RuntimeError("Project error: Attempted to delete directory " + str(res_path) + "that is not in project path")

    # raise RuntimeError("deleting" + str(res_path))
    shutil.rmtree(res_path)
