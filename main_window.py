import numpy as np
import sounddevice as sd
import rtmidi
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QGridLayout,
    QMainWindow,
    QApplication,
    QLabel,
)
from PyQt6.QtCore import QTimer, Qt

from backend.utils import midi_note_number_to_frequency
from backend.generator import Generator
from backend.midi_handler import MidiHandler
from oscillator_widget import OscillatorWidget
from synth_panel import SynthPanel
from info_window import InfoWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize oscillators
        self.osc1 = OscillatorWidget(
            name="Oscillator 1",
            default_shape='sawtooth',
            default_pitch=7,
            default_octave=-2,
            default_fine=-12
        )
        self.osc2 = OscillatorWidget(
            name="Oscillator 2",
            default_shape='square',
            default_octave=-3
        )
        self.osc3 = OscillatorWidget(
            name="Oscillator 3",
            default_shape='sine',
            default_pitch=0,
            default_octave=-3
        )
        self.oscillators = [self.osc1, self.osc2, self.osc3]

        # Initialize the Generator instance after creating oscillators
        self.generator = Generator()
        self.generator.set_oscillators(self.oscillators)

        self.setWindowTitle("Multi-Oscillator Synthesizer")
        self.initUI()
        self.initMidiHandlers()
        self.initAudioStream()

        # Create the FFT window
        self.info_window = InfoWindow()
        self.info_window.show()

        # Timer to update FFT
        self.timer = QTimer()
        self.timer.setInterval(50)  # Update 20 times per second
        self.timer.timeout.connect(self.update_info)
        self.timer.start()

    def initUI(self):
        # Main Layout
        main_layout = QGridLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Control Panel Layout (for hide/show buttons)
        control_layout = QHBoxLayout()
        control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Create Hide/Show buttons for each oscillator
        self.hide_buttons = []
        for osc in self.oscillators:
            btn = QPushButton(f"Hide {osc.name}")
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.clicked.connect(lambda checked, o=osc, b=btn: self.toggle_oscillator(o, b))
            self.hide_buttons.append(btn)
            control_layout.addWidget(btn)

        main_layout.addLayout(control_layout, 0, 0, 1, 2)

        # Add a button to toggle the FFT window
        self.toggle_info_button = QPushButton("Hide FFT Window")
        self.toggle_info_button.setCheckable(True)
        self.toggle_info_button.clicked.connect(self.toggle_info_window)
        # Add the button to your layout (e.g., in the control panel)
        control_layout.addWidget(self.toggle_info_button)

        # Oscillators Layout
        oscillators_layout = QHBoxLayout()
        oscillators_layout.addWidget(self.osc1)
        oscillators_layout.addWidget(self.osc2)
        oscillators_layout.addWidget(self.osc3)

        main_layout.addLayout(oscillators_layout, 1, 0)

        # Synth Panel
        self.synth_panel = SynthPanel(self.oscillators, self.generator)
        main_layout.addWidget(self.synth_panel, 1, 1)

        # Play Button
        play_button = QPushButton("Play Sound")
        play_button.clicked.connect(self.on_click)
        main_layout.addWidget(play_button, 2, 0, 1, 2)  # Span across two columns

        # Set the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def toggle_oscillator(self, oscillator, button):
        if oscillator.isVisible():
            oscillator.hide()
            button.setText(f"Show {oscillator.name}")
        else:
            oscillator.show()
            button.setText(f"Hide {oscillator.name}")

        # Adjust the main window size to fit the visible widgets
        self.adjustSize()

    def toggle_info_window(self):
        if self.info_window.isVisible():
            self.info_window.hide()
            self.toggle_fft_button.setText("Show FFT Window")
        else:
            self.info_window.show()
            self.toggle_fft_button.setText("Hide FFT Window")

    def update_info(self):
        samples = self.synth_panel.get_last_processed_samples()
        if samples is not None:
            self.info_window.update_info(samples, sample_rate=self.generator.sample_rate)

    def initMidiHandlers(self):
        midi_in = rtmidi.RtMidiIn()
        port_count = midi_in.getPortCount()
        if port_count == 0:
            print("NO MIDI INPUT PORTS!")
            return

        self.midi_handlers = []
        for port in range(port_count):
            handler = MidiHandler(port)
            handler.note_on.connect(self.handle_note_on)
            handler.note_off.connect(self.handle_note_off)
            handler.controller.connect(self.handle_controller)
            handler.start()
            self.midi_handlers.append(handler)

    def initAudioStream(self):
        self.stream = sd.OutputStream(
            samplerate=44100,
            channels=2,  # Number of output channels for stereo
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Audio callback status: {status}")

        samples = self.generator.generate_samples(frames)
        if samples is None or len(samples) == 0:
            outdata.fill(0)
        else:
            processed_samples = self.synth_panel.process_samples(samples)
            outdata[:] = processed_samples.T

    def handle_note_on(self, note_number, velocity):
        frequency = midi_note_number_to_frequency(note_number)
        amplitude = velocity / 127.0  # Scale amplitude based on velocity
        self.generator.add_note(frequency, amplitude)
        self.info_window.start_recording()
        print(f"Note On: {note_number} ({frequency:.2f} Hz), Velocity: {velocity}")

    def handle_note_off(self, note_number):
        print(f"handle_note_off called with note_number={note_number}, type={type(note_number)}")
        frequency = midi_note_number_to_frequency(note_number)
        self.generator.remove_note(frequency)
        self.info_window.stop_recording()
        print(f"Removed note {note_number} ({frequency:.2f} Hz) from generator")

    def handle_controller(self, controller_number, controller_value):
        # Obsługa kontrolerów MIDI, jeśli potrzebne
        print(f"CONTROLLER {controller_number}: {controller_value}")

    def on_click(self):
        # Przycisk Play może generować podstawową falę
        for osc in self.oscillators:
            osc.reference_frequency = 440
            osc.update_plots()
        self.on_play(velocity=127)

    def on_play(self, velocity=127.0):
        print("Playing mixed sound...")

        # Synth panel processing
        processed_signal = self.synth_panel.process_signal()

        # Normalizacja
        max_val = np.max(np.abs(processed_signal))
        if max_val > 0:
            processed_signal = processed_signal / max_val

        volume = 0.2 * (velocity / 127.0)
        processed_signal *= volume
        playback_signal = processed_signal.T

        sd.play(playback_signal, samplerate=self.generator.sample_rate, blocking=True)

    def update_plots(self):
        # Aktualizacja wykresów dla wszystkich oscylatorów
        for osc in self.oscillators:
            osc.update_plots()

    def closeEvent(self, event):
        for handler in getattr(self, 'midi_handlers', []):
            handler.stop()
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        event.accept()