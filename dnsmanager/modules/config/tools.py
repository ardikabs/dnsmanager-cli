import click
import configparser as cp

def show_config(config):
    for index, section in enumerate(config.sections()):
        if section == "DEFAULTS":
            click.echo(">> DEFAULTS Variable <<")
            for key in config[section]:
                click.echo(f"-> {key}: {config[section][key]}")
            click.echo("----------------\n")
            click.echo(">> Section Variable <<")
            continue

        click.echo(f"[{index}] Section ({section})")
        for key in config[section]:
            click.echo(f"-> {key.upper()}: {config[section][key]}")

def make_section_config(section, config, config_filepath, **component):
    config.add_section(section)
    for key in component:
        config.set(section, key, component[key])
    with open(config_filepath, "w") as config_file:
        config.write(config_file)
    return config

def remove_section_config(section, config, config_filepath):
    if config.has_section(section):
        config.remove_section(section)
        with open(config_filepath, "w") as config_file:
            config.write(config_file)
        return config
    else:
        return None

def remove_zone_section_config(zone_section, config, config_filepath):
    section = zone_section
    config = remove_section_config(section, config, config_filepath)
    if config:
        click.echo(f"Zone {zone_section} removed from config file ({config_filepath})")
    else:
        raise click.BadParameter(message=f"Zone {zone_section} not found on config file ({config_filepath})")

def make_zone_section_config(data, config, config_filepath):
    section = data["zone_name"]
    config = make_section_config(section, config, config_filepath, **dict(
        server=data["zone_server"],
        keyring_name=data["keyring_name"],
        keyring_value=data["keyring_value"]
    ))
    if config:
        click.echo(f"Zone {data['zone_name']} added to config file ({config_filepath})")
    else:
        raise click.BadParameter(message=f"Something error while generate config file ({config_filepath})")

