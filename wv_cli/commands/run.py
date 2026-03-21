"""wv run — development mode: build frontend then launch pywebview."""
import os

import click

from ..utils import find_project_root, load_config, run_cmd, fix_router_history, ensure_frontend_deps, inject_favicon, detect_package_manager


@click.command('run')
def run():
    """Run the app in development mode (builds frontend, then starts pywebview)."""

    project_root = find_project_root()
    config = load_config(project_root)

    click.echo('🔧 开发模式启动…')

    # 1. Fix Vue Router history mode for file:// compatibility
    fix_router_history(project_root)

    # 2. Build frontend
    frontend_dir = os.path.join(project_root, 'frontend')
    
    # 检测包管理器
    package_manager = detect_package_manager(project_root)
    click.echo(f'\n📦 构建前端（使用 {package_manager}）…')
    
    ensure_frontend_deps(frontend_dir, package_manager)
    run_cmd([package_manager, 'run', 'build'], cwd=frontend_dir)
    inject_favicon(project_root)

    # 3. Verify frontend/dist exists
    dist_dir = os.path.join(frontend_dir, 'dist')
    if not os.path.isdir(dist_dir):
        raise click.ClickException(
            "frontend/dist 不存在。\n"
            "请检查 npm run build 是否成功执行。"
        )

    # 4. Launch pywebview via uv
    backend_dir = os.path.join(project_root, 'backend')
    click.echo('\n🚀 启动 pywebview…')
    run_cmd(['uv', 'run', 'src/main.py'], cwd=backend_dir)