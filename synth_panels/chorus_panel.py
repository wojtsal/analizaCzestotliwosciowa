from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QSlider,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
import numpy as np

class ChorusPanel(QWidget):
    def __init__(self, name="Chorus"):
        super().__init__()
        self.name = name
        self.depth = 0.005  # Start with 5 ms depth
        self.rate = 1.0     # Start with 1 Hz rate
        self.mix = 0    # Start with 50% mix
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Title Label
        title_label = QLabel(self.name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        # Depth Slider
        depth_layout = QHBoxLayout()
        depth_label = QLabel("Depth (ms)")
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setRange(1, 50)  # 1 ms to 50 ms
        self.depth_slider.setValue(int(self.depth * 1000))
        self.depth_slider.valueChanged.connect(self.change_depth)
        self.depth_value_label = QLabel(f"{self.depth * 1000:.1f}")
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_slider)
        depth_layout.addWidget(self.depth_value_label)
        layout.addLayout(depth_layout)

        # Rate Slider
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate (Hz)")
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(10, 500)  # 1.0 Hz to 50 Hz
        self.rate_slider.setValue(int(self.rate * 10))
        self.rate_slider.valueChanged.connect(self.change_rate)
        self.rate_value_label = QLabel(f"{self.rate:.1f}")
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_value_label)
        layout.addLayout(rate_layout)

        # Mix Slider
        mix_layout = QHBoxLayout()
        mix_label = QLabel("Mix (%)")
        self.mix_slider = QSlider(Qt.Orientation.Horizontal)
        self.mix_slider.setRange(0, 100)  # 0% to 100%
        self.mix_slider.setValue(int(self.mix * 100))
        self.mix_slider.valueChanged.connect(self.change_mix)
        self.mix_value_label = QLabel(f"{self.mix * 100:.0f}")
        mix_layout.addWidget(mix_label)
        mix_layout.addWidget(self.mix_slider)
        mix_layout.addWidget(self.mix_value_label)
        layout.addLayout(mix_layout)

        self.setLayout(layout)

    def change_depth(self, value):
        self.depth = value / 1000.0  # ms to sec
        self.depth_value_label.setText(f"{self.depth * 1000:.1f}")
        print(f"{self.name} - Depth set to {self.depth * 1000:.1f} ms")

    def change_rate(self, value):
        self.rate = value / 10.0  # to Hz
        self.rate_value_label.setText(f"{self.rate:.1f}")
        print(f"{self.name} - Rate set to {self.rate:.1f} Hz")

    def change_mix(self, value):
        self.mix = value / 100.0  # [0, 1]
        self.mix_value_label.setText(f"{self.mix * 100:.0f}")
        print(f"{self.name} - Mix set to {self.mix * 100:.0f}%")

    def apply_chorus(self, signal, sample_rate=44100):
        # Ensure signal is stereo with shape (num_frames, 2)
        if signal.ndim == 1:
            signal = np.column_stack((signal, signal))

        N = signal.shape[0]
        max_delay_samples = int(self.depth * sample_rate)

        # Create LFOs for modulation
        t = np.arange(N)
        lfo_left = 0.5 * (1 + np.sin(2 * np.pi * self.rate * t / sample_rate))
        lfo_right = 0.5 * (1 + np.sin(2 * np.pi * self.rate * t / sample_rate + np.pi / 2))

        delay_left = (lfo_left * max_delay_samples).astype(int)
        delay_right = (lfo_right * max_delay_samples).astype(int)

        indices = np.arange(N)

        # Compute delayed indices
        indices_left = indices - delay_left
        indices_right = indices - delay_right

        # Ensure indices are within valid range
        indices_left = np.clip(indices_left, 0, N - 1)
        indices_right = np.clip(indices_right, 0, N - 1)

        delayed_left = signal[indices_left, 0]
        delayed_right = signal[indices_right, 1]

        delayed_signal = np.column_stack((delayed_left, delayed_right))

        # Adjust the mix calculation
        output = signal + self.mix * (delayed_signal - signal)
        return output