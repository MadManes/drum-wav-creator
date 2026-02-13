## ESTA ES LA MEJOR VERSION DE CODIGO UNICO

import pygame
import pyaudio
import threading
import librosa
import numpy as np
import os
import soundfile as sf
from queue import Queue

pygame.init()

# Configuración inicial
SAMPLE_RATE = 44100
CHANNELS = 2
FORMAT = pyaudio.paInt16
BUFFER_SIZE = 1024

BEATS_PER_MEASURE = 4
CELL_SIZE = 120
INSTRUMENT_HEIGHT = 30


# Cargar sonidos
def load_sound(file, volume=1.0):
    data, sr = sf.read(file, dtype='float32')
    if sr != SAMPLE_RATE:
        data = librosa.resample(data, orig_sr=sr, target_sr=SAMPLE_RATE)
    if data.ndim == 1:
        data = np.column_stack((data, data))

    final_data = data * volume

    return final_data

sounds = {
    'crash 1': load_sound('assets/sounds/crash_1.wav', 0.5),
    'crash 2': load_sound('assets/sounds/crash_2.wav', 0.7),
    'cowbell': load_sound('assets/sounds/cowbell.wav', 0.8),
    'Op. hihat': load_sound('assets/sounds/op_hihat.wav', 0.5),
    'H. tom': load_sound('assets/sounds/h_tom.wav', 1.4),
    'snare': load_sound('assets/sounds/snare.wav', 1.3),
    'F. tom': load_sound('assets/sounds/f_tom.wav', 1.5),
    'kick': load_sound('assets/sounds/kick.wav', 1.5),
    'F. hihat': load_sound('assets/sounds/f_hihat.wav', 0.8)
}

