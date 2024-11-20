# synth_panel.py

from PyQt6.QtWidgets import QVBoxLayout, QWidget
from synth_panels.mixer_panel import MixerPanel
from synth_panels.filter_panel import FilterPanel
from synth_panels.chorus_panel import ChorusPanel
from synth_panels.adsr_panel import ADSRPanel  # Import your ADSRPanel class
from threading import Lock
import numpy as np

class SynthPanel(QWidget):
    def __init__(self, oscillator_widgets, generator, name="Synth Panel"):
        super().__init__()
        self.name = name
        self.oscillators = oscillator_widgets
        self.generator = generator
        self.initUI()
        self.lock = Lock()
        self.last_processed_samples = None

    def initUI(self):
        layout = QVBoxLayout()

        # Mixer
        self.mixer = MixerPanel(self.oscillators)
        layout.addWidget(self.mixer)

        # Filter
        self.filter = FilterPanel()
        layout.addWidget(self.filter)

        # ADSR Panel
        self.adsr_panel = ADSRPanel()
        layout.addWidget(self.adsr_panel)

        # Chorus
        self.chorus = ChorusPanel()
        layout.addWidget(self.chorus)

        self.setLayout(layout)

    def get_adsr_params(self):
        return {
            'attack_time': self.adsr_panel.attack,
            'decay_time': self.adsr_panel.decay,
            'sustain_level': self.adsr_panel.sustain,
            'release_time': self.adsr_panel.release
        }

    def process_samples(self, samples):
        with self.lock:
            # Apply filter
            filtered_samples = self.filter.apply_filter(samples)

            # Apply chorus
            chorused_samples = self.chorus.apply_chorus(filtered_samples)

            # Store the last processed samples for FFT visualization
            self.last_processed_samples = chorused_samples.copy()

            return chorused_samples


    def apply_limiter(self, samples, threshold=0.9):
        # Simple hard limiter
        samples = np.clip(samples, -threshold, threshold)
        return samples

    def get_last_processed_samples(self):
        with self.lock:
            if self.last_processed_samples is not None:
                return self.last_processed_samples.copy()
            else:
                return None