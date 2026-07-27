#!/usr/bin/env python3
"""
Main launcher script for sh_gui desktop terminal application.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from sh_gui.main_window import MainWindow

def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" # Enable High DPI scaling

    app = QApplication(sys.argv)
    app.setApplicationName("sh GUI Terminal")
    app.setOrganizationName("CustomShell")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
