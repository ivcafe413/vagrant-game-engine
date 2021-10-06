from setuptools import find_packages, setup

setup(
    name="vagrantengine",
    packages=find_packages(include=["vagrantengine"]),
    version="0.1.0",
    description="Vagrant Technology Pygame-based Engine",
    author="Vagrant Technology",
    license="GNU GPL v3",
    install_requires=["pygame", "pyqtree", "transitions"]
)