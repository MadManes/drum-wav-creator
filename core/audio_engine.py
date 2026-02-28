import pyaudio
import threading
import soundfile as sf
import os
import numpy as np
from core.constants import SAMPLE_RATE, CHANNELS, BUFFER_SIZE, DEFAULT_BPM

from dataclasses import dataclass

@dataclass
class LoopBlock:
    start: int
    end: int
    times: int

@dataclass
class AudioEvent:
    time: float
    samples: np.ndarray
    duration: float
    instrument: str

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

        self.loop_blocks: list[LoopBlock] = []


    def set_bpm(self, bpm: float):
        if bpm <= 0:
            return
        with self.lock:
            self.bpm = bpm
            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0

    
    def add_loop_block(self, start_idx: int, end_idx: int, times: int):
        if times < 2:
            return

        if start_idx < 0 or end_idx >= len(self.measures):
            return

        if start_idx > end_idx:
            return

        with self.lock:

            # 🔥 Eliminar cualquier bloque que se superponga
            self.loop_blocks = [
                block for block in self.loop_blocks
                if not (block.start <= end_idx and block.end >= start_idx)
            ]

            # Crear nuevo bloque real
            new_block = LoopBlock(
                start=start_idx,
                end=end_idx,
                times=times
            )

            self.loop_blocks.append(new_block)

            # Ordenar por start (importante para generate_events)
            self.loop_blocks.sort(key=lambda b: b.start)

            self.generate_events()
            self.absolute_position = 0

    
    def clear_loop_blocks(self):
        with self.lock:
            self.loop_blocks.clear()
            self.generate_events()
            self.absolute_position = 0

    
    def clear_loop_block(self):
        with self.lock:
            self.loop_block = None

    
    def get_current_playback_time(self):
        if self.total_duration > 0:
            return self.absolute_position / SAMPLE_RATE
        return 0.0


    def calculate_beat_duration(self):
        return 60 / self.bpm
    

    def calculate_total_duration(self):
        total_duration_seconds = 0
        if not self.measures:
            return 0

        beat_duration = self.calculate_beat_duration()

        for measure_info in self.measures:
            beats_per_measure = measure_info.get('length', 4)
            total_duration_seconds += beat_duration * beats_per_measure

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
    
    def set_playback_time(self, time_seconds):
        self.current_playback_time = max(0, min(time_seconds, self.get_total_duration()))

    def set_playback_position_seconds(self, seconds: float):
        with self.lock:
            seconds = max(0, min(seconds, self.total_duration))
            self.absolute_position = int(seconds * SAMPLE_RATE)

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

    
    def get_time_at_measure(self, measure_idx: int) -> float:
        if measure_idx <= 0:
            return 0.0

        beat_duration = self.calculate_beat_duration()
        accumulated_time = 0.0

        for i in range(min(measure_idx, len(self.measures))):
            measure_info = self.measures[i]
            beats = measure_info.get('length', 4)
            accumulated_time += beats * beat_duration

        return accumulated_time
    

    def get_duration_of_measures(self, start_idx: int, end_idx: int) -> float:
        if start_idx < 0 or end_idx >= len(self.measures):
            return 0.0

        if start_idx > end_idx:
            return 0.0

        beat_duration = self.calculate_beat_duration()
        duration = 0.0

        for i in range(start_idx, end_idx + 1):
            measure_info = self.measures[i]
            beats = measure_info.get('length', 4)
            duration += beats * beat_duration

        return duration
    
    
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


    def insert_measure(self, index: int, beats: int, subdivisions: int):

        if beats <= 0 or subdivisions <= 0:
            return

        if index < 0:
            index = 0
        if index > len(self.measures):
            index = len(self.measures)

        new_measure = {
            "length": beats,          # IMPORTANTE: usar 'length', no 'beats'
            "subdivisions": subdivisions,            
        }

        with self.lock:

            # Insertar measure
            self.measures.insert(index, new_measure)

            # Crear patrón vacío correspondiente
            for inst in self.patterns:

                empty_pattern = [
                    [0] * subdivisions for _ in range(beats)
                ]

                self.patterns[inst].insert(index, empty_pattern)

            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0
       
                

    def add_measure(self, beats: int, subdivisions: int):
        self.insert_measure(len(self.measures), beats, subdivisions)

    
    def duplicate_measure(self, source_idx: int, insert_after_idx: int):

        if not (0 <= source_idx < len(self.measures)):
            return
    
        if not (0 <= insert_after_idx < len(self.measures)):
            return
    
        with self.lock:
        
            # Copiar estructura del compás
            original_measure = self.measures[source_idx]
            new_measure = original_measure.copy()
    
            insert_position = insert_after_idx + 1
            self.measures.insert(insert_position, new_measure)
    
            # Copiar patrones
            for inst in self.patterns:
                original_pattern = self.patterns[inst][source_idx]
                pattern_copy = [beat[:] for beat in original_pattern]
                self.patterns[inst].insert(insert_position, pattern_copy)
    
            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0



    # Mtodo para eliminar compases seleccionados
    def delete_measures(self, indices: list[int]):
        with self.lock:
            # Ajustar o eliminar bloques afectados
            updated_blocks = []

            for block in self.loop_blocks:
                if block.end < 0 or block.start >= len(self.measures):
                    continue
                
                # Si el bloque fue parcialmente eliminado, descartarlo
                if any(idx >= block.start and idx <= block.end for idx in indices):
                    continue
                
                updated_blocks.append(block)

            self.loop_blocks = updated_blocks

            for measure_idx in sorted(indices, reverse=True):
                if 0 <= measure_idx < len(self.measures):
                    del self.measures[measure_idx]
                    for inst in self.patterns:
                        del self.patterns[inst][measure_idx]

            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.absolute_position = 0

    
    def remove_loop_block(self, start, end):
        self.loop_blocks = [
            loop for loop in self.loop_blocks
            if not (loop.start == start and loop.end == end)
        ]


    def _generate_measure_events(self, measure_idx, accumulated_time, beat_duration):
        measure_info = self.measures[measure_idx]
        current_beats = measure_info.get('length', 4)
        current_subdiv = measure_info.get('subdivisions', 4)

        measure_duration = current_beats * beat_duration

        for inst in self.patterns:
            pattern_for_measure = self.patterns[inst][measure_idx]

            for beat_idx in range(current_beats):
                for subdiv_idx in range(current_subdiv):
                    if pattern_for_measure[beat_idx][subdiv_idx] == 1:
                        time = (
                            accumulated_time +
                            (beat_idx * beat_duration) +
                            (subdiv_idx / current_subdiv * beat_duration)
                        )

                        event = AudioEvent(
                            time=time,
                            samples=self.sounds[inst],
                            duration=len(self.sounds[inst]) / SAMPLE_RATE,
                            instrument=inst
                        )

                        self.events.append(event)

        return accumulated_time + measure_duration
    

    def get_current_time(self):
        with self.lock:
            return self.absolute_position / SAMPLE_RATE

    
    def get_visual_time(self):

        with self.lock:
            current_time = self.absolute_position / SAMPLE_RATE

        if not self.loop_blocks:
            return current_time

        for loop in self.loop_blocks:

            loop_start = self.get_time_at_measure(loop.start)
            loop_duration = self.get_duration_of_measures(loop.start, loop.end)
            expanded_duration = loop_duration * loop.times
            loop_end_expanded = loop_start + expanded_duration

            # 🔥 Si estamos dentro del bloque expandido
            if loop_start <= current_time < loop_end_expanded:

                time_inside = current_time - loop_start
                time_in_block = time_inside % loop_duration

                return loop_start + time_in_block

            # 🔥 Si ya pasó completamente el bloque expandido
            if current_time >= loop_end_expanded:
                # Saltar expansión pero sin modificar acumulativamente
                current_time = current_time - (expanded_duration - loop_duration)

        return current_time
    

    def get_visual_position_data(self):
        """
        Devuelve:
        - measure_index visual actual
        - offset en segundos dentro del compás
        """

        with self.lock:
            current_time = self.absolute_position / SAMPLE_RATE

        visual_time = self.get_visual_time()

        # encontrar compás actual
        accumulated = 0.0

        for i in range(self.get_measure_count()):
            measure_duration = self.get_duration_of_measures(i, i)

            if accumulated + measure_duration > visual_time:
                offset = visual_time - accumulated
                return i, offset

            accumulated += measure_duration

        return self.get_measure_count() - 1, 0.0
    

    # Genera la lista de eventos de audio basados en el patrn actual
    def generate_events(self):
        self.events = []

        beat_duration = self.calculate_beat_duration()

        # Creamos una lista expandida de índices reales
        expanded_measure_indices = []

        i = 0
        while i < len(self.measures):

            loop_applied = False

            for loop in self.loop_blocks:
                if loop.start == i:
                
                    block_range = list(range(loop.start, loop.end + 1))

                    for _ in range(loop.times):
                        expanded_measure_indices.extend(block_range)

                    i = loop.end + 1
                    loop_applied = True
                    break

            if not loop_applied:
                expanded_measure_indices.append(i)
                i += 1

        # Ahora generamos eventos linealmente
        accumulated_time = 0.0

        for measure_idx in expanded_measure_indices:

            measure_info = self.measures[measure_idx]
            beats = measure_info.get('length', 4)
            subdivs = measure_info.get('subdivisions', 4)

            for inst in self.patterns:
                pattern_for_measure = self.patterns[inst][measure_idx]

                for beat_idx in range(beats):
                    for subdiv_idx in range(subdivs):

                        if pattern_for_measure[beat_idx][subdiv_idx] == 1:

                            time = (
                                accumulated_time +
                                beat_idx * beat_duration +
                                (subdiv_idx / subdivs) * beat_duration
                            )

                            self.events.append(AudioEvent(
                                time=time,
                                samples=self.sounds[inst],
                                duration=len(self.sounds[inst]) / SAMPLE_RATE,
                                instrument=inst
                            ))

            accumulated_time += beats * beat_duration

        self.total_duration = accumulated_time
        self.events.sort(key=lambda e: e.time)


    def callback(self, in_data, frame_count, time_info, status):

        buffer = np.zeros((frame_count, CHANNELS), dtype=np.float32)

        with self.lock:
            playing = self.playing
            absolute_position = self.absolute_position
            events = self.events
            total_duration = self.total_duration

        if not playing or total_duration <= 0:
            silent = (buffer * 32767).astype(np.int16)
            return (silent.tobytes(), pyaudio.paContinue)

        total_samples = int(total_duration * SAMPLE_RATE)

        buffer_start_sample = absolute_position
        buffer_end_sample = absolute_position + frame_count

        # 🔥 SOLO PROCESAR EVENTOS DENTRO DEL RANGO
        for event in events:

            event_start = int(event.time * SAMPLE_RATE)
            event_end = event_start + len(event.samples)

            if event_end < buffer_start_sample:
                continue

            if event_start > buffer_end_sample:
                break  # eventos están ordenados → cortar aquí

            overlap_start = max(event_start, buffer_start_sample)
            overlap_end = min(event_end, buffer_end_sample)

            if overlap_start < overlap_end:

                buffer_offset = overlap_start - buffer_start_sample
                sample_offset = overlap_start - event_start
                length = overlap_end - overlap_start

                buffer[buffer_offset:buffer_offset+length] += \
                    event.samples[sample_offset:sample_offset+length]

        absolute_position += frame_count

        if absolute_position >= total_samples:
            absolute_position = 0

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
            start_frame = int(event.time * SAMPLE_RATE)
            end_frame = start_frame + len(event.samples)

            if start_frame >= total_frames:
                continue

            end_frame = min(end_frame, total_frames)
            sample_slice = slice(0, end_frame - start_frame)

            export_buffer[start_frame:end_frame] += event.samples[sample_slice]

        export_buffer = np.clip(export_buffer, -1, 1)
        export_buffer = (export_buffer * 32767).astype(np.int16)

        sf.write(filename, export_buffer, SAMPLE_RATE)
    