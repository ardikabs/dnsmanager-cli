
import os
import json
import click

from dnsmanager.scripts.config import ConfigFileProcessor
from dnsmanager.scripts.utils import (
    prompt_y_n_question,
    Threading
)

from .callbacks import (
    check_domain,
    check_availability_zone,
    check_existing_record_with_name,
    check_existing_record_with_content,   

)

from .services import init_dns_service
from  .utils import searching_dns, show_dns

RTYPE_CHOICES = ["A", "CNAME", "PTR", "MX", "TXT", "SRV"]

@click.command("find", help="Find available record to the zone")
@click.argument("domain", callback=check_domain)
@click.option("--content", 
    type=click.STRING,
    help="Content parameter of the record"
)
@click.option("--rtype", 
    type=click.STRING,
    help="Record type parameter of the record"
)
@click.option("--ttl", 
    type=click.INT,
    help="Time to live parameter of the record"
)
@click.option("--zone", 
    type=click.STRING,
    callback=check_availability_zone(),
    help="Selected zone. Must available in configuration file"
)
@click.pass_context
def find(ctx, domain, content, rtype, ttl, zone):
    config = ctx.obj["CONFIG"]
    available_zones = config["dns.zones"]["available"]
    kwargs = {
        "config": config, 
        "available_zones": available_zones,
        "domain": domain, 
        "content": content, 
        "rtype": rtype, 
        "ttl": ttl, 
        "zone": zone
    }

    threading = Threading(searching_dns, **kwargs)
    
    progressbar = click.progressbar(threading.progress, label=f"Searching Domain {domain}", show_eta=True) 
    with progressbar:
        for progress in progressbar:
            if threading.exception:
                raise click.ClickException(threading.exception)
                
            if progress is not None: 
                result = progress
                break

    if not result:
        click.echo(f"Warning: Domain [{domain}] are not available at the moment")
        ctx.exit(1)

    show_dns(result)

@click.command("new", help="New record to be added to the zone")
@click.argument("domain", callback=check_domain)
@click.option("--content", 
    type=click.STRING,
    help="Content parameter of the record"
)
@click.option("--rtype", 
    default="A",
    show_default=True,
    type=click.Choice(RTYPE_CHOICES), 
    help="Record type parameter of the record"
)
@click.option("--ttl",
    default=300,
    show_default=True,
    type=click.INT,
    help="Time to live parameter of the record"
)
@click.option(
    "--force", 
    is_flag=True, 
    show_default=True,
    help="Force adding record with replacing similar name"
)
@click.option("--zone",
    type=click.STRING,
    callback=check_availability_zone(allow_null=False),
    help="Selected zone. Must available in configuration file"
)
@click.option("-y", "--yes", is_flag=True, help="Answer yes for all prompt question")
@click.pass_context
def new(ctx, domain, content, rtype, ttl, force, zone, yes):
    config = ctx.obj["CONFIG"]
    section = f"dns.zones.{zone}"
    zone_obj = ConfigFileProcessor.select_storage_for(section, config)

    service = init_dns_service(zone_obj)
    rtype = rtype or zone_obj.get("rtype") or config.get("dns",{}).get("rtype")
    ttl = ttl or zone_obj.get("ttl") or config.get("dns",{}).get("ttl")

    answer = yes or prompt_y_n_question(
        f"Do you want to add new record [{domain}] in zone [{zone}] ?",
        default="no"
    )
    if not answer:
        ctx.exit(0)

    if force:
        result, err = service.update_record(
            name=domain,
            content=content,
            rtype=rtype,
            ttl=ttl
        )
    else:    
        data = service.import_records()
        if data:
            exist = list(filter(check_existing_record_with_name(domain, rtype=rtype), data))
            if len(exist) > 0:
                raise click.exceptions.UsageError(
                    message=f"Record already exist [{domain}] in zone [{zone}]"
                )
        result, err = service.add_record(
            name=domain,
            content=content,
            rtype=rtype,
            ttl=ttl
        )

    if err: 
        raise click.exceptions.UsageError(result)

    if result == "NOERROR":
        click.echo(f"Successfully add record [{domain}] in zone [{zone}]")
    else:
        click.echo(f"Error: {service.process_msg}")
        ctx.exit(1)    

