from PySide6.QtWidgets import QSpinBox


class NoScrollSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        QSpinBox.__init__(self, *args, **kwargs)
    def wheelEvent(self, e, /):
        print("wheelEvent")