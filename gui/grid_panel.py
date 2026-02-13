import pygame
import sys
import numpy as np

class GridPanel:
    def __init__(self, x, y, screen, engine, manager, gui):
        # ... (código __init__) ...
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.manager = manager
        self.gui = gui

        self.playback_line_color = (0, 200, 200)  # Turquesa
        self.playback_line_thickness = 2
        self.last_playback_position = 0

        self.width = screen.get_width() - x
        self.height = screen.get_height() * 0.68
        self.measure_width = 600 # Ancho fijo para cada compás
        self.header_height = 30 # Altura fija de la cabecera del compás

        self.scrollbar_height = 20

        self.visible_area_rect = pygame.Rect(self.x, self.y, self.width, self.height - self.scrollbar_height)
        self.current_content_draw_height = self.visible_area_rect.height - self.header_height

        self.content_surface = pygame.Surface((self.visible_area_rect.width, self.visible_area_rect.height), pygame.SRCALPHA)
        self.content_surface.fill((35, 35, 35, 255))

        self.scroll_x = 0
        self.max_scroll_x = 0

        self.scrollbar_track_rect = pygame.Rect(self.x, self.y + self.height - self.scrollbar_height, self.width, self.scrollbar_height)
        self.scrollbar_thumb_rect = pygame.Rect(self.scrollbar_track_rect.x, self.scrollbar_track_rect.y, self.scrollbar_height, self.scrollbar_height)

        self.is_dragging_thumb = False
        self.thumb_drag_start_x = 0
        self.scroll_start_on_drag = 0

        self.selected_measures_indices = []

        self._update_content_surface()


    def draw_playback_line(self, surface):
        #if not self.engine.playing:
        #    return

        total_duration = self.engine.total_duration
        if total_duration <= 0:
            return

        current_time = self.engine.get_current_playback_time()
        progress = current_time / total_duration
        
        # Calcular posición X en el contenido completo
        total_width = len(self.engine.measures) * self.measure_width
        line_x = progress * total_width
        
        # Convertir a posición en el área visible
        visible_line_x = line_x - self.scroll_x
        
        # Auto-scroll si la línea está cerca del borde
        scroll_margin = self.visible_area_rect.width * 0.5
        if visible_line_x > self.visible_area_rect.width - scroll_margin:
            self.scroll_x = min(self.max_scroll_x, line_x - self.visible_area_rect.width + scroll_margin)
            self._update_thumb_position()
        elif visible_line_x < scroll_margin:
            self.scroll_x = max(0, line_x - scroll_margin)
            self._update_thumb_position()

        # Dibujar línea en la posición calculada
        if 0 <= line_x <= total_width:
            pygame.draw.line(
                surface,
                self.playback_line_color,
                (line_x - self.scroll_x + self.visible_area_rect.x, self.visible_area_rect.y + 30),
                (line_x - self.scroll_x + self.visible_area_rect.x, self.visible_area_rect.bottom),
                self.playback_line_thickness
            )


    def _draw_measure_content(self, surface, measure_idx, x_base):
        #print(f"\n--- DEBUG: _draw_measure_content llamado para Compás {measure_idx + 1} en X base: {x_base} ---")
        y_start = self.header_height

        if measure_idx >= len(self.engine.measures):
            #print(f"DEBUG: _draw_measure_content: measure_idx {measure_idx} fuera de rango.")
            return

        measure = self.engine.measures[measure_idx]

        beats_per_measure = measure.get('length', 4)
        #print(f"DEBUG: _draw_measure_content: Beats per measure: {beats_per_measure} para Compás {measure_idx + 1}")

        subdivisions_per_beat = 16
        # NOTA: Esta lógica para obtener subdivisions_per_beat DEBE COINCIDIR con handle_event
        if self.engine.patterns and list(self.engine.patterns.values()):
            first_instrument_patterns = list(self.engine.patterns.values())[0]
            if measure_idx < len(first_instrument_patterns) and beats_per_measure > 0:
                 if measure_idx < len(first_instrument_patterns) and 0 < len(first_instrument_patterns[measure_idx]):
                      try:
                          subdivisions_per_beat = len(first_instrument_patterns[measure_idx][0])
                      except IndexError:
                           #print(f"Advertencia: _draw_measure_content - No se pudo obtener subdivisions_per_beat para Compás {measure_idx + 1} desde patrón. Usando defecto 16.")
                           subdivisions_per_beat = 16

                 subdivisions_per_beat = max(1, subdivisions_per_beat)

        #print(f"DEBUG: _draw_measure_content: Subdivisions per beat: {subdivisions_per_beat} para Compás {measure_idx + 1}")

        beat_width = self.measure_width / beats_per_measure if beats_per_measure > 0 else self.measure_width
        subdiv_width = beat_width / subdivisions_per_beat if subdivisions_per_beat > 0 else beat_width
        #print(f"DEBUG: _draw_measure_content: Visual beat_width: {beat_width:.2f}, subdiv_width: {subdiv_width:.2f} para Compás {measure_idx + 1}")


        num_instruments = len(self.engine.patterns.keys())
        drawable_grid_area_height = max(0, self.current_content_draw_height - self.header_height)
        inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40

        #print(f"DEBUG: _draw_measure_content: Dibujando {beats_per_measure} beats y {subdivisions_per_beat} subdivs...")
        for beat_idx in range(beats_per_measure):
            beat_x_base = x_base + (beat_idx * beat_width)
            for subdiv_idx in range(subdivisions_per_beat):
                x_pos = beat_x_base + (subdiv_idx * subdiv_width)

                for inst_idx, inst in enumerate(self.engine.patterns.keys()):
                    y_pos = y_start + inst_idx * inst_row_height
                    rect = pygame.Rect(x_pos, y_pos, subdiv_width - 1, inst_row_height - 1)

                    state = 0 # Estado por defecto es 0 (apagado)
                    # --- DEBUG: Intentar leer el estado de la celda ---
                    try:
                        if inst_idx < len(self.engine.patterns.keys()) and \
                           measure_idx < len(self.engine.patterns[inst]) and \
                           beat_idx < len(self.engine.patterns[inst][measure_idx]) and \
                           subdiv_idx < len(self.engine.patterns[inst][measure_idx][beat_idx]):

                             state = self.engine.patterns[inst][measure_idx][beat_idx][subdiv_idx]
                             # --- DEBUG: Imprimir el estado leído para esta celda ---
                             #print(f"DEBUG: _draw_measure_content - Comps {measure_idx + 1}, Inst '{inst}', Beat {beat_idx + 1}, Subdiv {subdiv_idx + 1}: Estado ledo = {state}")

                        else:
                             # Esto puede ocurrir si el pattern en el engine no tiene la forma esperada
                             #print(f"ADVERTENCIA (Indices Fuera): _draw_measure_content - ndices {measure_idx}, {inst_idx}, {beat_idx}, {subdiv_idx} fuera de rango para patrn de {inst}.")
                             state = 0 # Asegurarse de que el estado es 0 si hay un problema de ndice

                    except IndexError:
                         # Esto no debería ocurrir si la lógica de actualización de patrones es correcta
                         #print(f"ADVERTENCIA (IndexError): _draw_measure_content - Error de ndice para {inst} en Comps {measure_idx}, Beat {beat_idx}, Subdiv {subdiv_idx}")
                         state = 0 # Asegurarse de que el estado es 0 si hay una excepcin


                    color = (200, 0, 0) if state == 1 else (80, 80, 80)
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (100,100,100), rect, 1)

        #print(f"--- DEBUG: _draw_measure_content terminado para Compás {measure_idx + 1} ---")


    def _update_content_surface(self):
        # ... (código _update_content_surface, mantener debugs) ...
        #print("\n--- DEBUG: _update_content_surface llamado en GridPanel ---")
        self.total_content_width = len(self.engine.measures) * self.measure_width
        #print(f"DEBUG: Total measures: {len(self.engine.measures)}, total_content_width: {self.total_content_width}")

        new_surface_width = max(self.visible_area_rect.width, self.total_content_width)
        new_surface_height = self.visible_area_rect.height
        #print(f"DEBUG: visible_area_rect size: {self.visible_area_rect.size}, new_surface_size: {(new_surface_width, new_surface_height)}")


        if self.content_surface is None or self.content_surface.get_size() != (new_surface_width, new_surface_height):
             #print(f'DEBUG: (Re)Creando content_surface a tamaño ({new_surface_width}, {new_surface_height})')
             self.content_surface = pygame.Surface((new_surface_width, new_surface_height), pygame.SRCALPHA)

        self.content_surface.fill((35, 35, 35, 255))

        #print(f"DEBUG: Iniciando bucle de dibujo de compases. Número de compases en engine: {len(self.engine.measures)}")
        for measure_idx in range (len(self.engine.measures)):
            x_pos = measure_idx * self.measure_width
            # El debug dentro de _draw_measure_content ahora nos dirá los detalles por compás

            header_rect_content = pygame.Rect(x_pos, 0, self.measure_width, self.header_height)
            pygame.draw.rect(self.content_surface, (50, 50, 50), header_rect_content)
            pygame.draw.rect(self.content_surface, (255, 255, 0), header_rect_content, 2)
            text = self.gui.font.render(f"Compás {measure_idx + 1}", True, (255, 255, 255))
            text_rect = text.get_rect(center=header_rect_content.center)
            self.content_surface.blit(text, text_rect)

            self._draw_measure_content(self.content_surface, measure_idx, x_pos)

            if measure_idx in self.selected_measures_indices:
                 print(f"DEBUG: Dibujando recuadro de selección para Compás {measure_idx + 1}")
                 selection_rect = header_rect_content.copy()
                 selection_rect.height = self.visible_area_rect.height
                 pygame.draw.rect(self.content_surface, (255, 0, 0), selection_rect, 3)

        #print(f"DEBUG: Estado final de selected_measures_indices en _update_content_surface: {self.selected_measures_indices}")
        #print("DEBUG: Bucle de dibujo de compases terminado en _update_content_surface.")

        # --- DEBUG: Inspeccionar estructura de patrones después de dibujar ---
        #print("\n--- DEBUG: Inspeccionando estructura de patrones después de _update_content_surface ---")
        for measure_idx in range(len(self.engine.measures)):
             #print(f"DEBUG: Estructura de patrón para Compás {measure_idx + 1}:")
             if measure_idx < len(self.engine.measures):
                  measure_length = self.engine.measures[measure_idx].get('length', 4)
                  #print(f"  - Medida length (beats): {measure_length}")
                  for inst_idx, inst in enumerate(self.engine.patterns.keys()):
                       if measure_idx < len(self.engine.patterns[inst]):
                            pattern_for_measure = self.engine.patterns[inst][measure_idx]
                            num_beats_in_pattern = len(pattern_for_measure)
                            subdivs_per_beat_in_pattern = len(pattern_for_measure[0]) if num_beats_in_pattern > 0 and len(pattern_for_measure[0]) > 0 else 0 # Ensuring pattern_for_measure[0] is not empty
                            #print(f"    - Instrumento '{inst}': {num_beats_in_pattern} beats en patrón, {subdivs_per_beat_in_pattern} subdivs por beat en patrón.")
                            # Opcional: imprimir un snippet del patrón si es pequeño
                            # print(f"      Snippet: {pattern_for_measure[0][:5]}...") # Imprimir las primeras 5 subdivs del primer beat
                       else:
                           #print(f"    - Instrumento '{inst}': Patrón para Compás {measure_idx + 1} no encontrado.")
                           pass


        #print("--- DEBUG: Inspección de patrones terminada ---")
        # ... (resto del código) ...

        self.max_scroll_x = max(0, self.total_content_width - self.visible_area_rect.width)
        #print(f"DEBUG: max_scroll_x calculado: {self.max_scroll_x}")

        self.scroll_x = max(0, min(self.scroll_x, self.max_scroll_x))
        #print(f"DEBUG: scroll_x después de clamp: {self.scroll_x}")

        self._update_thumb_position()
        #print(f"DEBUG: scrollbar_thumb_rect después de update en _update_content_surface: {self.scrollbar_thumb_rect}")
        #print("--- DEBUG: _update_content_surface terminado ---")


    def draw(self, surface):
        # ... (código draw, mantener debugs thumb) ...
        # print("\n--- DEBUG: draw llamado en GridPanel ---")
        pygame.draw.rect(surface, (35, 35, 35), self.visible_area_rect)

        blit_area_in_content = pygame.Rect(self.scroll_x, 0, self.visible_area_rect.width, self.visible_area_rect.height)
        surface.blit(self.content_surface, self.visible_area_rect.topleft, area=blit_area_in_content)

        if self.max_scroll_x > 0:
             pygame.draw.rect(surface, (50, 50, 50), self.scrollbar_track_rect)

             # print(f"DEBUG: Intentando dibujar scrollbar_thumb_rect: {self.scrollbar_thumb_rect}")
             if self.scrollbar_thumb_rect.width > 0 and self.scrollbar_thumb_rect.height > 0:
                 pygame.draw.rect(surface, (100, 100, 100), self.scrollbar_thumb_rect)
                 pygame.draw.rect(surface, (150, 150, 150), self.scrollbar_thumb_rect, 1)
             # else:
                  # print("DEBUG: scrollbar_thumb_rect tiene dimensión cero, no se dibuja.")

        self.draw_playback_line(surface)


    # --- Método para manejar eventos (incluyendo scroll y clicks) ---
    def handle_event(self, event):
        # DEBUG: Imprimir si se recibe un evento MOUSEBUTTONDOWN o MOUSEWHEEL en GridPanel
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:             
            if hasattr(self.gui, 'measure_panel'):
                self.gui.measure_panel._update_info_panel()
            print(f"\n--- DEBUG: MOUSEBUTTONDOWN (Left) recibido en GridPanel en pos: {event.pos} ---")
            # Manejar arrastre del thumb de la barra de scroll
            if self.max_scroll_x > 0 and self.scrollbar_thumb_rect.collidepoint(event.pos):
                print(f"DEBUG: Clic en scrollbar_thumb_rect: {self.scrollbar_thumb_rect}")
                self.is_dragging_thumb = True
                self.thumb_drag_start_x = event.pos[0]
                self.scroll_start_on_drag = self.scroll_x
                print(f"DEBUG: Empezando a arrastrar thumb. scroll_x inicial: {self.scroll_x}")
                return # Consumir el evento si es un clic en el thum    
            # --- Lógica de SELECCIÓN de compás (clic en cabecera) ---
            if self.visible_area_rect.collidepoint(event.pos) and \
               event.pos[1] < self.visible_area_rect.y + self.header_height: # Check Y within header height in screen coords
                # print(f"DEBUG: Clic detectado en el área de cabecera en pos: {event.pos}")
                click_pos_in_visible_area = (event.pos[0] - self.visible_area_rect.x,
                                           event.pos[1] - self.visible_area_rect.y)
                click_pos_in_content_surface = (click_pos_in_visible_area[0] + self.scroll_x,
                                              click_pos_in_visible_area[1])
                print(f"DEBUG: Clic detectado en área de cabecera en pos: {event.pos}. Traducido a content_surface: {click_pos_in_content_surface}")
                header_height = self.header_height  
                print(f"DEBUG: Verificando colisión con cabeceras. Nmero de measures: {len(self.engine.measures)}")
                for measure_idx in range(len(self.engine.measures)):
                    header_rect_content = pygame.Rect(measure_idx * self.measure_width, 0, self.measure_width, self.header_height)
                    if header_rect_content.collidepoint(click_pos_in_content_surface):
                        print(f"DEBUG: Colisión detectada con cabecera de Compás {measure_idx + 1}")
                        if measure_idx in self.selected_measures_indices:
                            self.selected_measures_indices.remove(measure_idx)
                            print(f"DEBUG: Deseleccionado Compás {measure_idx + 1}. Selección actual: {self.selected_measures_indices}")
                        else:
                            self.selected_measures_indices.append(measure_idx)
                            print(f"DEBUG: Seleccionado Compás {measure_idx + 1}. Selección actual: {self.selected_measures_indices}")    
                        self._update_content_surface()
                        return # Consumir el evento


             # --- Manejar clicks en el área del grid (debajo de la cabecera) ---
             # Solo procesar si el click fue dentro del área visible del grid Y DEBAJO de la cabecera
            elif self.visible_area_rect.collidepoint(event.pos) and \
                 event.pos[1] >= self.visible_area_rect.y + self.header_height and \
                 event.pos[1] < self.visible_area_rect.bottom:

                print(f"--- DEBUG: Clic detectado en área de grid en pos: {event.pos} ---")
                click_pos_in_visible_area = (event.pos[0] - self.visible_area_rect.x,
                                             event.pos[1] - self.visible_area_rect.y)

                click_pos_in_content_surface = (click_pos_in_visible_area[0] + self.scroll_x,
                                                click_pos_in_visible_area[1])
                print(f"DEBUG: Click traducido a content_surface: {click_pos_in_content_surface}")

                measure_idx = int(click_pos_in_content_surface[0] // self.measure_width)

                if 0 <= measure_idx < len(self.engine.measures):
                    print(f"DEBUG: Clic en Compás {measure_idx + 1}")

                    click_y_in_grid_area = click_pos_in_content_surface[1] - self.header_height
                    num_instruments = len(self.engine.patterns.keys())
                    drawable_grid_area_height = max(0, self.current_content_draw_height - self.header_height)
                    inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40

                    inst_idx = int(click_y_in_grid_area // inst_row_height)

                    measure = self.engine.measures[measure_idx]
                    beats_per_measure = measure.get('length', 4)
                    # --- Lógica de cálculo de Subdivisions por beat para mapeo de clic ---
                    # NOTA: Esta lógica DEBE COINCIDIR con _draw_measure_content
                    subdivisions_per_beat = 16
                    if self.engine.patterns and list(self.engine.patterns.values()):
                        first_instrument_patterns = list(self.engine.patterns.values())[0]
                        if measure_idx < len(first_instrument_patterns) and beats_per_measure > 0:
                            if measure_idx < len(first_instrument_patterns) and 0 < len(first_instrument_patterns[measure_idx]):
                                try:
                                    subdivisions_per_beat = len(first_instrument_patterns[measure_idx][0])
                                except IndexError:
                                    print(f"Advertencia: handle_event - No se pudo obtener subdivisions_per_beat para Compás {measure_idx + 1} desde patrón. Usando defecto 16.")
                                    subdivisions_per_beat = 16

                            subdivisions_per_beat = max(1, subdivisions_per_beat)

                    print(f"DEBUG: Mapeo de clic para Compás {measure_idx + 1}: Beats per measure usado: {beats_per_measure}, Subdivisions per beat usado: {subdivisions_per_beat}")
                    beat_width = self.measure_width / beats_per_measure if beats_per_measure > 0 else self.measure_width
                    subdiv_width = beat_width / subdivisions_per_beat if subdivisions_per_beat > 0 else beat_width
                    print(f"DEBUG: Mapeo de clic para Compás {measure_idx + 1}: Anchos de mapeo beat_width: {beat_width:.2f}, subdiv_width: {subdiv_width:.2f}")


                    click_x_in_measure = click_pos_in_content_surface[0] % self.measure_width

                    beat_idx = int(click_x_in_measure // beat_width)
                    click_x_in_beat = click_x_in_measure % beat_width
                    subdiv_idx = int(click_x_in_beat // subdiv_width)

                    print(f"DEBUG: Clic en Compás {measure_idx + 1} mapeado a: InstIdx: {inst_idx}, BeatIdx: {beat_idx}, SubdivIdx: {subdiv_idx}")

                    # --- Lógica de ToggLEAR el estado de la celda ---
                    instrument_list = list(self.engine.patterns.keys())
                    if 0 <= inst_idx < len(instrument_list):
                        instrument_name = instrument_list[inst_idx]
                        # Verificar que los índices calculados existan en la estructura ACTUAL del patrón.
                        if measure_idx < len(self.engine.patterns[instrument_name]) and \
                            beat_idx < len(self.engine.patterns[instrument_name][measure_idx]) and \
                            subdiv_idx < len(self.engine.patterns[instrument_name][measure_idx][beat_idx]):

                            current_state = self.engine.patterns[instrument_name][measure_idx][beat_idx][subdiv_idx]
                            new_state = 1 if current_state == 0 else 0
                            self.engine.patterns[instrument_name][measure_idx][beat_idx][subdiv_idx] = new_state # <--- Toggles state

                            self.engine.generate_events()
                            self._update_content_surface()
                            print(f"DEBUG: Celda toggleda en: Comps {measure_idx + 1}, Instrumento {instrument_name}, Beat {beat_idx + 1}, Subdiv {subdiv_idx + 1}. Nuevo estado: {new_state}")
                            return # Consumir el evento si es un clic en una celda vlida
                        else:
                            print(f"ADVERTENCIA (handle_event): ndices calculados ({measure_idx}, {beat_idx}, {subdiv_idx}) fuera de rango para patrn de {instrument_name}. Patrn actual size: beats={len(self.engine.patterns[instrument_name][measure_idx]) if measure_idx < len(self.engine.patterns[instrument_name]) else 'N/A'}, subdivs={len(self.engine.patterns[instrument_name][measure_idx][0]) if measure_idx < len(self.engine.patterns[instrument_name]) and len(self.engine.patterns[instrument_name][measure_idx]) > 0 else 'N/A'}")


                    else:
                        print(f"ADVERTENCIA (handle_event): ndice de instrumento calculado ({inst_idx}) fuera de rango. Nmero de instrumentos: {len(instrument_list)}")


        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
             if self.is_dragging_thumb:
                  print("DEBUG: MOUSEBUTTONUP (Left) Terminando de arrastrar thumb.")
                  self.is_dragging_thumb = False


        elif event.type == pygame.MOUSEMOTION and self.is_dragging_thumb:
             # print(f"DEBUG: MOUSEMOTION recibido en GridPanel en pos: {event.pos}") # Este debug satura

             drag_delta_x = event.pos[0] - self.thumb_drag_start_x
             scrollbar_track_width = self.scrollbar_track_rect.width
             thumb_width = self.scrollbar_thumb_rect.width
             if (scrollbar_track_width - thumb_width) > 0:
                  scroll_delta_x = drag_delta_x * (self.max_scroll_x / (scrollbar_track_width - thumb_width))
             else:
                  scroll_delta_x = 0

             new_scroll_x = self.scroll_start_on_drag + scroll_delta_x
             self.scroll_x = max(0, min(new_scroll_x, self.max_scroll_x))
             self._update_thumb_position()


        # VER MOUSEWHEEL SI NO LO NECESITO CHAU...
        #elif event.type == pygame.MOUSEWHEEL:
        #     print(f"\n--- DEBUG: MOUSEWHEEL recibido en GridPanel con event.x={event.x}, event.y={event.y} ---")
        #     if self.visible_area_rect.collidepoint(event.pos) and self.max_scroll_x > 0:
        #          scroll_amount = event.x * -20
        #          print(f"DEBUG: Scroll amount de rueda: {scroll_amount}")
        #          new_scroll_x = self.scroll_x + scroll_amount
        #          self.scroll_x = max(0, min(new_scroll_x, self.max_scroll_x))
        #          print(f"DEBUG: Nuevo scroll_x después de rueda: {self.scroll_x}")
        #          self._update_content_surface()


        # Si el ratón está siendo arrastrado en el thumb, no procesar otros eventos (aunque ya retornamos antes si clic fue en thumb)
        # if self.is_dragging_thumb:
        #      return

    def update(self):
        pass


    # Método para actualizar la posición y tamaño del thumb
    def _update_thumb_position(self):
        print("\n--- DEBUG: _update_thumb_position llamado ---")
        # Asegurarse de que el track de la barra de scroll tiene ancho positivo y hay contenido para scrollear
        if self.scrollbar_track_rect.width > 0 and self.max_scroll_x > 0:
             print("DEBUG: Scrollbar necesario. Calculando thumb position.")
             scrollbar_track_width = self.scrollbar_track_rect.width
             # Calcular el ancho del thumb proporcionalmente
             # Asegurarse de que self.total_content_width no es cero para evitar división por cero.
             if self.total_content_width > 0:
                 visible_ratio = self.visible_area_rect.width / self.total_content_width
                 thumb_width = max(self.scrollbar_height, int(visible_ratio * scrollbar_track_width))
             else:
                 # Si no hay contenido, el thumb tiene el tamaño mínimo y se queda al inicio.
                 thumb_width = self.scrollbar_height
                 visible_ratio = 1.0 # Contenido cabe

             print(f"DEBUG: visible_area_rect.width: {self.visible_area_rect.width}, total_content_width: {self.total_content_width}")
             print(f"DEBUG: scrollbar_track_width: {scrollbar_track_width}, visible_ratio: {visible_ratio}, calculated thumb_width: {thumb_width}")


             # Calcular la posición X del thumb basada en la posición del scroll
             # Asegurarse de que max_scroll_x no es cero para evitar división por cero.
             if self.max_scroll_x > 0:
                 scroll_ratio = self.scroll_x / self.max_scroll_x
                 thumb_x_in_track = scroll_ratio * (scrollbar_track_width - thumb_width)
             else:
                  thumb_x_in_track = 0 # No hay scroll, thumb al inicio

             # Actualizar el Rect del thumb
             self.scrollbar_thumb_rect.width = thumb_width
             self.scrollbar_thumb_rect.height = self.scrollbar_height # Mantener la altura

             # La posición X del thumb es relativa al inicio del track de la scrollbar
             self.scrollbar_thumb_rect.x = self.scrollbar_track_rect.x + thumb_x_in_track
             self.scrollbar_thumb_rect.y = self.scrollbar_track_rect.y # Mantener la Y en el track

             print(f"DEBUG: scroll_x: {self.scroll_x}, max_scroll_x: {self.max_scroll_x}, scroll_ratio: {scroll_ratio}, thumb_x_in_track: {thumb_x_in_track}")
             print(f"DEBUG: Final scrollbar_thumb_rect en _update_thumb_position: {self.scrollbar_thumb_rect}")


        else:
            # Si no hay scrollbar (contenido cabe en el área visible), hacer el thumb invisible
            print("DEBUG: Scrollbar no necesario. Ocultando thumb.")
            self.scrollbar_thumb_rect.width = 0
            self.scrollbar_thumb_rect.height = self.scrollbar_height # Mantener la altura por si acaso
            self.scrollbar_thumb_rect.x = self.scrollbar_track_rect.x # Moverlo al inicio por si acaso
            self.scrollbar_thumb_rect.y = self.scrollbar_track_rect.y
            print(f"DEBUG: Final scrollbar_thumb_rect (oculto): {self.scrollbar_thumb_rect}")


    def update(self):
        # El update ya no dibuja, eso lo hace draw().
        # Si hubiera lógica de actualización de estado no relacionada con eventos o dibujado, iría aquí.
        pass