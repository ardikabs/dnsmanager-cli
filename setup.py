from setuptools import setup, find_packages

setup(
    name='dnsmanager',
    version='0.1.0',
    author='Ardika Bagus Saputro',
    author_email='ardikabs@gdn-commerce.com',
    url='https://github.com/ardikabs/dnsmanager-suites',
    py_modules=['dnsmanager'],
    install_requires=['click', "dnspython"],
    packages=["dnsmanager"],
    package_dir={"dnsmanager": "core"},
    entry_points = '''
        [console_scripts]
        dnsmanager=dnsmanager.cli:cli
    '''
)