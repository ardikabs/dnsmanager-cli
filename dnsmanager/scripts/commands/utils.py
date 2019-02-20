
import click

from dnsmanager.scripts.config import ConfigFileProcessor
from dnsmanager import utils
from .services import init_dns_service
from .callbacks import (
    check_domain,
    check_availability_zone,
    check_existing_record_with_name,
    check_existing_record_with_content,   

)

def show_dns(data):
    output = utils.Formatter.from_dict(
        data, 
        headers=["NAME", "CONTENT", "RTYPE", "TTL", "ZONE"],
        attr=["name", "content", "rtype", "ttl", "zone"]
    )
    click.echo("\n".join(output))

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
