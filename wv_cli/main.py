"""wv-cli: Scaffold tool for pywebview + Vue3 desktop apps."""
import click
from .commands.create import create
from .commands.run import run
from .commands.build import build


@click.group()
@click.version_option(version="0.1.0", prog_name="wv")
def cli():
    """wv-cli — pywebview + Vue3 desktop app scaffold tool."""
    pass


cli.add_command(create)
cli.add_command(run)
cli.add_command(build)
