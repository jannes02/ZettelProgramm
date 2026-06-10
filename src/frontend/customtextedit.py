from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QTextEdit


class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        #self.last_size = len(self.toPlainText())

    # def changeEvent(self, e, /):
    #     print("HALLLOOO")

        # text = self.toPlainText()
        # if len(text) >= 400:
        #     return QTextEdit.changeEvent(self, e)