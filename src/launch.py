import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget

from rsc_path import rsc_path
from src import version
from src.frontend.main_window import MainWindow

if __name__ == "__main__":
    if version.__version__ is not None:
        print(version.__version__)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(rsc_path("icons/app.ico")))
    app.setApplicationName("Zettelprogramm")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
