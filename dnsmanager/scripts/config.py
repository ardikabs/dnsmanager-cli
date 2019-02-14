
import click
import configparser
from click_configfile import (
    ConfigFileReader, 
    Param, 
    SectionSchema,
    matches_section,
    generate_configfile_names,
    select_params_from_section_schema,
    select_config_sections
)


class ConfigSectionSchema(object):
    """Describes all config sections of this configuration file."""

    @matches_section("DEFAULTS")
    class Defaults(SectionSchema):
        config_version = Param(type=str)

    @matches_section("dns")
    class DNS(SectionSchema):
        rtype = Param(type=str)
        ttl = Param(type=str)

    @matches_section("dns.zones")
    class DNSZoneAvailable(SectionSchema):
        available = Param(type=str, multiple=True)

    @matches_section("dns.zones.*")
    class DNSZoneItems(SectionSchema):
        name = Param(type=str)
        server = Param(type=str)
        keyring_name = Param(type=str)
        keyring_value = Param(type=str)

        
class ConfigFileProcessor(ConfigFileReader):
    config_files = ["config.cfg", "config.ini"]
    config_searchpath = ["."]
    config_section_schemas = [
        ConfigSectionSchema.Defaults,
        ConfigSectionSchema.DNS,
        ConfigSectionSchema.DNSZoneAvailable,
        ConfigSectionSchema.DNSZoneItems,
    ]

    @property
    def config_path(self):
        import os
        cls = self.__class__
        configfile_names = list(generate_configfile_names(cls.config_files, cls.config_searchpath))
        config_param = Param(type=click.File("r")) 
        config_file = config_param.parse(configfile_names[0])
        return os.path.realpath(config_file.name)

    @classmethod
    def read_config(cls):
        configfile_names = list(
            generate_configfile_names(cls.config_files, cls.config_searchpath))
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(configfile_names)

        if not cls.config_sections:
            # -- AUTO-DISCOVER (once): From cls.config_section_schemas
            cls.config_sections = cls.collect_config_sections_from_schemas()

        storage = {}
        for section_name in select_config_sections(parser.sections(),
                                                   cls.config_sections):
            # print("PROCESS-SECTION: %s" % section_name)
            config_section = parser[section_name]
            cls.process_config_section(parser, config_section, storage)
        return storage
        
    @classmethod
    def process_config_section(cls, parser_sections, config_section, storage):
        schema = cls.select_config_schema_for(config_section.name)
        if not schema:
            message = "No schema found for: section=%s"
            raise LookupError(message % config_section.name)

        # -- PARSE AND STORE CONFIG SECTION:
        section_storage = cls.select_storage_for(config_section.name, storage)
        section_data = parse_config_section(parser_sections, config_section, schema)
        section_storage.update(section_data)

def parse_config_section(parser, config_section, section_schema):

    storage = {}
    if config_section.get("inherit"):
        inherit_section = config_section.pop("inherit")
        inherit_schema = ConfigFileProcessor.select_config_schema_for(inherit_section)
        inherit_section_data = parse_config_section(
            parser, parser[inherit_section], inherit_schema)
        storage.update(inherit_section_data)

    for name, param in select_params_from_section_schema(section_schema):
        value = config_section.get(name, None)
        if value is None:
            if param.default is None:
                continue
            value = param.default
        else:
            value = param.parse(value)
        storage[name] = value
    return storage
