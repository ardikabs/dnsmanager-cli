import os
import sys
import click
import configparser as cp
import json
from . import __version__
from .core import DNSService
from .support import (
    init_service,
    fqdn_validator,
    zone_validator, 
    check_existing_record_with_name,
    check_existing_record_with_content,
    check_availability_zone,
    depend_on,
)
from .util import *
from .modules.config.tools import *

RTYPE_CHOICES = ["A", "CNAME", "PTR", "MX", "TXT", "SRV"]


@click.group(invoke_without_command=True)
@click.version_option(
    version=__version__, 
    prog_name="DNSManager",
    message=('%(prog)s version %(version)s')
)
@click.option(
    "--generate-config",
    "generate",
    is_flag=True,
    help="Generate base configuration file"
)
@click.option(
    "--config-file", envvar="DNSMANAGER_CONFIG_FILEPATH",
    type=click.File("r"),
    help="Configuration file path or use ENV variable with name DNSMANAGER_CONFIG_FILEPATH"
)
@click.pass_context
def cli(ctx, config_file, generate):
    if generate:
        config = cp.RawConfigParser()
        config.add_section("DEFAULTS")
        config.set("DEFAULTS", "rtype", "A")
        config.set("DEFAULTS", "ttl", 300)
        
        config.add_section("example.com")
        config.set("example.com", "server", "ns1.example.com")
        config.set("example.com", "keyring_name", "example-key")
        config.set("example.com", "keyring_value", "ZXhhbXBsZS5jb21rZXlyaW5ndmFsdWU==")
        with open("config.ini", "w") as file:
            config.write(file)
        sys.exit(1)

    if config_file is None:
        raise click.BadParameter(message="Configuration file are not set")

    config = cp.ConfigParser()
    config.read(os.path.realpath(config_file.name))
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config
    ctx.obj["CONFIG_FILEPATH"] = os.path.realpath(config_file.name)

@cli.command("config", short_help="DNS Manager configuration")
@click.option(
    "--show", 
    is_flag=True, 
    help="Show all configuration"
)
@click.option(
    "--zone-name", 
    type=click.STRING, 
    help="Zone name to be added on config file"
)
@click.option(
    "--zone-remove", 
    type=click.STRING, 
    help="Zone name to be deleted from config file"
)
@click.option(
    "--zone-server", 
    type=click.STRING, 
    callback=depend_on("zone_name", required=True), 
    help="Zone server (DNS Server) to be added on config file. It can be IPv4 address or FQDN"
)
@click.option(
    "--keyring-name", 
    callback=depend_on("zone_name", required=True), 
    type=click.STRING, 
    help="Zone keyring name to be added on config file"
)
@click.option(
    "--keyring-value", 
    callback=depend_on("zone_name", required=True), 
    type=click.STRING, 
    help="Zone keyring value to be added on config file"
)
@click.pass_context
def configuration(ctx, show, **kwargs):
    config = ctx.obj["CONFIG"]
    config_filepath = ctx.obj["CONFIG_FILEPATH"]
    if show:
        show_config(config=config)

    if kwargs.get("zone_remove") is not None:
        zone = kwargs.get("zone_remove")
        if not config.has_section(zone):
            raise click.BadParameter(message=f"Zone {zone} not found on config file ({config_filepath})")    

        answer = prompt_y_n_question(f"Do you want to remove ({zone}) section from config file({config_filepath}) ?")
        if answer:
            remove_zone_section_config(
                zone_section=zone, 
                config=config, 
                config_filepath=config_filepath
            )
        else:
            sys.exit(1)

    elif kwargs.get("zone_name") is not None:
        make_zone_section_config(
            data=kwargs, 
            config=config,
            config_filepath=config_filepath
        )

@cli.command("import", short_help="DNS Manager import record from zone")
@click.argument("zone", required=True, callback=check_availability_zone)
@click.option(
    "-f","--out-file", "out", 
    default="out.json", 
    type=click.File("w"), 
    show_default=True, 
    help="Destination output file name after import record from DNS zone"
)
@click.pass_context
def importing_records(ctx, zone, out):
    config = ctx.obj["CONFIG"]
    service = init_service(config[zone])
    result = service.import_records(domain=zone)
    out.write(json.dumps(result, indent=4))
    click.echo(f"Successfully imported {len(result)} in {os.path.realpath(out.name)}")

