# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tree widget with testing data."""

# Standard library imports
from collections import Counter

# Third party imports
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QFont
from qtpy.QtWidgets import QTreeWidget, QTreeWidgetItem
from spyder.config.base import get_translation

# Local imports
from spyder_unittest.backend.runnerbase import Category

try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

COL_POS = 0  # Position is not displayed but set as Qt.UserRole

COLORS = {
    Category.OK: QBrush(QColor("#C1FFBA")),
    Category.FAIL: QBrush(QColor("#FF0000")),
    Category.SKIP: QBrush(QColor("#C5C5C5"))
}


class DataTree(QTreeWidget):
    """Convenience tree widget to store and view unit testing data."""

    def __init__(self, parent=None):
        """Convenience tree widget to store and view unit testing data."""
        QTreeWidget.__init__(self, parent)
        self.header_list = [
            _('Status'), _('Name'), _('Message'), _('Time (ms)')
        ]
        self.testresults = []
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setColumnCount(len(self.header_list))
        self.setHeaderLabels(self.header_list)
        self.clear()
        self.setItemsExpandable(True)
        self.setSortingEnabled(False)

    def show_tree(self):
        """Populate the tree with unit testing data and display it."""
        self.clear()  # Clear before re-populating
        msg = self.populate_tree()
        for col in range(self.columnCount() - 1):
            self.resizeColumnToContents(col)
        return msg

    def populate_tree(self):
        """Create each item (and associated data) in the tree."""
        if not len(self.testresults):
            return _('No results to show.')

        try:
            monospace_font = self.window().editor.get_plugin_font()
        except AttributeError:  # If run standalone for testing
            monospace_font = QFont("Courier New")
            monospace_font.setPointSize(10)

        for testresult in self.testresults:
            testcase_item = QTreeWidgetItem(self)
            testcase_item.setData(0, Qt.DisplayRole, testresult.status)
            testcase_item.setData(1, Qt.DisplayRole, testresult.name)
            fullname = '{0}.{1}'.format(testresult.module, testresult.name)
            testcase_item.setToolTip(1, fullname)
            testcase_item.setData(2, Qt.DisplayRole, testresult.message)
            testcase_item.setData(3, Qt.DisplayRole, testresult.time * 1e3)
            color = COLORS[testresult.category]
            for col in range(self.columnCount()):
                testcase_item.setBackground(col, color)
            if testresult.extra_text:
                for line in testresult.extra_text.rstrip().split("\n"):
                    error_content_item = QTreeWidgetItem(testcase_item)
                    error_content_item.setData(0, Qt.DisplayRole, line)
                    error_content_item.setFirstColumnSpanned(True)
                    error_content_item.setFont(0, monospace_font)

        counts = Counter(res.category for res in self.testresults)
        if counts[Category.FAIL] == 1:
            test_or_tests = _('test')
        else:
            test_or_tests = _('tests')
        failed_txt = '{} {} failed'.format(counts[Category.FAIL],
                                           test_or_tests)
        passed_txt = '{} passed'.format(counts[Category.OK])
        other_txt = '{} other'.format(counts[Category.SKIP])
        msg = '<b>{}, {}, {}</b>'.format(failed_txt, passed_txt, other_txt)
        return msg

    def item_activated(self, item):
        """Called if user clicks on item."""
        filename, line_no = item.data(COL_POS, Qt.UserRole)
        self.parent().edit_goto.emit(filename, line_no, '')
