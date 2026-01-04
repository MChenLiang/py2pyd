# <center>py to pyd </center>

这是一个可以将 `.py` 转为 `.pyd` 的工具。

## 安装

- 方法一

这是一个 `rez` 可以直接拷贝到你项目的 package 中。

- 方法二

可以直接使用 `release` 文件夹里打包好的 [`py_to_pyd.exe`](release/py_to_pyd/1.0.0/py_to_pyd/py_to_pyd.exe) 。

## 使用
- 必要的条件：
> `py.exe` 必须要安装 `cython`

### 传入参数详解：

```text
py_to_pyd.exe -h
INFO: Showing help with the command 'py_to_pyd.exe -- --help'.

NAME
    py_to_pyd.exe

SYNOPSIS
    py_to_pyd.exe COMMAND | PY_EXE SRC TAG

POSITIONAL ARGUMENTS
    PY_EXE
    SRC
    TAG

COMMANDS
    COMMAND is one of the following:

     clone

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```

| TOML type | Python type | Details                              |
|-----------|-------------|--------------------------------------|
| --help    |             | 显示使用帮助                               |
| --PY_EXE  | `str`       | py执行程序。例如： mayapy.exe、hython.exe ... |
| --SRC     | `str`       | 源码文件路径                               |
| --TAG     | `str`       | 打包到什么位置                              |

### cmd中直接调用

```shell
py_to_pyd.exe mayapy.exe source target

```

### python中调用

```python
import locale
import subprocess

python_loc = "hython.exe"
source = ""
target = ""

cmd_str = (
    f" cmd /c py_to_pyd.exe"
    f" \"{python_loc}\""
    f" \"{source}\""
    f" \"{target}\""
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
```

### rez中使用

这是推荐的使用方法，更详细的使用案例请查看：[rez_build.py](tests/rez_build.py)

```shell
rez-env py_tp_pyd -- py2pyd hython.exe source target
```






