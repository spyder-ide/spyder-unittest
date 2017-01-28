# spyder-unittest

## Build Status
[![Build Status](https://travis-ci.org/spyder-ide/spyder-unittest.svg?branch=master)](https://travis-ci.org/spyder-ide/spyder-unittest)
[![Build status](https://ci.appveyor.com/api/projects/status/d9wa6whp1fpq4uii?svg=true)](https://ci.appveyor.com/project/spyder-ide/spyder-unittest)
[![CircleCI](https://circleci.com/gh/spyder-ide/spyder-unittest/tree/master.svg?style=shield)](https://circleci.com/gh/spyder-ide/spyder-unittest/tree/master)
[![Coverage Status](https://coveralls.io/repos/github/spyder-ide/spyder-unittest/badge.svg?branch=master)](https://coveralls.io/github/spyder-ide/spyder-unittest?branch=master)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/cce1ea0d121246ff876d2822e9e3d2a1/badge.svg)](https://www.quantifiedcode.com/app/project/cce1ea0d121246ff876d2822e9e3d2a1)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/spyder-ide/spyder-unittest/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/spyder-ide/spyder-unittest/?branch=master)

## Project information
[![Join the chat at https://gitter.im/spyder-ide/public](https://badges.gitter.im/spyder-ide/public.svg)](https://gitter.im/spyder-ide/public)

## Description

![screenshot](./screenshot.png)

This is a plugin for Spyder that integrates popular unit test
frameworks. It allows you to run tests and view the results.

## Status

This is a work in progress. It is useable, but only the basic functionality 
is implemented at the moment. The plugin supports the py.test and nose 
testing frameworks.

## Installation

See https://github.com/spyder-ide/spyder/wiki/User-plugins but in
short, the following command installs the development version of the
unittest plugin:

```python
pip install git+git://github.com/spyder-ide/spyder-unittest.git
```

The plugin is not yet included in PyPI.

## Dependencies

You need to have the following installed in order to run the unittest
plugin.

* [Spyder](https://github.com/spyder-ide/spyder) (obviously), at least version 3.0
* [lxml](http://lxml.de/)
* the testing framework that you will be using: [py.test](https://pytest.org)
  and/or [nose](https://nose.readthedocs.io)

In order to run the tests distributed with this plugin, you need
[nose](https://nose.readthedocs.io), [py.test](https://pytest.org) 
and [pytest-qt](https://github.com/pytest-dev/pytest-qt). If you use Python 2, 
you also need [mock](https://github.com/testing-cabal/mock).

## Usage

The plugin adds an item `Run unit tests` to the `Run` menu in Spyder.
Click on this to run the unit tests. After you specify the testing framework 
and the directory under which the tests are stored, the tests are run. 
The `Unit testing` window pane (displayed at the top of this file) will pop up 
with the results.

If you want to run tests in a different directory or switch testing
frameworks, click `Configure` in the Options menu (cogwheel icon), 
which is located in the upper right corner of the `Unit testing` pane.
