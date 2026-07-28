import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from sh_gui.main_window import MainWindow

def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" # Enable High DPI scaling

    app = QApplication(sys.argv)
    app.setApplicationName("Barber")
    app.setOrganizationName("BarberShell")

    icon_path = Path(__file__).resolve().parent.parent / "app_icon.icns"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
