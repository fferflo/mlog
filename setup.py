#!/usr/bin/env python3

from setuptools import setup

setup(
    name="mlog",
    version="0.1",
    description="Logger for machine learning experiments",
    author="Florian Fervers",
    author_email="florian.fervers@gmail.com",
    packages=["mlog"],
    url="https://github.com/fferflo/mlog",
    license="MIT",
    install_requires=[
        "dash",
        "plotly",
        "numpy",
        "dash-bootstrap-components",
        "dash-editor-components",
    ],
    zip_safe=False,
)
