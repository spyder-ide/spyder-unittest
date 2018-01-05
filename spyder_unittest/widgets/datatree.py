# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Model and view classes for storing and displaying test results."""

# Standard library imports
from collections import Counter

# Third party imports
from qtpy import PYQT4
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QFont
from qtpy.QtWidgets import QTreeView
from spyder.config.base import get_translation

# Local imports
from spyder_unittest.backend.abbreviator import Abbreviator
from spyder_unittest.backend.runnerbase import Category

try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

COLORS = {
    Category.OK: QBrush(QColor("#C1FFBA")),
    Category.FAIL: QBrush(QColor("#FF0000")),
    Category.SKIP: QBrush(QColor("#C5C5C5")),
    Category.PENDING: QBrush(QColor("#C5C5C5"))
}

STATUS_COLUMN = 0
NAME_COLUMN = 1
MESSAGE_COLUMN = 2
TIME_COLUMN = 3

HEADERS = [_('Status'), _('Name'), _('Message'), _('Time (ms)')]

TOPLEVEL_ID = 2 ** 32 - 1


class TestDataView(QTreeView):
    """Tree widget displaying test results."""

    def __init__(self, parent=None):
        """Constructor."""
        QTreeView.__init__(self, parent)
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setItemsExpandable(True)
        self.setSortingEnabled(False)

    def reset(self):
        """
        Reset internal state of the view and read all data afresh from model.

        This function is called whenever the model data changes drastically.
        """
        QTreeView.reset(self)
        self.resizeColumns()
        self.spanFirstColumn(0, self.model().rowCount() - 1)

    def rowsInserted(self, parent, firstRow, lastRow):
        """Called when rows are inserted."""
        QTreeView.rowsInserted(self, parent, firstRow, lastRow)
        self.resizeColumns()

    def dataChanged(self, topLeft, bottomRight, roles=[]):
        """Called when data in model has changed."""
        if PYQT4:
            QTreeView.dataChanged(self, topLeft, bottomRight)
        else:
            QTreeView.dataChanged(self, topLeft, bottomRight, roles)
        self.resizeColumns()
        while topLeft.parent().isValid():
            topLeft = topLeft.parent()
        while bottomRight.parent().isValid():
            bottomRight = bottomRight.parent()
        self.spanFirstColumn(topLeft.row(), bottomRight.row())

    def resizeColumns(self):
        """Resize column to fit their contents."""
        for col in range(self.model().columnCount()):
            self.resizeColumnToContents(col)

    def spanFirstColumn(self, firstRow, lastRow):
        """
        Make first column span whole row in second-level children.

        Note: Second-level children display the test output.

        Arguments
        ---------
        firstRow : int
            Index of first row to act on.
        lastRow : int
            Index of last row to act on. Note that this row is included in the
            range, following Qt conventions and contrary to Python conventions.
        """
        model = self.model()
        for row in range(firstRow, lastRow + 1):
            index = model.index(row, 0)
            for i in range(model.rowCount(index)):
                self.setFirstColumnSpanned(i, index, True)

    # Not yet implemented ...
    # def item_activated(self, item):
    #     """Called if user clicks on item."""
    #     COL_POS = 0  # Position is not displayed but set as Qt.UserRole
    #     filename, line_no = item.data(COL_POS, Qt.UserRole)
    #     self.parent().edit_goto.emit(filename, line_no, '')


