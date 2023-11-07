# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# Copyright (c) 2023- Spyder Project Contributors
#
# Released under the terms of the MIT License
# (see LICENSE.txt in the project root directory for details)
# -----------------------------------------------------------------------------

"""
Spyder-unittest Preferences Page.
"""

# Third party imports
from qtpy.QtWidgets import QGroupBox, QVBoxLayout
from spyder.api.preferences import PluginConfigPage
from spyder.api.translations import get_translation

# Localization
_ = get_translation('spyder_unittest')


class UnitTestConfigPage(PluginConfigPage):

    def setup_page(self) -> None:
        settings_group = QGroupBox(_('Settings'))
        widget = self.create_checkbox(
            _('Abbreviate test names'), 'abbrev_test_names', default=False)
        self.abbrev_box = widget.checkbox

        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.abbrev_box)
        settings_group.setLayout(settings_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(settings_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)
