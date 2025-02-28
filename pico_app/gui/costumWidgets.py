from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5 import uic
from tools import Channel
import os
from driver.enums import RANGE

class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()  # Custom signal for clicks

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setStyleSheet("color: green; text-decoration: underline;")
        
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()  # Emit the custom clicked signal

class ChannelBtn(QtWidgets.QWidget):

    update_signal = QtCore.pyqtSignal()

    def __init__(self, channel: Channel):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "channel_btn.ui"), self) 
        self.channel = channel
        self.name_label.setText(channel.name)
        self.update_text()

        self.scale_up.clicked.connect(self.action_scale_up)
        self.scale_down.clicked.connect(self.action_scale_down)

    def update_text(self):
        label = self.channel.range.name.split("_")[-1].lower()[:-1]
        self.range_label.setText(f"±{label}V")

        # Check for styling
        ranges = [item.value for item in RANGE]
        self.scale_up.setEnabled(self.channel.range.value != max(ranges))
        self.scale_down.setEnabled(self.channel.range.value != min(ranges))

    def apply_range(self, range=None):
        if range:
            self.channel.range = range
        self.update_text()
        self.refresh_hardware()

    def set_color(self, color=None):
        self.active_color = color if color else self.active_color
        bg_color = self.active_color if self.channel.active else "#bfc9ca"
        self.name_label.setStyleSheet(f"background-color: {bg_color}")
        self.range_label.setStyleSheet(f"background-color: {bg_color}")

    def refresh_hardware(self):
        if self.channel.active:
            self.update_signal.emit()

    def action_scale_up(self):
        self.channel.next_range()
        self.apply_range()

    def action_scale_down(self):
        self.channel.prv_range()
        self.apply_range()

class WelinqSpinBox(QtWidgets.QWidget):

    valueChanged = QtCore.pyqtSignal()

    def __init__(self, step:int=100, min=100, max=4000):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "spinbox_welinq.ui"), self) 

        self.name_label.setText("Sample rate")

        self.scale_up.clicked.connect(self.action_scale_up)
        self.scale_down.clicked.connect(self.action_scale_down)

        self._value = 2000
        self.step = step
        self.max_value = max
        self.min_value = min
        self.update_text()

    def update_text(self):
        
        self.range_label.setText(f"{self._value} Hz" if self._value < 1000 else f"{(self._value/1000):.1f} kHz")

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        if value < self.min_value:
            value = self.min_value
        elif value > self.max_value:
            value = self.max_value
        self._value = int(value)
        self.update_text()

    def action_scale_up(self):
        self.value += self.step
        self.valueChanged.emit()

    def action_scale_down(self):
        self.value -= self.step
        self.valueChanged.emit()

