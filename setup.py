# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Setup script for spyder_unittest
"""

from setuptools import setup, find_packages
import os
import os.path as osp


def get_version():
    """Get version from source file"""
    with open("spyder_unittest/__init__.py") as f:
        lines = f.read().splitlines()
        for l in lines:
            if "__version__" in l:
                version = l.split("=")[1].strip()
                version = version.replace("'", '').replace('"', '')
                return version

def get_package_data(name, extlist):
    """Return data files for package *name* with extensions in *extlist*"""
    flist = []
    # Workaround to replace os.path.relpath (not available until Python 2.6):
    offset = len(name) + len(os.pathsep)
    for dirpath, _dirnames, filenames in os.walk(name):
        for fname in filenames:
            if not fname.startswith('.') and osp.splitext(fname)[1] in extlist:
                flist.append(osp.join(dirpath, fname)[offset:])
    return flist


# Requirements
REQUIREMENTS = ['lxml', 'nose', 'pytest', 'spyder>=3']
EXTLIST = ['.jpg', '.png', '.json', '.mo', '.ini']
LIBNAME = 'spyder_unittest'


LONG_DESCRIPTION = """
This is a plugin for the Spyder IDE that integrates popular unit test
frameworks. It allows you to run tests and view the results.

**Status:**
This is a work in progress. It is useable, but only the basic functionality
is implemented at the moment. The plugin currently supports the py.test and nose
testing frameworks.
"""

setup(
    name=LIBNAME,
    version=get_version(),
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_data={LIBNAME: get_package_data(LIBNAME, EXTLIST)},
    keywords=["Qt PyQt4 PyQt5 spyder plugins testing"],
    install_requires=REQUIREMENTS,
    url='https://github.com/spyder-ide/spyder-unittest',
    license='MIT',
    author="Spyder Project Contributors",
    description='Plugin to run tests from within the Spyder IDE',
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Testing',
        'Topic :: Text Editors :: Integrated Development Environments (IDE)'])
