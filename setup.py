import sys
from setuptools import setup, find_packages

requires = (
    'Flask',
    'Flask-Script',
    'daemonize',
    'Flask-SQLAlchemy',
    'Flask-Restless'
)

setup(
    name = 'player_piano',
    version = '1.0',
    description = 'A web app for managing midi playlists and playing them directly to a midi interface',
    author = 'Ryan McGuire',
    author_email = 'ryan@enigmacurry.com',
    url = 'http://github.com/EnigmaCurry',
    install_requires = requires,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True
)

