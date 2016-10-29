spyder_unittesting
==================

This is a plugin for Spyder that integrates popular unit test
frameworks. It allows you to run tests and view the results.


Status
------

This is a work in progress. Only basic functionality is implemented.
At the moment, it only supports the py.test testing framework.

Installation
------------

See https://github.com/spyder-ide/spyder/wiki/User-plugins but in
short, the following command installs the development version of the
unittesting plugin:

    pip install git+git://github.com/spyder-ide/spyder-unittest.git

The plugin is not yet included in PyPI.

Usage
-----

The plugin adds an item `Run unit tests` to the `Run` menu in Spyder.
Click on this to run the unit tests. A window pane will pop up with
the results.
