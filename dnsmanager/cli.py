import os
import sys
import click
import configparser as cp
import json
from core import DNSService
from support import (
    zone_check, 
    zone_validator, 
    fqdn_validator, 
    depend_on,
    check_existing_record
)

RTYPE_CHOICES = ["A", "CNAME", "PTR", "MX", "TXT", "SRV"]

@click.group()
@click.option("--config-path", envvar="DNSMANAGER_CONFIG_PATH",
    type=click.Path(exists=True),
    help="Configuration file path or use ENV variable with name DNSMANAGER_CONFIG_PATH")
@click.pass_context
def cli(ctx, config_path):
    if config_path is None:
        raise click.BadParameter(message="Configuration file are not set")
    config = cp.ConfigParser()
    config.read(config_path)
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config
    ctx.obj["CONFIG_PATH"] = config_path
    
@cli.command("config", short_help="DNS Manager configuration")
@click.option("--show", is_flag=True, help="Show all configuration")
@click.option("--zone-name", type=click.STRING, help="Zone name to be added on config file")
@click.option("--zone-remove", type=click.STRING, help="Zone name to be deleted from config file")
@click.option("--zone-server", type=click.STRING, callback=depend_on("zone_name", required=True), help="Zone server (DNS Server) to be added on config file. It can be IPv4 address or FQDN")
@click.option("--keyring-name", callback=depend_on("zone_name", required=True), type=click.STRING, help="Zone keyring name to be added on config file")
@click.option("--keyring-value", callback=depend_on("zone_name", required=True), type=click.STRING, help="Zone keyring value to be added on config file")
@click.pass_context
def configuration(ctx, show, **kwargs):
    config = ctx.obj["CONFIG"]
    if show:
        for index, section in enumerate(config.sections()):
            if section == "DEFAULTS":
                click.echo(">> DEFAULTS Variable <<")
                for key in config[section]:
                    click.echo(f"-> {key}: {config[section][key]}")
                click.echo("----------------\n")
                click.echo(">> DNS Zone Variable <<")
                continue

            click.echo(f"[{index}] Zone ({section})")
            for key in config[section]:
                click.echo(f"-> {key.upper()}: {config[section][key]}")

    if kwargs.get("zone_remove") is not None:
        zone = kwargs.get("zone_remove")
        if config.has_section(zone):
            config.remove_section(zone)
            with open(ctx.obj["CONFIG_PATH"], "w") as configfile:
                config.write(configfile)
        else:
            raise click.BadParameter(message=f"Zone {zone} not found")

    elif kwargs.get("zone_name") is not None:
        zone = kwargs.get("zone_name")
        server = kwargs.get("zone_server")
        keyring_name = kwargs.get("keyring_name")
        keyring_value = kwargs.get("keyring_value")

        config.add_section(zone)
        config.set(zone, "server", server)
        config.set(zone, "keyring_name", keyring_name)
        config.set(zone, "keyring_value", keyring_value)
        with open(ctx.obj["CONFIG_PATH"], "w") as configfile:
            config.write(configfile)

@cli.command("import", short_help="DNS Manager import record from zone")
@click.argument("zone", required=True)
@click.option("-o","--out-path", "out", envvar="DNSMANAGER_IMPORT_PATH",
    type=click.File("w"), default="out.json",
    help="Destination output file after import record from DNS zone")
@click.pass_context
@zone_check
def importing(ctx, service, zone, out):
    result = service.import_records(domain=zone)
    out.write(json.dumps(result, indent=4))
    click.echo(f"Successfully imported {len(result)} in {out.name}")

@cli.command("new", short_help="Add new DNS Record")
@click.argument("record_name")
@click.option("--zone", required=True, type=click.STRING, help="DNS Zone that available on configuration file")
@click.option("--content", required=True, type=click.STRING, help="Record content")
@click.option("--rtype", "rtype", type=click.Choice(RTYPE_CHOICES), default="A", help="Record type")
@click.option("--ttl", type=click.INT, default=300, help="Record TTL")
@click.option("--force", is_flag=True, help="Force adding record with replacing similar name")
@click.pass_context
@zone_check
def new(ctx, service, zone, record_name, content, rtype, ttl, force):
    config = ctx.obj["CONFIG"]
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
                filter(check_existing_record(name=record_name, zone=zone, rtype=rtype),data)
            )
            if len(exist) > 0:
                raise click.exceptions.UsageError(
                    message=f"DNS Record already exist {record_name} in zone {zone}"
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
@click.argument("record_name")
@click.option("--zone", required=True, type=click.STRING, help="DNS Zone that available on configuration file")
@click.option("--content", required=True, type=click.STRING, help="Record content")
@click.option("--rtype", type=click.Choice(RTYPE_CHOICES), default="A", help="Record type")
@click.option("--ttl", type=click.INT, default=300, help="Record TTL")
@click.pass_context
@zone_check
def update(ctx, service, zone, record_name, content, rtype, ttl):
    config = ctx.obj["CONFIG"]
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
@click.option("--zone", callback=zone_validator, type=click.STRING, help="DNS Zone that available on configuration file")
@click.pass_context
@zone_check
def remove(ctx, service, zone, record_name, fqdn):
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
@click.argument("fqdn", callback=fqdn_validator)
@click.option("--zone", callback=zone_validator, type=click.STRING, help="DNS Zone that available on configuration file")
@click.pass_context
@zone_check
def check(ctx, service, zone, record_name, fqdn):
    data = service.import_records(domain=zone)
    if data:
        exists = list(
            filter(check_existing_record(name=record_name, zone=zone),data)
        )

        click.echo(">> DNS Record Information <<")
        for d in exists:
            click.echo(f"> FQDN: {d.get('name')}.{d.get('zone')}")
            click.echo(f"> Name: {d.get('name')}")
            click.echo(f"> Content: {d.get('content')}")
            click.echo(f"> RType: {d.get('rtype')}")
            click.echo(f"> TTL: {d.get('ttl')}")
            click.echo(f"> Zone: {d.get('zone')}\n")

    else:
        click.echo("No data")

cli.add_command(configuration)
cli.add_command(importing)
cli.add_command(check)
cli.add_command(new)
cli.add_command(update)
cli.add_command(remove)

if __name__ == "__main__":
    cli()