from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, pyqtSlot
import pyqtgraph as pg
import numpy as np

class InfoWindow(QMainWindow):
    update_data_signal = pyqtSignal(np.ndarray)
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Info Window")
        self.initUI()


        # Connect the signals to the update methods
        self.update_data_signal.connect(self.update_displays)
        self.start_recording_signal.connect(self.start_recording_slot)
        self.stop_recording_signal.connect(self.stop_recording_slot)

        # Variables for recording
        self.is_recording = False
        self.recorded_samples = []
        self.sample_rate = 44100  # Default sample rate

        # Sample buffer for accumulating samples
        self.sample_buffer = np.array([])

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Waveform Plot (Live)
        self.plot_waveform = pg.PlotWidget(title="Live Waveform")
        self.plot_waveform.setLabel('left', 'Amplitude')
        self.plot_waveform.setLabel('bottom', 'Time (s)')
        self.plot_waveform.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_waveform)

        # FFT Plot
        self.plot_fft = pg.PlotWidget(title="FFT")
        self.plot_fft.setLabel('left', 'Amplitude')
        self.plot_fft.setLabel('bottom', 'Frequency (Hz)')
        self.plot_fft.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_fft)

        # Frozen Waveform Plot
        self.plot_frozen_waveform = pg.PlotWidget(title="Captured Waveform")
        self.plot_frozen_waveform.setLabel('left', 'Amplitude')
        self.plot_frozen_waveform.setLabel('bottom', 'Time (s)')
        self.plot_frozen_waveform.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_frozen_waveform)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_info(self, samples, sample_rate=44100):
        if not self.is_recording:
            return
        self.sample_rate = sample_rate
        self.update_data_signal.emit(samples)

        if not self.main_window.generator.has_active_notes():
            # No active notes; stop recording and freeze the display
            self.stop_recording()


    def update_displays(self, samples):
        try:
            # Ensure samples are in the correct shape
            if samples.ndim == 2:
                # Convert stereo to mono
                samples = samples.mean(axis=1)

            # Accumulate samples
            self.sample_buffer = np.concatenate((self.sample_buffer, samples))

            # Limit the buffer size to, e.g., 4096 samples
            if len(self.sample_buffer) > 4096:
                self.sample_buffer = self.sample_buffer[-4096:]

            samples_to_plot = self.sample_buffer.copy()
            N = len(samples_to_plot)
            if N == 0:
                return  # Avoid division by zero

            # Time axis for waveform
            t = np.linspace(0, N / self.sample_rate, N)

            # Update live waveform plot
            self.plot_waveform.clear()
            self.plot_waveform.plot(t, samples_to_plot, pen='c')
            self.plot_waveform.setXRange(0, N / self.sample_rate)
            self.plot_waveform.setYRange(samples_to_plot.min() * 1.1, samples_to_plot.max() * 1.1)

            # Apply a window function to reduce spectral leakage
            window = np.hanning(N)
            samples_windowed = samples_to_plot * window

            # Compute FFT
            yf_full = np.fft.fft(samples_windowed)
            yf = 2.0 / N * np.abs(yf_full[0:N // 2])
            xf = np.fft.fftfreq(N, d=1 / self.sample_rate)[0:N // 2]

            # Update FFT plot
            self.plot_fft.clear()
            self.plot_fft.plot(xf, yf, pen='y')
            self.plot_fft.setXRange(0, self.sample_rate / 2)
            self.plot_fft.setYRange(0, yf.max() * 1.1)

            # Use linear scale
            self.plot_fft.setLogMode(x=False, y=False)
            self.plot_fft.invertY(False)

            # Record samples if recording is active
            if self.is_recording:
                self.recorded_samples.append(samples.copy())

        except Exception as e:
            print(f"Exception in update_displays: {e}")

    def start_recording(self):
        self.start_recording_signal.emit()

    @pyqtSlot()
    def start_recording_slot(self):
        self.is_recording = True
        self.recorded_samples = []  # Reset recorded samples

    def stop_recording(self):
        self.stop_recording_signal.emit()

    @pyqtSlot()
    def stop_recording_slot(self):
        self.is_recording = False

        # Concatenate recorded samples
        if self.recorded_samples:
            full_samples = np.concatenate(self.recorded_samples)
            N = len(full_samples)
            t = np.linspace(0, N / self.sample_rate, N)

            # Update frozen waveform plot
            self.plot_frozen_waveform.clear()
            self.plot_frozen_waveform.plot(t, full_samples, pen='m')
            self.plot_frozen_waveform.setXRange(0, t[-1])
            self.plot_frozen_waveform.setYRange(full_samples.min() * 1.1, full_samples.max() * 1.1)

            # Calculate and plot the envelope
            envelope = np.abs(full_samples)
            self.plot_frozen_waveform.plot(t, envelope, pen='r')

        else:
            print("No samples recorded.")