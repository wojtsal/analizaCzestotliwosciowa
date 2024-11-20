# filter_panel.py

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QSlider,
    QRadioButton,
    QButtonGroup,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
import numpy as np
from scipy.signal import butter, lfilter
from scipy.signal import filtfilt



class FilterPanel(QWidget):
    def __init__(self, name="Filter", sample_rate=44100):
        super().__init__()
        self.name = name
        self.filter_type = "low_pass"
        self.filter_freq = 20000  # Default frequency
        self.sample_rate = sample_rate
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Title Label
        title_label = QLabel(self.name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        # Filter Type Selection
        type_layout = QHBoxLayout()
        self.filter_group = QButtonGroup()
        low_pass = QRadioButton("Low Pass")
        high_pass = QRadioButton("High Pass")
        low_pass.setChecked(True)
        self.filter_group.addButton(low_pass)
        self.filter_group.addButton(high_pass)
        low_pass.toggled.connect(self.change_filter_type)
        high_pass.toggled.connect(self.change_filter_type)
        type_layout.addWidget(low_pass)
        type_layout.addWidget(high_pass)
        layout.addLayout(type_layout)

        # Filter Frequency Slider
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency")
        self.freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.freq_slider.setRange(20, 20000)
        self.freq_slider.setValue(self.filter_freq)
        self.freq_slider.valueChanged.connect(self.change_filter_freq)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_slider)
        layout.addLayout(freq_layout)

        self.setLayout(layout)

    def change_filter_type(self):
        selected_button = self.filter_group.checkedButton()
        if selected_button.text() == "Low Pass":
            self.filter_type = "low_pass"
        elif selected_button.text() == "High Pass":
            self.filter_type = "high_pass"
        print(f"{self.name} - Filter type changed to {self.filter_type}")

    def change_filter_freq(self, value):
        self.filter_freq = value
        print(f"{self.name} - Filter frequency set to {self.filter_freq} Hz")

    def apply_filter(self, y):
        nyq = 0.5 * self.sample_rate
        normal_cutoff = self.filter_freq / nyq
        order = 3

        if self.filter_type == 'low_pass':
            b, a = butter(order, normal_cutoff, btype='low', analog=False)
        elif self.filter_type == 'high_pass':
            b, a = butter(order, normal_cutoff, btype='high', analog=False)
        else:
            raise ValueError("Invalid filter type")

        # Apply the filter to each channel
        #filtered_signal = lfilter(b, a, y, axis=0)
        filtered_signal = filtfilt(b, a, y, axis=0)

        return filtered_signal

        # yf = np.fft.fft(y)
        # xf = np.fft.fftfreq(len(y), 1 / 44100)
        # if self.filter_type == 'low_pass':
        #     yf[np.abs(xf) > self.filter_freq] = 0
        # elif self.filter_type == 'high_pass':
        #     yf[np.abs(xf) < self.filter_freq] = 0
        # y_filtered = np.fft.ifft(yf).real
        # return y_filtered