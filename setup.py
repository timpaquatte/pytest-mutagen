import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="pytest-mutagen",
    version="1.0",
    author="Harrison Goldstein, Timothée Paquatte",
    author_email="hgo@seas.upenn.edu",
    description="Add the mutation testing feature to pytest",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hgoldstein95/pytest-mutagen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"pytest11": ["mutagen = plugin", ]},
    python_requires='>=3.6',
)