class TestDataModel(QAbstractItemModel):
    """
    Model class storing test results for display.

    Test results are stored as a list of TestResults in the property
    `self.testresults`. Every test is exposed as a child of the root node,
    with extra information as second-level nodes.

    As in every model, an iteem of data is identified by its index, which is
    a tuple (row, column, id). The id is TOPLEVEL_ID for top-level items.
    For level-2 items, the id is the index of the test in `self.testresults`.

    Signals
    -------
    sig_summary(str)
       Emitted with new summary if test results change.
    """

    sig_summary = Signal(str)

    def __init__(self, parent=None):
        """Constructor."""
        QAbstractItemModel.__init__(self, parent)
        self.abbreviator = Abbreviator()
        self.testresults = []
        try:
            self.monospace_font = parent.window().editor.get_plugin_font()
        except AttributeError:  # If run standalone for testing
            self.monospace_font = QFont("Courier New")
            self.monospace_font.setPointSize(10)

    @property
    def testresults(self):
        """List of test results."""
        return self._testresults

    @testresults.setter
    def testresults(self, new_value):
        """Setter for test results."""
        self.beginResetModel()
        self.abbreviator = Abbreviator(res.name for res in new_value)
        self._testresults = new_value
        self.endResetModel()
        self.emit_summary()

    def add_testresults(self, new_tests):
        """
        Add new test results to the model.

        Arguments
        ---------
        new_tests : list of TestResult
        """
        firstRow = len(self.testresults)
        lastRow = firstRow + len(new_tests) - 1
        for test in new_tests:
            self.abbreviator.add(test.name)
        self.beginInsertRows(QModelIndex(), firstRow, lastRow)
        self.testresults.extend(new_tests)
        self.endInsertRows()
        self.emit_summary()

    def update_testresults(self, new_results):
        """
        Update some test results by new results.

        The tests in `new_results` should already be included in
        `self.testresults` (otherwise a `KeyError` is raised). This function
        replaces the existing results by `new_results`.

        Arguments
        ---------
        new_results: list of TestResult
        """
        idx_min = idx_max = None
        for new_result in new_results:
            for (idx, old_result) in enumerate(self.testresults):
                if old_result.name == new_result.name:
                    self.testresults[idx] = new_result
                    if idx_min is None:
                        idx_min = idx_max = idx
                    else:
                        idx_min = min(idx_min, idx)
                        idx_max = max(idx_max, idx)
                    break
            else:
                raise KeyError('test not found')
        if idx_min is not None:
            self.dataChanged.emit(self.index(idx_min, 0),
                                  self.index(idx_max, len(HEADERS) - 1))
            self.emit_summary()

    def index(self, row, column, parent=QModelIndex()):
        """
        Construct index to given item of data.

        If `parent` not valid, then the item of data is on the top level.
        """
        if not self.hasIndex(row, column, parent):  # check bounds etc.
            return QModelIndex()
        if not parent.isValid():
            return self.createIndex(row, column, TOPLEVEL_ID)
        else:
            testresult_index = parent.row()
            return self.createIndex(row, column, testresult_index)

    def data(self, index, role):
        """
        Return data in `role` for item of data that `index` points to.

        If `role` is `DisplayRole`, then return string to display.
        If `role` is `TooltipRole`, then return string for tool tip.
        If `role` is `FontRole`, then return monospace font for level-2 items.
        If `role` is `BackgroundRole`, then return background color
        """
        if not index.isValid():
            return None
        row = index.row()
        column = index.column()
        id = index.internalId()
        if role == Qt.DisplayRole:
            if id != TOPLEVEL_ID:
                return self.testresults[id].extra_text[index.row()]
            elif column == STATUS_COLUMN:
                return self.testresults[row].status
            elif column == NAME_COLUMN:
                return self.abbreviator.abbreviate(self.testresults[row].name)
            elif column == MESSAGE_COLUMN:
                return self.testresults[row].message
            elif column == TIME_COLUMN:
                time = self.testresults[row].time
                return str(time * 1e3) if time else ''
        elif role == Qt.ToolTipRole:
            if id == TOPLEVEL_ID and column == NAME_COLUMN:
                return self.testresults[row].name
        elif role == Qt.FontRole:
            if id != TOPLEVEL_ID:
                return self.monospace_font
        elif role == Qt.BackgroundRole:
            if id == TOPLEVEL_ID:
                testresult = self.testresults[row]
                return COLORS[testresult.category]
        else:
            return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return data for specified header."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return HEADERS[section]
        else:
            return None

    def parent(self, index):
        """Return index to parent of item that `index` points to."""
        if not index.isValid():
            return QModelIndex()
        id = index.internalId()
        if id == TOPLEVEL_ID:
            return QModelIndex()
        else:
            return self.index(id, 0)

    def rowCount(self, parent=QModelIndex()):
        """Return number of rows underneath `parent`."""
        if not parent.isValid():
            return len(self.testresults)
        if parent.internalId() == TOPLEVEL_ID and parent.column() == 0:
            return len(self.testresults[parent.row()].extra_text)
        return 0

    def columnCount(self, parent=QModelIndex()):
        """Return number of rcolumns underneath `parent`."""
        if not parent.isValid():
            return len(HEADERS)
        else:
            return 1

    def summary(self):
        """Return summary for current results."""
        def n_test_or_tests(n):
            test_or_tests = _('test') if n == 1 else _('tests')
            return '{} {}'.format(n, test_or_tests)

        if not len(self.testresults):
            return _('No results to show.')
        counts = Counter(res.category for res in self.testresults)
        if all(counts[cat] == 0
               for cat in (Category.FAIL, Category.OK, Category.SKIP)):
            txt = n_test_or_tests(counts[Category.PENDING])
            return _('collected {}').format(txt)
        msg = _('{} failed').format(n_test_or_tests(counts[Category.FAIL]))
        msg += _(', {} passed').format(counts[Category.OK])
        if counts[Category.SKIP]:
            msg += _(', {} other').format(counts[Category.SKIP])
        if counts[Category.PENDING]:
            msg += _(', {} pending').format(counts[Category.PENDING])
        return msg

    def emit_summary(self):
        """Emit sig_summary with summary for current results."""
        self.sig_summary.emit(self.summary())
