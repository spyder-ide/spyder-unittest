# spyder-unittest

[![license](https://img.shields.io/pypi/l/spyder-unittest.svg)](./LICENSE)
[![pypi version](https://img.shields.io/pypi/v/spyder-unittest.svg)](https://pypi.python.org/pypi/spyder-unittest)
[![Join the chat at https://gitter.im/spyder-ide/public](https://badges.gitter.im/spyder-ide/spyder.svg)](https://gitter.im/spyder-ide/public)
[![OpenCollective Backers](https://opencollective.com/spyder/backers/badge.svg?color=blue)](#backers)
[![OpenCollective Sponsors](https://opencollective.com/spyder/sponsors/badge.svg?color=blue)](#sponsors)

[![Build Status](https://travis-ci.org/spyder-ide/spyder-unittest.svg?branch=master)](https://travis-ci.org/spyder-ide/spyder-unittest)
[![Build status](https://ci.appveyor.com/api/projects/status/d9wa6whp1fpq4uii?svg=true)](https://ci.appveyor.com/project/spyder-ide/spyder-unittest)
[![CircleCI](https://circleci.com/gh/spyder-ide/spyder-unittest/tree/master.svg?style=shield)](https://circleci.com/gh/spyder-ide/spyder-unittest/tree/master)
[![Coverage Status](https://coveralls.io/repos/github/spyder-ide/spyder-unittest/badge.svg?branch=master)](https://coveralls.io/github/spyder-ide/spyder-unittest?branch=master)

![Screenshot of spyder-unittest plugin](./screenshot.png)

----

## Important Announcement: Spyder needs your support!

Since mid-November 2017, [Anaconda, Inc](https://www.anaconda.com/) has
stopped funding Spyder development, after doing so for the past 18
months. Therefore, without additional funds, development will shift to
maintaining Spyder 3 at a slower pace than before, while working
toward an eventual Spyder 4 feature release sometime in the future.
At the moment we do not plan to spend much effort on the development of 
Spyder plugins, such as this one.

However, with your contribution of effort and funding, we will be able to
both continue to maintain Spyder 3 at a faster pace, and fund development of
new features for Spyder 4 and its plugins (including this plugin and the
spyder-notebook plugin) at a greatly accelerated rate.

There are many ways to [help with development](
https://github.com/spyder-ide/spyder/wiki/Contributing-to-Spyder), many of
which don't require any programming, and if you're able to make a
financial contribution to help support your favorite community IDE, you can
donate through our [OpenCollective](https://opencollective.com/spyder).

We appreciate all the help you can provide us and can't thank you enough for
supporting the work of the Spyder devs and Spyder development! To learn more
about the current situation and our future plans, please read this [page](
https://github.com/spyder-ide/spyder/wiki/Anaconda-stopped-funding-Spyder).

----

## Description

Spyder-unittest is a plugin for Spyder that integrates popular unit test
frameworks. It allows you to run tests and view the results.

The plugin supports the `unittest` framework in the Python
standard library and the `py.test` and `nose` testing frameworks.
Support for `py.test` is most complete at the moment.

## Installation

The unittest plugin is available in the `spyder-ide` channel in Anaconda and in PyPI,
so it can be installed with the following commands:

* Using Anaconda: `conda install -c spyder-ide spyder-unittest`
* Using pip: `pip install spyder-unittest`

All dependencies will be automatically installed. You have to restart Spyder before
you can use the plugin.

## Usage

The plugin adds an item `Run unit tests` to the `Run` menu in Spyder.
Click on this to run the unit tests. After you specify the testing framework 
and the directory under which the tests are stored, the tests are run. 
The `Unit testing` window pane (displayed at the top of this file) will pop up 
with the results. If you are using `py.test`, you can double-click on a test
to view it in the editor.

If you want to run tests in a different directory or switch testing
frameworks, click `Configure` in the Options menu (cogwheel icon), 
which is located in the upper right corner of the `Unit testing` pane.

## Feedback

Bug reports, feature requests and other ideas are more than welcome on the
[issue tracker](https://github.com/spyder-ide/spyder-unittest/issues).
You may use <http://groups.google.com/group/spyderlib> for general discussion.

## Development

Development of the plugin is done at https://github.com/spyder-ide/spyder-unittest .
You can install the development version of the plugin by cloning the git repository
and running `pip install .`, possibly with the `--editable` flag.

The plugin has the following dependencies:

* [spyder](https://github.com/spyder-ide/spyder) (obviously), at least version 3.0
* [lxml](http://lxml.de/)
* the testing framework that you will be using: [py.test](https://pytest.org)
  and/or [nose](https://nose.readthedocs.io)

In order to run the tests distributed with this plugin, you need
[nose](https://nose.readthedocs.io), [py.test](https://pytest.org) 
and [pytest-qt](https://github.com/pytest-dev/pytest-qt). If you use Python 2, 
you also need [mock](https://github.com/testing-cabal/mock).

You are very welcome to submit code contributations in the form of pull
requests to the
[issue tracker](https://github.com/spyder-ide/spyder-unittest/issues).
GitHub is configured to run pull requests automatically against the test suite
and against several automatic style checkers using
[ciocheck](https://github.com/ContinuumIO/ciocheck).
The style checkers can be rather finicky so you may want to install ciocheck
locally and run them before submitting the code.

## Contributing

Everyone is welcome to contribute!

## Backers

Support us with a monthly donation and help us continue our activities.

[![Backers](https://opencollective.com/spyder/backers.svg)](https://opencollective.com/spyder#support)

## Sponsors

Become a sponsor to get your logo on our README on Github.

[![Sponsors](https://opencollective.com/spyder/sponsors.svg)](https://opencollective.com/spyder#support)
