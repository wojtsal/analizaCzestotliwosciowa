from PyQt6.QtCore import QThread, pyqtSignal
import rtmidi
from backend import utils

class MidiHandler(QThread):
    note_on = pyqtSignal(int, int)  # note_number, velocity
    note_off = pyqtSignal(int)
    controller = pyqtSignal(int, int) # controller_number, controller_value

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.running = True
        self.midi_in = rtmidi.RtMidiIn()
        try:
            self.midi_in.openPort(port)
            self.midi_in.ignoreTypes(False, False, False)
            port_name = self.midi_in.getPortName(port)
            print(f"MIDI Handler started on port {port}: {port_name}")
        except Exception as e:
            print(f"Failed to open MIDI port {port}: {e}")

    def run(self):
        while self.running:
            try:
                # Retrieve a MIDI message with a timeout of 10 ms
                msg = self.midi_in.getMessage(10)
                if msg:
                    midi_message = msg  # rtmidi.MidiMessage object
                    self.process_message(midi_message)
            except Exception as e:
                print(f"Error in MIDI handler on port {self.port}: {e}")

    def process_message(self, midi):
        if midi.isNoteOn():
            note_number = midi.getNoteNumber()
            velocity = midi.getVelocity()
            print(f"Note On: note_number={note_number}, velocity={velocity}")
            self.note_on.emit(note_number, velocity)
        elif midi.isNoteOff():
            note_number = midi.getNoteNumber()
            print(f"Note Off: note_number={note_number}")
            self.note_off.emit(note_number)
        elif midi.isController():
            controller_number = midi.getControllerNumber()
            controller_value = midi.getControllerValue()
            self.controller.emit(controller_number, controller_value)

    def stop(self):
        self.running = False
        self.wait()
        self.midi_in.closePort()
        print(f"MIDI Handler stopped on port {self.port}")

def get_midi_note_name(note_number):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F',
             'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    note = notes[note_number % 12]
    return f"{note}{octave}"