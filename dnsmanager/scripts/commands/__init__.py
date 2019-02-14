
AVAILABLE_COMMANDS = (
    "find",
    "new",
    "update",
    "remove",
)

import click

def init_command(cli, **kwargs):
    from importlib import import_module
    from inspect import getmembers, isfunction
    
    modules = import_module(
        f".cmd", 
        package=__name__
    )
    
    for name, func in getmembers(modules):
        if name in AVAILABLE_COMMANDS:
            cli.add_command(func)
