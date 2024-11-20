# utils.py
import re

# List of note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F',
              'F#', 'G', 'G#', 'A', 'A#', 'B']

# Mapping of note names to semitone offsets from A4
NOTE_SEMITONES = {
    'C': -9,
    'C#': -8,
    'Db': -8,
    'D': -7,
    'D#': -6,
    'Eb': -6,
    'E': -5,
    'F': -4,
    'F#': -3,
    'Gb': -3,
    'G': -2,
    'G#': -1,
    'Ab': -1,
    'A': 0,
    'A#': 1,
    'Bb': 1,
    'B': 2
}

def get_midi_note_name(note_number):
    """
    Converts a MIDI note number to a note name.
    """
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F',
             'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    note = notes[note_number % 12]
    return f"{note}{octave}"

def midi_note_number_to_frequency(note_number):
    print(f"midi_note_number_to_frequency called with note_number={note_number}, type={type(note_number)}")
    frequency = 440.0 * (2 ** ((note_number - 69) / 12))
    return frequency

def note_name_to_frequency(note_name):
    """
    Converts a note name (e.g., 'A4') to its corresponding frequency in Hz.
    """
    match = re.fullmatch(r'^([A-Ga-g])([#b]?)(-?\d+)$', note_name.strip())
    if not match:
        raise ValueError(f"Invalid note name format: '{note_name}'")

    note, accidental, octave = match.groups()
    note = note.upper()
    if accidental:
        note += accidental

    if note not in NOTE_SEMITONES:
        raise ValueError(f"Invalid note: '{note}'")

    octave = int(octave)
    semitone_distance = NOTE_SEMITONES[note] + (octave - 4) * 12
    frequency = 440.0 * (2 ** (semitone_distance / 12))
    return frequency

# Example usage:
# note_number = 69
# print(f"MIDI note {note_number} is {get_midi_note_name(note_number)} with frequency {midi_note_number_to_frequency(note_number)} Hz")