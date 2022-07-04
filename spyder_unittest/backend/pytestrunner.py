# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for pytest framework."""

# Standard library imports
import os
import os.path as osp
import re

# Local imports
from spyder.config.base import get_translation
from spyder_unittest.backend.runnerbase import (Category, RunnerBase,
                                                TestResult, COV_TEST_NAME)
from spyder_unittest.backend.zmqstream import ZmqStreamReader

try:
    _ = get_translation('spyder_unittest')
except KeyError:
    import gettext
    _ = gettext.gettext


class PyTestRunner(RunnerBase):
    """Class for running tests within pytest framework."""

    module = 'pytest'
    name = 'pytest'

    def get_versions(self):
        """Return versions of framework and its plugins."""
        import pytest
        versions = ['pytest {}'.format(pytest.__version__)]

        class GetPluginVersionsPlugin():
            def pytest_cmdline_main(self, config):
                nonlocal versions
                plugininfo = config.pluginmanager.list_plugin_distinfo()
                if plugininfo:
                    for plugin, dist in plugininfo:
                        versions.append("   {} {}".format(dist.project_name,
                                                          dist.version))

        # --capture=sys needed on Windows to avoid
        # ValueError: saved filedescriptor not valid anymore
        pytest.main(['-V', '--capture=sys'],
                    plugins=[GetPluginVersionsPlugin()])
        return versions

    def create_argument_list(self, config, cov_path):
        """Create argument list for testing process."""
        pyfile = os.path.join(os.path.dirname(__file__), 'pytestworker.py')
        arguments = [pyfile, str(self.reader.port)]
        if config.coverage:
            arguments += [f'--cov={cov_path}', '--cov-report=term-missing']
        return arguments


    def start(self, config, cov_path, executable, pythonpath):
        """Start process which will run the unit test suite."""
        self.config = config
        self.reader = ZmqStreamReader()
        self.reader.sig_received.connect(self.process_output)
        RunnerBase.start(self, config, cov_path, executable, pythonpath)

    def process_output(self, output):
        """
        Process output of test process.

        Parameters
        ----------
        output : list
            list of decoded Python object sent by test process.
        """
        collected_list = []
        collecterror_list = []
        starttest_list = []
        result_list = []
        for result_item in output:
            if result_item['event'] == 'config':
                self.rootdir = result_item['rootdir']
            elif result_item['event'] == 'collected':
                testname = convert_nodeid_to_testname(result_item['nodeid'])
                collected_list.append(testname)
            elif result_item['event'] == 'collecterror':
                tupl = logreport_collecterror_to_tuple(result_item)
                collecterror_list.append(tupl)
            elif result_item['event'] == 'starttest':
                starttest_list.append(logreport_starttest_to_str(result_item))
            elif result_item['event'] == 'logreport':
                testresult = logreport_to_testresult(result_item, self.rootdir)
                result_list.append(testresult)

        if collected_list:
            self.sig_collected.emit(collected_list)
        if collecterror_list:
            self.sig_collecterror.emit(collecterror_list)
        if starttest_list:
            self.sig_starttest.emit(starttest_list)
        if result_list:
            self.sig_testresult.emit(result_list)

    def process_coverage(self, output):
        """Search the output text for coverage details.

        Called by the function 'finished' at the very end.
        """
        cov_results = re.search(
            r'-*? coverage:.*?-*\nTOTAL\s.*?\s(\d*?)\%.*\n=*',
            output, flags=re.S)
        if cov_results:
            total_coverage = cov_results.group(1)
            cov_report = TestResult(
                Category.COVERAGE, f'{total_coverage}%', COV_TEST_NAME)
            # create a fake test, then emit the coverage as the result
            # This gives overall test coverage, used in TestDataModel.summary
            self.sig_collected.emit([COV_TEST_NAME])
            self.sig_testresult.emit([cov_report])

            # also build a result for each file's coverage
            header = "".join(cov_results.group(0).split("\n")[1:3])
            # coverage report columns:
            # Name  Stmts   Miss  Cover   Missing
            for row in re.findall(
                    r'^((.*?\.py) .*?(\d+%).*?(\d[\d\,\-\ ]*)?)$',
                    cov_results.group(0), flags=re.M):
                lineno = (int(re.search(r'^(\d*)', row[3]).group(1)) - 1
                          if row[3] else None)
                file_cov = TestResult(
                    Category.COVERAGE, row[2], row[1],
                    message=_('Missing: {}').format(row[3] if row[3] else _("(none)")),
                    extra_text=_('{}\n{}').format(header, row[0]), filename=row[1],
                    lineno=lineno)
                self.sig_collected.emit([row[1]])
                self.sig_testresult.emit([file_cov])

    def finished(self):
        """
        Called when the unit test process has finished.

        This function emits `sig_finished`.
        """
        self.reader.close()
        output = self.read_all_process_output()
        if self.config.coverage:
            self.process_coverage(output)
        self.sig_finished.emit([], output)


def normalize_module_name(name):
    """
    Convert module name reported by pytest to Python conventions.

    This function strips the .py suffix and replaces '/' by '.', so that
    'ham/spam.py' becomes 'ham.spam'.
    """
    if name.endswith('.py'):
        name = name[:-3]
    return name.replace('/', '.')


def convert_nodeid_to_testname(nodeid):
    """Convert a nodeid to a test name."""
    module, name = nodeid.split('::', 1)
    module = normalize_module_name(module)
    return '{}.{}'.format(module, name)


def logreport_collecterror_to_tuple(report):
    """Convert a 'collecterror' logreport to a (str, str) tuple."""
    module = normalize_module_name(report['nodeid'])
    return (module, report['longrepr'])


def logreport_starttest_to_str(report):
    """Convert a 'starttest' logreport to a str."""
    return convert_nodeid_to_testname(report['nodeid'])


def logreport_to_testresult(report, rootdir):
    """Convert a logreport sent by test process to a TestResult."""
    status = report['outcome']
    if report['outcome'] in ('failed', 'xpassed') or report['witherror']:
        cat = Category.FAIL
    elif report['outcome'] in ('passed', 'xfailed'):
        cat = Category.OK
    else:
        cat = Category.SKIP
    testname = convert_nodeid_to_testname(report['nodeid'])
    message = report.get('message', '')
    extra_text = report.get('longrepr', '')
    if 'sections' in report:
        if extra_text:
            extra_text +=  '\n'
        for (heading, text) in report['sections']:
            extra_text += '----- {} -----\n{}'.format(heading, text)
    filename = osp.join(rootdir, report['filename'])
    result = TestResult(cat, status, testname, message=message,
                        time=report['duration'], extra_text=extra_text,
                        filename=filename, lineno=report['lineno'])
    return result
