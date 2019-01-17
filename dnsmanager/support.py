
import click
from .core import DNSService

def init_service(zone_section):
    service = DNSService(
        nameserver=zone_section.get("server"),
        keyring_name=zone_section.get("keyring_name"),
        keyring_value=zone_section.get("keyring_value")
    )
    return service

def check_availability_zone(ctx, param, value):
    config = ctx.obj["CONFIG"]
    if not config.has_section(value):
        raise click.BadParameter(
            message=f"DNS Zone ({value}) not found in configuration file ({ctx.obj['CONFIG_FILEPATH']})!",
            param_hint=value
        )
    return value

def fqdn_validator(ctx, param, value):
    if value:
        ctx.params["record_name"] = value.split(".")[0]
    return value

def zone_validator(ctx, param, value):
    if not value and ctx.params.get("fqdn") is not None:
        fqdn = ctx.params.get("fqdn")
        value = ".".join(fqdn.split(".")[1:])

    return check_availability_zone(ctx, param, value)

def depend_on(key, required=False):

    def validate(ctx, param, value):
        if ctx.params.get(key) is not None and value is None and required:
            raise click.BadParameter(
                message=f"Option {param.name.upper()} can't be blank if {key.upper()} are set",
                param_hint=param.name
            )
        elif ctx.params.get(key) is None and value:
            raise click.BadParameter(
                message=f"Option {key.upper()} can't be blank if {param.name.upper()} are set",
                param_hint=param.name
            )
        return value
    return validate

def check_existing_record_with_name(name, zone, rtype=None):

    def filtering(data):
        comparator = (data.get("name") == name and data.get("zone") == zone)
        if rtype:
            comparator = comparator and data.get("rtype") == rtype
        return comparator
    return filtering

def check_existing_record_with_content(content, zone, rtype=None):

    def filtering(data):
        comparator = (data.get("content") == content and data.get("zone") == zone)
        if rtype:
            comparator = comparator and data.get("rtype") == rtype
        return comparator
    return filtering