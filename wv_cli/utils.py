"""Shared utility functions for wv-cli."""

import os
import platform
import shutil
import subprocess

import click
import toml


# ---------------------------------------------------------------------------
# wv.toml helpers
# ---------------------------------------------------------------------------


def load_config(project_root: str) -> dict:
    """Load wv.toml from the project root. Raises click.ClickException on failure."""
    config_path = os.path.join(project_root, "wv.toml")
    if not os.path.isfile(config_path):
        raise click.ClickException(
            f"wv.toml not found in {project_root}. "
            "Are you inside a wv project directory?"
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return toml.load(f)


def find_project_root() -> str:
    """Walk up from cwd until wv.toml is found. Returns the directory path."""
    cwd = os.path.abspath(os.getcwd())
    candidate = cwd
    while True:
        if os.path.isfile(os.path.join(candidate, "wv.toml")):
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            raise click.ClickException(
                "wv.toml not found. Run this command from inside a wv project."
            )
        candidate = parent


# ---------------------------------------------------------------------------
# Environment checks
# ---------------------------------------------------------------------------


def check_command(cmd: str) -> bool:
    """Return True if the shell command is available on PATH."""
    return shutil.which(cmd) is not None


def require_node():
    """Abort with a helpful message if node/npm is missing."""
    if not check_command("node") or not check_command("npm"):
        raise click.ClickException(
            "Node.js / npm not found.\nPlease install Node.js from: https://nodejs.org"
        )


def require_pnpm():
    """Abort with a helpful message if pnpm is missing."""
    if not check_command("pnpm"):
        raise click.ClickException(
            "pnpm not found.\nInstall it with: npm install -g pnpm"
        )


def require_uv():
    """Abort with a helpful message if uv is missing."""
    if not check_command("uv"):
        raise click.ClickException(
            "uv not found.\n"
            "Install it with:  pip install uv\n"
            "  or (Windows):    winget install astral-sh.uv"
        )


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------


def _resolve_cmd(cmd: str) -> str:
    """On Windows, resolve e.g. 'npm' → 'npm.cmd' so subprocess can find it."""
    if platform.system() == "Windows":
        resolved = shutil.which(cmd)
        if resolved:
            return resolved
    return cmd


def ensure_npm_deps(frontend_dir: str) -> None:
    """Run `npm install` if node_modules is missing or package.json has changed."""
    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.isdir(node_modules):
        click.echo("  📥 Installing frontend dependencies (npm install)…")
        run_cmd(["npm", "install"], cwd=frontend_dir)


def detect_package_manager(project_root: str) -> str:
    """Detect which package manager the project uses based on lock files.

    Priority:
    1. pnpm-lock.yaml -> pnpm
    2. yarn.lock -> yarn (future support)
    3. package-lock.json -> npm
    4. Default -> npm
    """
    frontend_dir = os.path.join(project_root, "frontend")
    pnpm_lock = os.path.join(frontend_dir, "pnpm-lock.yaml")

    if os.path.isfile(pnpm_lock):
        return "pnpm"
    return "npm"


def detect_frontend_framework(project_root: str) -> str:
    """Detect which frontend framework the project uses.

    Detection logic:
    1. Check for Vue specific files (src/router/index.ts with createWebHistory)
    2. Check for React specific files (src/main.jsx or src/main.tsx)
    3. Check package.json for dependencies
    4. Default to 'vue' for backward compatibility
    """
    frontend_dir = os.path.join(project_root, "frontend")

    # Check for Vue Router - strong indicator of Vue project
    vue_router_file = os.path.join(frontend_dir, "src", "router", "index.ts")
    vue_router_file_js = os.path.join(frontend_dir, "src", "router", "index.js")
    if os.path.isfile(vue_router_file) or os.path.isfile(vue_router_file_js):
        return "vue"

    # Check for React entry files
    react_main_jsx = os.path.join(frontend_dir, "src", "main.jsx")
    react_main_tsx = os.path.join(frontend_dir, "src", "main.tsx")
    if os.path.isfile(react_main_jsx) or os.path.isfile(react_main_tsx):
        return "react"

    # Check package.json for framework dependencies
    package_json = os.path.join(frontend_dir, "package.json")
    if os.path.isfile(package_json):
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                import json

                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "vue" in deps:
                    return "vue"
                elif "react" in deps:
                    return "react"
        except Exception:
            pass

    # Default to vue for backward compatibility
    return "vue"


def ensure_frontend_deps(frontend_dir: str, package_manager: str = "npm") -> None:
    """Install frontend dependencies using the specified package manager."""
    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.isdir(node_modules):
        click.echo(
            f"  📥 Installing frontend dependencies ({package_manager} install)…"
        )
        run_cmd([package_manager, "install"], cwd=frontend_dir)


def run_cmd(args: list, cwd: str = None, shell: bool = False):
    """Run a command, streaming output to the terminal. Raise on non-zero exit."""
    args = [_resolve_cmd(args[0])] + args[1:]
    click.echo(f"  $ {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, shell=shell)
    if result.returncode != 0:
        raise click.ClickException(
            f"Command failed (exit {result.returncode}): {' '.join(args)}"
        )


# ---------------------------------------------------------------------------
# Favicon injection
# ---------------------------------------------------------------------------


def inject_favicon(project_root: str) -> None:
    """
    After `npm run build`, overwrite every favicon.ico found under
    frontend/dist/ with the project's own icon/favicon.ico.
    Idempotent and skipped gracefully when source or dist is missing.
    """
    src_ico = os.path.join(project_root, "icon", "favicon.ico")

    if not os.path.isfile(src_ico):
        click.echo("Skipping favicon injection: icon/favicon.ico not found\n")
        return

    dist_dir = os.path.join(project_root, "frontend", "dist")
    if not os.path.isdir(dist_dir):
        click.echo("Skipping favicon injection: frontend/dist not found\n")
        return

    replaced = 0
    for dirpath, _, filenames in os.walk(dist_dir):
        for filename in filenames:
            if filename.lower() == "favicon.ico":
                dst = os.path.join(dirpath, filename)
                shutil.copy2(src_ico, dst)
                rel = os.path.relpath(dst, project_root)
                click.echo(f"✔ Injected favicon: {rel}")
                replaced += 1

    if replaced == 0:
        click.echo("Skipping favicon injection: no favicon.ico found in dist\n")
