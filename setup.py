import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="hypothesis-mutagen",
    version="1.0.0",
    author="Harrison Goldstein, Timothée Paquatte",
    author_email="hgo@seas.upenn.edu",
    description="Add the mutation testing feature to hypothesis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hgoldstein95/hypothesis-mutagen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"pytest11": ["mutagen = pytest_mutagen", ]},
    python_requires='>=3.6',
)