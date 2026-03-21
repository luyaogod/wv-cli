"""wv create — scaffold a new pywebview + Vue3 project."""
import os
import shutil

import click
import toml

from ..utils import require_node, require_uv, run_cmd, check_command
from ..templates import (
    WV_TOML,
    CONFIG_PY,
    MAIN_PY,
    BRIDGE_INIT_PY,
    BRIDGE_API_PY,
    SPEC_FILE,
    ISS_FILE,
    ROOT_GITIGNORE,
    BACKEND_GITIGNORE,
)

# 包内默认图标目录：wv_cli/icon/
_PKG_ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon')


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
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def _copy_default_icons(project_dir: str) -> None:
    """
    Copy default favicon.ico and logo.png from the wv-cli package's icon/
    directory into the project's icon/ directory.
    Skips files that already exist (safe for `wv create .`).
    """
    for filename in ('favicon.ico', 'logo.png'):
        src = os.path.join(_PKG_ICON_DIR, filename)
        dst = os.path.join(project_dir, 'icon', filename)
        if os.path.exists(dst):
            continue
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            click.echo(f'  ⚠ 未找到默认图标：{src}，跳过复制')


def _scaffold_directories(project_dir: str) -> None:
    dirs = [
        'icon',
        'frontend',
        'backend/src/bridge',
        'backend/tests',
        'build/publish',
    ]
    for d in dirs:
        _makedirs(os.path.join(project_dir, d))


def _scaffold_files(
    project_dir: str,
    project_name: str,
    version: str,
    window_title: str,
    author: str,
) -> None:
    ctx = dict(
        project_name=project_name,
        version=version,
        window_title=window_title,
        author=author,
    )

    _write_text(os.path.join(project_dir, 'wv.toml'), WV_TOML.format(**ctx))

    _write_text(
        os.path.join(project_dir, 'backend', 'src', 'config.py'),
        CONFIG_PY.format(**ctx),
    )

    _write_text(os.path.join(project_dir, 'backend', 'src', 'main.py'), MAIN_PY)

    _write_text(
        os.path.join(project_dir, 'backend', 'src', 'bridge', '__init__.py'),
        BRIDGE_INIT_PY,
    )

    _write_text(
        os.path.join(project_dir, 'backend', 'src', 'bridge', 'api.py'),
        BRIDGE_API_PY,
    )

    _write_text(
        os.path.join(project_dir, 'build', f'{project_name}.spec'),
        SPEC_FILE.format(**ctx),
    )

    _write_text(
        os.path.join(project_dir, 'build', f'{project_name}.iss'),
        ISS_FILE.format(**ctx),
    )

    # 项目根目录 .gitignore
    _write_text(os.path.join(project_dir, '.gitignore'), ROOT_GITIGNORE)


# ---------------------------------------------------------------------------
# wv create command
# ---------------------------------------------------------------------------

@click.command('create')
@click.argument('directory', required=False, default=None)
def create(directory):
    """Create a new pywebview + Vue3 desktop app project."""

    cwd = os.path.abspath(os.getcwd())

    if directory is None:
        project_name = click.prompt('项目名称', default='my-app')
        project_dir = os.path.join(cwd, project_name)
    elif directory == '.':
        default_name = os.path.basename(cwd)
        project_name = click.prompt('项目名称', default=default_name)
        project_dir = cwd
    else:
        project_dir = os.path.abspath(directory)
        project_name = click.prompt('项目名称', default=os.path.basename(project_dir))

    window_title = click.prompt('窗口标题', default=project_name)
    version = click.prompt('版本号', default='1.0.0')
    author = click.prompt('作者', default='')

    click.echo('\n🔍 检查运行环境…')
    require_node()
    click.echo('  ✔ Node.js / npm')
    require_uv()
    click.echo('  ✔ uv')

    # 检测并选择包管理器
    has_npm = check_command('npm')
    has_pnpm = check_command('pnpm')
    
    package_manager = 'npm'  # 默认
    if has_npm and has_pnpm:
        package_manager = click.prompt(
            '选择包管理器',
            type=click.Choice(['npm', 'pnpm']),
            default='npm'
        )
    elif has_pnpm:
        package_manager = 'pnpm'
        click.echo('  ✔ pnpm')
    else:
        click.echo('  ✔ npm')

    click.echo('\n📁 创建项目结构…')
    _scaffold_directories(project_dir)
    _scaffold_files(project_dir, project_name, version, window_title, author)
    _copy_default_icons(project_dir)
    click.echo('  ✔ 目录与文件已生成')

    click.echo(f'\n🖼  初始化前端（{package_manager} create vue@latest）…')
    frontend_dir = os.path.join(project_dir, 'frontend')
    _makedirs(frontend_dir)
    run_cmd([package_manager, 'create', 'vue@latest', '.'], cwd=frontend_dir)

    click.echo('\n🐍 初始化后端（uv）…')
    backend_dir = os.path.join(project_dir, 'backend')
    run_cmd(['uv', 'init', '--no-workspace', '--vcs', 'none'], cwd=backend_dir)
    run_cmd(['uv', 'venv'], cwd=backend_dir)
    run_cmd(['uv', 'add', 'pywebview', 'pyinstaller'], cwd=backend_dir)

    _write_text(os.path.join(backend_dir, '.gitignore'), BACKEND_GITIGNORE)

    rel = os.path.relpath(project_dir, cwd)
    cd_hint = f'\n  cd {rel}' if rel != '.' else ''

    click.echo(f"""
✔ 项目创建完成！{cd_hint}

下一步：
  wv run      # 开发模式运行（构建前端 + 启动 pywebview）
  wv build    # 生产构建（PyInstaller 打包）
""")