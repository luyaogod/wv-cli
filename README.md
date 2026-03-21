# wv-cli

A command-line scaffold tool for building **pywebview (Python backend) + Vue 3 / React (frontend)** desktop apps.

## Requirements

- Python ≥ 3.9
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Node.js / npm](https://nodejs.org) — for the frontend
- [pnpm](https://pnpm.io/) *(optional)* — alternative package manager
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
| Project name | directory name |
| Window title | project name |
| Version | `1.0.0` |
| Author | *(empty)* |
| Package manager | `npm` (auto-detected) |
| Frontend template | `Vue 3 + TypeScript` |

Available frontend templates:
- Vue 3 + TypeScript (`vue-ts`)
- Vue 3 + JavaScript (`vue`)
- React + TypeScript (`react-ts`)
- React + JavaScript (`react`)

After answering, the CLI will:
1. Scaffold the full directory structure
2. Initialize the frontend with `create-vite`
3. Initialize the backend with `uv`

### Run in development mode

```bash
cd my-app
wv run
```

Builds the frontend, then launches the pywebview window loading `frontend/dist`.

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
├── frontend/          ← Vue 3 or React (Vite)
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

## Frontend Router Note

When using Vue Router or React Router, ensure you use **HashHistory** mode for
`file://` protocol compatibility after packaging:

- **Vue**: Use `createWebHashHistory` instead of `createWebHistory`
- **React**: Use `createHashHistory` instead of `createBrowserHistory`

The CLI will remind you about this after `wv create`, `wv run`, and `wv build`.

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
