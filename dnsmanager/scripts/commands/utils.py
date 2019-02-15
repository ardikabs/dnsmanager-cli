
import click

from dnsmanager.scripts.config import ConfigFileProcessor
from .services import init_dns_service
from .callbacks import (
    check_domain,
    check_availability_zone,
    check_existing_record_with_name,
    check_existing_record_with_content,   

)

def show_dns(data):
    click.echo(f"{'CONTENT': <15} {'RTYPE': <10} {'TTL': <10} {'ZONE': <15} {'NAME': <5}")
    for d in data:
        output = "{content: <15} {rtype: <10} {ttl: <10} {zone: <15} {name: <5}".format(
            name=f"{d.get('name')}",
            content=f"{d.get('content')}",
            rtype=f"{d.get('rtype')}",
            ttl=f"{d.get('ttl')}",
            zone=f"{d.get('zone')}"
        )
        click.echo(output)


def searching_dns(config, available_zones, domain, content, rtype, ttl, zone):
    data = []
    if not zone:
        for zone in available_zones:
            section = f"dns.zones.{zone}"
            zone_obj = ConfigFileProcessor.select_storage_for(section, config)
            service = init_dns_service(zone_obj)
            data.extend(service.import_records())
    elif zone in available_zones:
        section = f"dns.zones.{zone}"
        zone_obj = ConfigFileProcessor.select_storage_for(section, config)
        service = init_dns_service(zone_obj)
        data.extend(service.import_records())
    else:
        raise click.BadParameter(
            message=f"Zone ({value}) not found in configuration file ({ctx.obj['CONFIG_PATH']})",
            param_hint="zone"
        )
    if not data:
        click.echo("Error: No record data found!", err=True)
    if content: 
        exists = filter(check_existing_record_with_content(content, rtype=rtype), data)
    else: 
        exists = filter(check_existing_record_with_name(domain, rtype=rtype), data)
    
    return list(exists)