@cli.command("new", short_help="Add new DNS Record")
@click.argument("record_name", required=True)
@click.option(
    "--zone", 
    required=True,
    callback=check_availability_zone,
    type=click.STRING, 
    help="DNS Zone that available on configuration file"
)
@click.option(
    "--content", 
    required=True, 
    type=click.STRING, 
    help="Record content"
)
@click.option(
    "--rtype", 
    default="A", 
    type=click.Choice(RTYPE_CHOICES), 
    help="Record type", 
    show_default=True
)
@click.option(
    "--ttl", 
    default=300, 
    type=click.INT, 
    show_default=True,
    help="Record TTL"
)
@click.option(
    "--force", 
    is_flag=True, 
    show_default=True,
    help="Force adding record with replacing similar name"
)
@click.pass_context
def new_record(ctx, zone, record_name, content, rtype, ttl, force):
    config = ctx.obj["CONFIG"]
    service = init_service(config[zone])
    rtype = rtype or config[zone]["rtype"] or config["DEFAULTS"]["rtype"]
    ttl = ttl or config[zone]["ttl"] or config["DEFAULTS"]["ttl"]

    if force:
        result = service.replace_record(
            zone=zone,
            record_name=record_name,
            record_content=content,
            record_type=rtype,
            record_ttl=ttl
        )
    else:    
        data = service.import_records(domain=zone)
        if data:
            exist = list(
                filter(check_existing_record_with_name(name=record_name, zone=zone, rtype=rtype),data)
            )
            if len(exist) > 0:
                raise click.exceptions.UsageError(
                    message=f"DNS record already exist {record_name} in zone {zone}"
                )
        result = service.add_record(
            zone=zone,
            record_name=record_name,
            record_content=content,
            record_type=rtype,
            record_ttl=ttl
        )
    
    if result == "NOERROR":
        click.echo(f"Successfully add record ({record_name}) in zone {zone}")
    else:
        if service.process_msg:
            click.echo(f"Process Message: {service.process_msg}")
        raise click.exceptions.UsageError(
            message=result
        )

@cli.command("update", short_help="Update a DNS Record")
@click.argument("record_name", required=True)
@click.option(
    "--zone",
    required=True, 
    callback=check_availability_zone, 
    type=click.STRING, 
    help="DNS Zone that available on configuration file"
)
@click.option(
    "--content",
    required=True, 
    type=click.STRING, help="Record content"
)
@click.option(
    "--rtype",
    default="A", 
    type=click.Choice(RTYPE_CHOICES), 
    show_default=True,
    help="Record type"
)
@click.option(
    "--ttl",
    default=300, 
    type=click.INT, 
    show_default=True,
    help="Record TTL"
)
@click.pass_context
def update_record(ctx, zone, record_name, content, rtype, ttl):
    config = ctx.obj["CONFIG"]
    service = init_service(config[zone])
    rtype = rtype or config[zone]["rtype"] or config["DEFAULTS"]["rtype"]
    ttl = ttl or config[zone]["ttl"] or config["DEFAULTS"]["ttl"]
    
    result = service.replace_record(
        zone=zone,
        record_name=record_name,
        record_content=content,
        record_type=rtype,
        record_ttl=ttl
    )

    if result == "NOERROR":
        click.echo(f"Successfully update record ({record_name}) in zone {zone}")
    else:
        if service.process_msg:
            click.echo(f"Process Message: {service.process_msg}")
        raise click.exceptions.UsageError(
            message=result
        )

@cli.command("rm", short_help="Remove a DNS Record")
@click.argument("fqdn", callback=fqdn_validator)
@click.option(
    "--zone", 
    callback=zone_validator, 
    type=click.STRING, 
    help="DNS Zone that available on configuration file"
)
@click.pass_context
def remove_record(ctx, zone, record_name, fqdn):
    config = ctx.obj["CONFIG"]
    service = init_service(config[zone])
    result = service.remove_record(
        zone=zone,
        record_name=record_name
    )
    if result == "NOERROR":
        click.echo(f"Successfully remove record ({record_name}) in zone {zone}")
    else:
        if service.process_msg:
            click.echo(f"Process Message: {service.process_msg}")
        raise click.exceptions.UsageError(
            message=result
        )

@cli.command("check", short_help="Check a DNS Record")
@click.argument("fqdn", required=False, callback=fqdn_validator)
@click.option(
    "--zone", 
    callback=zone_validator, 
    type=click.STRING,
    help="DNS Zone that available on configuration file"
)
@click.option(
    "--with-content", "content",
    callback=depend_on("zone"),
    type=click.STRING,
    help="Content of the record to be check"
)
@click.pass_context
def check_record(ctx, zone, fqdn, content=None, record_name=None):
    config = ctx.obj["CONFIG"]
    service = init_service(config[zone])
    data = service.import_records(domain=zone)
    if not data:
        click.echo("No Data")
        sys.exit(1)
    
    exists = None
    if content:
        exists = list(
            filter(check_existing_record_with_content(content=content, zone=zone), data)
        )
    elif zone and not record_name:
        raise click.BadOptionUsage(message="FQDN is needed", option_name="zone")
    elif record_name:
        exists = list(
            filter(check_existing_record_with_name(name=record_name, zone=zone),data)
        )

    click.echo(">> DNS Record Information <<")
    if not exists:
        click.echo(f"FQDN ({fqdn}): Not available")
    else:
        for d in exists:
            fqdn = fqdn or f"{d.get('name')}.{d.get('zone')}"
            click.echo(f"-> FQDN: {fqdn}")
            click.echo(f"-> Name: {d.get('name')}")
            click.echo(f"-> Content: {d.get('content')}")
            click.echo(f"-> RType: {d.get('rtype')}")
            click.echo(f"-> TTL: {d.get('ttl')}")
            click.echo(f"-> Zone: {d.get('zone')}\n")

if __name__ == "__main__":
    cli()