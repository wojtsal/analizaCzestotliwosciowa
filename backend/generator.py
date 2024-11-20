import numpy as np
from scipy import signal
import threading
import random

class ADSREnvelope:
    def __init__(self, attack_time, decay_time, sustain_level, release_time, sample_rate):
        self.attack_time = attack_time
        self.decay_time = decay_time
        self.sustain_level = sustain_level
        self.release_time = release_time
        self.sample_rate = sample_rate
        self.state = 'idle'
        self.current_amplitude = 0.0


    def note_on(self):
        self.state = 'attack'
        self.current_amplitude = 0.0

    def note_off(self):
        self.state = 'release'

    def process(self, num_frames):
        envelope = np.zeros(num_frames)
        for i in range(num_frames):
            if self.state == 'attack':
                envelope[i] = self.current_amplitude
                increment = 1.0 / (self.attack_time * self.sample_rate)
                self.current_amplitude += increment
                if self.current_amplitude >= 1.0:
                    self.current_amplitude = 1.0
                    self.state = 'decay'
            elif self.state == 'decay':
                envelope[i] = self.current_amplitude
                decrement = (1.0 - self.sustain_level) / (self.decay_time * self.sample_rate)
                self.current_amplitude -= decrement
                if self.current_amplitude <= self.sustain_level:
                    self.current_amplitude = self.sustain_level
                    self.state = 'sustain'
            elif self.state == 'sustain':
                envelope[i] = self.sustain_level
            elif self.state == 'release':
                envelope[i] = self.current_amplitude
                decrement = self.sustain_level / (self.release_time * self.sample_rate)
                self.current_amplitude -= decrement
                if self.current_amplitude <= 0.0:
                    self.current_amplitude = 0.0
                    self.state = 'idle'
            else:  # 'idle'
                envelope[i] = 0.0
        return envelope

class Note:
    def __init__(self, frequency, velocity, sample_rate):
        self.frequency = frequency
        self.velocity = velocity
        self.envelope = ADSREnvelope(
            attack_time=1,    # Increased attack time to 50 ms
            decay_time=0.1,
            sustain_level=0.8,
            release_time=0.2,
            sample_rate=sample_rate
        )
        self.envelope.note_on()
        self.active = True  # Indicates if the note is active or in release phase
        self.just_started = True

class Generator:
    def __init__(self, sample_rate=44100):
        self.oscillators = []
        self.sample_rate = sample_rate
        self.active_notes = []  # List of Note instances
        self.phase = {}  # Dictionary to track phase for each oscillator and note
        self.lock = threading.Lock()
        self.last_processed_samples = np.zeros(1)  # Initialize with a single zero

    def add_note(self, frequency, velocity, MAX_POLYPHONY=16):
        with self.lock:
            if len(self.active_notes) >= MAX_POLYPHONY:
                oldest_note = self.active_notes.pop(0)
                keys_to_remove = [key for key in self.phase if key[0] == oldest_note]
                for key in keys_to_remove:
                    del self.phase[key]
            note = Note(frequency, velocity, self.sample_rate)
            self.active_notes.append(note)

    def remove_note(self, frequency):
        with self.lock:
            for note in self.active_notes:
                if note.frequency == frequency:
                    note.envelope.note_off()
                    note.active = False

    def set_oscillators(self, oscillators):
        self.oscillators = oscillators

    def apply_fade(self, samples, fade_in_samples, fade_out_samples):
        total_samples = len(samples)
        # Handle fade-in
        if fade_in_samples > 0:
            fade_in_curve = np.linspace(0.0, 1.0, fade_in_samples)
            samples[:fade_in_samples] *= fade_in_curve[:, np.newaxis]
        # Handle fade-out (if needed)
        if fade_out_samples > 0:
            fade_out_curve = np.linspace(1.0, 0.0, fade_out_samples)
            samples[-fade_out_samples:] *= fade_out_curve[:, np.newaxis]
        return samples

    def apply_soft_clipping(self, samples, threshold=0.9):
        return samples / (1 + np.abs(samples / threshold))

    def generate_samples(self, num_frames):
        buffer = np.zeros((num_frames, 2))  # Initialize stereo buffer
        with self.lock:
            notes = self.active_notes.copy()
        if not notes:
            return buffer

        notes_to_remove = []

        for note in notes:
            frequency = note.frequency
            velocity = note.velocity
            note_buffer = np.zeros((num_frames, 2))  # Stereo buffer for the note
            envelope = note.envelope.process(num_frames)
            if np.all(envelope == 0.0) and not note.active:
                # Note has finished releasing
                notes_to_remove.append(note)
                continue
            for osc in self.oscillators:
                # Get oscillator parameters
                shape = osc.shape
                base_octave = osc.base_octave
                pitch_semitones = osc.pitch_semitones
                fine_tune = osc.fine_tune
                amplitude = (velocity) * osc.volume / 4  # Scale amplitude

                # Calculate the final frequency for this oscillator
                freq = frequency * (2 ** base_octave)
                freq *= 2 ** (pitch_semitones / 12)
                freq *= 2 ** (fine_tune / 1200)

                # Phase tracking key
                key = (note, osc)

                # Initialize phase if not already done
                if key not in self.phase:
                    self.phase[key] = np.random.uniform(0, 2 * np.pi)
                phase = self.phase[key]

                # Calculate phase increment per sample
                phase_increment = 2 * np.pi * freq / self.sample_rate

                # Generate phases for each sample
                sample_indices = np.arange(num_frames)
                phases = phase + sample_indices * phase_increment

                # Update phase for next buffer
                self.phase[key] = (phases[-1] + phase_increment) % (2 * np.pi)

                # Generate waveform based on shape
                if shape == 'sine':
                    samples = amplitude * np.sin(phases)
                elif shape == 'square':
                    samples = amplitude * signal.square(phases)
                elif shape == 'sawtooth':
                    samples = amplitude * signal.sawtooth(phases)
                elif shape == 'triangle':
                    samples = amplitude * signal.sawtooth(phases, width=0.5)
                elif shape == 'whitenoise':
                    samples = amplitude * np.random.normal(0, 1, num_frames)
                else:
                    samples = amplitude * np.sin(phases)

                # Multiply samples by the envelope
                samples *= envelope

                # Ensure samples are in the shape (num_frames, 1)
                samples = samples[:, np.newaxis]

                # Apply fade-in if the note has just started
                if note.just_started:
                    fade_in_samples = 100  # Number of samples for fade-in (adjust as needed)
                    samples = self.apply_fade(samples, fade_in_samples, 0)
                    note.just_started = False  # Reset the flag after applying fade-in

                # Duplicate the samples for both channels (stereo)
                samples_stereo = np.column_stack((samples, samples))

                # Add to note buffer
                note_buffer += samples_stereo

            # Add note buffer to main buffer
            buffer += note_buffer

        # Remove notes that have finished releasing
        with self.lock:
            for note in notes_to_remove:
                self.active_notes.remove(note)
                # Clean up phase data
                keys_to_remove = [key for key in self.phase if key[0] == note]
                for key in keys_to_remove:
                    del self.phase[key]

        return buffer