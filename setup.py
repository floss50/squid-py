#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = ['keeper-contracts', 'web3==4.5.0', 'pyyaml', 'coloredlogs']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="leucothia",
    author_email='devops@oceanprotocol.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    description="🐳 Ocean/Web3py wrapper.",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='squid-py',
    name='squid-py',
    packages=find_packages(
        include=['squid_py', 'squid_py.keeper', 'squid_py.utils', 'squid_py.ddo', 'squid_py.models', 'squid_py.ocean']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/oceanprotocol/squid-py',
    version='0.2.4',
    zip_safe=False,
)
