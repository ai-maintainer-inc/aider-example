#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["Click>=7.0", "aider-chat==0.13.0"]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Douglas Schonholtz",
    author_email="douglas@ai-maintainer.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    entry_points={
        "console_scripts": [
            "ai_maintainer_aider=ai_maintainer_aider.cli:main",
        ],
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="ai_maintainer_aider",
    name="ai_maintainer_aider",
    packages=find_packages(include=["ai_maintainer_aider", "ai_maintainer_aider.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/dschonholtz/ai_maintainer_aider",
    version="0.1.0",
    zip_safe=False,
)
