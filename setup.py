#!/usr/bin/env python

from pathlib import Path

import setuptools

requirements_file = Path(__file__).parent / 'requirements.txt'
with requirements_file.open('r') as fh:
    requirement_lines = fh.readlines()

dev_requirements_file = Path(__file__).parent / 'requirements-dev.txt'
with dev_requirements_file.open('r') as fh:
    dev_requirement_lines = fh.readlines()

setuptools.setup(
    name='gitfail',
    description='Set up common git fails',
    url='https://github.com/keithchev/git-fail',
    packages=setuptools.find_packages(),
    python_requires='>3.8',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'gitfail = gitfail.cli.main:main',
        ]
    },
    install_requires=requirement_lines,
    extras_require={'dev': dev_requirement_lines},
)
