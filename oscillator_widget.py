import numpy as np
from scipy import signal
from scipy.fft import fft
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QDial,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from scipy.io.wavfile import write
from backend.utils import note_name_to_frequency
import pyqtgraph as pg
import pandas as pd


class OscillatorWidget(QWidget):
    def __init__(self, name="Oscillator", default_shape='sine', default_pitch=0, default_octave=0, default_fine=0):
        super().__init__()
        self.name = name
        self.volume = 1

        self.shape = default_shape
        self.base_octave = default_octave
        self.fine_tune = default_fine
        self.pitch_semitones = default_pitch
        self.distortion = 0
        self.filter_type = 'low_pass'
        self.filter_freq = 1000
        self.reference_frequency = 440

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        title_label = QLabel(self.name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        ## wave
        self.plot_wave = pg.PlotWidget(title="Waveform")
        self.plot_wave.setXRange(0, 0.01)
        layout.addWidget(self.plot_wave)

        # FFT
        self.plot_fft = pg.PlotWidget(title="FFT")
        self.plot_fft.setXRange(20, 20000)
        layout.addWidget(self.plot_fft)

        controls_layout = QHBoxLayout()

        # Shape Dial
        self.dial_shape = self.create_dial("Shape", 0, 4, 1, self.change_shape)
        controls_layout.addWidget(self.dial_shape)

        # Base Octave Dial
        self.dial_base_octave = self.create_dial("Octave", -4, 4, 1, self.change_base_octave, defaul_value=self.base_octave)
        controls_layout.addWidget(self.dial_base_octave)

        # Pitch Semitone Dial
        self.dial_pitch_semitones = self.create_dial("Pitch", -12, 12, 1, self.change_pitch_semitones, defaul_value=self.pitch_semitones)
        controls_layout.addWidget(self.dial_pitch_semitones)

        # Fine Tune Dial
        self.dial_fine_tune = self.create_dial("Fine", -100, 100, 1, self.change_fine_tune,
                                                     defaul_value=self.fine_tune)
        controls_layout.addWidget(self.dial_fine_tune)


        # Save Csv Button
        button_save_layout = QVBoxLayout()
        self.button_csv_save = self.create_button("Save to .csv", self.save_csv)
        button_save_layout.addWidget(self.button_csv_save)

        # Load Csv Button
        self.button_wav_save = self.create_button("Save to .wav", self.save_wav)
        button_save_layout.addWidget(self.button_wav_save)

        controls_layout.addLayout(button_save_layout)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

        # Initialize Plot
        self.update_plots()

    def create_button(self, title, callback):
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        button = QPushButton()
        button.setText(title)
        button.clicked.connect(callback)
        return button

    def create_dial(self, title, min_val, max_val, step,  callback, defaul_value=0,):
        dial_widget = QWidget()
        dial_layout = QVBoxLayout()
        label = QLabel(f"{title}: {defaul_value}")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setFixedSize(80, 20)
        dial = QDial()
        dial.setRange(min_val, max_val)
        dial.setNotchesVisible(True)
        dial.setWrapping(False)

        dial.setValue(defaul_value)

        dial_layout.addWidget(label)

        def update_tooltip(value):
            callback(value)
            label.setText( f"{title}: {value}")

        dial.valueChanged.connect(update_tooltip)

        dial_layout.addWidget(dial)
        dial_widget.setLayout(dial_layout)
        return dial_widget

    def change_shape(self, value):
        shape_funcs = {
            0: 'sine',
            1: 'square',
            2: 'sawtooth',
            3: 'triangle',
            4: 'whitenoise'
        }
        self.shape = shape_funcs.get(value, 'sine')
        print(f"{self.name} - Shape changed to {self.shape}")
        self.update_plots()

    def change_base_octave(self, value):
        self.base_octave = value
        print(f"{self.name} - Base Octave changed to {self.base_octave}")
        self.update_plots()

    def change_pitch_semitones(self, value):
        self.pitch_semitones = max(min(value, 12), -12)
        print(f"{self.name} - Pitch shifted by {self.pitch_semitones} semitones")
        self.update_plots()

    def change_fine_tune(self, value):
        self.fine_tune = max(min(value, 100), -100)
        self.update_plots()

    def get_final_frequency(self):
        freq = self.reference_frequency * (2 ** self.base_octave)
        freq *= 2 ** (self.pitch_semitones / 12)
        freq *= 2 ** (self.fine_tune / 1200)
        return freq

    def get_waveform(self):
        self.freq = self.get_final_frequency()
        print(f"{self.name} - Final frequency: {self.freq:.2f} Hz")

        # Generate time array
        sample_rate = 44100  # You can adjust this if needed
        duration = 1  # Duration in seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        if self.shape == 'sine':
            y = self.sine_wave(self.freq, t)
        elif self.shape == 'square':
            y = self.square_wave(self.freq, t)
        elif self.shape == 'sawtooth':
            y = self.sawtooth_wave(self.freq, t)
        elif self.shape == 'triangle':
            y = self.triangle_wave(self.freq, t)
        elif self.shape == 'whitenoise':
            y = self.white_noise(t)
        else:
            y = self.sine_wave(self.freq, t)
        return y

    def update_plots(self):
        y = self.get_waveform()
        sample_rate = 44100
        duration = 1
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        # Update waveform plot
        self.plot_wave.clear()
        self.plot_wave.plot(t, y)
        self.plot_wave.setXRange(0, 0.01)

        # Update FFT plot
        xf, yf = self.transform_fourier(y, sample_rate)
        self.plot_fft.clear()
        self.plot_fft.plot(xf, yf)
        self.plot_fft.setXRange(20, 20000)

    def save_csv(self):
        default_filename = self.name + ".csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save .csv File", default_filename, "CSV Files (*.csv)")

        try:
            data = {"x": self.generator.t, "y": self.get_waveform()}
            dataframe = pd.DataFrame(data)
            dataframe.to_csv(file_path, index=False, sep="\t")
            print(f"Dane zapisane do: {file_path}")


            QMessageBox.information(self, "Error" f"File saved as:\n{file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
            QMessageBox.critical(self, "Error", f"Couldn't save the file:\n{e}")

    def save_wav(self):
        default_filename = self.name

        file_path, _ = QFileDialog.getSaveFileName(self, "Save .wav File", default_filename, "WAV Files (*.wav)")
        y = self.get_waveform()
        y_normalized = 0.2 * y / np.max(np.abs(y)) if np.max(np.abs(y)) != 0 else y
        y_int16 = np.int16(y_normalized * 32767)

        try:
            write(file_path, self.generator.sample_rate, y_int16)
            print(f"Dane zapisane do: {file_path}")

            QMessageBox.information(self, "Error", f"File saved as:\n{file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
            QMessageBox.critical(self, "Error", f"Couldn't save the file:\n{e}")

    def sine_wave(self, freq, t):
        return np.sin(2 * np.pi * freq * t)

    def square_wave(self, freq, t):
        return signal.square(2 * np.pi * freq * t)

    def sawtooth_wave(self, freq, t):
        return signal.sawtooth(2 * np.pi * freq * t)

    def triangle_wave(self, freq, t):
        return signal.sawtooth(2 * np.pi * freq * t, width=0.5)

    def white_noise(self, t):
        return np.random.normal(-1, 1, len(t))

    def transform_fourier(self, y, sample_rate):
        N = len(y)
        yf = 2.0 / N * np.abs(fft(y)[0:N // 2])
        xf = np.fft.fftfreq(N, d=1 / sample_rate)[0:N // 2]
        return xf, yf