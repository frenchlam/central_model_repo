from setuptools import find_packages, setup
from central_model_registry import __version__

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='central_model_registry',
    version=__version__,
    description='Project for Central Model Registry',
    author='Yassine Essawabi, Florent Moiny',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=required,
    setup_requires=['wheel'],
)
