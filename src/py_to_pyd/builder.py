#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
from rez.packages import get_latest_package
from rez.serialise import load_from_file, FileFormat
import os
import sys
import subprocess
import pathlib
import locale


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
def get_name_and_version():
    data = load_from_file(f"{pathlib.Path(__file__).parent}/package.py", FileFormat.py)
    name = data.get("name")
    version = data.get("version")
    return name, version


def main():
    curr_folder = pathlib.Path(__file__).parent
    root_folder = pathlib.Path(__file__).parents[2].absolute()
    tools_package = str(root_folder / "packages").replace("\\", "/")
    pip_package = str(root_folder / "pip_packages").replace("\\", "/")
    # 设置环境变量
    os.environ['REZ_TOOLS_PACKAGES_PATH'] = tools_package
    os.environ['REZ_PIP_PACKAGES_PATH'] = pip_package
    os.environ['REZ_PACKAGES_PATH'] = ";".join([tools_package, pip_package])

    # 添加rez到环境变量
    pkg_rez = get_latest_package("rez")
    rez_folder = pathlib.Path(pkg_rez.uri).parent / pkg_rez.name
    rez_cmd_folder = str(rez_folder / "Scripts" / "rez")
    os.environ['PATH'] = f'{rez_folder};{rez_cmd_folder};' + os.environ.get('PATH', '')

    # 设置python_loc
    os.environ["python_loc"] = f'"{os.path.dirname(sys.executable)}"'

    # 切换到脚本所在目录
    os.chdir(str(curr_folder))

    # 运行rez-build命令
    cmd_build = ['rez-build', '-ci', '--prefix', tools_package, "--fail-graph"]
    print(" ".join(cmd_build))
    try:
        result = subprocess.run(
            cmd_build,
            check=True,
            env=os.environ,  # 显式传递当前环境变量给子进程
            encoding=locale.getpreferredencoding()
        )
        print("Command executed successfully.")
        print("Output:")
        print(result.stdout)
    except FileNotFoundError:
        print("Error: 'rez-build' command not found.")
    except subprocess.CalledProcessError as e:
        print("Error during rez-build execution:")
        print(f"Return code: {e.returncode}")
        print("Stderr:")
        print(e.stderr)
        raise e


if __name__ == '__main__':
    main()
