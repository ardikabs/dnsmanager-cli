from dnsmanager import (
    __version__,
    __author__,
    __email__,
    __url__
)
from setuptools import setup, find_packages
setup(
    name='dnsmanager',
    version=__version__,
    author=__author__,
    author_email=__email__,
    url=__url__,
    py_modules=['dnsmanager'],
    install_requires=['click', "dnspython"],
    packages=["dnsmanager"],
    package_dir={"dnsmanager": "dnsmanager"},
    entry_points = '''
        [console_scripts]
        dnsmanager=dnsmanager.cli:cli
    '''
)