@click.command("put", help="Put an update of the record in the zone")
@click.argument("domain", callback=check_domain)
@click.option("--content", 
    type=click.STRING,
    help="Content parameter of the record"
)
@click.option("--rtype", 
    default="A",
    show_default=True,
    type=click.Choice(RTYPE_CHOICES), 
    help="Record type parameter of the record"
)
@click.option("--ttl", 
    default=300,
    show_default=True,
    type=click.INT,
    help="Time to live parameter of the record"
)
@click.option("--zone", 
    type=click.STRING,
    callback=check_availability_zone(allow_null=False),
    help="Selected zone. Must available in configuration file"
)
@click.option("-y", "--yes", is_flag=True, help="Answer yes for all prompt question")
@click.pass_context
def update(ctx, domain, content, rtype, ttl, zone, yes):
    config = ctx.obj["CONFIG"]
    section = f"dns.zones.{zone}"
    zone_obj = ConfigFileProcessor.select_storage_for(section, config)

    service = init_dns_service(zone_obj)
    rtype = rtype or zone_obj.get("rtype") or config.get("dns",{}).get("rtype")
    ttl = ttl or zone_obj.get("ttl") or config.get("dns",{}).get("ttl")

    answer = yes or prompt_y_n_question(
        f"Do you want to update record [{domain}] in zone [{zone}] ?",
        default="no"
    )
    if not answer:
        ctx.exit(0)
    
    result, err = service.update_record(
        name=domain,
        content=content,
        rtype=rtype,
        ttl=ttl
    )

    if err: 
        raise click.exceptions.UsageError(result)

    if result == "NOERROR":
        click.echo(f"Successfully update record [{domain}] in zone [{zone}]")
    else:
        click.echo(f"Error: {service.process_msg}")
        ctx.exit(1)

@click.command("rm", help="Delete record from the zone")
@click.argument("domain", callback=check_domain)
@click.option("--rtype", 
    default="A",
    show_default=True,
    type=click.Choice(RTYPE_CHOICES), 
    help="Record type parameter of the record"
)
@click.option("--zone", 
    type=click.STRING,
    callback=check_availability_zone(allow_null=False),
    help="Selected zone. Must available in configuration file"
)
@click.option("-y", "--yes", is_flag=True, help="Answer yes for all prompt question")
@click.pass_context
def remove(ctx, domain, rtype, zone, yes):
    config = ctx.obj["CONFIG"]
    section = f"dns.zones.{zone}"
    zone_obj = ConfigFileProcessor.select_storage_for(section, config)

    service = init_dns_service(zone_obj)
    rtype = rtype or zone_obj.get("rtype") or config.get("dns",{}).get("rtype")

    answer = yes or prompt_y_n_question(
        f"Do you want to remove record [{domain}] in zone [{zone}] ?",
        default="no"
    )
    if not answer:
        ctx.exit(0)

    result, err = service.remove_record(
        name=domain,
        rtype=rtype
    )

    if err: 
        raise click.exceptions.UsageError(result)

    if result == "NOERROR":
        click.echo(f"Successfully remove record [{domain}] in zone [{zone}]")
    else:
        click.echo(f"Error: {service.process_msg}")
        ctx.exit(1)

@click.command("import", help="Import record from the zone")
@click.argument("zone", callback=check_availability_zone())
@click.option(
    "-f","--out-file", "out", 
    default="out.json", 
    type=click.File("w"), 
    show_default=True, 
    help="Destination output file name after import record from zone"
)
@click.pass_context
def import_records(ctx, zone, out):
    config = ctx.obj["CONFIG"]
    section = f"dns.zones.{zone}"
    zone_obj = ConfigFileProcessor.select_storage_for(section, config)
    service = init_dns_service(zone_obj)
    result = service.import_records()
    out.write(json.dumps(result, indent=4))
    click.echo(f"Successfully imported {len(result)} in {os.path.realpath(out.name)}")