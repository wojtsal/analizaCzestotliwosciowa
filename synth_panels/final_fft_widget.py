import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class FinalFFTWidget(QWidget):
    def __init__(self, name="Final FFT"):
        super().__init__()
        self.name = name
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.plot_fft = pg.PlotWidget(title=self.name)
        self.plot_fft.setLabel('left', 'Amplitude')
        self.plot_fft.setLabel('bottom', 'Frequency (Hz)')
        self.plot_fft.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_fft)
        self.setLayout(layout)

    def update_fft(self, samples, sample_rate=44100):
        try:
            # Ensure samples are in the correct shape
            if samples.ndim == 2:
                # Convert stereo to mono
                samples = samples.mean(axis=0)

            N = len(samples)
            if N == 0:
                return  # Avoid division by zero

            # Apply a window function to reduce spectral leakage
            window = np.hanning(N)
            samples_windowed = samples * window

            # Compute FFT using the oscillator's method
            yf_full = np.fft.fft(samples_windowed)
            yf = 2.0 / N * np.abs(yf_full[0:N // 2])
            xf = np.fft.fftfreq(N, d=1 / sample_rate)[0:N // 2]

            # Update plot
            self.plot_fft.clear()
            self.plot_fft.plot(xf, yf, pen='y')

            # Set x-axis range from 0 Hz to Nyquist frequency
            nyquist = sample_rate / 2
            self.plot_fft.setXRange(0, nyquist)

            # Set y-axis range based on data
            self.plot_fft.setYRange(0, yf.max() * 1.1)  # Add 10% padding

            # Use linear scale (assuming oscillators use linear scale)
            self.plot_fft.setLogMode(x=False, y=False)

            # Ensure y-axis is not inverted
            self.plot_fft.invertY(False)

        except Exception as e:
            print(f"Exception in update_fft: {e}")