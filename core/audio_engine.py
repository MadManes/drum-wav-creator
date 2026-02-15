import pyaudio
import threading
import soundfile as sf
import os
import numpy as np
from core.constants import SAMPLE_RATE, CHANNELS, BUFFER_SIZE, DEFAULT_BPM

# Constantes de audio
FORMAT = pyaudio.paInt16

class AudioEngine:
    def __init__(self, sounds):
        self.sounds = sounds        
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.events = []
        self.absolute_position = 0        
        self.playing = False        
        self.total_duration = 0
        self.lock = threading.Lock()
        self.bpm = DEFAULT_BPM

        # Lista para almacenar la informacin de cada medida (beats y subdivisiones)
        self.measures = []

        # Diccionario para almacenar los patrones de los instrumentos
        self.patterns = {inst: [] for inst in sounds.keys()}


    def set_bpm(self, bpm: float):
        if bpm <= 0:
            return
        with self.lock:
            self.bpm = bpm
            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0

    
    def get_current_playback_time(self):
        if self.total_duration > 0:
            return (self.absolute_position % (self.total_duration * SAMPLE_RATE)) / SAMPLE_RATE
        return 0.0


    def calculate_beat_duration(self):
        return 60 / self.bpm
    

    def calculate_total_duration(self):
        total_duration_seconds = 0
        if not self.measures:
            return 0

        for measure_info in self.measures:
            beats_per_measure = measure_info.get('length', 4)
            total_duration_seconds += self.calculate_beat_duration() * beats_per_measure

        return total_duration_seconds
    
    
    def get_instruments(self):
        return list(self.patterns.keys())


    def get_measure_count(self):
        return len(self.measures)
    

    def get_measure_length(self, measure_idx):
        measure = self.get_measure_info(measure_idx)
        if measure:
            return measure.get("length", 4)
        return 4
    

    def get_measure_info(self, measure_idx):
        if 0 <= measure_idx < len(self.measures):
            return self.measures[measure_idx]
        return None


    def get_subdivisions(self, measure_idx):
        if 0 <= measure_idx < len(self.measures):
            return self.measures[measure_idx].get("subdivisions", 4)
        return 4


    def get_cell_state(self, instrument, measure_idx, beat, subdiv_idx):
        if instrument in self.patterns and \
           measure_idx < len(self.patterns[instrument]) and \
           beat < len(self.patterns[instrument][measure_idx]) and \
           subdiv_idx < len(self.patterns[instrument][measure_idx][beat]):
            return self.patterns[instrument][measure_idx][beat][subdiv_idx]
        return 0
    

    def is_playing(self):
        return self.playing

    def get_total_duration(self):
        return self.total_duration
    
    def get_bpm(self):
        return self.bpm

    def update_measure_structure(self, measure_idx: int, beats: int, subdivisions: int):
        if beats <= 0 or subdivisions <= 0:
            return

        with self.lock:
            if 0 <= measure_idx < len(self.measures):
                self.measures[measure_idx]['length'] = beats
                self.measures[measure_idx]['subdivisions'] = subdivisions

                for inst in self.patterns:
                    self.patterns[inst][measure_idx] = [
                        [0] * subdivisions for _ in range(beats)
                    ]

                self.total_duration = self.calculate_total_duration()
                self.generate_events()
                self.absolute_position = 0

    def repeat_measures(self, start_idx: int, end_idx: int, times: int):
        if times <= 0:
            return
    
        with self.lock:
            if start_idx < 0 or end_idx >= len(self.measures):
                return
    
            original_measures = self.measures[start_idx:end_idx+1]
    
            for _ in range(times):
                insert_position = end_idx + 1
    
                for i, measure in enumerate(original_measures):
                    self.measures.insert(insert_position + i, measure.copy())
    
                    for inst in self.patterns:
                        pattern_copy = [
                            beat[:] for beat in self.patterns[inst][start_idx + i]
                        ]
                        self.patterns[inst].insert(insert_position + i, pattern_copy)
    
            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0



    def toggle_cell(self, instrument, measure_idx, beat, subdiv_idx):
        with self.lock:
            if instrument in self.patterns and \
               measure_idx < len(self.patterns[instrument]) and \
               beat < len(self.patterns[instrument][measure_idx]) and \
               subdiv_idx < len(self.patterns[instrument][measure_idx][beat]):

                current = self.patterns[instrument][measure_idx][beat][subdiv_idx]
                self.patterns[instrument][measure_idx][beat][subdiv_idx] = 1 - current
                self.generate_events()


    def start(self):
        if self.stream is None or not self.stream.is_active():
            self.stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=BUFFER_SIZE,
                stream_callback=self.callback
            )
            self.stream.start_stream()

        if self.total_duration > 0 and self.absolute_position / SAMPLE_RATE >= self.total_duration:
            self.absolute_position = 0

        self.playing = True

             

    def stop(self):
        self.playing = False
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
                

    def add_measure(self, beats: int, subdivisions: int):
        if beats <= 0:
            beats = 4
        if subdivisions <= 0:
            subdivisions = 4

        with self.lock:
            self.measures.append({
                'length': beats,
                'subdivisions': subdivisions
            })

            for inst in self.patterns:
                self.patterns[inst].append(
                    [[0] * subdivisions for _ in range(beats)]
                )

            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0


    # Mtodo para eliminar compases seleccionados
    def delete_measures(self, indices: list[int]):
        with self.lock:
            for measure_idx in sorted(indices, reverse=True):
                if 0 <= measure_idx < len(self.measures):
                    del self.measures[measure_idx]
                    for inst in self.patterns:
                        del self.patterns[inst][measure_idx]

            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0
    

    # Genera la lista de eventos de audio basados en el patrn actual
    def generate_events(self):
        self.events = [] # Limpiar la lista de eventos para regenerarla
        beat_duration = self.calculate_beat_duration()
        accumulated_time = 0.0        

        for measure_idx, measure_info in enumerate(self.measures):
            current_beats = measure_info.get('length', 4)
            current_subdiv = measure_info.get('subdivisions', 4)
            measure_duration = current_beats * beat_duration

            for inst in self.patterns:
                if inst in self.patterns and measure_idx < len(self.patterns[inst]):
                    pattern_for_measure = self.patterns[inst][measure_idx]
                    pattern_beats = len(pattern_for_measure)
                    pattern_subdivs_per_beat = 0
                    if pattern_beats > 0 and len(pattern_for_measure[0]) > 0:
                        pattern_subdivs_per_beat = len(pattern_for_measure[0])
                    if pattern_beats == current_beats and pattern_subdivs_per_beat == current_subdiv:
                        for beat_idx in range(current_beats):
                            for subdiv_idx in range(current_subdiv):
                                if pattern_for_measure[beat_idx][subdiv_idx] == 1:
                                    time = accumulated_time + (beat_idx * beat_duration) + (subdiv_idx / current_subdiv * beat_duration)
                                    event_data = {
                                        'time': time,
                                        'sound': self.sounds[inst], # sound y samples suelen ser lo mismo si cargas samples completos
                                        'duration': len(self.sounds[inst]) / SAMPLE_RATE,
                                        'samples': self.sounds[inst], # Contiene los datos de audio (ndarray)
                                        'instruments': inst
                                    }
                                    self.events.append(event_data)
            accumulated_time += measure_duration

    def callback(self, in_data, frame_count, time_info, status):
        buffer = np.zeros((frame_count, CHANNELS), dtype=np.float32)
    
        with self.lock:
            playing = self.playing
            total_duration = self.total_duration
            absolute_position = self.absolute_position
            events = self.events.copy()
    
        if playing and total_duration > 0:
            total_samples = int(total_duration * SAMPLE_RATE)
    
            if total_samples > 0:
                absolute_position %= total_samples
                current_time = absolute_position / SAMPLE_RATE
    
                buffer_start_time = current_time
                buffer_end_time = current_time + frame_count / SAMPLE_RATE
    
                for event in events:
                    start_time = event["time"]
                    event_samples = event["samples"]
                    event_duration = event["duration"]
    
                    if start_time >= buffer_end_time:
                        continue
                    if start_time + event_duration <= buffer_start_time:
                        continue
                    
                    event_start_frame = int((start_time - buffer_start_time) * SAMPLE_RATE)
                    sample_offset = max(0, -event_start_frame)
    
                    buffer_start_frame = max(0, event_start_frame)
    
                    frames_available = min(
                        frame_count - buffer_start_frame,
                        len(event_samples) - sample_offset
                    )
    
                    if frames_available > 0:
                        buffer[
                            buffer_start_frame : buffer_start_frame + frames_available
                        ] += event_samples[
                            sample_offset : sample_offset + frames_available
                        ]
    
                absolute_position += frame_count
    
        with self.lock:
            self.absolute_position = absolute_position
    
        buffer = np.clip(buffer, -1, 1)
        buffer = (buffer * 32767).astype(np.int16)
    
        return (buffer.tobytes(), pyaudio.paContinue)
        
        
    def export(self, filename):
        duration = self.total_duration
        total_frames = int(duration * SAMPLE_RATE)
        export_buffer = np.zeros((total_frames, CHANNELS), dtype=np.float32)

        for event in self.events:
            start_frame = int(event['time'] * SAMPLE_RATE)
            end_frame = start_frame + len(event['samples'])

            if start_frame >= total_frames:
                continue

            end_frame = min(end_frame, total_frames)
            sample_slice = slice(0, end_frame - start_frame)

            export_buffer[start_frame:end_frame] += event['samples'][sample_slice]

        export_buffer = np.clip(export_buffer, -1, 1)
        export_buffer = (export_buffer * 32767).astype(np.int16)

        sf.write(filename, export_buffer, SAMPLE_RATE)
    