class AudioEngine:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.events = []
        self.absolute_position = 0
        self.loop_start_position = 0
        self.playing = False
        self.looping = False
        self.total_duration = 0
        self.lock = threading.Lock()
        self.bpm = 120  #164
        self.measures = []
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
        }

        # Atributo para file project
        self.project_name = ""

    def save_project(self, filename):
        filepath = f"projects/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Crea la carpeta si no existe
        project_data = {
            'bpm': self.bpm,
            'measures': self.measures,
            'patterns': self.patterns,
            'project_name': self.project_name
        }
        np.savez(filepath, **project_data) ## Ver bien que hace este
        print(f'Proyecto guardado en: {filepath}.npz')

        return filename

    def load_project(self, filename):
        filepath = f"projects/{filename}.npz"
        try:
            self.absolute_position = 0
            data = np.load(filepath, allow_pickle=True)
            #print(f'Tipo de data[patterns]: {type(data['patterns'])}')
            #print(f'Contenido de data[patterns]: {data['patterns']}')
            self.bpm = data['bpm'].item() # item() para convertir np.array escalar a tipo nativo
            self.measures = list(data['measures']) # Convierte de np array a lista

            # ver esta linea lo de inst != bpm y != measures chequea que no sean esas keys??
            loaded_patterns = data['patterns'].item()
            self.patterns = {inst: list(loaded_patterns[inst]) for inst in loaded_patterns}
            if 'project_name' in data:
                self.project_name = str(data['project_name'].item()) # Carga nombre y convierte a string
            else:
                self.project_name = "" # Si no hay nombre, inicializar vacio

            self.total_duration = self.calculate_total_duration()
            self.generate_events() #En la linea siguiente: CARGADO {self.project_name} DESDE LOAD CON EXITO')
            return True # Indica carga exitosa

        except FileNotFoundError:
            #print(f'Archivo no encontrado: {filepath}')
            return False # Fallo la carga

    def set_project_name(self, name):
        self.project_name = name

    def calculate_beat_duration(self):
        return 60 / self.bpm

    def calculate_total_duration(self):
        #print("\n>>> En calculate total direction: OK <<<")
        #print(f'Measures: {self.measures}')

        total_duration_seconds = 0
        if not self.measures:
            return 0

        for measure in self.measures:
            beats_per_measure = measure['length']
            total_duration_seconds += 60 / self.bpm * beats_per_measure

        #print(f'Calculated total duration seconds: {total_duration_seconds}')
        #print(f'Calculated total duration seconds: {total_duration_seconds}')

        return total_duration_seconds

        #total_beats = sum(measure['length'] for measure in self.measures)
        #return total_beats * self.calculate_beat_duration()

    def start(self):
        if not self.playing:
            self.playing = True
            self.looping = True
            self.stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=BUFFER_SIZE,
                stream_callback=self.callback
            )
            self.stream.start_stream()
            if self.absolute_position > self.total_duration * SAMPLE_RATE:
                self.absolute_position = 0
        else:
            if not self.stream.is_active():
                self.stream = self.pa.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True,
                    frames_per_buffer=BUFFER_SIZE,
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
                self.stream.close()
                self.stream = None

    def add_measure(self):
        current_beats = int(self.gui.input_values['beats']) if hasattr(self, 'gui') else 4
        current_subdiv = int(self.gui.input_values['subdivisions']) if hasattr(self, 'gui') else 16

        self.measures.append({'length': current_beats})
        for inst in self.patterns:
            self.patterns[inst].append([[0] * current_subdiv for _ in range(current_beats)])

        self.total_duration = self.calculate_total_duration()

    def update_pattern(self, instrument, measure_idx, beat, subdiv_idx, value):
        with self.lock:
            if measure_idx < len(self.patterns[instrument]):
                self.patterns[instrument][measure_idx][beat][subdiv_idx] = value
            #print(f'\n\nASI SE VE UN PATTERN ORIGINAL:\n {self.patterns}')
            self.generate_events()

    def generate_events(self):
        #print(f'------ generate events() llamada ------')
        #print(f'BPM: {self.bpm}')
        #print(f'MEDIDAS: {self.measures}')
        #print(f'Patrones: Instrumentos: {list(self.patterns.keys())}')
        #print("\n>>> generate events OK <<<\n")
        self.events = []
        beat_duration = self.calculate_beat_duration()
        accumulated_time = 0.0

        for inst in self.patterns:
            accumulated_time = 0.0

            for measure_idx, measure in enumerate(self.patterns[inst]):
                current_beats = len(measure)
                measure_duration = current_beats * beat_duration
                #print(f'Medida {measure_idx + 1}, Beats {current_beats}, Duracion {measure_duration}')
                for beat_idx in range(current_beats):
                    current_subdiv = len(measure[beat_idx])
                    for subdiv_idx in range(current_subdiv):
                        if measure[beat_idx][subdiv_idx] == 1:
                            time = accumulated_time + (beat_idx * beat_duration) + (subdiv_idx / current_subdiv * beat_duration)
                            self.events.append({
                                    'time': time,
                                    'sound': sounds[inst],
                                    'duration': len(sounds[inst]) / SAMPLE_RATE,
                                    'samples': sounds[inst],
                                    'instruments': inst
                                })
                            # DEBUG SOLO LOS PRIMEROS 5 EVENTOS
                            #if len(self.events) < 5:
                            #    print(f'EVENTO:\nTiempo: {time:.3f}, Instrumento: {inst}, Medida: {measure_idx + 1},\nBeat: {beat_idx + 1}, Subdiv: {subdiv_idx + 1}')

                accumulated_time += measure_duration

        self.events.sort(key=lambda x: x['time'])

    def callback(self, in_data, frame_count, time_info, status):
        buffer = np.zeros((frame_count, CHANNELS), dtype=np.float32)
        #current_time = self.absolute_position / SAMPLE_RATE
        with self.lock:
            if self.looping and self.total_duration > 0:
                total_duration_samples_rounded = int(round(self.total_duration * SAMPLE_RATE))
                modulo_result = int(self.absolute_position) % total_duration_samples_rounded
                current_time = modulo_result / SAMPLE_RATE
                #current_time = (self.absolute_position % round(self.total_duration * SAMPLE_RATE)) / SAMPLE_RATE
                #print(f'\nCallback:\n-absolute position type: {type(self.absolute_position)},\ntotal duration type: {type(self.total_duration)}: {self.total_duration:.3f}')
                #print(f'SAMPLE RATE: {SAMPLE_RATE}, total duration samples rounded type: {type(total_duration_samples_rounded)}: {total_duration_samples_rounded}')
                #print(f'\n-total duration samples rounded: {total_duration_samples_rounded},\n-modulo result: {modulo_result}')
                #print(f'\n\n-current time: {current_time:.3f},\n-total duration: {self.total_duration:.3f},\n-absolute position: {self.absolute_position}')
                for event in self.events:
                    start_time = event['time']
                    end_time = start_time + event['duration']
                    ## DEBUG TIEMPO
                    #print(f'EVENTO:\nInstrumento: {event['instruments']}, Start: {start_time:.3f}, End: {end_time:.3f}')
                    condition =  (current_time <= start_time < current_time + frame_count/SAMPLE_RATE or
                                  current_time < end_time <= current_time + frame_count/SAMPLE_RATE or
                                 (start_time < current_time and end_time > current_time + frame_count/SAMPLE_RATE))
                    #print(f'\nCondicion de reproduccion: {condition}')
                    if condition:
                        start_pos = int((start_time - current_time) * SAMPLE_RATE)
                        play_pos = max(-start_pos, 0)
                        start_pos = max(start_pos, 0)
                        max_samples = len(event['samples']) - play_pos
                        samples_to_copy = min(frame_count - start_pos, max_samples)
                        samples_to_copy = max(0, samples_to_copy)
                        if samples_to_copy == 0:
                            continue

                        buffer_slice = buffer[start_pos:start_pos + samples_to_copy]
                        sample_slice = event['samples'][play_pos:play_pos + samples_to_copy]
                        if buffer_slice.shape == sample_slice.shape:
                            buffer[start_pos:start_pos + samples_to_copy] += sample_slice
                        else:
                            min_len = min(buffer_slice.shape[0], sample_slice.shape[0])
                            buffer[start_pos:start_pos + min_len] += sample_slice[:min_len]


            self.absolute_position += frame_count
            buffer = np.clip(buffer, -1, 1)
            buffer = (buffer * 32767).astype(np.int16)

            return (buffer.tobytes(), pyaudio.paContinue)

    def export(self, filename, duration):
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

    def export_project(self, filename, duration):
        self.stop() # Stop playback
        self.export(filename, duration) # Call existing export method
        print(f'Proyecto exportado como: {filename}')


