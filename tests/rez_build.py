#!/usr/bin/env python
# -*- coding:UTF-8 -*-

# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
import os
import pathlib
import random
import shutil
import stat
import subprocess
import tempfile
import locale
import re
import fire

from rez.packages import get_latest_package


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
class FileAlreadyExistError(Exception):
    """When the file already exist."""
    pass


def random_chars(count=8):
    characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
    choose = random.choice
    letters = [choose(characters) for dummy in range(count)]
    return ''.join(letters)


def _get_temp(filename):
    # 获取系统的临时文件夹路径
    temp_folder = pathlib.Path(tempfile.gettempdir()) / random_chars() / filename
    return temp_folder


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

        # 使用re匹配模式
        self.remove_files_patterns = [
            r"^package\.py$",
            r"^.*build\.py$",
            r"^auto_pep8\.py$",
            r"^ui_body_builder_backup\.py$",
            r"^builder\.py$",
            r".*backup\.py$"  # 匹配所有以backup.py结尾的文件

        ]

        self.remove_folders_patterns = [
            r"^build$",
            r"^other$",
            r"^__pycache__$",
            r"^file$",
            r"^tmp$",
            r"^config_zip$",
            r"^fix$",
            r"^icons_del$",
            r"^Texture$",
            r"^delete$",
            r"^del$"
        ]

        self.copy_folders_patterns = [
            r"^exe$",
            r"^site-packages$",
            r"^third-party$",
            r"^plug-ins$",
            r"^icons$",
        ]

        self.copy_files_patterns = [
            r"^__init__\.py$",
            r"^script_tool\.py$",
            r"^additional_assemble_script\.py$",
            r"^resources\.py$",
        ]

        self.maya_conf_version = ["plug-ins", "site-packages"]

        # 预编译正则表达式以提高性能
        self.remove_files_regex = [re.compile(pattern) for pattern in self.remove_files_patterns]
        self.remove_folders_regex = [re.compile(pattern) for pattern in self.remove_folders_patterns]
        self.copy_folders_regex = [re.compile(pattern) for pattern in self.copy_folders_patterns]
        self.copy_files_regex = [re.compile(pattern) for pattern in self.copy_files_patterns]

    def _match_pattern(self, name, patterns):
        """检查名称是否匹配任一正则表达式模式"""
        for pattern in patterns:
            if pattern.search(name):
                return True
        return False

    def to_pyd(self, python_loc=""):
        """
        将需要编译的py文件编译到workspace
        """
        source_files = []
        source = pathlib.Path(self.source_path)

        # 遍历源目录
        for folder in source.rglob("**"):
            if not folder.is_dir():
                continue

            relative = folder.relative_to(source)

            # 检查文件夹路径中的任何部分是否匹配移除模式
            should_skip = False
            for part in relative.parts:
                if self._match_pattern(part, self.remove_folders_regex):
                    should_skip = True
                    break

            if should_skip:
                continue

            # 检查是否是复制文件夹（如果是，则跳过处理其中的.py文件）
            is_copy_folder = False
            for part in relative.parts:
                if self._match_pattern(part, self.copy_folders_regex):
                    is_copy_folder = True
                    break

            for file in folder.iterdir():
                if file.is_dir():
                    continue

                filename, suffix = file.name, file.suffix
                if suffix != ".py":
                    continue

                # 检查是否需要移除
                if self._match_pattern(filename, self.remove_files_regex):
                    continue

                # 检查是否需要复制（特殊处理）
                if self._match_pattern(filename, self.copy_files_regex):
                    continue

                # 如果所在文件夹是需要复制的文件夹，也跳过
                if is_copy_folder:
                    continue

                source_files.append(file.relative_to(source))

        # 创建目标文件夹并复制文件
        # 假设 _get_temp 函数已定义
        dst = _get_temp(self.name)
        for each in source_files:
            src, tgt = source / each, dst / each
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(src), str(tgt))

        # 转为pyd
        workspace = pathlib.Path(self.workspace)
        workspace.mkdir(exist_ok=True, parents=True)
        if python_loc:
            package = get_latest_package("py_to_pyd")
            assert package, RuntimeError("没有找到包体：｛py_to_pyd｝")

            cmd_str = (
                f" rez-env {package.name} -- py2pyd"
                f" \"{python_loc}\""
                f" \"{dst}\""
                f" \"{workspace}\""
            ).replace("\\", "/")

            try:
                result = subprocess.run(
                    cmd_str,
                    shell=True,
                    check=True,
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
                print(e)
                raise e
        else:
            shutil.copytree(dst, workspace, symlinks=True)

    def build_py_file(self):
        """构建过程：匹配拷贝列表的优先处理，默认情况也拷贝"""

        # 存储结果
        files_to_copy = set()
        folders_to_copy = set()
        excluded_paths = set()

        def _should_exclude_file(filename):
            """判断单个文件是否应该被排除"""
            return self._match_pattern(filename, self.remove_files_regex)

        def _should_exclude_folder(foldername):
            """判断文件夹是否应该被排除"""
            return self._match_pattern(foldername, self.remove_folders_regex)

        def _is_in_excluded_directory(path):
            """检查路径是否在已排除的目录中"""
            path_str = str(path)
            for excluded in excluded_paths:
                if path_str.startswith(excluded):
                    return True
            return False

        source = pathlib.Path(self.source_path)

        # 使用栈进行深度优先遍历
        stack = [(source, source)]

        while stack:
            current_path, rel_path = stack.pop()

            # 如果是文件夹
            if current_path.is_dir():
                folder_name = rel_path.name

                # 检查是否应该排除这个文件夹
                if self._match_pattern(folder_name, self.remove_folders_regex):
                    excluded_paths.add(str(rel_path))
                    # 排除文件夹：跳过所有子内容，不递归遍历
                    continue

                # 检查是否在已排除的目录中
                if _is_in_excluded_directory(str(rel_path)):
                    continue

                # 检查是否匹配拷贝文件夹模式
                if self._match_pattern(folder_name, self.copy_folders_regex):
                    folders_to_copy.add(rel_path)
                    # 不继续遍历，整个文件夹会特殊处理
                    continue
                else:
                    # 默认情况：拷贝文件夹
                    folders_to_copy.add(rel_path)

                try:
                    for item in current_path.iterdir():
                        stack.append((item, rel_path / item.name))
                except (PermissionError, OSError):
                    continue
            else:
                # 处理文件
                file_name = rel_path.name
                file_suffix = rel_path.suffix
                # 检查是否在已排除的目录中
                if _is_in_excluded_directory(str(rel_path.parent)):
                    continue

                # 检查是否应该排除这个文件
                if _should_exclude_file(file_name):
                    continue

                # 检查是否匹配拷贝文件模式
                if self._match_pattern(file_name, self.copy_files_regex):
                    files_to_copy.add(rel_path)
                elif file_suffix.startswith(".py"):
                    continue
                elif file_suffix == ".ui":
                    continue
                else:
                    # 默认情况：也拷贝文件
                    files_to_copy.add(rel_path)

        # 创建目标目录
        dst = pathlib.Path(self.workspace) / self.name
        dst.mkdir(parents=True, exist_ok=True)

        # 拷贝所有文件（包括明确匹配的和默认的）
        for f in files_to_copy:
            t = dst / f.relative_to(source)
            t.parent.mkdir(exist_ok=True, parents=True)
            try:
                shutil.copy2(f, t)  # 使用copy2保留元数据
            except (OSError, IOError) as e:
                print(f"Warning: Failed to copy {f}: {e}")

        # 处理文件夹
        maya_ver = os.environ.get("REZ_MAYA_VERSION", "")

        for f_folder in folders_to_copy:
            if f_folder == source:  # 跳过根目录本身
                continue

            t_folder = dst / f_folder.relative_to(source)

            # 如果目标文件夹已存在，跳过（避免重复创建）
            if t_folder.exists():
                continue

            stem = f_folder.stem

            # 检查是否为需要特殊处理的maya配置文件夹
            if stem in self.maya_conf_version and maya_ver:
                # 创建目标文件夹
                t_folder.mkdir(parents=True, exist_ok=True)

                # 只拷贝对应maya版本的子文件夹
                for nf in f_folder.iterdir():
                    if nf.is_dir():
                        nf_stem = nf.stem
                        if nf_stem.startswith("maya"):
                            if nf_stem == f"maya{maya_ver}":
                                try:
                                    shutil.copytree(nf, t_folder / nf_stem, symlinks=True)
                                except (OSError, IOError) as e:
                                    print(f"Warning: Failed to copy {nf}: {e}")
                        else:
                            # 非maya开头的文件夹，直接拷贝
                            try:
                                shutil.copytree(nf, t_folder / nf_stem, symlinks=True)
                            except (OSError, IOError) as e:
                                print(f"Warning: Failed to copy {nf}: {e}")
            else:
                # 普通文件夹，直接拷贝（包括明确匹配的和默认的）
                try:
                    # 检查是否匹配拷贝文件夹模式
                    if self._match_pattern(f_folder.name, self.copy_folders_regex):
                        # 明确匹配的文件夹，完整拷贝
                        shutil.copytree(f_folder, t_folder, symlinks=True, dirs_exist_ok=True)
                    else:
                        # 默认的文件夹，也拷贝
                        shutil.copytree(f_folder, t_folder, symlinks=True, dirs_exist_ok=True)
                except (OSError, IOError) as e:
                    print(f"Warning: Failed to copy folder {f_folder}: {e}")

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

    def build(self, python_loc=""):
        """
        Build rez package.
        Args:
            python_loc:
        Returns:

        """
        maya_ver = os.environ["REZ_MAYA_VERSION"]
        if python_loc:
            python_loc = f"{python_loc}/Maya{maya_ver}/bin/mayapy.exe"
        # 封装pyd到workspace
        self.to_pyd(python_loc)
        # 拷贝文件到workspace
        self.build_py_file()
        # 安装
        self.install()
        # 备份
        self.backup()

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


if __name__ == "__main__":
    func = Builder()
    fire.Fire(func.build)
