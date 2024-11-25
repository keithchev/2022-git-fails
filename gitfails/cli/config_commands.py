import json
import os
import pathlib
import click

from gitfails import logger
from gitfails.config import CONFIG_FILEPATH, init_config, read_config, write_config


@click.command()
@click.argument("reset", type=bool, default=False, required=False)
@click.pass_context
def init(ctx, reset):
    """
    Create the config file if it does not exist
    """
    init_config(reset=reset)
    click.echo("Initialized config file")


@click.command()
def reset():
    init_config(reset=True)
    click.echo("Reset config file")


@click.command()
def view():
    config = read_config()
    click.echo(json.dumps(config, indent=4))
    click.echo(f"Config file at '{CONFIG_FILEPATH}'")


@click.command()
def rm():
    if os.path.exists(CONFIG_FILEPATH):
        os.remove(CONFIG_FILEPATH)
    click.echo(f"Deleted config file '{CONFIG_FILEPATH}'")


@click.command()
@click.argument("path", type=pathlib.Path, required=True)
def set_working_dir(path):
    """Set the top-level directory (in which repos are created)"""

    config = read_config()
    config["working_dir"] = str(pathlib.Path(path).expanduser().resolve())

    os.makedirs(config["working_dir"], exist_ok=True)
    write_config(config)

    click.echo("Set working directory to %s" % config["working_dir"])
