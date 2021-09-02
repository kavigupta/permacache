import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="permacache",
    version="2.1.0",
    author="Kavi Gupta",
    author_email="permacache@kavigupta.org",
    description="Permanant cache.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kavigupta/permacache",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["filelock>=3.0.12", "appdirs>=1.4.4"],
    entry_points={
        "console_scripts": ["permacache=permacache.main:main"],
    },
)
