#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for spyder.unittesting
"""

from setuptools import setup, find_packages
import os
import os.path as osp


def get_version():
    """ """
    with open("spyder_unittesting/__init__.py") as f:
        lines = f.read().splitlines()
        for l in lines:
            if "__version__" in l:
                version = l.split("=")[1].strip()
                version = version.replace("'", '').replace('"', '')
                return version


def get_readme():
    """ """
    with open('README.md') as f:
        readme = str(f.read())
    return readme


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
REQUIREMENTS = []
EXTLIST = ['.jpg', '.png', '.json', '.mo', '.ini']
LIBNAME = 'spyder.unittesting'


setup(
    name=LIBNAME,
    version=get_version(),
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_data={LIBNAME: get_package_data(LIBNAME, EXTLIST)},
    keywords=["Qt PyQt4 PyQt5 PySide spyder plugins spyplugins unittesting"],
    install_requires=REQUIREMENTS,
    url='https://github.com/spyder-ide/spyder.unittesting',
    license='MIT',
    author='Joseph Martinot-Lagarde',
    author_email='',
    maintainer='The Spyder Development Team',
    maintainer_email='',
    description='This is a plugin to run unit tests from within'
                ' the Spyder IDE.',
    long_description=get_readme(),
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Widget Sets'])
