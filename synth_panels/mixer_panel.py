from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QSlider,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
import numpy as np


class MixerPanel(QWidget):
    def __init__(self, oscillator_widgets, name="Mixer"):
        super().__init__()
        self.oscillators = oscillator_widgets
        self.name = name
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        title_label = QLabel(self.name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        # Volume Control for Each Oscillator
        for osc in self.oscillators:
            osc_layout = QHBoxLayout()
            label = QLabel(osc.name)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(100)  # Default volume at 100%
            slider.valueChanged.connect(lambda value, o=osc: self.set_volume(o, value))
            osc_layout.addWidget(label)
            osc_layout.addWidget(slider)
            layout.addLayout(osc_layout)

        self.setLayout(layout)

    def set_volume(self, oscillator, value):
        oscillator.volume = value / 100.0  # Normalize to 0.0 - 1.0
        print(f"{oscillator.name} - Volume set to {oscillator.volume}")

    def mix_signals(self):
        # Generate mixed signal from active notes
        # Since the Generator now handles active notes, we may need to adjust this method
        pass  # We'll handle mixing within the Generator for real-time audio