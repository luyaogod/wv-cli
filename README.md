# wv-cli

A command-line scaffold tool for building **pywebview (Python backend) + Vue 3 (frontend)** desktop apps.

## Requirements

- Python ≥ 3.9
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Node.js / npm](https://nodejs.org) — for the Vue 3 frontend
- [Inno Setup 6](https://jrsoftware.org/isdl.php) *(Windows only, required for `--publish`)*

## Installation

```bash
pip install wv-cli
```

Or install from source with `uv`:

```bash
git clone https://github.com/yourname/wv-cli
cd wv-cli
uv pip install -e .
```

## Quick Start

### Create a new project

```bash
# Interactive — creates ./my-app/
wv create

# In the current directory
wv create .

# Explicit directory
wv create path/to/my-app
```

You will be prompted for:
| Prompt | Default |
|---|---|
| 项目名称 (project name) | directory name |
| 窗口标题 (window title) | project name |
| 版本号 (version) | `1.0.0` |
| 作者 (author) | *(empty)* |

After answering, the CLI will:
1. Scaffold the full directory structure
2. Run `npm create vue@latest` for the frontend (you drive the Vue prompts)
3. Run `uv init / venv / add pywebview pyinstaller` for the backend

### Run in development mode

```bash
cd my-app
wv run
```

Builds the Vue frontend, then launches the pywebview window loading `frontend/dist`.

### Production build

```bash
wv build
```

Builds the frontend and runs PyInstaller to produce `build/dist/<project-name>/`.

### Build + Windows installer

```bash
wv build --publish
```

Runs the full build, then calls Inno Setup to produce
`build/publish/<project-name>-<version>-setup.exe`.

Configure the Inno Setup path in `wv.toml` if needed:

```toml
[build]
inno_setup_path = "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
```

## Generated Project Structure

```
my-app/
├── icon/
│   ├── favicon.ico
│   └── logo.png
├── frontend/          ← Vue 3 (npm create vue@latest)
│   └── dist/          ← built by wv run / wv build
├── backend/
│   ├── .venv/         ← uv virtual environment
│   └── src/
│       ├── main.py
│       ├── config.py
│       └── bridge/
│           ├── __init__.py
│           └── api.py
├── build/
│   ├── my-app.spec    ← PyInstaller config
│   ├── my-app.iss     ← Inno Setup config
│   └── publish/       ← installer output
└── wv.toml
```

## Frontend Router Auto-Fix

`wv run` and `wv build` automatically replace `createWebHistory` with
`createWebHashHistory` in `frontend/src/router/index.{ts,js}` before building.
This ensures the app works correctly when loaded via the `file://` protocol
after packaging. The replacement is **idempotent** — running it multiple times
has no side effects.

## `wv.toml` Reference

```toml
[project]
name = "my-app"
version = "1.0.0"
window_title = "My App"
author = ""

[build]
inno_setup_path = "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
```

## Extending the JS Bridge

Edit `backend/src/bridge/api.py`:

```python
class Api:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

    def read_file(self, path: str) -> str:
        with open(path) as f:
            return f.read()
```

Call from Vue:

```js
const result = await window.pywebview.api.greet('World')
```

## License

MIT
