# -*- coding: utf-8 -*-

name = 'py_to_pyd'

version = '1.0.0'

description = "'.py' 转为 '.pyd' 工具"

def commands():
    root = this.root
    name = this.name
    
    upload_cos = f"{root}/{name}/py_to_pyd.exe"
    cmd = f'cmd /c {upload_cos}'
    
    alias("py2pyd", cmd)

timestamp = 1767553183

license = 'GNU General Public License v3.0'

author = 'MCL'

format_version = 2
