"""Shared utility functions for wv-cli."""
import os
import platform
import re
import shutil
import subprocess
import sys

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
            "Node.js / npm not found.\n"
            "Please install Node.js from: https://nodejs.org"
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
    node_modules = os.path.join(frontend_dir, 'node_modules')
    if not os.path.isdir(node_modules):
        click.echo('  📥 安装前端依赖（npm install）…')
        run_cmd(['npm', 'install'], cwd=frontend_dir)


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
    src_ico = os.path.join(project_root, 'icon', 'favicon.ico')

    if not os.path.isfile(src_ico):
        click.echo('跳过 favicon 注入：icon/favicon.ico 不存在')
        return

    dist_dir = os.path.join(project_root, 'frontend', 'dist')
    if not os.path.isdir(dist_dir):
        click.echo('跳过 favicon 注入：frontend/dist 不存在')
        return

    replaced = 0
    for dirpath, _, filenames in os.walk(dist_dir):
        for filename in filenames:
            if filename.lower() == 'favicon.ico':
                dst = os.path.join(dirpath, filename)
                shutil.copy2(src_ico, dst)
                rel = os.path.relpath(dst, project_root)
                click.echo(f'✔ 已注入 favicon：{rel}')
                replaced += 1

    if replaced == 0:
        click.echo('跳过 favicon 注入：dist 中未找到 favicon.ico')

# ---------------------------------------------------------------------------
# Frontend router fix
# ---------------------------------------------------------------------------

def fix_router_history(project_root: str) -> None:
    """
    Replace createWebHistory with createWebHashHistory in the Vue Router
    entry file so that file:// protocol works correctly after packaging.
    This function is idempotent.
    """
    router_dir = os.path.join(project_root, "frontend", "src", "router")

    if not os.path.isdir(router_dir):
        click.echo("跳过路由修复：未检测到 router 目录")
        return

    target_file = None
    for filename in ("index.ts", "index.js"):
        candidate = os.path.join(router_dir, filename)
        if os.path.isfile(candidate):
            target_file = candidate
            break

    if target_file is None:
        click.echo("跳过路由修复：未找到 router/index.ts 或 router/index.js")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "createWebHistory" not in content:
        click.echo("跳过路由修复：未检测到 createWebHistory，无需修改")
        return

    # \b boundary: createWebHashHistory does NOT contain createWebHistory as a
    # substring, so this replacement is idempotent.
    new_content = re.sub(r"\bcreateWebHistory\b", "createWebHashHistory", content)

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    rel_path = os.path.relpath(target_file, project_root)
    click.echo(f"✔ 已修复：{rel_path}（createWebHistory → createWebHashHistory）")