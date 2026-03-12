# 项目改造指南：适配 wv-cli 管理

本文档帮助你将现有的 pywebview + Vue 项目改造为 wv-cli 标准项目，以便使用 wv-cli 进行统一管理。

---

## 一、工具概述

**wv-cli** 是一个用于构建 **pywebview (Python后端) + Vue 3 (前端)** 桌面应用的脚手架工具。

核心命令：
- `wv run` - 开发模式（构建前端 + 启动 pywebview）
- `wv build` - 生产构建（PyInstaller 打包）
- `wv build --publish` - 构建 + 生成 Windows 安装包（Inno Setup）

---

## 二、标准项目结构

改造后的项目必须遵循以下目录结构：

```
my-app/
├── wv.toml              # 项目配置文件（必须）
├── .gitignore
├── icon/
│   ├── favicon.ico      # 应用图标
│   └── logo.png
├── frontend/            # Vue 3 前端项目
│   ├── src/
│   │   └── router/
│   │       └── index.ts/js   # 会被自动修复为 HashHistory
│   └── dist/            # 构建输出目录
├── backend/             # Python 后端
│   ├── .venv/           # uv 虚拟环境
│   ├── src/
│   │   ├── main.py      # pywebview 入口
│   │   ├── config.py    # 路径配置
│   │   └── bridge/
│   │       ├── __init__.py
│   │       └── api.py   # JS Bridge API 定义
│   └── tests/
└── build/
    ├── my-app.spec      # PyInstaller 配置
    ├── my-app.iss       # Inno Setup 配置
    └── publish/         # 安装包输出目录
```

---

## 三、关键改造要求

### 1. 必须创建 wv.toml

项目根目录必须包含 `wv.toml` 文件：

```toml
[project]
name = "项目名"
version = "1.0.0"
window_title = "窗口标题"
author = "作者名"

[build]
inno_setup_path = "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
```

### 2. 后端入口文件 (backend/src/main.py)

必须实现以下逻辑：

```python
import sys
import os
import webview
from config import WINDOW_TITLE, HTML_PATH_DEV, HTML_PATH_APP


def get_html_path() -> str:
    """根据运行环境返回正确的 HTML 路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包环境
        base = sys._MEIPASS
        return os.path.join(base, HTML_PATH_APP)
    else:
        # 开发环境
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, HTML_PATH_DEV)


def main():
    from bridge.api import Api
    api = Api()
    window = webview.create_window(
        WINDOW_TITLE,
        url=get_html_path(),
        js_api=api,
    )
    webview.start()


if __name__ == '__main__':
    main()
```

### 3. 后端配置文件 (backend/src/config.py)

```python
HTML_PATH_DEV = '../../frontend/dist/index.html'   # 开发模式
HTML_PATH_APP = '_f_dist/index.html'                # 打包模式
WINDOW_TITLE = "窗口标题"  # 从 wv.toml 读取
```

### 4. JS Bridge 规范 (backend/src/bridge/api.py)

所有暴露给前端的 Python API 必须定义在此文件中：

```python
class Api:
    """
    pywebview JS API 类
    前端通过 window.pywebview.api.<method>() 调用
    """
    
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"
    
    # 在此添加更多方法...
```

前端调用方式：
```javascript
const result = await window.pywebview.api.greet('World')
```

### 5. Vue Router 适配

- **必须**使用 `createWebHashHistory` 而非 `createWebHistory`
- wv-cli 会自动将 `createWebHistory` 替换为 `createWebHashHistory`（幂等操作）
- 这是为了确保 `file://` 协议下路由正常工作

### 6. PyInstaller 配置 (build/{project_name}.spec)

```python
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['../backend/src/main.py'],
    pathex=['../backend/src'],
    binaries=[],
    datas=[
        ('../frontend/dist', '_f_dist'),   # 关键：打包前端资源
        ('../icon', 'icon'),
    ],
    hiddenimports=['webview'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='项目名',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='../icon/favicon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='项目名',
)
```

### 7. Inno Setup 配置 (build/{project_name}.iss) - Windows 可选

```ini
[Setup]
AppName=项目名
AppVersion=1.0.0
DefaultDirName={autopf}\项目名
DefaultGroupName=项目名
OutputDir=publish
OutputBaseFilename=项目名-1.0.0-setup
SetupIconFile=../icon/favicon.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "../build/dist/项目名/*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\项目名"; Filename: "{app}\项目名.exe"
Name: "{commondesktop}\项目名"; Filename: "{app}\项目名.exe"

[Run]
Filename: "{app}\项目名.exe"; Description: "立即启动"; Flags: nowait postinstall skipifsilent
```

### 8. .gitignore 配置

根目录 `.gitignore`：
```
build/dist/
build/publish/
frontend/dist/
frontend/node_modules/
backend/.venv/
backend/__pycache__/
backend/**/__pycache__/
.DS_Store
Thumbs.db
.vscode/
.idea/
```

---

## 四、依赖管理

后端必须使用 `uv` 管理：
- 虚拟环境：`backend/.venv/`
- 必需依赖：`pywebview`, `pyinstaller`
- 运行方式：`uv run src/main.py`

---

## 五、改造检查清单

- [ ] 创建 `wv.toml` 配置文件
- [ ] 调整目录结构符合标准
- [ ] 重构后端入口文件 `main.py` 支持双模式路径
- [ ] 创建 `config.py` 配置文件
- [ ] 将 JS API 迁移到 `bridge/api.py`
- [ ] 确保 Vue Router 使用 HashHistory 模式
- [ ] 创建 PyInstaller spec 文件
- [ ] 创建 Inno Setup iss 文件（如需要安装包）
- [ ] 添加/更新 `.gitignore`
- [ ] 测试 `wv run` 开发模式
- [ ] 测试 `wv build` 生产构建

---

## 六、注意事项

1. **路径处理**：开发模式和打包模式的 HTML 路径不同，必须通过 `get_html_path()` 动态判断
2. **JS Bridge**：所有 Python→JS 的 API 必须通过 `Api` 类暴露，`js_api=api` 参数传入
3. **资源打包**：前端构建输出 `frontend/dist` 在打包时会被复制到 `_f_dist`
4. **图标注入**：构建时会自动将 `icon/favicon.ico` 注入到 `frontend/dist` 中
5. **幂等修复**：`wv run` 和 `wv build` 会自动修复 Vue Router，多次运行无副作用
