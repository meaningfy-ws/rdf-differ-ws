# setup.py
# Date: 12/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com
import re

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('requirements-dev.txt') as f:
    requirements_dev = f.read().splitlines()

extras = {
    'test': requirements_dev,
}


def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)


version = find_version('eds4jinja2/__init__.py')

packages = find_packages(exclude=('examples*', 'test*'))

setup(
    name="eds4jinja2",
    version=version,
    install_requires=requirements,
    tests_require=requirements_dev,
    extras_require=extras,
    packages=find_packages(exclude=("test*",)),
    include_package_data=True,
    # data_files={
    #     'eds4jinja2_templates': ['templates/**/*'],
    # },
    # package_data={'': ['*.txt'], },
    author="Eugeniu Costetchi",
    author_email="costezki.eugen@gmail.com",
    maintainer="Eugeniu Costetchi",
    maintainer_email="costezki.eugen@gmail.com",
    description="Embed the data source specifications in your JINJA templates directly, " \
                "and enjoy the dynamic data contexts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # long_description_content_type="text/x-rst",
    url="https://github.com/meaningfy-ws/eds4jinja2",
    platforms='any',
    keywords='template, jinja, report, report generation, rdf, sparql, linked-data, data-source, dynamic-context',
    # exclude=["tests", "test_*"],
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    python_requires='>=3.8',
    entry_points={
        "console_scripts": ["mkreport=eds4jinja2.entrypoints.cli.main:build_report"],
    },
)
