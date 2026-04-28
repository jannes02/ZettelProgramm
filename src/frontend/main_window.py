import subprocess
import sys
from datetime import datetime

from PySide6 import QtCore
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QSizePolicy, QLabel, \
    QLineEdit
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt

from rsc_path import rsc_path
from src.backend.flyer_builder import FlyerBuilder
from src.frontend.event_widget import EventWidget

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.event_widgets = []

        loader = QUiLoader()
        file = QFile(rsc_path("ui/main_window.ui"))
        print(rsc_path("ui/main_window.ui"))
        file.open(QFile.ReadOnly)
        ui = loader.load(file)
        file.close()
        if not ui:
            print(loader.errorString())
            sys.exit(-1)

        self.setCentralWidget(ui.centralWidget())
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        print(int(geometry.width() * 0.6),
            int(geometry.height() * 0.6))
        self.resize(
            int(geometry.width() * 0.6),
            int(geometry.height() * 0.6)
        )

        self.pdf_widget = self.findChild(QWidget, "pdf_widget")
        self.doc = QPdfDocument(self)
        self.doc.load(rsc_path("pdf/HDW-Flyer.pdf"))
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.doc)
        self.pdf_view.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred))
        layout = QVBoxLayout(self.pdf_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pdf_view)

        self.btn_add_event = self.findChild(QPushButton, "btn_add_event")
        self.btn_compile = self.findChild(QPushButton, "btn_compile")
        self.btn_print = self.findChild(QPushButton, "btn_print")
        self.findChild(QPushButton, "btn_export").clicked.connect(self.export_pdf)
        self.btn_print.clicked.connect(self.print_pdf)
        self.vbox_events = self.findChild(QVBoxLayout, "vb_events")

        self.btn_add_event.clicked.connect(self.add_widget)
        self.btn_compile.clicked.connect(self.compile)

        self.le_title = self.findChild(QLineEdit, "le_title")
        self.le_title.setText("Heute im Haus")
        self.le_date = self.findChild(QLineEdit, "le_date")
        self.le_date.setText(datetime.today().strftime("%d.%m.%Y"))

        self.sc_export = QShortcut(QKeySequence("Ctrl+E"), self)
        self.sc_export.activated.connect(self.export_pdf)

        self.sc_add = QShortcut(QKeySequence("Ctrl++"), self)
        self.sc_add.activated.connect(self.add_widget)

        self.sc_refresh = QShortcut(QKeySequence("F5"), self)
        self.sc_refresh.activated.connect(self.compile)

        self.sc_print = QShortcut(QKeySequence("Ctrl+P"), self)
        self.sc_print.activated.connect(self.print_pdf)


    @QtCore.Slot()
    def add_widget(self):
        widget = EventWidget(self)
        self.event_widgets.append(widget)
        self.vbox_events.addWidget(widget)
        self.findChild(QLabel, "lbl_placeholder").setVisible(False)
        self.compile()

    @QtCore.Slot()
    def remove_widget(self, widget):
        self.event_widgets.remove(widget)
        self.vbox_events.removeWidget(widget)
        widget.deleteLater()
        if len(self.event_widgets) == 0:
            self.findChild(QLabel, "lbl_placeholder").setVisible(True)
        self.compile()

    @QtCore.Slot()
    def compile(self):
        events = []
        for i, ew in enumerate(self.event_widgets):
            events.append(ew.get_data(i=i))

        builder = FlyerBuilder(rsc_path("pdf/HDW-Flyer.pdf"))
        builder.build(event_descriptions=events,
                      title=self.le_title.text(),
                      date=self.le_date.text())
        self.refresh_pdf()

    @QtCore.Slot()
    def print_pdf(self):
        self.compile()
        self.print_pdf_dialog()

    def print_pdf_dialog(self):
        sumatra_path = rsc_path("sumatra/SumatraPDF.exe")
        subprocess.Popen([
            sumatra_path,
            "-print-dialog",
            rsc_path("pdf/HDW-Flyer.pdf"),
            "-exit-when-done"
        ])

    @QtCore.Slot()
    def export_pdf(self):
        self.compile()
        self.export_pdf_dialog()

    def export_pdf_dialog(self):
        sumatra_path = rsc_path("sumatra/SumatraPDF.exe")
        # win32api.ShellExecute(
        #     0, None,
        #     sumatra_path,
        #     f'-print-to "Microsoft Print to PDF" "{rsc_path("pdf/HDW-Flyer.pdf")}"',
        #     None, 1
        # )
        subprocess.Popen([
            sumatra_path,
            "-print-to",
            'Microsoft Print to PDF',
            rsc_path("pdf/HDW-Flyer.pdf")
        ])

    def refresh_pdf(self):
        self.doc.load(rsc_path("pdf/HDW-Flyer.pdf"))
        self.pdf_view.setDocument(self.doc)
        self.update_zoom()

    @QtCore.Slot()
    def update_zoom(self):
        if self.doc.pageCount() == 0:
            return
        page_size = self.doc.pagePointSize(0)
        viewport = self.pdf_view.viewport()
        zoom_w = viewport.width() / (page_size.width() * 1.34)
        zoom_h = viewport.height() / (page_size.height() * 1.34)
        self.pdf_view.setZoomFactor(min(zoom_w, zoom_h))

    def resizeEvent(self, event, /):
        super().resizeEvent(event)
        self.compile()

    def showEvent(self, event, /):
        super().showEvent(event)
        self.compile()