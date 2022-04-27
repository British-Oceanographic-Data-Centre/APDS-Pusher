from setuptools import setup
from urllib.request import urlopen
from urllib.error import URLError

try:
    urlopen("https://repo.bodc.me/repository/pypi-bodc/simple/", timeout=5)
except URLError as ex:
    raise ConnectionError("Could not connect to BODC internal PyPI, you need to be behind the firewall") from ex

setup(use_scm_version=True)
