#!/usr/bin/env python
# -*- coding:UTF-8 -*-

# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
# from __future__ import unicode_literals

# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
import fire
import os
import re
import sys
import gc
import linecache
import shutil
import pathlib
import tempfile
import random
import subprocess

write_kwargs = {}
__PY_3__ = sys.version_info.major > 2
if __PY_3__:
    write_kwargs.update({"encoding": "UTF-8"})
    from subprocess import DEVNULL  # Python 3
else:
    DEVNULL = open(os.devnull, 'wb')  # Python 2


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
class FileAlreadyExistError(Exception):
    """When the file already exist."""
    pass


def random_chars(count=8):
    """
    获取随机字符串
    Args:
        count:

    Returns:

    """
    characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
    choose = random.choice
    letters = [choose(characters) for dummy in range(count)]
    return ''.join(letters)


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
class PyToPyd(object):
    def __init__(self, py_exe, source_folder, release_folder):

        rm_paths = ["", " ", "~", "."]
        if source_folder in rm_paths:
            return
        if release_folder in rm_paths:
            return

        self._py_exe_ = py_exe
        self._source_folder_ = pathlib.Path(source_folder)
        self._release_folder_ = pathlib.Path(release_folder)

    def run(self):
        py_exe = self._py_exe_
        source_folder = self._source_folder_
        release_folder = self._release_folder_ / source_folder.stem

        next_folder_p = pathlib.Path(tempfile.gettempdir()) / random_chars()
        next_folder = next_folder_p / source_folder.stem

        self.copy_tree(source_folder, next_folder)
        to_pyd_fs, copy_fs, using_numpy = self.edit_file(next_folder)

        # write setup
        setup_to_pyd = "#!/usr/bin/env python\n"
        setup_to_pyd += "# -*- coding:UTF-8 -*-\n"
        if using_numpy:
            setup_to_pyd += "import numpy as np\n"
        setup_to_pyd += "import setuptools \n"  # 这一句会自动查找vs版本
        setup_to_pyd += "from distutils.core import setup\n"
        setup_to_pyd += "from Cython.Build import cythonize\n"
        setup_to_pyd += "from distutils.extension import Extension\n"
        setup_to_pyd += "extensions = ["

        extend = list()
        for f in to_pyd_fs:
            relative = f.relative_to(next_folder_p)
            relative_path = str(relative.parent / relative.stem).replace("\\", "/").replace("/", ".")
            ext = "Extension(\"%s\", [\"%s\"])" % (relative_path, str(f).replace("\\", "/"))
            extend.append(ext)
        exts_txt = ', '.join(extend)

        setup_to_pyd += exts_txt
        setup_to_pyd += "]\n"
        setup_to_pyd += ("setup(ext_modules=cythonize(extensions, compiler_directives="
                         "{\"language_level\": 2})")
        if using_numpy:
            setup_to_pyd += ", include_dirs=[np.get_include()],"
        setup_to_pyd += ")"

        # 写setupToPyd.py文件
        setup_f = next_folder_p / "setupToPyd.py"
        with open(str(setup_f), "w", **write_kwargs) as f:
            f.write(setup_to_pyd)

        bat_file_path = next_folder_p / "start.bat"

        os_env = os.environ.copy()
        path = os_env.get("PATH").split(";")
        path = ";".join([p for p in path if not any(['REZ' in part.upper() for part in pathlib.Path(p).parts])])

        pypath = os_env.get("PYTHONPATH").split(";")
        pypath = ";".join([p for p in pypath if not any(['REZ' in part.upper() for part in pathlib.Path(p).parts])])

        with open(str(bat_file_path), 'w', **write_kwargs) as f:
            f.write("@echo off\n")
            f.write("set PATH={}\n".format(path))
            f.write("set PYTHONPATH={}\n".format(pypath))
            f.write('cd /d "{}"\n'.format(next_folder_p))
            f.write('"{}" {} build_ext --inplace\n'.format(py_exe, setup_f))
            f.write('exit %errorlevel%\n')

        os.chdir(next_folder_p)

        print(f"批处理文件: {bat_file_path}")
        process = subprocess.Popen(
            "cmd /c {}".format(bat_file_path),
            cwd=str(next_folder_p),
            stdin=DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # 实时读取输出
        print("\n开始读取输出:")
        stdout_lines = []
        stderr_lines = []

        # 读取标准输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output = output.strip()
                print(output)
                stdout_lines.append(output)

        # 读取标准错误
        while True:
            error = process.stderr.readline()
            if error == '' and process.poll() is not None:
                break
            if error:
                error = error.strip()
                print(f"错误: {error}")
                stderr_lines.append(error)

        # 等待进程结束
        returncode = process.wait()

        if returncode:
            # 获取剩余的输出
            stdout, stderr = process.communicate()
            if stdout:
                stdout_lines.append(stdout.strip())
            if stderr:
                stderr_lines.append(stderr.strip())

            print(f"\nCommand '{bat_file_path}' returned with exit status {returncode}")
            print("Standard output:")
            for line in stdout_lines:
                print(f"  {line}")

            print("\nStandard error:")
            for line in stderr_lines:
                print(f"  {line}")

            raise RuntimeError("执行失败")

        del process

        dst = next_folder
        for f in copy_fs:
            t = dst / f.relative_to(source_folder)
            t.parent.mkdir(exist_ok=True, parents=True)
            shutil.copyfile(f, t)


        for f in to_pyd_fs:
            c = f.parent / "{}.c".format(f.stem)
            pyc = f.parent / "{}.pyc".format(f.stem)

            c.exists() and c.unlink()
            pyc.exists() and pyc.unlink()
            f.exists() and f.unlink()

        # to release
        release_folder.mkdir(exist_ok=True, parents=True)
        self.copy_tree(next_folder, release_folder)

        shutil.rmtree(next_folder_p, ignore_errors=True)
        print("👍Great!")
        return True

    def _get_lines(self, py_f):
        try:
            lines = linecache.getlines(py_f)
            linecache.clearcache()
        except:
            with open(str(py_f), mode="rb") as f:
                lines = f.readlines()

        return lines

    def edit_file(self, folder):
        patten = re.compile(r"import (?:maya|pymel|hou|nuke|unreal)\.\w+ as \w+")
        release = folder
        using_np = False
        rm_file = ["__init__", "Qt"]
        copy_fs = []

        files = (f for f in release.rglob("**/*") if f.is_file() and f.suffix in [".py", ".pyx"])
        to_pyd_fs = []
        for f in files:
            stem = f.stem
            if stem not in rm_file:
                to_pyd_fs.append(f)
            else:
                copy_fs.append(f)

        for f in to_pyd_fs:

            py_f = str(f)
            lines = self._get_lines(py_f)

            f_txt = ''
            for each in lines:
                each = str(each)
                if each.startswith("import numpy"):
                    using_np = True
                if each.startswith("from __future__ import "):
                    f_txt += "#%s" % each
                match = patten.match(each)
                if not match:
                    f_txt += each
                    continue
                spl = match.group().split(' ')
                module, file_name = spl[1].split('.')
                out_txt = 'from {} import {} as {}\n'.format(module, file_name, spl[-1])
                f_txt += out_txt

            with open(str(py_f), 'w', **write_kwargs) as _f:
                _f.write(f_txt)

            del lines
            gc.collect()

        return to_pyd_fs, copy_fs, using_np

    def copy_tree(self, source, workspace):
        print(f"👉Copy tree: {source} --> {workspace}")
        shutil.copytree(source, workspace, dirs_exist_ok=True, symlinks=True)


def run(py_exe, src, tag):
    func = PyToPyd(py_exe, src, tag)
    return func.run()


if __name__ == "__main__":
    fire.Fire(run)
    sys.exit(0)
