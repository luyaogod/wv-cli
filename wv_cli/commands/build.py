"""wv build — production build with optional Windows installer packaging."""

import os
import platform

import click

from ..utils import (
    find_project_root,
    load_config,
    run_cmd,
    ensure_frontend_deps,
    inject_favicon,
    detect_package_manager,
    detect_frontend_framework,
)


@click.command("build")
@click.option(
    "--publish",
    is_flag=True,
    default=False,
    help="Also create a Windows installer with Inno Setup after building.",
)
def build(publish: bool):
    """Build the project for production.

    Use --publish to additionally generate a Windows installer via Inno Setup.
    """

    project_root = find_project_root()
    config = load_config(project_root)

    project_name = config["project"]["name"]
    version = config["project"]["version"]

    click.echo(f"🏗  Production build: {project_name} v{version}")

    # Detect frontend framework
    frontend_framework = detect_frontend_framework(project_root)
    click.echo(f"  📋 Detected frontend framework: {frontend_framework}")

    # 2. Build frontend
    frontend_dir = os.path.join(project_root, "frontend")

    # Detect package manager
    package_manager = detect_package_manager(project_root)
    click.echo(f"\n📦 Building frontend (using {package_manager})…")

    ensure_frontend_deps(frontend_dir, package_manager)
    run_cmd([package_manager, "run", "build"], cwd=frontend_dir)
    inject_favicon(project_root)

    # Verify frontend/dist
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.isdir(dist_dir):
        raise click.ClickException(
            "frontend/dist does not exist.\n"
            "Please check if npm run build executed successfully, then try again."
        )

    # 3. Run PyInstaller
    build_dir = os.path.join(project_root, "build")
    spec_file = os.path.join(build_dir, f"{project_name}.spec")

    if not os.path.isfile(spec_file):
        raise click.ClickException(
            f"Spec file not found: {spec_file}\n"
            "Please ensure the current directory is a wv project root and the build/ directory is complete."
        )

    # Clean output directory to avoid PyInstaller confirmation prompt
    output_dir = os.path.join(build_dir, "dist", project_name)
    if os.path.isdir(output_dir):
        click.echo(f"  🗑 Cleaning previous build: {output_dir}")
        import shutil

        shutil.rmtree(output_dir)

    click.echo("\n📦 PyInstaller packaging…")
    backend_dir = os.path.join(project_root, "backend")
    run_cmd(
        [
            "uv",
            "run",
            "pyinstaller",
            spec_file,
            "--distpath",
            os.path.join(build_dir, "dist"),
        ],
        cwd=backend_dir,
    )

    click.echo(f"\n✔ Build complete: build/dist/{project_name}/")

    # Reminder about HashHistory
    click.echo("""
💡 Tip: If using Vue Router or React Router, ensure you use HashHistory mode
   (createWebHashHistory / createHashHistory) for file:// protocol compatibility.
""")

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

    if platform.system() != "Windows":
        click.echo(
            "\n⚠  --publish is only supported on Windows (requires Inno Setup), skipping installer generation."
        )
        return

    inno_path = config.get("build", {}).get(
        "inno_setup_path",
        "C:/Program Files (x86)/Inno Setup 6/ISCC.exe",
    )

    if not os.path.isfile(inno_path):
        raise click.ClickException(
            f"Inno Setup not found: {inno_path}\n"
            "Please install Inno Setup and configure the correct inno_setup_path in wv.toml.\n"
            "Download: https://jrsoftware.org/isdl.php"
        )

    iss_file = os.path.join(build_dir, f"{project_name}.iss")
    if not os.path.isfile(iss_file):
        raise click.ClickException(f"ISS file not found: {iss_file}")

    click.echo("\n📦 Inno Setup packaging installer…")
    run_cmd([inno_path, iss_file])

    installer = os.path.join(
        build_dir, "publish", f"{project_name}-{version}-setup.exe"
    )
    click.echo(f"\n✔ Installer generated: {installer}")