class DrumGUI:
    def __init__(self, engine):
        self.engine = engine
        self.font = pygame.font.SysFont('Arial', 20)
        self.screen = pygame.display.set_mode((1280, 600))
        self.clock = pygame.time.Clock()
        self.selected_measures = set()

        # Atributos INPUT
        self.active_input = None
        self.input_values = {'beats': '4', 'subdivisions': '16'}
        self.cursor_visible = False
        self.cursor_timer = 0

        self.input_beats_rect = pygame.Rect(160, 500, 60, 30)
        self.input_subdiv_rect = pygame.Rect(320, 500, 60, 30)

        self.instrument_rects = []
        self.measure_grid = []
        self.measure_width = 600
        self.left_panel_width = 200
        self.selected_inst = None
        self.create_gui_elements()

        # Atributos de SCROLL
        self.scroll_x = 0
        self.max_scroll_x = 0
        self.scrollbar_rect = pygame.Rect(200, 550, 880, 20) # Ajustar para responsive para todo lo que se imprime (botones, grid, instrtuments, etc)
        self.scrollbar_handle_rect = pygame.Rect(200, 550, 100, 20) # barrita scroll
        self.is_scrolling = False # Para ver si esta arrastrando la barra de scroll
        self.mouse_offset_x = 0 # offset del puntero del mouse dentro de la barrita de scroll al empezar a arrastrar
        self.scroll_mouse_offset = 0

        self.engine.gui = self

        # Atributos SAVE/LOAD
        self.save_button_rect = pygame.Rect(290, 10, 30, 30) # El rojo
        self.load_button_rect = pygame.Rect(330, 10, 30, 30) # El verde
        self.export_button_rect = pygame.Rect(370, 10, 30, 30) # Nuevo botón exportar


        # Popup de SAVE
        self.save_popup_rect = pygame.Rect(340, 150, 600, 300)
        self.save_input_rect = pygame.Rect(360, 200, 560, 30)
        self.save_list_rect = pygame.Rect(360, 240, 560, 150)
        self.save_accept_btn_rect = pygame.Rect(720, 400, 100, 30)
        self.save_cancel_btn_rect = pygame.Rect(840, 400, 100, 30)
        self.save_popup_rect = pygame.Rect(340, 159, 600, 300)

        self.project_input_text = "" # Texto ingresado para nombre del proyecto
        self.saved_projects = self.get_saved_projects_list() # Lista guardada usando el metodo get saved list

        self.save_list_scroll_y = 0
        self.save_list_item_height = 25 # Altura de cada iterm en la lista
        self.load_list_item_height = self.save_list_item_height

        self.is_save_popup_visible = False # Controla visibilidad de esta ventana

        # Popup de LOAD
        self.load_popup_rect = pygame.Rect(340, 150, 600, 300)
        self.load_list_rect = pygame.Rect(360, 200, 560, 190)
        self.load_accept_btn_rect = pygame.Rect(720, 400, 100, 30)
        self.load_cancel_btn_rect = pygame.Rect(840, 400, 100, 30)
        self.load_popup_rect = pygame.Rect(340, 159, 600, 300)

        self.load_list_scroll_y = 0
        self.selected_poject_index = - 1 # -1 es igual a ningun proyecto seleccionado

        self.is_load_popup_visible = False # Controla visibilidad de esta ventana


    def create_gui_elements(self):
        # Lista de instrumentos
        y = 50
        for i, inst in enumerate(self.engine.patterns.keys()):
            rect = pygame.Rect(0, y + 30, 150, INSTRUMENT_HEIGHT) # 150 es el width de la columna instrumentos
            self.instrument_rects.append((rect, inst))
            y += INSTRUMENT_HEIGHT + 10

        # Botones
        self.add_measure_btn = pygame.Rect(20, 10, 120, 30)
        self.play_btn = pygame.Rect(160, 10, 120, 30)

    def get_saved_projects_list(self):
        projects_dir = "projects" # Carpeta donde se guardan los proyectos
        if not os.path.exists(projects_dir):
            return [] # Si no existe la carpeta, devuelve lista vacía
        files = [f for f in os.listdir(projects_dir) if f.endswith(".npz")] # Lista archivos .prj
        return sorted([f.replace(".npz", "") for f in files]) # Nombres sin extensión y ordenados

    def draw_grid(self):
        if self.is_save_popup_visible or self.is_load_popup_visible: # Si popup visible, oscurecer grid
            surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA) # Superficie transparente
            surface.fill((0, 0, 0, 150)) # Relleno negro semi-transparente
            self.screen.blit(surface, (0, 0)) # Dibujar encima de la pantalla

        if not self.is_save_popup_visible and not self.is_load_popup_visible: # Dibujar grid solo si no hay popup
            x_base = self.left_panel_width - self.scroll_x
            y_start = 80
            self.measure_grid = []
            self.total_grid_width = len(self.engine.measures) * self.measure_width
            visible_width = self.screen.get_width() - self.left_panel_width
            self.max_scroll_x = max(0, self.total_grid_width - visible_width)

            for measure_idx, measure in enumerate(self.engine.measures):
                x = x_base + (measure_idx * self.measure_width)
                current_beats = measure['length']

                if x + self.measure_width > self.left_panel_width and x < self.screen.get_width():
                    # Rect de compas (sin cambios)
                    measure_rect = pygame.draw.rect(self.screen, (50, 50, 50), (x, y_start, self.measure_width, 400), 1)
                    border_color = (100, 100, 100) if measure_idx not in self.selected_measures else (255, 0, 0)
                    pygame.draw.rect(self.screen, border_color, measure_rect, 2)
                    # Rect de solapa (sin cambios)
                    tab_rect = pygame.Rect(x, y_start - 30, 50, 25)
                    pygame.draw.rect(self.screen, (100, 100, 100), tab_rect)
                    text = self.font.render(str(measure_idx + 1), True, (255, 255, 255))
                    self.screen.blit(text, (x + 5, y_start - 25))

                    beat_width = self.measure_width / current_beats
                    for beat_idx in range(current_beats):
                        current_subdiv = len(self.engine.patterns['snare'][measure_idx][beat_idx])
                        subdiv_width = beat_width / current_subdiv
                        for subdiv_idx in range(current_subdiv):
                            x_pos = int(round(x + (beat_idx * beat_width) + (subdiv_idx * subdiv_width)))

                            for inst_idx, inst in enumerate(self.engine.patterns):
                                if (measure_idx < len(self.engine.patterns[inst]) and
                                    beat_idx < len(self.engine.patterns[inst][measure_idx]) and
                                    subdiv_idx < len(self.engine.patterns[inst][measure_idx][beat_idx])):

                                    state = self.engine.patterns[inst][measure_idx][beat_idx][subdiv_idx]
                                    cell_width = int(round(subdiv_width)) - 1

                                    rect = pygame.Rect(
                                        x_pos,
                                        y_start + inst_idx * (INSTRUMENT_HEIGHT + 10),
                                        cell_width,
                                        INSTRUMENT_HEIGHT
                                    )
                                    self.measure_grid.append((rect, (measure_idx, beat_idx, subdiv_idx, inst)))
                                    color = (255, 0, 0) if state else (200, 200, 200) if subdiv_idx != 0 else (150,150,150)
                                    pygame.draw.rect(self.screen, color, rect)

            self.max_scroll_x = max(0, self.total_grid_width - visible_width)
        self.draw_scrollbar()

    def calculate_total_grid_width(self):
        total_width = 0
        for measure_idx , measure in enumerate(self.engine.measures):
            total_width += (BEATS_PER_MEASURE * CELL_SIZE) + 10

        return total_width

    def draw_scrollbar(self):
        scrollbar_rect = pygame.Rect(200, 550, self.screen.get_width() - self.left_panel_width - 30, 15)

        # Fondo
        pygame.draw.rect(self.screen, (100, 100, 100), scrollbar_rect)

        # Borde
        pygame.draw.rect(self.screen, (230, 80, 80), (scrollbar_rect.x - 1, scrollbar_rect.y - 1, scrollbar_rect.width + 1, scrollbar_rect.height + 2), 2)

        # Posicion barrita
        if self.max_scroll_x > 0: # Solo si hay scroll posible
            handle_width = max(50, (scrollbar_rect.width**2) / self.total_grid_width)
            handle_x = self.left_panel_width + (self.scroll_x / self.max_scroll_x) * (scrollbar_rect.width - handle_width)

            self.scrollbar_handle_rect.update(
                handle_x,
                self.scrollbar_rect.y,
                handle_width,
                self.scrollbar_rect.height
            )

            # Dibujar
            pygame.draw.rect(self.screen, (180, 180, 180), (handle_x, 550, handle_width, 15))

    def handle_click(self, pos):
        if self.add_measure_btn.collidepoint(pos):
            self.engine.add_measure()
        elif self.play_btn.collidepoint(pos):
            if self.engine.playing:
                self.engine.stop()
            else:
                self.engine.start()
        elif not self.is_save_popup_visible and not self.is_load_popup_visible: # Solo si no hay popup activo
            for rect, data in self.measure_grid:
                if rect.collidepoint(pos):
                    measure_idx, beat, subdiv_idx, inst = data
                    current = self.engine.patterns[inst][measure_idx][beat][subdiv_idx]
                    self.engine.update_pattern(inst, measure_idx, beat, subdiv_idx, 0 if current else 1)
            for measure_idx in range(len(self.engine.measures)):
                measure_x = self.left_panel_width - self.scroll_x + (measure_idx * self.measure_width)
                tab_rect = pygame.Rect(measure_x, 50, 50, 25)
                if tab_rect.collidepoint(pos):
                    if measure_idx in self.selected_measures:
                        self.selected_measures.remove(measure_idx)
                    else:
                        self.selected_measures.add(measure_idx)

        if self.input_beats_rect.collidepoint(pos):
            self.active_input = 'beats'
            pygame.key.set_text_input_rect(self.input_beats_rect)
            pygame.key.start_text_input()
        elif self.input_subdiv_rect.collidepoint(pos):
            self.active_input = 'subdivisions'
            pygame.key.set_text_input_rect(self.input_subdiv_rect)
            pygame.key.start_text_input()
        else:
            self.active_input = None
            pygame.key.stop_text_input()

        # --- MANEJO CLICKS BOTONES GUARDAR/CARGAR y POPUPS ---
        if self.save_button_rect.collidepoint(pos): # Botón GUARDAR
            self.is_save_popup_visible = True # Mostrar ventana emergente guardar
            self.project_input_text = self.engine.project_name # Inicializar input con nombre actual
            self.saved_projects = self.get_saved_projects_list() # Actualizar lista de proyectos
            self.save_list_scroll_y = 0 # Resetear scroll de lista guardar
            self.active_input = 'save_project_name'
            pygame.key.set_text_input_rect(self.save_input_rect)
            pygame.key.start_text_input()

        elif self.load_button_rect.collidepoint(pos): # Botón CARGAR
            self.is_load_popup_visible = True # Mostrar ventana emergente cargar
            self.saved_projects = self.get_saved_projects_list() # Actualizar lista de proyectos
            self.load_list_scroll_y = 0 # Resetear scroll de lista cargar
            self.selected_project_index = -1 # Deseleccionar proyecto previamente cargado

        elif self.export_button_rect.collidepoint(pos): # Botón EXPORTAR
            filename = "output.wav" # Fixed filename for now
            duration = self.engine.total_duration
            self.engine.export_project(filename, duration)


        # --- Manejo Clicks en ventana emergente GUARDAR ---
        if self.is_save_popup_visible:
            if self.save_accept_btn_rect.collidepoint(pos): # Botón Aceptar en Guardar
                filename = self.project_input_text.strip() # Obtener nombre del input
                if filename: # Si hay nombre
                    saved_filename = self.engine.save_project(filename) # Guardar proyecto
                    if saved_filename:
                        #print(f"Proyecto guardado como: {saved_filename}")
                        self.saved_projects = self.get_saved_projects_list() # Recargar lista de proyectos
                        self.is_save_popup_visible = False # Cerrar popup
                else:
                    print("Por favor, ingresa un nombre para guardar el proyecto.") # Mensaje si no hay nombre

            elif self.save_cancel_btn_rect.collidepoint(pos): # Botón Cancelar en Guardar
                self.is_save_popup_visible = False # Cerrar popup
                self.active_input = None
                pygame.key.stop_text_input()

            # Click en lista de proyectos guardados en Guardar para sobrescribir
            if self.save_list_rect.collidepoint(pos):
                list_y_offset = self.save_list_rect.y + 10 - self.save_list_scroll_y
                for i, project_name in enumerate(self.saved_projects):
                    item_rect = pygame.Rect(self.save_list_rect.x + 10, list_y_offset + i * self.save_list_item_height, self.save_list_rect.width - 20, self.save_list_item_height)
                    if item_rect.collidepoint(pos):
                        self.project_input_text = project_name # Cargar nombre de proyecto en input para sobrescribir
                        break # Salir del loop después de encontrar coincidencia
            elif self.save_input_rect.collidepoint(pos):
                self.active_input = 'save_project_name'
                pygame.key.set_text_input_rect(self.save_input_rect)
                pygame.key.start_text_input()

        # --- Manejo Clicks en ventana emergente CARGAR ---
        if self.is_load_popup_visible:
            if self.load_accept_btn_rect.collidepoint(pos): # Botón Aceptar en Cargar
                if self.selected_project_index != -1: # Si hay proyecto seleccionado
                    filename_to_load = self.saved_projects[self.selected_project_index] # Obtener nombre archivo seleccionado
                    if self.engine.load_project(filename_to_load): # Cargar proyecto
                        print(f"Proyecto cargado: {filename_to_load}")
                        self.is_load_popup_visible = False # Cerrar popup
                    else:
                        print(f"Error al cargar el proyecto: {filename_to_load}") # Error si falla carga

            elif self.load_cancel_btn_rect.collidepoint(pos): # Botón Cancelar en Cargar
                self.is_load_popup_visible = False # Cerrar popup
                pygame.key.stop_text_input()

            # Click en lista de proyectos guardados en Cargar para seleccionar
            if self.load_list_rect.collidepoint(pos):
                list_y_offset = self.load_list_rect.y + 10 - self.load_list_scroll_y
                for i, project_name in enumerate(self.saved_projects):
                    item_rect = pygame.Rect(self.load_list_rect.x + 10, list_y_offset + i * self.save_list_item_height, self.load_list_rect.width - 20, self.load_list_item_height)
                    if item_rect.collidepoint(pos):
                        self.selected_project_index = i # Guardar indice del proyecto seleccionado
                        break # Salir del loop después de encontrar coincidencia


    def handle_event(self, event):
        # --- MANEJO EVENTO TEXTINPUT PARA BEATS Y SUBDIVISIONS
        if event.type == pygame.TEXTINPUT:
            if self.active_input and event.text.isdigit():
                current = self.input_values[self.active_input]
                new_value = current + event.text

                if len(new_value) <= 2:
                    if self.active_input == 'beats' and 2 <= int(new_value) <= 7:
                        self.input_values[self.active_input] = new_value
                    elif self.active_input == 'subdivisions' and 1 <= int(new_value) <= 16:
                        self.input_values[self.active_input] = new_value

        elif event.type == pygame.KEYDOWN:
            if self.active_input:
                if event.key == pygame.K_RETURN:
                    self.update_measure_structure()
                    self.active_input = None
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_values[self.active_input] = self.input_values[self.active_input][:-1]

        # --- MANEJO EVENTOS TEXTINPUT/KEYDOWN para INPUT NOMBRE PROYECTO en GUARDAR ---
        if self.is_save_popup_visible: # Solo si popup guardar visible
            if event.type == pygame.TEXTINPUT:
                self.project_input_text += event.text # Añadir texto ingresado al input
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.project_input_text = self.project_input_text[:-1] # Borrar último caracter

        # --- MANEJO EVENTOS MOUSEWHEEL para SCROLL LISTA GUARDAR/CARGAR ---
        if event.type == pygame.MOUSEWHEEL:
            if self.is_save_popup_visible and self.save_list_rect.collidepoint(pygame.mouse.get_pos()): # Scroll lista guardar
                self.save_list_scroll_y = max(0, min(self.save_list_scroll_y - event.y * 15, max(0, len(self.saved_projects) * self.save_list_item_height - self.save_list_rect.height + 20))) # Ajustar límites scroll

            elif self.is_load_popup_visible and self.load_list_rect.collidepoint(pygame.mouse.get_pos()): # Scroll lista cargar
                self.load_list_scroll_y = max(0, min(self.load_list_scroll_y - event.y * 15, max(0, len(self.saved_projects) * self.load_list_item_height - self.load_list_rect.height + 20))) # Ajustar límites scroll


    def update_measure_structure(self):
        try:
            new_beats = int(self.input_values['beats'])
            new_subdiv = int(self.input_values['subdivisions'])

            if not (2 <= new_beats <= 7) or not (1 <= new_subdiv <= 16):
                return

            for measure_idx in self.selected_measures:
                # Mantener datos existentes
                for inst in self.engine.patterns:
                    new_pattern = []

                    for beat_idx in range(new_beats):
                        if beat_idx < len(self.engine.patterns[inst][measure_idx]):
                            old_subdiv = self.engine.patterns[inst][measure_idx][beat_idx]
                            new_subdiv_list = old_subdiv[:new_subdiv] + [0] * (new_subdiv - len(old_subdiv))
                        else:
                            new_subdiv_list = [0] * new_subdiv

                        new_pattern.append(new_subdiv_list)

                    self.engine.patterns[inst][measure_idx] = new_pattern

                self.engine.measures[measure_idx]['length'] = new_beats

            self.engine.total_duration = self.engine.calculate_total_duration()
            self.engine.generate_events()
            self.scroll_x = 0

        except ValueError:
            pass

    def draw_inputs(self):
        for input_type, rect in [('beats', self.input_beats_rect),
                                 ('subdivisions', self.input_subdiv_rect)]:

            # Dibujar inputs
            pygame.draw.rect(self.screen, (30, 30, 30), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            #pygame.draw.rect(self.screen, (200, 200, 200), self.input_beats_rect, 2)
            #pygame.draw.rect(self.screen, (200, 200, 200), self.input_subdiv_rect, 2)

            #beats_text = self.font.render(self.input_values['beats'], True, (255, 255, 255))
            #subdiv_text = self.font.render(self.input_values['subdivisions'], True, (255, 255, 255))

            # Texto
            text_surf = self.font.render(self.input_values[input_type], True, (255, 255, 255))
            if input_type == 'beats':
                self.screen.blit(text_surf, (rect.x + 25, rect.y + 3))
            else:
                self.screen.blit(text_surf, (rect.x + 18, rect.y + 3)) # Corregir movimiento cuando borro la unidad en subdiv

            # Cursor parpadeante
            if self.active_input == input_type:
                if pygame.time.get_ticks() % 1000 < 500:
                    cursor_x = rect.x + 5 + text_surf.get_width()
                    pygame.draw.line(self.screen, (255, 255, 255),
                                     (rect.x + 36, rect.y + 5),
                                     (rect.x + 36, rect.y + 25), 2)

        # Etiquetas
        label_beats = self.font.render("Beats: ", True, (255, 255, 255))
        label_subdiv = self.font.render("Subdiv: ", True, (255, 255, 255))
        self.screen.blit(label_beats, (100, 500))
        self.screen.blit(label_subdiv, (250, 500))

    def draw_buttons(self): # Nueva función para dibujar botones
        # Botón Añadir Compás / Play (sin cambios)
        pygame.draw.rect(self.screen, (0, 200, 0), self.add_measure_btn)
        pygame.draw.rect(self.screen, (0, 0, 200), self.play_btn)
        # Botón Guardar (Rojo)
        pygame.draw.rect(self.screen, (200, 0, 0), self.save_button_rect) # Rojo
        # Botón Cargar (Verde Oscuro)
        pygame.draw.rect(self.screen, (0, 100, 0), self.load_button_rect) # Verde Oscuro
        # Botón Exportar (Morado)
        pygame.draw.rect(self.screen, (128, 0, 128), self.export_button_rect) # Morado


    def draw_save_popup(self): # Nueva función para dibujar ventana emergente Guardar
        if not self.is_save_popup_visible: # No dibujar si no está visible
            return

        # Fondo ventana emergente
        pygame.draw.rect(self.screen, (80, 80, 80), self.save_popup_rect)
        # Borde ventana emergente
        pygame.draw.rect(self.screen, (200, 200, 200), self.save_popup_rect, 2)

        # Rectángulo input nombre proyecto
        pygame.draw.rect(self.screen, (30, 30, 30), self.save_input_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.save_input_rect, 2)

        # Texto input nombre proyecto
        text_surface = self.font.render(self.project_input_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (self.save_input_rect.x + 5, self.save_input_rect.y + 5))

        # Cursor en input nombre proyecto
        if pygame.time.get_ticks() % 1000 < 500: # Cursor parpadeante
            cursor_x = self.save_input_rect.x + 5 + text_surface.get_width()
            pygame.draw.line(self.screen, (255, 255, 255), (cursor_x, self.save_input_rect.y + 5), (cursor_x, self.save_input_rect.y + 25), 2)

        # Rectángulo lista proyectos guardados
        pygame.draw.rect(self.screen, (50, 50, 50), self.save_list_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.save_list_rect, 2)

        # Lista de proyectos guardados (con scroll)
        list_y_offset = self.save_list_rect.y + 10 - self.save_list_scroll_y # Offset para scroll
        for i, project_name in enumerate(self.saved_projects):
            text_y_pos = list_y_offset + i * self.save_list_item_height
            if self.save_list_rect.top <= text_y_pos + self.save_list_item_height <= self.save_list_rect.bottom: # Solo dibujar items visibles
                text_surface = self.font.render(project_name, True, (255, 255, 255))
                self.screen.blit(text_surface, (self.save_list_rect.x + 10, text_y_pos))

        # Botón Aceptar Guardar
        pygame.draw.rect(self.screen, (0, 200, 0), self.save_accept_btn_rect)
        text_surface = self.font.render("Guardar", True, (255, 255, 255))
        self.screen.blit(text_surface, (self.save_accept_btn_rect.x + 15, self.save_accept_btn_rect.y + 5))
        # Botón Cancelar Guardar
        pygame.draw.rect(self.screen, (200, 0, 0), self.save_cancel_btn_rect)
        text_surface = self.font.render("Cancelar", True, (255, 255, 255))
        self.screen.blit(text_surface, (self.save_cancel_btn_rect.x + 15, self.save_cancel_btn_rect.y + 5))

    def draw_load_popup(self): # Nueva función para dibujar ventana emergente Cargar
        if not self.is_load_popup_visible: # No dibujar si no está visible
            return

        # Fondo ventana emergente
        pygame.draw.rect(self.screen, (80, 80, 80), self.load_popup_rect)
        # Borde ventana emergente
        pygame.draw.rect(self.screen, (200, 200, 200), self.load_popup_rect, 2)

        # Rectángulo lista proyectos guardados
        pygame.draw.rect(self.screen, (50, 50, 50), self.load_list_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.load_list_rect, 2)

        # Lista de proyectos guardados (con selección y scroll)
        list_y_offset = self.load_list_rect.y + 10 - self.load_list_scroll_y # Offset para scroll
        for i, project_name in enumerate(self.saved_projects):
            text_y_pos = list_y_offset + i * self.save_list_item_height
            item_rect = pygame.Rect(self.load_list_rect.x + 10, text_y_pos, self.load_list_rect.width - 20, self.load_list_item_height)
            if self.load_list_rect.top <= text_y_pos + self.load_list_item_height <= self.load_list_rect.bottom: # Solo dibujar items visibles
                text_color = (255, 255, 255) # Color por defecto
                if i == self.selected_project_index: # Si está seleccionado, cambiar color
                    pygame.draw.rect(self.screen, (0, 150, 150), item_rect) # Rect de selección
                    text_color = (0, 0, 0) # Texto negro para selección
                text_surface = self.font.render(project_name, True, text_color)
                self.screen.blit(text_surface, (self.load_list_rect.x + 10, text_y_pos))

        # Botón Aceptar Cargar (Verde - deshabilitado si no hay proyectos)
        accept_button_color = (0, 200, 0) if self.saved_projects else (50, 50, 50) # Verde o gris si no hay proyectos
        pygame.draw.rect(self.screen, accept_button_color, self.load_accept_btn_rect)
        text_surface = self.font.render("Cargar", True, (255, 255, 255) if self.saved_projects else (150, 150, 150)) # Texto blanco o gris si deshabilitado
        self.screen.blit(text_surface, (self.load_accept_btn_rect.x + 15, self.load_accept_btn_rect.y + 5))
        # Botón Cancelar Cargar
        pygame.draw.rect(self.screen, (200, 0, 0), self.load_cancel_btn_rect)
        text_surface = self.font.render("Cancelar", True, (255, 255, 255))
        self.screen.blit(text_surface, (self.load_cancel_btn_rect.x + 15, self.load_cancel_btn_rect.y + 5))

    def draw_popups(self): # Nueva función para agrupar el dibujo de popups
        self.draw_save_popup()
        self.draw_load_popup()

    def draw(self):
        self.screen.fill((30, 30, 30))

        self.draw_buttons() # Dibujar botones Add Measure/Play/Save/Load
        self.draw_grid() # Dibujar el grid (oscurecido si popup activo)
        self.draw_inputs() # Dibujar inputs Beats/Subdiv

        self.draw_popups() # Dibujar ventanas emergentes Guardar/Cargar (si están visibles)

        # Instrumentos (sin cambios)
        for rect, name in self.instrument_rects:
            pygame.draw.rect(self.screen, (100, 100, 100), rect)
            text = self.font.render(name, True, (255,255,255))
            self.screen.blit(text, (rect.x + 10, rect.y + 6))

        pygame.display.flip()


    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.engine.stop()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if self.scrollbar_handle_rect.collidepoint(pos) and self.max_scroll_x > 0:
                        self.is_scrolling = True
                        self.mouse_offset_x = pos[0] - self.scrollbar_handle_rect.x
                    self.handle_click(pygame.mouse.get_pos())
                elif event.type in (pygame.KEYDOWN, pygame.TEXTINPUT, pygame.MOUSEWHEEL): # Añadido MOUSEWHEEL
                    self.handle_event(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: # Boton izquierdo del mouse
                        self.is_scrolling = False # Detiene el scroll
                elif event.type == pygame.MOUSEMOTION:
                    if self.is_scrolling: # Si se esta arrastrando el scroll
                        delta_x = event.pos[0] - self.scroll_mouse_offset - self.left_panel_width
                        self.scroll_x = (delta_x / (self.screen.get_width() - self.left_panel_width)) * self.max_scroll_x
                        self.scroll_x = max(0,min(self.scroll_x, self.max_scroll_x))

            # Actualizar cursor parpadeante
            self.cursor_timer = (self.cursor_timer + 1) % 30

            self.draw()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    engine = AudioEngine()
    engine.add_measure()  # Medida inicial

    gui = DrumGUI(engine)
    gui.run()