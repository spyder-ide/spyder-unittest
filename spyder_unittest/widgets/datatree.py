# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Model and view classes for storing and displaying test results."""

# Standard library imports
from collections import Counter
from operator import attrgetter

# Third party imports
from qtpy import PYQT4
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QFont
from qtpy.QtWidgets import QMenu, QTreeView
from spyder.config.base import get_translation
from spyder.utils.palette import QStylePalette, SpyderPalette
from spyder.utils.qthelpers import create_action

# Local imports
from spyder_unittest.backend.abbreviator import Abbreviator
from spyder_unittest.backend.runnerbase import Category

try:
    _ = get_translation('spyder_unittest')
except KeyError:
    import gettext
    _ = gettext.gettext

COLORS = {
    Category.OK:       SpyderPalette.COLOR_SUCCESS_1,
    Category.FAIL:     SpyderPalette.COLOR_ERROR_1,
    Category.SKIP:     SpyderPalette.COLOR_WARN_1,
    Category.PENDING:  QStylePalette.COLOR_BACKGROUND_1,
    Category.COVERAGE: QStylePalette.COLOR_ACCENT_1
}

STATUS_COLUMN = 0
NAME_COLUMN = 1
MESSAGE_COLUMN = 2
TIME_COLUMN = 3

HEADERS = [_('Status'), _('Name'), _('Message'), _('Time (ms)')]

TOPLEVEL_ID = 2 ** 32 - 1


class TestDataView(QTreeView):
    """
    Tree widget displaying test results.

    Signals
    -------
    sig_edit_goto(str, int): Emitted if editor should go to some position.
        Arguments are file name and line number (zero-based).
    """

    sig_edit_goto = Signal(str, int)
    __test__ = False  # this is not a pytest test class

    def __init__(self, parent=None):
        """Constructor."""
        QTreeView.__init__(self, parent)
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setItemsExpandable(True)
        self.setSortingEnabled(True)
        self.header().setSortIndicatorShown(False)
        self.header().sortIndicatorChanged.connect(self.sortByColumn)
        self.header().sortIndicatorChanged.connect(
                lambda col, order: self.header().setSortIndicatorShown(True))
        self.setExpandsOnDoubleClick(False)
        self.doubleClicked.connect(self.go_to_test_definition)

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
        self.spanFirstColumn(firstRow, lastRow)

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

    def contextMenuEvent(self, event):
        """Called when user requests a context menu."""
        index = self.indexAt(event.pos())
        index = self.make_index_canonical(index)
        if not index:
            return  # do nothing if no item under mouse position
        contextMenu = self.build_context_menu(index)
        contextMenu.exec_(event.globalPos())

    def go_to_test_definition(self, index):
        """Ask editor to go to definition of test corresponding to index."""
        index = self.make_index_canonical(index)
        filename, lineno = self.model().data(index, Qt.UserRole)
        if filename is not None:
            if lineno is None:
                lineno = 0
            self.sig_edit_goto.emit(filename, lineno)

    def make_index_canonical(self, index):
        """
        Convert given index to canonical index for the same test.

        For every test, the canonical index points to the item on the top level
        in the first column corresponding to the given position. If the given
        index is invalid, then return None.
        """
        if not index.isValid():
            return None
        while index.parent().isValid():  # find top-level node
            index = index.parent()
        index = index.sibling(index.row(), 0)  # go to first column
        return index

    def build_context_menu(self, index):
        """Build context menu for test item that given index points to."""
        contextMenu = QMenu(self)
        if self.isExpanded(index):
            menuItem = create_action(self, _('Collapse'),
                                     triggered=lambda: self.collapse(index))
        else:
            menuItem = create_action(self, _('Expand'),
                                     triggered=lambda: self.expand(index))
            menuItem.setEnabled(self.model().hasChildren(index))
        contextMenu.addAction(menuItem)
        menuItem = create_action(
                self, _('Go to definition'),
                triggered=lambda: self.go_to_test_definition(index))
        test_location = self.model().data(index, Qt.UserRole)
        menuItem.setEnabled(test_location[0] is not None)
        contextMenu.addAction(menuItem)
        return contextMenu

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


class TestDataModel(QAbstractItemModel):
    """
    Model class storing test results for display.

    Test results are stored as a list of TestResults in the property
    `self.testresults`. Every test is exposed as a child of the root node,
    with extra information as second-level nodes.

    As in every model, an iteem of data is identified by its index, which is
    a tuple (row, column, id). The id is TOPLEVEL_ID for top-level items.
    For level-2 items, the id is the index of the test in `self.testresults`.

    Attributes
    ----------
    is_dark_interface : bool
        Whether to use colours appropriate for a dark user interface.

    Signals
    -------
    sig_summary(str)
       Emitted with new summary if test results change.
    """

    sig_summary = Signal(str)
    __test__ = False  # this is not a pytest test class

    def __init__(self, parent=None):
        """Constructor."""
        QAbstractItemModel.__init__(self, parent)
        self.abbreviator = Abbreviator()
        self.is_dark_interface = False
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
        If `role` is `BackgroundRole`, then return background color.
        If `role` is `TextAlignmentRole`, then return right-aligned for time.
        If `role` is `UserRole`, then return location of test as (file, line).
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
                # don't abbreviate for the code coverage filename
                if self.testresults[row].category == Category.COVERAGE:
                    return self.testresults[row].name
                return self.abbreviator.abbreviate(self.testresults[row].name)
            elif column == MESSAGE_COLUMN:
                return self.testresults[row].message
            elif column == TIME_COLUMN:
                time = self.testresults[row].time
                return '' if time is None else '{:.2f}'.format(time * 1e3)
        elif role == Qt.ToolTipRole:
            if id == TOPLEVEL_ID and column == NAME_COLUMN:
                return self.testresults[row].name
        elif role == Qt.FontRole:
            if id != TOPLEVEL_ID:
                return self.monospace_font
        elif role == Qt.BackgroundRole:
            if id == TOPLEVEL_ID:
                testresult = self.testresults[row]
                color = COLORS[testresult.category]
                return QBrush(QColor(color))
        elif role == Qt.TextAlignmentRole:
            if id == TOPLEVEL_ID and column == TIME_COLUMN:
                return Qt.AlignRight
        elif role == Qt.UserRole:
            if id == TOPLEVEL_ID:
                testresult = self.testresults[row]
                return (testresult.filename, testresult.lineno)
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

    def sort(self, column, order):
        """Sort model by `column` in `order`."""
        def key_time(result):
            return result.time or -1

        self.beginResetModel()
        reverse = order == Qt.DescendingOrder
        if column == STATUS_COLUMN:
            self.testresults.sort(key=attrgetter('category', 'status'),
                                  reverse=reverse)
        elif column == NAME_COLUMN:
            self.testresults.sort(key=attrgetter('name'), reverse=reverse)
        elif column == MESSAGE_COLUMN:
            self.testresults.sort(key=attrgetter('message'), reverse=reverse)
        elif column == TIME_COLUMN:
            self.testresults.sort(key=key_time, reverse=reverse)
        self.endResetModel()

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
        if counts[Category.COVERAGE]:
            # find the coverage result and get its status
            coverage = [res for res in self.testresults
                        if res.category == Category.COVERAGE][0].status
            msg += _(', {} coverage').format(coverage)
        return msg

    def emit_summary(self):
        """Emit sig_summary with summary for current results."""
        self.sig_summary.emit(self.summary())
