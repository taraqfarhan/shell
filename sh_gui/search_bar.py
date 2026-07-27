"""
Interactive Search Bar widget for searching terminal text.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal

class SearchBar(QWidget):
    search_requested = pyqtSignal(str, bool, bool) # query, backward, case_sensitive
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Search terminal output...")
        self.input_field.textChanged.connect(self.on_text_changed)
        self.input_field.returnPressed.connect(self.find_next)
        layout.addWidget(self.input_field)

        self.match_label = QLabel("0 matches", self)
        self.match_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(self.match_label)

        self.case_checkbox = QCheckBox("Match Case", self)
        self.case_checkbox.setStyleSheet("color: #cdd6f4; font-size: 11px;")
        self.case_checkbox.stateChanged.connect(self.on_text_changed)
        layout.addWidget(self.case_checkbox)

        self.prev_btn = QPushButton("▲ Prev", self)
        self.prev_btn.setFixedSize(60, 26)
        self.prev_btn.clicked.connect(self.find_prev)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▼ Next", self)
        self.next_btn.setFixedSize(60, 26)
        self.next_btn.clicked.connect(self.find_next)
        layout.addWidget(self.next_btn)

        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setStyleSheet("background: transparent; color: #f38ba8; font-weight: bold;")
        self.close_btn.clicked.connect(self.hide_bar)
        layout.addWidget(self.close_btn)

        self.hide()

    def show_bar(self):
        self.show()
        self.input_field.setFocus()
        self.input_field.selectAll()

    def hide_bar(self):
        self.hide()
        self.closed.emit()

    def on_text_changed(self):
        query = self.input_field.text()
        case_sensitive = self.case_checkbox.isChecked()
        if query:
            self.search_requested.emit(query, False, case_sensitive)

    def find_next(self):
        query = self.input_field.text()
        case_sensitive = self.case_checkbox.isChecked()
        if query:
            self.search_requested.emit(query, False, case_sensitive)

    def find_prev(self):
        query = self.input_field.text()
        case_sensitive = self.case_checkbox.isChecked()
        if query:
            self.search_requested.emit(query, True, case_sensitive)

    def update_match_count(self, count: int, current: int = 0):
        if count == 0:
            self.match_label.setText("No matches")
        else:
            self.match_label.setText(f"{current} of {count} matches")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_bar()
        else:
            super().keyPressEvent(event)
