"""wv run — development mode: build frontend then launch pywebview."""

import os

import click

from ..utils import (
    find_project_root,
    run_cmd,
    ensure_frontend_deps,
    inject_favicon,
    detect_package_manager,
    detect_frontend_framework,
)


@click.command("run")
def run():
    """Run the app in development mode (builds frontend, then starts pywebview)."""

    project_root = find_project_root()

    click.echo("🔧 Starting development mode…")

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

    # 3. Verify frontend/dist exists
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.isdir(dist_dir):
        raise click.ClickException(
            "frontend/dist does not exist.\n"
            "Please check if npm run build executed successfully."
        )

    # 4. Launch pywebview via uv
    backend_dir = os.path.join(project_root, "backend")
    click.echo("\n🚀 Starting pywebview…")
    run_cmd(["uv", "run", "src/main.py"], cwd=backend_dir)

    # Reminder about HashHistory
    click.echo("""
💡 Tip: If using Vue Router or React Router, ensure you use HashHistory mode
   (createWebHashHistory / createHashHistory) for file:// protocol compatibility.
""")
