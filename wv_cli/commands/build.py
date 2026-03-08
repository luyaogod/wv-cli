"""wv build — production build with optional Windows installer packaging."""
import os
import platform
import sys

import click

from ..utils import find_project_root, load_config, run_cmd, fix_router_history, ensure_npm_deps, inject_favicon


@click.command('build')
@click.option(
    '--publish',
    is_flag=True,
    default=False,
    help='Also create a Windows installer with Inno Setup after building.',
)
def build(publish: bool):
    """Build the project for production.

    Use --publish to additionally generate a Windows installer via Inno Setup.
    """

    project_root = find_project_root()
    config = load_config(project_root)

    project_name = config['project']['name']
    version = config['project']['version']

    click.echo(f'🏗  生产构建：{project_name} v{version}')

    # 1. Fix Vue Router history mode
    fix_router_history(project_root)

    # 2. Build frontend
    frontend_dir = os.path.join(project_root, 'frontend')
    click.echo('\n📦 构建前端…')
    ensure_npm_deps(frontend_dir)
    run_cmd(['npm', 'run', 'build'], cwd=frontend_dir)
    inject_favicon(project_root)

    # Verify frontend/dist
    dist_dir = os.path.join(frontend_dir, 'dist')
    if not os.path.isdir(dist_dir):
        raise click.ClickException(
            "frontend/dist 不存在。\n"
            "请检查 npm run build 是否成功执行，然后重试。"
        )

    # 3. Run PyInstaller
    build_dir = os.path.join(project_root, 'build')
    spec_file = os.path.join(build_dir, f'{project_name}.spec')

    if not os.path.isfile(spec_file):
        raise click.ClickException(
            f"未找到 spec 文件：{spec_file}\n"
            "请确认当前目录是 wv 项目根目录，且 build/ 目录完整。"
        )

    click.echo('\n📦 PyInstaller 打包…')
    backend_dir = os.path.join(project_root, 'backend')
    run_cmd(
        ['uv', 'run', 'pyinstaller', spec_file, '--distpath', os.path.join(build_dir, 'dist')],
        cwd=backend_dir,
    )

    click.echo(f'\n✔ 构建完成：build/dist/{project_name}/')

    # 4. Optional: Inno Setup packaging (Windows only)
    if publish:
        _publish_installer(project_root, config, project_name, version, build_dir)


def _publish_installer(
    project_root: str,
    config: dict,
    project_name: str,
    version: str,
    build_dir: str,
) -> None:
    """Generate a Windows installer using Inno Setup."""

    if platform.system() != 'Windows':
        click.echo(
            '\n⚠  --publish 仅支持 Windows 平台（需要 Inno Setup），已跳过安装包生成。'
        )
        return

    inno_path = config.get('build', {}).get(
        'inno_setup_path',
        'C:/Program Files (x86)/Inno Setup 6/ISCC.exe',
    )

    if not os.path.isfile(inno_path):
        raise click.ClickException(
            f"未找到 Inno Setup：{inno_path}\n"
            "请安装 Inno Setup 后在 wv.toml 中配置正确的 inno_setup_path。\n"
            "下载：https://jrsoftware.org/isdl.php"
        )

    iss_file = os.path.join(build_dir, f'{project_name}.iss')
    if not os.path.isfile(iss_file):
        raise click.ClickException(
            f"未找到 iss 文件：{iss_file}"
        )

    click.echo('\n📦 Inno Setup 打包安装程序…')
    run_cmd([inno_path, iss_file])

    installer = os.path.join(
        build_dir, 'publish', f'{project_name}-{version}-setup.exe'
    )
    click.echo(f'\n✔ 安装包已生成：{installer}')