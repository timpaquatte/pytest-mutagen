import os
from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()


def local_file(name):
    return os.path.relpath(os.path.join(os.path.dirname(__file__), name))

SOURCE = local_file("src")

__version__ = None
with open(local_file("src/pytest_mutagen/_version.py")) as o:
    exec(o.read())
assert __version__ is not None


setup(
    name="pytest-mutagen",
    version=__version__,
    author="Timothee Paquatte <timothee.paquatte@polytechnique.edu>, Harrison Goldstein <hgo@seas.upenn.edu>",
    author_email="hgo@seas.upenn.edu",
    description="Add the mutation testing feature to pytest",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hgoldstein95/pytest-mutagen",
    packages=find_packages(SOURCE),
    package_dir={"": SOURCE},
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
    ],
    entry_points={"pytest11": ["mutagen = pytest_mutagen.plugin", ]},
    python_requires='>=3.6',
    install_requires=['pytest>=5.4', ],
    keywords="python testing property-based-testing",
)