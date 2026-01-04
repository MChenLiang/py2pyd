#!/usr/bin/env python
# -*- coding:UTF-8 -*-

# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
name = "py_to_pyd"
version = "1.0.0"
description = """  '.py' 转为 '.pyd' 工具 """
author = "MCL"
license = """GNU General Public License v3.0"""


@early()
def pre_build_command():
    import os
    import stat
    import shutil
    from rez.packages import config as package_config
    import pathlib

    def remove_tree(path):
        def rm_readonly(func, path_, _):
            os.chmod(path_, stat.S_IWRITE)
            func(path_)

        shutil.rmtree(path, onerror=rm_readonly)

    #
    if not os.environ.get("is_init_build"):
        os.environ["is_init_build"] = "1"

        package_path = pathlib.Path(package_config.packages_path[0]) / str(this.name) / version
        if package_path.exists():
            remove_tree(str(package_path))
            print(f"👉remove tree : {package_path}")
        print("--------    " * 10)


@early()
def build_command():
    import os

    python_loc = os.getenv("python_loc", None)
    assert python_loc, KeyError(u"没有找到python安装路径")

    args = f" --python_loc {python_loc}"
    cmd = "rez_py {root}/rez_build.py " + args
    _command = f"{cmd}"

    package = os.environ.get("REZ_TOOLS_PACKAGES_PATH")
    path = os.environ.get("PATH")

    command = (f"$env:REZ_PACKAGES_PATH='{package}'"
               f"\n$env:PATH='{path}'"
               f"\n{_command}"
               )
    return command


def commands():
    root = this.root
    name = this.name

    upload_cos = f"{root}/{name}/py_to_pyd.exe"
    cmd = f'cmd /c {upload_cos}'

    alias("py2pyd", cmd)
