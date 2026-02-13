import pyaudio
import threading
import soundfile as sf
import os
import numpy as np

# Constantes de audio
SAMPLE_RATE = 44100
CHANNELS = 2
FORMAT = pyaudio.paInt16
BUFFER_SIZE = 1024

class AudioEngine:
    def __init__(self, sounds):
        self.sounds = sounds
        self.gui = None
        self.grid_panel = None

        self.SAMPLE_RATE = SAMPLE_RATE
        self.CHANNELS = CHANNELS
        self.FORMAT = FORMAT
        self.BUFFER_SIZE = BUFFER_SIZE

        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.events = []
        self.absolute_position = 0
        self.loop_start_position = 0
        self.playing = False
        self.looping = False
        self.total_duration = 0
        self.lock = threading.Lock()
        self.bpm = 155

        # Lista para almacenar la informacin de cada medida (beats y subdivisiones)
        self.measures = []

        # Diccionario para almacenar los patrones de los instrumentos
        self.patterns = {
            'crash 1': [],
            'crash 2': [],
            'cowbell': [],
            'Op. hihat': [],
            'H. tom': [],
            'snare': [],
            'F. tom': [],
            'kick': [],
            'F. hihat': []
            # Asegrate de que todos tus instrumentos estn listados aqu
        }


    # Mtodos de guardado y carga (comentados como en tu cdigo original)
    #def save_project(self, filename):
    #    filepath = f"projects/{filename}"
    #    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    #    project_data = {
    #        'bpm': self.bpm,
    #        'measures': self.measures,
    #        'patterns': self.patterns,
    #        'project_name': self.project_name
    #    }
    #    np.savez(filepath, **project_data)
    #    print(f'Proyecto guardado en: {filepath}.npz')
    #    return filename

    #def load_project(self, filename):
    #    filepath = f"projects/{filename}.npz"
    #    try:
    #        self.absolute_position = 0
    #        data = np.load(filepath, allow_pickle=True)
    #        self.bpm = data['bpm'].item()
    #        # Cargar measures que ahora son dicts
    #        self.measures = [dict(m) for m in data['measures']]

    #        loaded_patterns = data['patterns'].item()
    #        self.patterns = {inst: [list(beat_list) for beat_list in measure] for inst, measure in loaded_patterns.items()}

    #        if 'project_name' in data:
    #            self.project_name = str(data['project_name'].item())
    #        else:
    #            self.project_name = ""

    #        self.total_duration = self.calculate_total_duration()
    #        self.generate_events()
    #        print(f'CARGADO {self.project_name} DESDE LOAD CON EXITO')
    #        return True
    #    except FileNotFoundError:
    #        print(f'Archivo no encontrado: {filepath}')
    #        return False

    #def set_project_name(self, name):
    #    self.project_name = name


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

    def start(self):
        if not self.playing:
            self.playing = True
            self.looping = True
            self.stream = self.pa.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                output=True,
                frames_per_buffer=self.BUFFER_SIZE,
                stream_callback=self.callback
            )
            self.stream.start_stream()
            if self.total_duration > 0 and self.absolute_position / self.SAMPLE_RATE >= self.total_duration:
                self.absolute_position = 0
        else:
             if not self.stream or not self.stream.is_active():
                 self.stream = self.pa.open(
                     format=self.FORMAT,
                     channels=self.CHANNELS,
                     rate=self.SAMPLE_RATE,
                     output=True,
                     frames_per_buffer=self.BUFFER_SIZE,
                     stream_callback=self.callback
                 )
                 self.stream.start_stream()
             self.playing = True
             self.looping = True

    def stop(self):
        if self.playing:
            self.playing = False
            self.looping = False
            if self.stream and self.stream.is_active():
                self.stream.stop_stream()
                #self.stream.close() # Comentado para posible reanudacin ms rpida
                #self.stream = None # Comentado si no cierras el stream

    def add_measure(self):
        # Obtener beats y subdivisiones de los inputs de la GUI al añadir
        current_beats = 4
        current_subdiv = 4

        if hasattr(self, 'gui') and self.gui is not None and hasattr(self.gui, 'input_values'):
            try:
                beats_str = self.gui.input_values.get('beats', '4')
                subdivs_str = self.gui.input_values.get('subdivisions', '4')

                current_beats = int(beats_str)
                current_subdiv = int(subdivs_str)

                # Asegurar valores > 0 al añadir
                if current_beats <= 0: current_beats = 4
                if current_subdiv <= 0: current_subdiv = 16

            except ValueError:
                print("Advertencia: Valores de beats o subdivisiones no numricos al aadir. Usando por defecto.")
                current_beats = 4
                current_subdiv = 16

        # Añadir beats Y subdivisiones a la lista de medidas
        self.measures.append({'length': current_beats, 'subdivisions': current_subdiv})

        # Inicializar el patrn para el nuevo compás con las dimensiones obtenidas
        for inst in self.patterns:
            # Asegurar que la lista para el instrumento tenga espacio para el nuevo compás
            while len(self.patterns[inst]) < len(self.measures):
                 # Añadir la estructura de patrón para el nuevo compás
                 self.patterns[inst].append([[0] * current_subdiv for _ in range(current_beats)])

        # Recalcular duracin total y eventos despus de añadir
        self.total_duration = self.calculate_total_duration()
        self.generate_events()

        # Notificar al grid_panel para que se redibuje
        if self.grid_panel:
            self.grid_panel._update_content_surface()


    # Mtodo para eliminar compases seleccionados
    def delete_selected_measures(self):
        if self.gui and self.gui.grid_panel:
            # Obtener los ndices seleccionados y ordenarlos de mayor a menor para eliminarlos sin afectar ndices futuros en el mismo bucle
            selected_indices = sorted(self.gui.grid_panel.selected_measures_indices, reverse=True)

            if not selected_indices:
                #print("No hay compases seleccionados para eliminar.") # Comentado para reducir output
                return

            # Usar un lock si la eliminacin puede ocurrir durante la reproduccin (ms seguro)
            with self.lock:
                for measure_idx in selected_indices:
                    if 0 <= measure_idx < len(self.measures):
                        # Eliminar la informacin de la medida de la lista measures
                        del self.measures[measure_idx]
                        # Eliminar el patrn correspondiente para cada instrumento
                        for inst in self.patterns:
                            if measure_idx < len(self.patterns[inst]): # Asegurar que el ndice existe en la lista del instrumento
                                del self.patterns[inst][measure_idx]
                            #else:
                                #print(f"ADVERTENCIA: Intento de eliminar patrn para {inst} en ndice {measure_idx}, pero no existe.") # Comentado para reducir output


            # Despus de eliminar, recalcular todo y actualizar GUI
            self.total_duration = self.calculate_total_duration()
            self.generate_events()
            self.gui.grid_panel.selected_measures_indices = [] # Limpiar seleccin
            self.gui.grid_panel._update_content_surface() # Redibujar grid

        #else:
            #print("ADVERTENCIA: delete_selected_measures llamado pero grid_panel o gui no estn disponibles.") # Comentado para reducir output


    # Actualiza el estado de una celda especfica en el patrn
    # Este mtodo se llama desde grid_panel cuando se hace clic en una celda
    def update_pattern(self, instrument, measure_idx, beat, subdiv_idx, value):
        with self.lock:
            # Antes de actualizar, verificar que los ndices son vlidos segn la estructura ACTUAL del patrn
            if instrument in self.patterns and \
               measure_idx < len(self.patterns[instrument]) and \
               beat < len(self.patterns[instrument][measure_idx]) and \
               subdiv_idx < len(self.patterns[instrument][measure_idx][beat]):
                # Actualizar el estado de la celda especfica
                self.patterns[instrument][measure_idx][beat][subdiv_idx] = value
                # Regenerar eventos para que el cambio se refleje en la reproduccin
                self.generate_events()
            #else:
                #print(f"ADVERTENCIA: Intento de actualizar patrn con ndices invlidos: {instrument}, {measure_idx}, {beat}, {subdiv_idx}. El patrn no tiene esas dimensiones.") # Comentado para reducir output


    # Genera la lista de eventos de audio basados en el patrn actual
    def generate_events(self):
        # --- DEBUG: Mostrar contenido de eventos ANTES de limpiar/regenerar (opcional, puede ser largo) ---
        # print("\n--- DEBUG: Contenido de self.events ANTES de generar ---")
        # for i, event in enumerate(self.events[:5]): # Mostrar solo los primeros 5 para no saturar
        #      print(f"  DEBUG Antes [{i}]: Tiempo={event.get('time'):.4f}, Inst='{event.get('instruments')}', Samples len={len(event.get('samples', []))}, Samples type={type(event.get('samples'))}")

        self.events = [] # Limpiar la lista de eventos para regenerarla
        beat_duration = self.calculate_beat_duration()
        accumulated_time = 0.0

        print("\n--- DEBUG: Generando eventos ---")

        for inst in self.patterns:
            accumulated_time = 0.0

            for measure_idx, measure_info in enumerate(self.measures):
                current_beats = measure_info.get('length', 4)
                current_subdiv = measure_info.get('subdivisions', 16)

                measure_duration = current_beats * beat_duration

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
                                        'duration': len(self.sounds[inst]) / self.SAMPLE_RATE,
                                        'samples': self.sounds[inst], # Contiene los datos de audio (ndarray)
                                        'instruments': inst
                                    }
                                    self.events.append(event_data)
                                    # --- DEBUG: Mostrar detalles de CADA evento generado ---
                                    print(f"DEBUG Evento Generado: Tiempo={event_data['time']:.4f}, Instrumento='{event_data['instruments']}', Medida={measure_idx + 1}, Beat={beat_idx + 1}, Subdiv={subdiv_idx + 1}, Samples len={len(event_data.get('samples', []))}, Samples type={type(event_data.get('samples'))}, Samples dtype={getattr(event_data.get('samples'), 'dtype', 'N/A')}")

                    else:
                         print(f"ADVERTENCIA CRITICA: Patrn inconsistente para instrumento '{inst}' en compas {measure_idx + 1}.")
                         print(f"Dimensiones esperadas (de measure): {current_beats} beats, {current_subdiv} subdivs.")
                         print(f"Dimensiones encontradas (de pattern): {pattern_beats} beats, {pattern_subdivs_per_beat} subdivs (primer beat).")
                         print("Saltando generacin de eventos para este patrn/compas inconsistente.")


                accumulated_time += measure_duration


        # --- DEBUG: Mostrar contenido de eventos DESPUS de sortear ---
        print(f"--- DEBUG: Generacin de eventos terminada. Total eventos: {len(self.events)} ---")
        for i, event in enumerate(self.events[:5]): # Mostrar solo los primeros 5
             print(f"  DEBUG Despus [{i}]: Tiempo={event.get('time'):.4f}, Inst='{event.get('instruments')}', Samples len={len(event.get('samples', []))}, Samples type={type(event.get('samples'))}")


    def callback(self, in_data, frame_count, time_info, status):
        # El callback se ejecuta en otro hilo. Los prints aqu deben ser mínimos.
        buffer = np.zeros((frame_count, self.CHANNELS), dtype=np.float32)
        # Reiniciar posición si se completa un loop
    
        
        with self.lock:
            if self.looping and self.total_duration > 0:
                if self.absolute_position >= self.total_duration * self.SAMPLE_RATE:
                    self.absolute_position = 0
                total_duration_samples_rounded = int(round(self.total_duration * self.SAMPLE_RATE))
                if total_duration_samples_rounded <= 0:
                    #print("ADVERTENCIA: Duracin total en samples <= 0 en callback.") # Evitar prints constantes
                    return (buffer.tobytes(), pyaudio.paContinue)

                modulo_result = int(self.absolute_position) % total_duration_samples_rounded
                current_time = modulo_result / self.SAMPLE_RATE

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
                        buffer_end_time = current_time + frame_count / self.SAMPLE_RATE

                        if (start_time < buffer_end_time and event_duration + start_time > buffer_start_time):

                            event_start_in_buffer_frames = int((start_time - buffer_start_time) * self.SAMPLE_RATE)

                            sample_start_in_event_frames = max(0, -event_start_in_buffer_frames)
                            frames_to_copy = min(frame_count - event_start_in_buffer_frames, len(event_samples) - sample_start_in_event_frames)

                            frames_to_copy = max(0, frames_to_copy)

                            if frames_to_copy > 0:
                                buffer_start_frame = max(0, event_start_in_buffer_frames)
                                buffer_end_frame = buffer_start_frame + frames_to_copy

                                sample_start_frame = sample_start_in_event_frames
                                sample_end_frame = sample_start_frame + frames_to_copy

                                # --- DEBUG Callback: Mostrar shapes antes de la operacin ---
                                # print(f"DEBUG Callback SLICE: buffer slice shape={buffer[buffer_start_frame:buffer_end_frame].shape}, sample slice shape={event_samples[sample_start_frame:sample_end_frame].shape}") # Evitar prints constantes
                                # print(f"DEBUG Callback SLICE: buffer frames {buffer_start_frame}:{buffer_end_frame}, sample frames {sample_start_frame}:{sample_end_frame}") # Evitar prints constantes


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
            return (self.absolute_position % (self.total_duration * self.SAMPLE_RATE)) / self.SAMPLE_RATE
        return 0.0
        
        
    def export(self, filename, duration):
        total_frames = int(duration * self.SAMPLE_RATE)
        export_buffer = np.zeros((total_frames, self.CHANNELS), dtype=np.float32)

        for event in self.events:
            start_frame = int(event['time'] * self.SAMPLE_RATE)
            end_frame = start_frame + len(event['samples'])

            if start_frame >= total_frames:
                continue

            end_frame = min(end_frame, total_frames)
            sample_slice = slice(0, end_frame - start_frame)

            export_buffer[start_frame:end_frame] += event['samples'][sample_slice]

        export_buffer = np.clip(export_buffer, -1, 1)
        export_buffer = (export_buffer * 32767).astype(np.int16)

        sf.write(filename, export_buffer, self.SAMPLE_RATE)

    def export_project(self, filename, duration):
        self.stop()
        self.export(filename, duration)
        print(f'Proyecto exportado como: {filename}')                