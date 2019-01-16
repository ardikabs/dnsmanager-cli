
from functools import wraps

import click
from .core import DNSService

def zone_check(f):
    def decorated_func(ctx, **kwargs):
        zone = kwargs.get("zone")
        config = ctx.obj["CONFIG"]
        if not config.has_section(zone):
            raise click.BadParameter(
                message="You need to register DNS Zone first before importing the record!",
                param_hint=zone
            )
        zone = config[zone]
        service = DNSService(
            nameserver=zone.get("server"),
            keyring_name=zone.get("keyring_name"),
            keyring_value=zone.get("keyring_value")
        )
        kwargs["service"] = service
        return f(ctx, **kwargs)
    
    return decorated_func

def zone_validator(ctx, param, value):
    if not value:
        fqdn = ctx.params.get("fqdn")
        zone = ".".join(fqdn.split(".")[1:])
        return zone
    return value    

def fqdn_validator(ctx, param, value):
    if value:
        ctx.params["record_name"] = value.split(".")[0]
    return value


def depend_on(key, required=False):

    def validate(ctx, param, value):
        if ctx.params.get(key) is not None and value is None and required:
            raise click.BadParameter(
                message=f"Invalid option, {param.name} should be set cause it required if {key} are set",
                param_hint=param.name
            )
        elif ctx.params.get(key) is None and value:
            raise click.BadParameter(
                message=f"This value can't be blank if {key} are set",
                param_hint=param.name
            )
        return value
    return validate

def check_existing_record(name, zone, rtype=None):

    def filtering(data):
        comparator = (data.get("name") == name and data.get("zone") == zone)
        if rtype:
            comparator = comparator and data.get("rtype") == rtype
        return comparator
    return filtering