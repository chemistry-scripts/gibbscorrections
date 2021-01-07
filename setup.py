from setuptools import setup

long_description = (
    "A module that automatises the tedious process of retrieving a Gaussian 16 geometry, and setting up and running"
    + "a single point Orca calculation at that geometry. Of course, for a bunch of files at the same time."
)

setup(
    name="gibbscorrections",
    version="0.2.4",
    long_description=long_description,
    url="http://github.com/chemistry-scripts/gibbscorrections",
    author="Emmanuel Nicolas",
    author_email="latruelle@users.noreply.github.com",
    license="MIT",
    packages=["gibbscorrections"],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "gibbscorrections=gibbscorrections:main",
        ]
    },
)
