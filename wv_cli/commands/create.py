"""wv create — scaffold a new pywebview + Vue3 project."""

import os
import shutil
import signal
import sys

import click
import questionary

from ..utils import require_node, require_uv, run_cmd, check_command
from ..templates import (
    WV_TOML,
    CONFIG_PY,
    MAIN_PY,
    MAIN_PY_WITH_DB,
    BRIDGE_INIT_PY,
    BRIDGE_API_PY,
    BRIDGE_API_PY_WITH_DB,
    DB_INIT_PY,
    DB_MODELS_PY,
    DB_UTILS_PY,
    SPEC_FILE,
    ISS_FILE,
    ROOT_GITIGNORE,
    BACKEND_GITIGNORE,
    PROJECT_README_MD,
    PROJECT_README_MD_WITH_DB,
)

# 包内默认图标目录：wv_cli/icon/
_PKG_ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon")

# Track project directory for cleanup on interrupt
_project_dir_to_cleanup = None


def _cleanup_on_interrupt(signum, frame):
    """Handle Ctrl+C by cleaning up partial project directory."""
    global _project_dir_to_cleanup
    click.echo("\n\n⚠ Interrupted by user.", err=True)
    if _project_dir_to_cleanup and os.path.exists(_project_dir_to_cleanup):
        click.echo(f"Cleaning up: {_project_dir_to_cleanup}", err=True)
        try:
            shutil.rmtree(_project_dir_to_cleanup)
            click.echo("✔ Cleanup completed.", err=True)
        except Exception as e:
            click.echo(f"⚠ Cleanup failed: {e}", err=True)
    sys.exit(130)  # Standard exit code for Ctrl+C


# ---------------------------------------------------------------------------
# Directory / file creation helpers
# ---------------------------------------------------------------------------


def _makedirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _write_text(path: str, content: str, overwrite: bool = False) -> None:
    """Write text to path; skip if file already exists and overwrite is False."""
    if os.path.exists(path) and not overwrite:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _copy_default_icons(project_dir: str) -> None:
    """
    Copy default favicon.ico and logo.png from the wv-cli package's icon/
    directory into the project's icon/ directory.
    Skips files that already exist (safe for `wv create .`).
    """
    for filename in ("favicon.ico", "logo.png"):
        src = os.path.join(_PKG_ICON_DIR, filename)
        dst = os.path.join(project_dir, "icon", filename)
        if os.path.exists(dst):
            continue
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            click.echo(f"  ⚠ Default icon not found: {src}, skipping")


def _scaffold_directories(project_dir: str, use_sqlite: bool = False) -> None:
    dirs = [
        "icon",
        "frontend",
        "backend/src/bridge",
        "backend/tests",
        "build/publish",
    ]
    if use_sqlite:
        dirs.append("backend/src/db")
        dirs.append("backend/data")
    for d in dirs:
        _makedirs(os.path.join(project_dir, d))


def _scaffold_files(
    project_dir: str,
    project_name: str,
    version: str,
    window_title: str,
    author: str,
    use_sqlite: bool = False,
    package_manager: str = "npm",
) -> None:
    ctx = dict(
        project_name=project_name,
        version=version,
        window_title=window_title,
        author=author,
        package_manager=package_manager,
    )

    _write_text(os.path.join(project_dir, "wv.toml"), WV_TOML.format(**ctx))

    _write_text(
        os.path.join(project_dir, "backend", "src", "config.py"),
        CONFIG_PY.format(**ctx),
    )

    # Choose main.py template based on database option
    main_template = MAIN_PY_WITH_DB if use_sqlite else MAIN_PY
    _write_text(os.path.join(project_dir, "backend", "src", "main.py"), main_template)

    _write_text(
        os.path.join(project_dir, "backend", "src", "bridge", "__init__.py"),
        BRIDGE_INIT_PY,
    )

    # Choose api.py template based on database option
    api_template = BRIDGE_API_PY_WITH_DB if use_sqlite else BRIDGE_API_PY
    _write_text(
        os.path.join(project_dir, "backend", "src", "bridge", "api.py"),
        api_template,
    )

    # Scaffold database module if SQLite is selected
    if use_sqlite:
        _write_text(
            os.path.join(project_dir, "backend", "src", "db", "__init__.py"),
            DB_INIT_PY,
        )
        _write_text(
            os.path.join(project_dir, "backend", "src", "db", "models.py"),
            DB_MODELS_PY,
        )
        _write_text(
            os.path.join(project_dir, "backend", "src", "db", "utils.py"),
            DB_UTILS_PY,
        )

    # Write project README.md
    readme_template = PROJECT_README_MD_WITH_DB if use_sqlite else PROJECT_README_MD
    _write_text(os.path.join(project_dir, "README.md"), readme_template.format(**ctx))

    _write_text(
        os.path.join(project_dir, "build", f"{project_name}.spec"),
        SPEC_FILE.format(**ctx),
    )

    _write_text(
        os.path.join(project_dir, "build", f"{project_name}.iss"),
        ISS_FILE.format(**ctx),
    )

    # 项目根目录 .gitignore
    _write_text(os.path.join(project_dir, ".gitignore"), ROOT_GITIGNORE)


