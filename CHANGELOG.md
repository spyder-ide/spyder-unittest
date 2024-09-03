# History of changes

## Version 0.7.0 (2024/09/03)

This release updates the plugin to be used with Spyder 6 and fixes two bugs.

### Bug fixes

* Save command-line arguments ([Issue 216](https://github.com/spyder-ide/spyder-unittest/issues/216), [PR 217](https://github.com/spyder-ide/spyder-unittest/pull/217) by [@abdullahkhalids](https://github.com/abdullahkhalids))
  * Thanks to [Abdullah Khalid](https://github.com/abdullahkhalids) for this contribution!
* Update installation instructions to point to conda-forge ([Issue 220](https://github.com/spyder-ide/spyder-unittest/issues/220), [PR 223](https://github.com/spyder-ide/spyder-unittest/pull/223))

### Maintenance

* Make plugin compatible with Spyder 6 ([Issue 198](https://github.com/spyder-ide/spyder-unittest/issues/198), [Issue 210](https://github.com/spyder-ide/spyder-unittest/issues/210), [Issue 215](https://github.com/spyder-ide/spyder-unittest/issues/215), [Issue 221](https://github.com/spyder-ide/spyder-unittest/issues/221), [PR 223](https://github.com/spyder-ide/spyder-unittest/pull/223), [PR 222](https://github.com/spyder-ide/spyder-unittest/pull/222), [PR 218](https://github.com/spyder-ide/spyder-unittest/pull/218))


## Version 0.6.0 (2023-07-02)

### New Features

* Support nose2 and drop support for nose ([Issue 178](https://github.com/spyder-ide/spyder-unittest/issues/178), [PR 200](https://github.com/spyder-ide/spyder-unittest/pull/200))
* New menu item for running only a single test ([Issue 88](https://github.com/spyder-ide/spyder-unittest/issues/88), [PR 211](https://github.com/spyder-ide/spyder-unittest/pull/211))
* New configuration option for adding extra command-line arguments when running tests ([Issue 199](https://github.com/spyder-ide/spyder-unittest/issues/199), [PR 204](https://github.com/spyder-ide/spyder-unittest/pull/204))
* New configuration option to disable or enable abbreviating the test name ([Issue 122](https://github.com/spyder-ide/spyder-unittest/issues/122), [PR 208](https://github.com/spyder-ide/spyder-unittest/pull/208))

### Bug Fixes

* Execute `unittest` tests programmatically for robustness ([Issue 73](https://github.com/spyder-ide/spyder-unittest/issues/73), [Issue 76](https://github.com/spyder-ide/spyder-unittest/issues/76), [Issue 160](https://github.com/spyder-ide/spyder-unittest/issues/160), [PR 202](https://github.com/spyder-ide/spyder-unittest/pull/202))
* Support changed format of `unittest` output in Python 3.11 ([Issue 193](https://github.com/spyder-ide/spyder-unittest/issues/193), [PR 190](https://github.com/spyder-ide/spyder-unittest/pull/190), [PR 194](https://github.com/spyder-ide/spyder-unittest/pull/194), by [@juliangilbey](https://github.com/juliangilbey))
* Fix keyboard shortcut for running tests ([Issue 172](https://github.com/spyder-ide/spyder-unittest/issues/172), [PR 203](https://github.com/spyder-ide/spyder-unittest/pull/203))
* Use colours from Spyder's standard palette to get a uniform UI ([Issue 186](https://github.com/spyder-ide/spyder-unittest/issues/186), [PR 187](https://github.com/spyder-ide/spyder-unittest/pull/187))

### Maintenance

* Keep plugin up-to-date with latest changes in Spyder 5 ([Issue 195](https://github.com/spyder-ide/spyder-unittest/issues/195), [Issue 206](https://github.com/spyder-ide/spyder-unittest/issues/206), [Issue 209](https://github.com/spyder-ide/spyder-unittest/issues/209), [PR 197](https://github.com/spyder-ide/spyder-unittest/pull/197), [PR 207](https://github.com/spyder-ide/spyder-unittest/pull/207), [PR 214](https://github.com/spyder-ide/spyder-unittest/pull/214))
* Update translations ([PR 212](https://github.com/spyder-ide/spyder-unittest/pull/212))
* Fix integration tests for the plugin ([Issue 167](https://github.com/spyder-ide/spyder-unittest/issues/167), [PR 197](https://github.com/spyder-ide/spyder-unittest/pull/197))
* Update GitHub workflow for running tests ([PR 192](https://github.com/spyder-ide/spyder-unittest/pull/192), [PR 196](https://github.com/spyder-ide/spyder-unittest/pull/196), [PR 201](https://github.com/spyder-ide/spyder-unittest/pull/201))


## Version 0.5.1 (2022/09/03)

### New Features

* Tests are executed using the Python interpreter set in Preferences (instead of the interpreter that Spyder runs under), by [@stevetracvc](https://github.com/stevetracvc) ([Issue 65](https://github.com/spyder-ide/spyder-unittest/issues/65), [PR 174](https://github.com/spyder-ide/spyder-unittest/pull/174))
* You can display test coverage, though only for pytest; by [@stevetracvc](https://github.com/stevetracvc) ([Issue 33](https://github.com/spyder-ide/spyder-unittest/issues/33), [PR 175](https://github.com/spyder-ide/spyder-unittest/pull/175))

### Bug Fixes and Maintenance

* Use the correct environment when checking which testing frameworks are installed ([Issue 177](https://github.com/spyder-ide/spyder-unittest/issues/177), [PR 182](https://github.com/spyder-ide/spyder-unittest/pull/182))
* A message is shown if pytest exits abnormally ([Issue 176](https://github.com/spyder-ide/spyder-unittest/issues/176), [PR 180](https://github.com/spyder-ide/spyder-unittest/pull/180))
* The plugin no longer supports Python 2 ([Issue 156](https://github.com/spyder-ide/spyder-unittest/issues/156), [PR 179](https://github.com/spyder-ide/spyder-unittest/pull/179))
* Resolve warnings emitted by test suite for spyder-unittest ([Issue 173](https://github.com/spyder-ide/spyder-unittest/issues/173), [PR 181](https://github.com/spyder-ide/spyder-unittest/pull/181))


## Version 0.5.0 (2022/01/20)

* Update plugin for Spyder 5.2 ([Issue 163](https://github.com/spyder-ide/spyder-unittest/issues/163), [PR 166](https://github.com/spyder-ide/spyder-unittest/pull/166)). No version of the plugin is compatible with Spyder 5.0 or 5.1.
* Add partial translations for Brazilian Portuguese, French and German ([Issue 30](https://github.com/spyder-ide/spyder-unittest/issues/30), [PR 168](https://github.com/spyder-ide/spyder-unittest/pull/168), [PR 169](https://github.com/spyder-ide/spyder-unittest/pull/169), [PR 170](https://github.com/spyder-ide/spyder-unittest/pull/170)).


## Version 0.4.1 (2020/05/23)

This release fixes several bugs and other issues, allowing the plugin to be
used with Spyder 4.1. This release can not be used with Python 2.

### Issues Closed

* [Issue 154](https://github.com/spyder-ide/spyder-unittest/issues/154) - Make plugin depend on Python 3 ([PR 155](https://github.com/spyder-ide/spyder-unittest/pull/155))
* [Issue 145](https://github.com/spyder-ide/spyder-unittest/issues/145) - Go to test definition only works when run from root dir ([PR 149](https://github.com/spyder-ide/spyder-unittest/pull/149))
* [Issue 138](https://github.com/spyder-ide/spyder-unittest/issues/138) - Move CI to github actions ([PR 143](https://github.com/spyder-ide/spyder-unittest/pull/143))
* [Issue 127](https://github.com/spyder-ide/spyder-unittest/issues/127) - Teardown function's logs not captured ([PR 151](https://github.com/spyder-ide/spyder-unittest/pull/151))
* [Issue 115](https://github.com/spyder-ide/spyder-unittest/issues/115) - Report pytest plugins used while running a test suite ([PR 146](https://github.com/spyder-ide/spyder-unittest/pull/146))
* [Issue 47](https://github.com/spyder-ide/spyder-unittest/issues/47) - pytest statuses "expected-fail" and "unexpectedly passing" not yet reflected in Category ([PR 151](https://github.com/spyder-ide/spyder-unittest/pull/151))

In this release 6 issues were closed.

### Pull Requests Merged

* [PR 155](https://github.com/spyder-ide/spyder-unittest/pull/155) - PR: Require Python 3.5 or later ([154](https://github.com/spyder-ide/spyder-unittest/issues/154))
* [PR 153](https://github.com/spyder-ide/spyder-unittest/pull/153) - Fix tests that could never fail
* [PR 152](https://github.com/spyder-ide/spyder-unittest/pull/152) - Fix pytest output processing
* [PR 151](https://github.com/spyder-ide/spyder-unittest/pull/151) - Fix pytest backend ([47](https://github.com/spyder-ide/spyder-unittest/issues/47), [127](https://github.com/spyder-ide/spyder-unittest/issues/127))
* [PR 150](https://github.com/spyder-ide/spyder-unittest/pull/150) - Fix test_pytestrunner_start
* [PR 149](https://github.com/spyder-ide/spyder-unittest/pull/149) - Fix pytest test filename path resolution ([145](https://github.com/spyder-ide/spyder-unittest/issues/145))
* [PR 148](https://github.com/spyder-ide/spyder-unittest/pull/148) - Use set_status_label function
* [PR 147](https://github.com/spyder-ide/spyder-unittest/pull/147) - Fix abbreviator if name has parameters with dots
* [PR 146](https://github.com/spyder-ide/spyder-unittest/pull/146) - Show version info of test installed frameworks and their plugins ([115](https://github.com/spyder-ide/spyder-unittest/issues/115))
* [PR 144](https://github.com/spyder-ide/spyder-unittest/pull/144) - Dynamic sizing of text editor window ([12202](https://github.com/spyder-ide/spyder/issues/12202))
* [PR 143](https://github.com/spyder-ide/spyder-unittest/pull/143) - Move CI to GitHub actions ([138](https://github.com/spyder-ide/spyder-unittest/issues/138))
* [PR 141](https://github.com/spyder-ide/spyder-unittest/pull/141) - Fix status label
* [PR 139](https://github.com/spyder-ide/spyder-unittest/pull/139) - Fix TextEditor constructor

In this release 13 pull requests were closed.


## Version 0.4.0 (2020/01/07)

This release updates the plugin to be used with Spyder 4 and fixes some bugs.

### Issues Closed

* [Issue 133](https://github.com/spyder-ide/spyder-unittest/issues/133) - Colours make text hard to read when run in dark mode ([PR 135](https://github.com/spyder-ide/spyder-unittest/pull/135))
* [Issue 129](https://github.com/spyder-ide/spyder-unittest/issues/129) - Docstrings in test functions confuse unittest's output parser ([PR 134](https://github.com/spyder-ide/spyder-unittest/pull/134))
* [Issue 128](https://github.com/spyder-ide/spyder-unittest/issues/128) - KeyError: 'test not found' ([PR 132](https://github.com/spyder-ide/spyder-unittest/pull/132))

In this release 3 issues were closed.

### Pull Requests Merged

* [PR 135](https://github.com/spyder-ide/spyder-unittest/pull/135) - PR: Use appropriate colours when Spyder is in dark mode ([133](https://github.com/spyder-ide/spyder-unittest/issues/133))
* [PR 134](https://github.com/spyder-ide/spyder-unittest/pull/134) - PR: Allow for unittest tests to have docstrings ([129](https://github.com/spyder-ide/spyder-unittest/issues/129))
* [PR 132](https://github.com/spyder-ide/spyder-unittest/pull/132) - PR: Use nodeid provided by pytest in itemcollected hook ([128](https://github.com/spyder-ide/spyder-unittest/issues/128))
* [PR 131](https://github.com/spyder-ide/spyder-unittest/pull/131) - PR: Compatibility fixes for Spyder 4

In this release 4 pull requests were closed.


## Version 0.3.1 (2018/06/15)

This version fixes some bugs and also includes some cosmetic changes.

### Issues Closed

* [Issue 117](https://github.com/spyder-ide/spyder-unittest/issues/117) - Rename "py.test" to "pytest" throughout ([PR 119](https://github.com/spyder-ide/spyder-unittest/pull/119))
* [Issue 113](https://github.com/spyder-ide/spyder-unittest/issues/113) - NameError in test file causes internal error ([PR 118](https://github.com/spyder-ide/spyder-unittest/pull/118))
* [Issue 112](https://github.com/spyder-ide/spyder-unittest/issues/112) - Plugin confused by tests writing to `sys.__stdout__` ([PR 114](https://github.com/spyder-ide/spyder-unittest/pull/114))

In this release 3 issues were closed.

### Pull Requests Merged

* [PR 121](https://github.com/spyder-ide/spyder-unittest/pull/121) - PR: Update readme to remove funding appeal, harmonize with other readmes and minor fixes
* [PR 120](https://github.com/spyder-ide/spyder-unittest/pull/120) - Remove unused variables when initializing localization
* [PR 119](https://github.com/spyder-ide/spyder-unittest/pull/119) - Replace 'py.test' by 'pytest' ([117](https://github.com/spyder-ide/spyder-unittest/issues/117))
* [PR 118](https://github.com/spyder-ide/spyder-unittest/pull/118) - Use str() to convert pytest's longrepr to a string ([113](https://github.com/spyder-ide/spyder-unittest/issues/113))
* [PR 114](https://github.com/spyder-ide/spyder-unittest/pull/114) - Use ZMQ sockets to communicate results of pytest run ([112](https://github.com/spyder-ide/spyder-unittest/issues/112))

In this release 5 pull requests were closed.

## Version 0.3.0 (2018/02/16)

This version includes improved support of `py.test` (test results are displayed as they come in, double clicking on a test result opens the test in the editor) as well as various other improvements.

### Issues Closed

* [Issue 106](https://github.com/spyder-ide/spyder-unittest/issues/106) - After sorting, test details are lost ([PR 110](https://github.com/spyder-ide/spyder-unittest/pull/110))
* [Issue 103](https://github.com/spyder-ide/spyder-unittest/issues/103) - "Go to" not working unless working directory is correctly set ([PR 109](https://github.com/spyder-ide/spyder-unittest/pull/109))
* [Issue 98](https://github.com/spyder-ide/spyder-unittest/issues/98) - Running unittest tests within py.test results in error ([PR 102](https://github.com/spyder-ide/spyder-unittest/pull/102))
* [Issue 96](https://github.com/spyder-ide/spyder-unittest/issues/96) - Use new colors for passed and failed tests ([PR 108](https://github.com/spyder-ide/spyder-unittest/pull/108))
* [Issue 94](https://github.com/spyder-ide/spyder-unittest/issues/94) - Enable sorting in table of test results ([PR 104](https://github.com/spyder-ide/spyder-unittest/pull/104))
* [Issue 93](https://github.com/spyder-ide/spyder-unittest/issues/93) - Handle errors in py.test's collection phase ([PR 99](https://github.com/spyder-ide/spyder-unittest/pull/99))
* [Issue 92](https://github.com/spyder-ide/spyder-unittest/issues/92) - Retitle "Kill" (tests) button to "Stop" ([PR 107](https://github.com/spyder-ide/spyder-unittest/pull/107))
* [Issue 89](https://github.com/spyder-ide/spyder-unittest/issues/89) - Write tests for UnitTestPlugin ([PR 95](https://github.com/spyder-ide/spyder-unittest/pull/95))
* [Issue 87](https://github.com/spyder-ide/spyder-unittest/issues/87) - Don't display test time when using unittest ([PR 105](https://github.com/spyder-ide/spyder-unittest/pull/105))
* [Issue 86](https://github.com/spyder-ide/spyder-unittest/issues/86) - Use sensible precision when displaying test times ([PR 105](https://github.com/spyder-ide/spyder-unittest/pull/105))
* [Issue 83](https://github.com/spyder-ide/spyder-unittest/issues/83) - Changes for compatibility with new undocking behavior of Spyder ([PR 84](https://github.com/spyder-ide/spyder-unittest/pull/84))
* [Issue 77](https://github.com/spyder-ide/spyder-unittest/issues/77) - Be smarter about abbreviating test names
* [Issue 71](https://github.com/spyder-ide/spyder-unittest/issues/71) - Save before running tests (?) ([PR 101](https://github.com/spyder-ide/spyder-unittest/pull/101))
* [Issue 50](https://github.com/spyder-ide/spyder-unittest/issues/50) - Use py.test's API to run tests ([PR 91](https://github.com/spyder-ide/spyder-unittest/pull/91))
* [Issue 43](https://github.com/spyder-ide/spyder-unittest/issues/43) - Save selected test framework ([PR 90](https://github.com/spyder-ide/spyder-unittest/pull/90))
* [Issue 31](https://github.com/spyder-ide/spyder-unittest/issues/31) - Add issues/PRs templates ([PR 111](https://github.com/spyder-ide/spyder-unittest/pull/111))
* [Issue 13](https://github.com/spyder-ide/spyder-unittest/issues/13) - Display test results as they come in ([PR 91](https://github.com/spyder-ide/spyder-unittest/pull/91))
* [Issue 12](https://github.com/spyder-ide/spyder-unittest/issues/12) - Double clicking on test name should take you somewhere useful ([PR 100](https://github.com/spyder-ide/spyder-unittest/pull/100))

In this release 18 issues were closed.

### Pull Requests Merged

* [PR 111](https://github.com/spyder-ide/spyder-unittest/pull/111) - Update docs for new release ([31](https://github.com/spyder-ide/spyder-unittest/issues/31))
* [PR 110](https://github.com/spyder-ide/spyder-unittest/pull/110) - Emit modelReset after sorting test results ([106](https://github.com/spyder-ide/spyder-unittest/issues/106))
* [PR 109](https://github.com/spyder-ide/spyder-unittest/pull/109) - Store full path to file containing test in TestResult ([103](https://github.com/spyder-ide/spyder-unittest/issues/103))
* [PR 108](https://github.com/spyder-ide/spyder-unittest/pull/108) - Use paler shade of red as background for failing tests ([96](https://github.com/spyder-ide/spyder-unittest/issues/96))
* [PR 107](https://github.com/spyder-ide/spyder-unittest/pull/107) - Relabel 'Kill' button ([92](https://github.com/spyder-ide/spyder-unittest/issues/92))
* [PR 105](https://github.com/spyder-ide/spyder-unittest/pull/105) - Improve display of test times ([87](https://github.com/spyder-ide/spyder-unittest/issues/87), [86](https://github.com/spyder-ide/spyder-unittest/issues/86))
* [PR 104](https://github.com/spyder-ide/spyder-unittest/pull/104) - Allow user to sort tests ([94](https://github.com/spyder-ide/spyder-unittest/issues/94))
* [PR 102](https://github.com/spyder-ide/spyder-unittest/pull/102) - Use nodeid when collecting tests using py.test ([98](https://github.com/spyder-ide/spyder-unittest/issues/98))
* [PR 101](https://github.com/spyder-ide/spyder-unittest/pull/101) - Save all files before running tests ([71](https://github.com/spyder-ide/spyder-unittest/issues/71))
* [PR 100](https://github.com/spyder-ide/spyder-unittest/pull/100) - Implement go to test definition for py.test ([12](https://github.com/spyder-ide/spyder-unittest/issues/12))
* [PR 99](https://github.com/spyder-ide/spyder-unittest/pull/99) - Handle errors encountered when py.test collect tests ([93](https://github.com/spyder-ide/spyder-unittest/issues/93))
* [PR 97](https://github.com/spyder-ide/spyder-unittest/pull/97) - Abbreviate module names when displaying test names
* [PR 95](https://github.com/spyder-ide/spyder-unittest/pull/95) - Add unit tests for plugin ([89](https://github.com/spyder-ide/spyder-unittest/issues/89))
* [PR 91](https://github.com/spyder-ide/spyder-unittest/pull/91) - Display py.test results as they come in ([50](https://github.com/spyder-ide/spyder-unittest/issues/50), [13](https://github.com/spyder-ide/spyder-unittest/issues/13))
* [PR 90](https://github.com/spyder-ide/spyder-unittest/pull/90) - Load and save configuration for tests ([43](https://github.com/spyder-ide/spyder-unittest/issues/43))
* [PR 85](https://github.com/spyder-ide/spyder-unittest/pull/85) - Remove PySide from CI scripts and remove Scrutinizer
* [PR 84](https://github.com/spyder-ide/spyder-unittest/pull/84) - PR: Show undock action ([83](https://github.com/spyder-ide/spyder-unittest/issues/83))

In this release 17 pull requests were closed.


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
