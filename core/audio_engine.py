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
        # El callback se ejecuta en otro hilo. Los prints aqu deben ser mínimos.
        buffer = np.zeros((frame_count, CHANNELS), dtype=np.float32)
        # Reiniciar posición si se completa un loop
    
        
        with self.lock:
            if self.playing and self.total_duration > 0:
                if self.absolute_position >= self.total_duration * SAMPLE_RATE:
                    self.absolute_position = 0
                total_duration_samples_rounded = int(round(self.total_duration * SAMPLE_RATE))
                if total_duration_samples_rounded <= 0:
                    #print("ADVERTENCIA: Duracin total en samples <= 0 en callback.") # Evitar prints constantes
                    return (buffer.tobytes(), pyaudio.paContinue)

                modulo_result = int(self.absolute_position) % total_duration_samples_rounded
                current_time = modulo_result / SAMPLE_RATE

                # --- DEBUG Callback: Verificar la lista de eventos ANTES de iterar (opcional) ---
                # print(f"DEBUG Callback: Procesando buffer en tiempo {current_time:.4f}. Nmero de eventos: {len(self.events)}") # Evitar prints constantes

                for event in self.events:
                    try: # Usar try-except para atrapar errores dentro del bucle sin romper el callback
                        start_time = event.get('time')
                        event_samples = event.get('samples')
                        event_duration = event.get('duration', 0)


                        # --- DEBUG Callback: Verificar el evento individual ---
                        #print(f"DEBUG Callback: Evento en tiempo {current_time:.4f}, Event start {start_time:.4f}. Inst: {event.get('instruments')}. Samples type: {type(event_samples)}") # Evitar prints constantes

                        # Verificaciones robustas antes de usar los datos del evento
                        if start_time is None or event_samples is None or not isinstance(event_samples, np.ndarray) or len(event_samples) == 0:
                             print(f"ADVERTENCIA Callback: Evento invlido o incompleto encontrado en tiempo {current_time:.4f}. Datos: {event}")
                             continue # Saltar este evento invlido


                        buffer_start_time = current_time
                        buffer_end_time = current_time + frame_count / SAMPLE_RATE

                        if (start_time < buffer_end_time and event_duration + start_time > buffer_start_time):

                            event_start_in_buffer_frames = int((start_time - buffer_start_time) * SAMPLE_RATE)

                            sample_start_in_event_frames = max(0, -event_start_in_buffer_frames)
                            frames_to_copy = min(frame_count - event_start_in_buffer_frames, len(event_samples) - sample_start_in_event_frames)

                            frames_to_copy = max(0, frames_to_copy)

                            if frames_to_copy > 0:
                                buffer_start_frame = max(0, event_start_in_buffer_frames)
                                buffer_end_frame = buffer_start_frame + frames_to_copy

                                sample_start_frame = sample_start_in_event_frames
                                sample_end_frame = sample_start_frame + frames_to_copy

                                if buffer_end_frame <= frame_count and sample_end_frame <= len(event_samples):
                                     buffer[buffer_start_frame:buffer_end_frame] += event_samples[sample_start_frame:sample_end_frame]
                                else:
                                     # Manejar este caso cortando al mximo posible
                                     actual_frames_to_copy = min(frame_count - buffer_start_frame, len(event_samples) - sample_start_frame)
                                     if actual_frames_to_copy > 0:
                                         buffer[buffer_start_frame:buffer_start_frame + actual_frames_to_copy] += event_samples[sample_start_frame:sample_start_frame + actual_frames_to_copy]


                    except Exception as e:
                        # Capturar cualquier excepcin en el callback y reportarla (sin romper el hilo de audio)
                        print(f"\nERROR en AudioEngine Callback: {e}")
                        # Podras aadir ms detalles del evento que caus el error si es posible
                        # print(f"Evento problemtico: {event}") # Cuidado con el tamao de los datos aqu
                        # No retornar paComplete a menos que quieras detener el stream
                        pass # Continuar procesando otros eventos si es posible


            self.absolute_position += frame_count
            buffer = np.clip(buffer, -1, 1)
            buffer = (buffer * 32767).astype(np.int16)

            return (buffer.tobytes(), pyaudio.paContinue)
        
    
    def get_current_playback_time(self):
        if self.total_duration > 0:
            return (self.absolute_position % (self.total_duration * SAMPLE_RATE)) / SAMPLE_RATE
        return 0.0
        
        
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
    