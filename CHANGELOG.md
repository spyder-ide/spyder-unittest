# History of changes

## Version 0.2.0 (2017/08/20)

The main change in this version is that it adds support for tests written 
using the `unittest` framework available in the standard Python library.

### Issues Closed

* [Issue 79](https://github.com/spyder-ide/spyder-unittest/issues/79) - Remove QuantifiedCode
* [Issue 74](https://github.com/spyder-ide/spyder-unittest/issues/74) - Also test against spyder's master branch in CI
* [Issue 70](https://github.com/spyder-ide/spyder-unittest/issues/70) - Point contributors to ciocheck
* [Issue 41](https://github.com/spyder-ide/spyder-unittest/issues/41) - Add function for registering test frameworks
* [Issue 15](https://github.com/spyder-ide/spyder-unittest/issues/15) - Check whether test framework is installed
* [Issue 11](https://github.com/spyder-ide/spyder-unittest/issues/11) - Abbreviate test names
* [Issue 4](https://github.com/spyder-ide/spyder-unittest/issues/4) - Add unittest support

In this release 7 issues were closed.

### Pull Requests Merged

* [PR 82](https://github.com/spyder-ide/spyder-unittest/pull/82) - Enable Scrutinizer
* [PR 81](https://github.com/spyder-ide/spyder-unittest/pull/81) - Update README.md
* [PR 80](https://github.com/spyder-ide/spyder-unittest/pull/80) - Install Spyder from github 3.x branch when testing on Circle
* [PR 78](https://github.com/spyder-ide/spyder-unittest/pull/78) - Properly handle test frameworks which are not installed
* [PR 75](https://github.com/spyder-ide/spyder-unittest/pull/75) - Shorten test name displayed in widget
* [PR 72](https://github.com/spyder-ide/spyder-unittest/pull/72) - Support unittest
* [PR 69](https://github.com/spyder-ide/spyder-unittest/pull/69) - Process coverage stats using coveralls
* [PR 68](https://github.com/spyder-ide/spyder-unittest/pull/68) - Add framework registry for associating testing frameworks with runners
* [PR 67](https://github.com/spyder-ide/spyder-unittest/pull/67) - Install the tests alongside the module

In this release 9 pull requests were closed.

## Version 0.1.2 (2017/03/04)

This version fixes a bug in the packaging code.

### Pull Requests Merged

* [PR 63](https://github.com/spyder-ide/spyder-unittest/pull/63) - Fix parsing of module version

In this release 1 pull request was closed.


## Version 0.1.1 (2017/02/11)

This version improves the packaging. The code itself was not changed. 

### Issues Closed

* [Issue 58](https://github.com/spyder-ide/spyder-unittest/issues/58) - Normalized copyright information
* [Issue 57](https://github.com/spyder-ide/spyder-unittest/issues/57) - Depend on nose and pytest at installation
* [Issue 56](https://github.com/spyder-ide/spyder-unittest/issues/56) - Add the test suite to the release tarball

In this release 3 issues were closed.

### Pull Requests Merged

* [PR 59](https://github.com/spyder-ide/spyder-unittest/pull/59) - Improve distributed package

In this release 1 pull request was closed.


## Version 0.1.0 (2017/02/05)

Initial release, supporting nose and py.test frameworks.