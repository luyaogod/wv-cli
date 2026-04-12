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
| SQLite database | `No` |

Available frontend templates:
- Vue 3 + TypeScript (`vue-ts`)
- Vue 3 + JavaScript (`vue`)
- React + TypeScript (`react-ts`)
- React + JavaScript (`react`)

**SQLite Database Support:**
When enabled, the project will include:
- SQLAlchemy ORM with a sample `User` model
- Database utilities for session management
- Example API methods (`create_user`, `get_users`, `delete_user`)
- `backend/data/` directory for the SQLite database file

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
│   ├── data/          ← SQLite database files (if enabled)
│   └── src/
│       ├── main.py
│       ├── config.py
│       ├── bridge/
│       │   ├── __init__.py
│       │   └── api.py
│       └── db/        ← Database module (if SQLite enabled)
│           ├── __init__.py
│           ├── models.py
│           └── utils.py
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

## Database Usage (SQLite)

When you enable SQLite support during project creation, the following database API methods are available:

```python
# backend/src/bridge/api.py
class Api:
    def create_user(self, name: str, email: str = "") -> dict:
        """Create a new user."""
        ...

    def get_users(self) -> list:
        """Get all users."""
        ...

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        ...
```

Call from frontend:

```js
// Create a user
const newUser = await window.pywebview.api.create_user('John', 'john@example.com')

// Get all users
const users = await window.pywebview.api.get_users()

// Delete a user
const success = await window.pywebview.api.delete_user(1)
```

### Customizing Database Models

Edit `backend/src/db/models.py` to add your own models:

```python
from sqlalchemy import Column, Integer, String
from db.models import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    completed = Column(Integer, default=0)
```

Then regenerate the database by deleting `backend/data/app.db` and restarting the app.

## Migrating Existing Projects to wv-cli

If you have an existing pywebview + Vue/React project and want to use wv-cli for development and building, follow this guide to make minimal changes.

### 🚀 Quick Migration with AI

**Copy the prompt below and paste it to your AI assistant** (ChatGPT, Claude, etc.) to get automated help with migration:

```
I want to migrate my existing pywebview desktop app to use wv-cli for development and building.

My project structure:
- Frontend: [Vue 3 / React] located at [frontend/]
- Backend: Python with pywebview located at [backend/ or src/]
- Current entry point: [main.py or app.py]

Please help me:
1. Create a wv.toml configuration file
2. Adjust the project structure to match wv-cli conventions
3. Update the backend entry point to work with wv-cli
4. Ensure the JS Bridge API is properly exposed
5. Configure PyInstaller spec for building

Requirements:
- Minimize changes to existing code
- Keep the existing frontend code as-is
- Preserve the current JS Bridge API structure
```

### Manual Migration Steps

#### 1. Create `wv.toml`

Add this configuration file to your project root:

```toml
[project]
name = "your-app-name"
version = "1.0.0"
window_title = "Your App Title"
author = "Your Name"
package_manager = "npm"  # or "pnpm"

[build]
inno_setup_path = "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
```

#### 2. Adjust Project Structure

wv-cli expects this structure:

```
your-project/
├── wv.toml              # Add this
├── icon/
│   ├── favicon.ico      # App icon
│   └── logo.png
├── frontend/            # Your existing frontend
│   ├── src/
│   ├── dist/            # Build output
│   └── package.json
├── backend/             # Your existing backend
│   ├── src/
│   │   ├── main.py      # Entry point
│   │   ├── config.py    # Create this
│   │   └── bridge/
│   │       ├── __init__.py
│   │       └── api.py    # Your JS Bridge API
│   └── .venv/           # uv virtual environment
└── build/
    ├── your-app.spec    # PyInstaller config
    └── publish/         # Installer output
```

#### 3. Create `backend/src/config.py`

```python
# Development mode: load index.html directly from frontend/dist
HTML_PATH_DEV = '../../frontend/dist/index.html'

# Packaged mode: PyInstaller bundles frontend/dist contents into _f_dist
HTML_PATH_APP = '_f_dist/index.html'

# Window title (injected from wv.toml at project creation time)
WINDOW_TITLE = "Your App Title"
```

#### 4. Update Backend Entry Point

Modify your `main.py` to use the config:

```python
import sys
import os
import webview
from config import WINDOW_TITLE, HTML_PATH_DEV, HTML_PATH_APP

def get_html_path() -> str:
    """Resolve the correct HTML path depending on the runtime environment."""
    if getattr(sys, 'frozen', False):
        # PyInstaller packaged environment
        base = sys._MEIPASS
        return os.path.join(base, HTML_PATH_APP)
    else:
        # Development environment
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

#### 5. Ensure JS Bridge API is in `bridge/api.py`

Move your existing API class to this location:

```python
class Api:
    """Your existing JS Bridge API methods."""

    def your_existing_method(self, arg):
        # Your implementation
        pass
```

#### 6. Initialize uv Environment

```bash
cd backend
uv init --no-workspace --vcs none
uv venv
uv add pywebview pyinstaller
# If using SQLite:
# uv add sqlalchemy alembic
```

#### 7. Build and Run

```bash
# Development mode
wv run

# Production build
wv build

# Build with installer
wv build --publish
```

### Important Notes

- **Frontend Router**: If using Vue Router or React Router, ensure you use **HashHistory** mode
- **Static Assets**: Make sure your frontend build outputs to `frontend/dist/`
- **PyInstaller**: The spec file in `build/` should bundle `frontend/dist` into `_f_dist`

## License

MIT
