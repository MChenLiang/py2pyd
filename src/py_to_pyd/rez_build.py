#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
import os
import subprocess
import pathlib
import shutil
import stat
import fire


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
class FileAlreadyExistError(Exception):
    """When the file already exist."""
    pass


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
class Builder(object):
    def __init__(self):
        self.build_path = os.environ["REZ_BUILD_PATH"]
        self.install_path = os.environ["REZ_BUILD_INSTALL_PATH"]
        self.name = os.environ["REZ_BUILD_PROJECT_NAME"]
        self.version = os.environ["REZ_BUILD_PROJECT_VERSION"]
        self.source_path = os.environ["REZ_BUILD_SOURCE_PATH"]
        self.variant_index = os.environ["REZ_BUILD_VARIANT_INDEX"]
        self.workspace = os.path.join(self.build_path, "workspace")
        self.user_package = os.environ["REZ_USED_PACKAGES_PATH"].split(";")[0]
        self.package_name = os.environ["REZ_BUILD_PROJECT_NAME"]

    def build(self, python_loc):
        """Build rez package."""

        workspace = pathlib.Path(self.workspace) / self.name
        workspace.exists() and self.remove_tree(str(workspace))
        workspace.mkdir(exist_ok=True, parents=True)

        # 打包exe到workspace
        build_to_exe = self.to_exe(python_loc, workspace)

        # 如果是install，进行安装
        self.install()

        # 备份
        self.backup()

    def to_exe(self, python_loc, workspace):
        exe_name = self.package_name
        output_dir = workspace
        py_folder = pathlib.Path(python_loc)
        nuitka = py_folder.joinpath("Scripts", "nuitka.cmd")

        packages = [
            "fire", "chardet"
        ]
        packages_all = ",".join(packages)

        curr_folder = pathlib.Path(self.source_path)
        exe_path = curr_folder / f"{exe_name}.py"
        icon = curr_folder / "icons" / "球球验证系统.ico"

        cmd = (f"{nuitka}"
               # f" --disable-console"  # 是否显示窗口: 如果有print的显示信息，就把这个打开吧
               f" --mingw64"  # 使用**编译
               f" --standalone"  # 脱离单独可执行环境
               f" --show-memory"
               f" --show-progress"
               f" --output-dir={output_dir}"  # 输出路径
               f" --include-package={packages_all}"
               f" --onefile"  # 打包成单个文件
               f" --output-filename={exe_name}"  # 打包成单个文件
               f" --onefile-tempdir={'{TEMP}'}/{exe_name}"  # 单文件解压位置
               f" --nofollow-imports"
               f" --windows-icon-from-ico={icon}"  # 图标
               f" --windows-company-name=知识面过窄（北京）科技有限公司"  # 
               f" --windows-product-name={self.package_name}"  # 
               f" --windows-product-version={self.version}"  # 
               f" {exe_path}")
        subprocess.run(cmd, shell=True, check=True)

        # delete process
        for each in output_dir.iterdir():
            if each.is_dir():
                self.remove_tree(each)

        exe_path = output_dir / f"{exe_name}.exe"

        return exe_path

    def install(self):
        """Copy files from work directory to self.install_path."""
        if os.environ.get("REZ_BUILD_INSTALL") != "1":
            return
        if os.path.exists(self.install_path):
            self.remove_tree(self.install_path)
        workspace = pathlib.Path(self.workspace) / self.name
        install_path = pathlib.Path(self.install_path) / self.name
        shutil.copytree(workspace, install_path, symlinks=True)
        self.remove_tree(self.workspace)

    def backup(self):
        source_path = pathlib.Path(self.source_path)
        # 这里不要放到rez包里，会影响启动
        target = pathlib.Path(self.install_path.replace("packages", "source")) / self.name
        target.exists() and self.remove_tree(str(target))
        shutil.copytree(source_path, target, symlinks=True, dirs_exist_ok=True)

    @staticmethod
    def remove_tree(path):
        """Remove directory.

        Args:
            path (str): The directory to remove.
        """

        def rm_readonly(func, path_, _):
            """Remove read-only files on Windows.

            Reference from https://stackoverflow.com/questions/1889597 and
            https://github.com/ansible/ansible/issues/34335

            Args:
                func (function): Function which will remove the file/folder.
                path_ (str): Path to file/folder which should be removed.
                _: ignore.
            """
            os.chmod(path_, stat.S_IWRITE)
            func(path_)

        shutil.rmtree(path, onerror=rm_readonly)


if __name__ in ("__main__", "__builtin__"):
    func = Builder()
    fire.Fire(func.build)
