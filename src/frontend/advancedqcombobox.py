import json
import os

from PySide6 import QtCore
from PySide6.QtWidgets import QComboBox

from rsc_path import rsc_path


class AdvancedQComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        QComboBox.__init__(self, *args, **kwargs)
        self.activated.connect(self.choose)
        self.dirname = os.path.dirname(__file__)
        with open(os.path.join(self.dirname, rsc_path("persistence/rooms.json")), 'r') as f:
            file = f.read()
        self.buffered_items = json.loads(file)
        self.clear()
        self.addItems(self.buffered_items)

    @QtCore.Slot()
    def choose(self, index):
        items = [self.itemText(i) for i in range(self.count())]
        output = json.dumps(items)
        if output != self.buffered_items:
            with open(os.path.join(self.dirname, rsc_path("persistence/rooms.json")), 'w') as f:
                f.write(output)

    @QtCore.Slot()
    def wheelEvent(self, e, /):
        self.parent().wheelEvent(e)