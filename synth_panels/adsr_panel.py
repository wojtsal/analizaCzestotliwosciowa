from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QSlider,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
import numpy as np


class ADSRPanel(QWidget):
    def __init__(self, name="ADSR Envelope"):
        super().__init__()
        self.name = name
        self.attack = 0.1
        self.decay = 0.5
        self.sustain = 0.0
        self.release = 0.1
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Title Label
        title_label = QLabel(self.name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        #Attack Slider
        attack_layout = QHBoxLayout()
        attack_label = QLabel("Attack")
        self.attack_slider = QSlider(Qt.Orientation.Horizontal)
        self.attack_slider.setRange(0, 1000)  # ms
        self.attack_slider.setValue(int(self.attack * 1000))
        self.attack_slider.valueChanged.connect(self.change_attack)
        attack_layout.addWidget(attack_label)
        attack_layout.addWidget(self.attack_slider)
        layout.addLayout(attack_layout)

        # Decay Slider
        decay_layout = QHBoxLayout()
        decay_label = QLabel("Decay")
        self.decay_slider = QSlider(Qt.Orientation.Horizontal)
        self.decay_slider.setRange(0, 1000) # ms
        self.decay_slider.setValue(int(self.decay * 1000))
        self.decay_slider.valueChanged.connect(self.change_decay)
        decay_layout.addWidget(decay_label)
        decay_layout.addWidget(self.decay_slider)
        layout.addLayout(decay_layout)

        # Sustain Slider
        sustain_layout = QHBoxLayout()
        sustain_label = QLabel("Sustain")
        self.sustain_slider = QSlider(Qt.Orientation.Horizontal)
        self.sustain_slider.setRange(0, 100)
        self.sustain_slider.setValue(int(self.sustain * 100))
        self.sustain_slider.valueChanged.connect(self.change_sustain)
        sustain_layout.addWidget(sustain_label)
        sustain_layout.addWidget(self.sustain_slider)
        layout.addLayout(sustain_layout)

        # Release Slider
        release_layout = QHBoxLayout()
        release_label = QLabel("Release")
        self.release_slider = QSlider(Qt.Orientation.Horizontal)
        self.release_slider.setRange(0, 1000) #ms
        self.release_slider.setValue(int(self.release * 1000))
        self.release_slider.valueChanged.connect(self.change_release)
        release_layout.addWidget(release_label)
        release_layout.addWidget(self.release_slider)
        layout.addLayout(release_layout)

        self.setLayout(layout)

    def change_attack(self, value):
        self.attack = value / 1000.0
        print(f"{self.name} - Attack set to {self.attack} seconds")

    def change_decay(self, value):
        self.decay = value / 1000.0
        print(f"{self.name} - Decay set to {self.decay} seconds")

    def change_sustain(self, value):
        self.sustain = value / 100.0
        print(f"{self.name} - Sustain set to {self.sustain}")

    def change_release(self, value):
        self.release = value / 1000.0
        print(f"{self.name} - Release set to {self.release} seconds")

    def apply_adsr(self, y):
        attack_samples = int(self.attack * 44100)
        decay_samples = int(self.decay * 44100)
        release_samples = int(self.release * 44100)
        sustain_level = self.sustain

        envelope = np.ones_like(y)

        # Attack phase
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay phase
        if decay_samples > 0:
            start = attack_samples
            end = attack_samples + decay_samples
            envelope[start:end] = np.linspace(1, sustain_level, decay_samples)

        # Sustain phase
        sustain_start = attack_samples + decay_samples
        sustain_end = len(y) - release_samples
        if sustain_end > sustain_start:
            envelope[sustain_start:sustain_end] = sustain_level

        # Release phase
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(sustain_level, 0, release_samples)

        return y * envelope