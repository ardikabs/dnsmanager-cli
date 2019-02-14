
import os
import click
import configparser

from dnsmanager import __version__
from .config import ConfigFileProcessor
from .commands import init_command


@click.group(invoke_without_command=True)
@click.version_option(
    version=__version__, 
    prog_name="DNSManager",
    message=('%(prog)s version %(version)s')
)
@click.option("--config-path", 
    type=click.Path(exists=True),
    envvar="DNSMANAGER_CONFIG_PATH", 
    help="Configuration file path. You can set with ENV variable (DNSMANAGER_CONFIG_PATH) to be loaded automatically"
)
@click.pass_context
def cli(ctx, config_path):
    """ 
    An DNS Manager to interact with DNS Server

    # for now only support DNS BIND9
    """

    cfp = ConfigFileProcessor()
    if config_path:
        cfp.config_searchpath = [config_path]

    try:
        config = cfp.read_config()
    except configparser.DuplicateOptionError as e:
        click.echo(f"Error: Config ({e.source}). " 
                    f"Option <{e.option}> in section ({e.section}) "
                    f"already exist [line {e.lineno}]"
        )
        ctx.exit(0)
    except configparser.DuplicateSectionError as e:
        click.echo(f"Error: Config ({e.source}). " 
                    f"Duplicate section ({e.section}) [line {e.lineno}]"
        )
        ctx.exit(0)
    
    if not config:
        raise click.ClickException(
            message="No configuration file found [config.cfg / config.ini]"
        )
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config
    ctx.obj["CONFIG_PATH"] = cfp.config_path

init_command(cli)