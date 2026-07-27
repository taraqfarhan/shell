"""
Quick command bar and shortcut buttons for sh_gui.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel
from PyQt6.QtCore import pyqtSignal

class QuickActionsBar(QWidget):
    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        label = QLabel("⚡ Quick Actions:", self)
        label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 11px;")
        layout.addWidget(label)

        # Preset commands
        presets = [
            ("📁 ls -la", "ls -la\n"),
            ("📍 pwd", "pwd\n"),
            ("📜 history", "history\n"),
            ("⚙️ jobs", "jobs\n"),
            ("🧹 clear", "clear\n"),
            ("👤 user", "echo $USER\n")
        ]

        for text, cmd in presets:
            btn = QPushButton(text, self)
            btn.setStyleSheet("""
                QPushButton {
                    background: #313244;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #89b4fa;
                    color: #11111b;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda _, c=cmd: self.command_submitted.emit(c))
            layout.addWidget(btn)

        layout.addStretch()

        self.custom_input = QLineEdit(self)
        self.custom_input.setPlaceholderText("Type command & press Enter...")
        self.custom_input.setStyleSheet("font-size: 11px; max-width: 200px;")
        self.custom_input.returnPressed.connect(self.send_custom_command)
        layout.addWidget(self.custom_input)

    def send_custom_command(self):
        cmd = self.custom_input.text().strip()
        if cmd:
            self.command_submitted.emit(cmd + "\n")
            self.custom_input.clear()