# ---------------------------------------------------------------------------
# wv create command
# ---------------------------------------------------------------------------


@click.command("create")
@click.argument("directory", required=False, default=None)
def create(directory):
    """Create a new pywebview + Vue3 desktop app project."""
    global _project_dir_to_cleanup

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, _cleanup_on_interrupt)

    cwd = os.path.abspath(os.getcwd())
    project_dir = None
    project_created = False

    try:
        if directory is None:
            project_name = click.prompt("Project name", default="my-app")
            project_dir = os.path.join(cwd, project_name)
        elif directory == ".":
            default_name = os.path.basename(cwd)
            project_name = click.prompt("Project name", default=default_name)
            project_dir = cwd
        else:
            project_dir = os.path.abspath(directory)
            project_name = click.prompt(
                "Project name", default=os.path.basename(project_dir)
            )

        # Track directory for cleanup (only if it's a new directory, not current dir)
        if directory != ".":
            _project_dir_to_cleanup = project_dir

        window_title = click.prompt("Window title", default=project_name)
        version = click.prompt("Version", default="1.0.0")
        author = click.prompt("Author", default="")

        click.echo("\n🔍 Checking environment…")
        require_node()
        click.echo("  ✔ Node.js / npm")
        require_uv()
        click.echo("  ✔ uv")

        # Detect and select package manager
        has_npm = check_command("npm")
        has_pnpm = check_command("pnpm")

        package_manager = "npm"  # default
        if has_npm and has_pnpm:
            package_manager = questionary.select(
                "Select package manager", choices=["npm", "pnpm"], default="npm"
            ).ask()
        elif has_pnpm:
            package_manager = "pnpm"
            click.echo("  ✔ pnpm")
        else:
            click.echo("  ✔ npm")

        # Select frontend template
        frontend_template = questionary.select(
            "Select frontend template",
            choices=[
                questionary.Choice("vue-ts", value="vue-ts"),
                questionary.Choice("vue", value="vue"),
                questionary.Choice("react-ts", value="react-ts"),
                questionary.Choice("react", value="react"),
            ],
            default="vue-ts",
        ).ask()

        # Select database option
        use_sqlite = questionary.confirm(
            "Include SQLite database support?",
            default=False,
        ).ask()

        click.echo("\n📁 Creating project structure…")
        _scaffold_directories(project_dir, use_sqlite)
        project_created = True  # Mark that we've created files
        _scaffold_files(project_dir, project_name, version, window_title, author, use_sqlite, package_manager)
        _copy_default_icons(project_dir)
        click.echo("  ✔ Directories and files created")

        # 1. Initialize backend first
        click.echo("\n🐍 Creating backend (uv)…")
        backend_dir = os.path.join(project_dir, "backend")
        run_cmd(["uv", "init", "--no-workspace", "--vcs", "none"], cwd=backend_dir)
        run_cmd(["uv", "venv"], cwd=backend_dir)
        # Add dependencies based on database option
        deps = ["pywebview", "pyinstaller"]
        if use_sqlite:
            deps.extend(["sqlalchemy", "alembic"])
        run_cmd(["uv", "add"] + deps, cwd=backend_dir)
        _write_text(os.path.join(backend_dir, ".gitignore"), BACKEND_GITIGNORE)
        click.echo("✔ Backend created")

        # 2. Initialize frontend
        frontend_dir = os.path.join(project_dir, "frontend")
        _makedirs(frontend_dir)

        if package_manager == "npm":
            click.echo(
                f"\n🌐 Creating frontend (npx create-vite --template {frontend_template})…"
            )
            run_cmd(
                [
                    "npx",
                    "create-vite@latest",
                    ".",
                    "--template",
                    frontend_template,
                    "--no-interactive",
                ],
                cwd=frontend_dir,
            )
        else:
            click.echo(
                f"\n🌐 Creating frontend (pnpm dlx create-vite --template {frontend_template})…"
            )
            run_cmd(
                [
                    "pnpm",
                    "dlx",
                    "create-vite@latest",
                    ".",
                    "--template",
                    frontend_template,
                    "--no-interactive",
                ],
                cwd=frontend_dir,
            )

        # Clear cleanup tracking on successful completion
        _project_dir_to_cleanup = None

        rel = os.path.relpath(project_dir, cwd)
        cd_hint = f"\n  cd {rel}" if rel != "." else ""

        click.echo(f"""
✔ Project created!{cd_hint}

Next steps:
  wv run      # Development mode (build frontend + launch pywebview)
  wv build    # Production build (PyInstaller packaging)

💡 Tip: If using Vue Router or React Router, ensure you use HashHistory mode
   (createWebHashHistory / createHashHistory) for file:// protocol compatibility.
""")

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt that wasn't caught by signal handler
        click.echo("\n\n⚠ Interrupted by user.", err=True)
        if project_created and project_dir and os.path.exists(project_dir):
            click.echo(f"Cleaning up: {project_dir}", err=True)
            try:
                shutil.rmtree(project_dir)
                click.echo("✔ Cleanup completed.", err=True)
            except Exception as e:
                click.echo(f"⚠ Cleanup failed: {e}", err=True)
        sys.exit(130)
