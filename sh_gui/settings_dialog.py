"""
Settings dialog for configuring sh_gui appearance and terminal settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, 
    QComboBox, QSpinBox, QPushButton, QFontComboBox, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSignal

from sh_gui.themes import THEMES

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminal Settings")
        self.setMinimumSize(450, 320)
        self.settings = dict(current_settings)

        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget(self)
        
        # 1. Appearance Tab
        app_tab = QWidget()
        app_layout = QFormLayout(app_tab)
        
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.settings.get("theme", "Catppuccin Mocha"))
        app_layout.addRow("Theme Palette:", self.theme_combo)

        self.font_combo = QFontComboBox(self)
        self.font_combo.setCurrentFont(QFontComboBox().font())
        self.font_combo.setMonospacedFontsOnly(True)
        self.font_combo.setCurrentText(self.settings.get("font_family", "Menlo"))
        app_layout.addRow("Font Family:", self.font_combo)

        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(8, 36)
        self.font_size_spin.setValue(self.settings.get("font_size", 13))
        app_layout.addRow("Font Size (pt):", self.font_size_spin)

        tabs.addTab(app_tab, "🎨 Appearance")

        # 2. Terminal Tab
        term_tab = QWidget()
        term_layout = QFormLayout(term_tab)

        self.scrollback_spin = QSpinBox(self)
        self.scrollback_spin.setRange(500, 50000)
        self.scrollback_spin.setSingleStep(500)
        self.scrollback_spin.setValue(self.settings.get("scrollback_lines", 5000))
        term_layout.addRow("Scrollback Buffer Lines:", self.scrollback_spin)

        tabs.addTab(term_tab, "🖥️ Terminal")

        layout.addWidget(tabs)

        # Dialog Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_and_accept(self):
        new_settings = {
            "theme": self.theme_combo.currentText(),
            "font_family": self.font_combo.currentFont().family(),
            "font_size": self.font_size_spin.value(),
            "scrollback_lines": self.scrollback_spin.value()
        }
        self.settings_changed.emit(new_settings)
        self.accept()
