from dnsmanager import (
    __version__,
    __author__,
    __email__,
    __url__,
    __description__
)
from setuptools import setup, find_packages
setup(
    name='dnsmanager',
    version=__version__,
    author=__author__,
    author_email=__email__,
    url=__url__,
    description=__description__,
    py_modules=['dnsmanager'],
    install_requires=["click", "click_configfile", "dnspython"],
    packages=find_packages(),
    entry_points = '''
        [console_scripts]
        dnsmanager=dnsmanager.scripts.cli:cli
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)