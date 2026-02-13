import pygame
import pygame_gui
import sys

class GridPanel:
    def __init__(self, x, y, screen, engine, manager, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.manager = manager
        self.gui = gui

        # Dimensiones del área visible del GridPanel (esto es el tamaño del contenedor UI)
        self.width = screen.get_width() - x
        self.height = screen.get_height() * 0.68
        self.measure_width = 600
        # La altura de la cabecera es fija
        self.header_height = 30

        # Altura potencial por defecto de la barra de scroll horizontal
        self.default_scrollbar_height = 20

        # Scroll Container
        self.scroll_container_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=self.scroll_container_rect,
            manager=self.manager,
            allow_scroll_x=True,
            allow_scroll_y=False,
            # object_id=pygame_gui.core.ObjectID(class_id='@GridPanelScrollingContainer')
        )

        # Superficie del contenido total (donde dibujaremos todos los compases)
        self.content_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.content_surface.fill((35, 35, 35, 255))

        # UIImage que contendrá nuestra superficie de contenido
        self.content_image_element = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(0, 0, self.width, self.height),
            image_surface=self.content_surface,
            manager=self.manager,
            container=self.scroll_container
        )

        self.total_content_width = self.width

        # Atributo para almacenar los índices de los compases seleccionados
        self.selected_measures_indices = []

        # Altura actual de dibujo para el contenido del grid (se calculará dinámicamente)
        self.current_content_draw_height = self.height - self.header_height - self.default_scrollbar_height


        # Dibujar el grid inicial si hay compases al inicio
        self._update_content_surface()


    def _draw_measure_content(self, surface, measure_idx, x_base):
        y_start = self.header_height
        if measure_idx >= len(self.engine.measures):
            return

        measure = self.engine.measures[measure_idx]
        beats_per_measure = measure.get('length', 4)
        subdivisions_per_beat = 16
        # Asegurarse de obtener el número de subdivisiones del patrón si existe
        if self.engine.patterns and list(self.engine.patterns.values()): # Verificar si hay instrumentos y patrones
            first_instrument_patterns = list(self.engine.patterns.values())[0]
            if measure_idx < len(first_instrument_patterns) and beats_per_measure > 0:
                 if 0 < len(first_instrument_patterns[measure_idx]):
                      subdivisions_per_beat = len(first_instrument_patterns[measure_idx][0])
                 subdivisions_per_beat = max(1, subdivisions_per_beat)

        beat_width = self.measure_width / beats_per_measure
        subdiv_width = beat_width / subdivisions_per_beat
        num_instruments = len(self.engine.patterns.keys())
        drawable_grid_area_height = max(0, self.current_content_draw_height)
        inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40


        for beat_idx in range(beats_per_measure):
            beat_x_base = x_base + (beat_idx * beat_width)
            for subdiv_idx in range(subdivisions_per_beat):
                x_pos = beat_x_base + (subdiv_idx * subdiv_width)

                for inst_idx, inst in enumerate(self.engine.patterns.keys()):
                    y_pos = y_start + inst_idx * inst_row_height
                    rect = pygame.Rect(x_pos, y_pos, subdiv_width - 1, inst_row_height - 1)

                    state = 0
                    try:
                        # Acceder al estado de la celda
                        state = self.engine.patterns[inst][measure_idx][beat_idx][subdiv_idx]
                    except IndexError:
                        pass

                    color = (200, 0, 0) if state == 1 else (80, 80, 80) # Rojo si estado es 1, Gris si 0
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (100,100,100), rect, 1)


    def _update_content_surface(self):
        self.total_content_width = len(self.engine.measures) * self.measure_width
        new_surface_width = max(self.width, self.total_content_width)

        horizontal_scrollbar_height_to_consider = self.default_scrollbar_height
        if self.scroll_container.horiz_scroll_bar and self.scroll_container.horiz_scroll_bar.visible:
             horizontal_scrollbar_height_to_consider = self.scroll_container.horiz_scroll_bar.rect.height

        self.current_content_draw_height = self.height - self.header_height - horizontal_scrollbar_height_to_consider
        new_surface_height = self.height

        if self.content_surface is None or self.content_surface.get_size() != (new_surface_width, new_surface_height):
             self.content_surface = pygame.Surface((new_surface_width, new_surface_height), pygame.SRCALPHA)

        self.content_surface.fill((35, 35, 35, 255))


        for measure_idx in range (len(self.engine.measures)):
            x_pos = measure_idx * self.measure_width

            # Cabecera del compas (fondo y borde base)
            header_rect_content = pygame.Rect(x_pos, 0, self.measure_width, self.header_height)
            pygame.draw.rect(self.content_surface, (50, 50, 50), header_rect_content)
            pygame.draw.rect(self.content_surface, (255, 255, 0), header_rect_content, 2)
            text = self.gui.font.render(f"Compás {measure_idx + 1}", True, (255, 255, 255))
            text_rect = text.get_rect(center=header_rect_content.center)
            self.content_surface.blit(text, text_rect)

            # Dibujar contenido del compas (grid)
            self._draw_measure_content(self.content_surface, measure_idx, x_pos)

            # Dibujar recuadro rojo si el compás está seleccionado (DESPUÉS del contenido)
            if measure_idx in self.selected_measures_indices:
                 selection_rect = header_rect_content.copy()
                 selection_rect.height = self.header_height + max(0, self.current_content_draw_height)
                 pygame.draw.rect(self.content_surface, (255, 0, 0), selection_rect, 3)


        self.content_image_element.set_image(self.content_surface)

        if self.content_image_element.get_relative_rect().size != self.content_surface.get_size():
            self.content_image_element.set_dimensions((new_surface_width, new_surface_height))

        total_content_height_for_scrolling_area = self.header_height + max(0, self.current_content_draw_height)
        self.scroll_container.set_scrollable_area_dimensions((self.total_content_width, total_content_height_for_scrolling_area))


    def update(self):
        pass

    # --- Método para manejar eventos del GridPanel (con detección de colisiones y clicks en celdas) ---    
    def handle_event(self, event):        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Click izquierdo
            scroll_container_abs_rect = self.scroll_container.get_abs_rect()
            if scroll_container_abs_rect.collidepoint(event.pos):
                click_pos_in_container_visible_area = (event.pos[0] - scroll_container_abs_rect.x,
                                                      event.pos[1] - scroll_container_abs_rect.y)

                scroll_x_offset = 0.0
                if self.scroll_container.horiz_scroll_bar:
                    if hasattr(self.scroll_container.horiz_scroll_bar, 'scroll_position'):
                         scroll_x_offset = self.scroll_container.horiz_scroll_bar.scroll_position

                # --- CORRECCIÓN ESPECULATIVA: Aplicar un factor de corrección al scroll offset ---
                # Hipótesis: El desplazamiento visual real es ligeramente diferente al scroll_x_offset reportado.
                # Intentamos un factor ligeramente menor que 1. Si el desfase es hacia la derecha
                # (clickeas a la derecha de lo que se pinta), necesitas reducir el offset efectivo.
                # Si el desfase es hacia la izquierda, necesitas aumentarlo.
                # Puedes ajustar este factor (0.995 es solo un ejemplo inicial)
                # Un factor de 1.0 no aplica corrección.
                correction_factor = 0.995 # Intenta valores como 0.99, 0.998, 1.001, etc.
                adjusted_scroll_x_offset = scroll_x_offset * correction_factor
                # Considera también redondear el resultado final ajustado si es necesario,
                # pero probemos primero con solo el factor.


                header_height = self.header_height
                total_drawable_height = self.header_height + max(0, self.current_content_draw_height)

                # --- Verificar si el click está dentro del área de dibujo total ---
                if click_pos_in_container_visible_area[1] < total_drawable_height:

                    # --- Si el click es en la cabecera (dentro de la altura de la cabecera) ---
                    if click_pos_in_container_visible_area[1] < header_height:
                         # Lógica de selección de compás (con colisión)
                         # Usamos el scroll offset AJUSTADO para la traducción de coordenadas
                         for measure_idx in range(len(self.engine.measures)):
                             header_x_pos_content = measure_idx * self.measure_width
                             header_rect_in_container_view = pygame.Rect(
                                 header_x_pos_content - adjusted_scroll_x_offset, # Usar el offset ajustado
                                 0,
                                 self.measure_width,
                                 header_height
                             )

                             if header_rect_in_container_view.collidepoint(click_pos_in_container_visible_area):
                                  if measure_idx in self.selected_measures_indices:
                                      self.selected_measures_indices.remove(measure_idx)
                                  else:
                                      self.selected_measures_indices.append(measure_idx)
                                  self._update_content_surface()
                                  return

                    # --- Si el click es en el área del grid (debajo de la cabecera) ---
                    else:
                        # Calcular la posición del click relativa a la superficie de contenido total
                        # --- Usar el scroll offset AJUSTADO ---
                        click_pos_in_content_surface_x = click_pos_in_container_visible_area[0] + adjusted_scroll_x_offset
                        click_pos_in_content_surface = (click_pos_in_content_surface_x, click_pos_in_container_visible_area[1])


                        # Mapear la posición en content_surface a índices del grid
                        measure_idx = int(click_pos_in_content_surface[0] // self.measure_width)

                        # ... (resto del código para calcular inst_idx, beat_idx, subdiv_idx y actualizar estado) ...
                        # Asegúrate de que TODAS las partes que usan una coordenada X derivada de
                        # click_pos_in_content_surface_x usen la variable actualizada.


                        # Verificar si el índice de compás es válido
                        if 0 <= measure_idx < len(self.engine.measures):
                            # Calcular la posición Y relativa al inicio del área del grid (debajo de la cabecera)
                            click_y_in_grid_area = click_pos_in_content_surface[1] - self.header_height

                            # Obtener el número de instrumentos y calcular la altura de fila
                            num_instruments = len(self.engine.patterns.keys())
                            drawable_grid_area_height = max(0, self.current_content_draw_height)
                            inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40

                            # Calcular el índice del instrumento
                            inst_idx = int(click_y_in_grid_area // inst_row_height)

                            # Obtener beats y subdivs para ESTE compás y recalcular anchos
                            measure = self.engine.measures[measure_idx]
                            beats_per_measure = measure.get('length', 4)
                            subdivisions_per_beat = 16
                            if self.engine.patterns and list(self.engine.patterns.values()):
                                first_instrument_patterns = list(self.engine.patterns.values())[0]
                                if measure_idx < len(first_instrument_patterns) and beats_per_measure > 0:
                                    if 0 < len(first_instrument_patterns[measure_idx]):
                                        subdivisions_per_beat = len(first_instrument_patterns[measure_idx][0])
                                    subdivisions_per_beat = max(1, subdivisions_per_beat)

                            beat_width = self.measure_width / beats_per_measure if beats_per_measure > 0 else self.measure_width
                            subdiv_width = beat_width / subdivisions_per_beat if subdivisions_per_beat > 0 else beat_width

                            # Calcular la posición X dentro del compás
                            # --- Usar click_pos_in_content_surface_x (con adjusted_scroll_x_offset) ---
                            click_x_in_measure = click_pos_in_content_surface_x % self.measure_width

                            # Calcular el índice del beat
                            beat_idx = int(click_x_in_measure // beat_width)

                            # Calcular la posición X dentro del beat
                            click_x_in_beat = click_x_in_measure % beat_width

                            # Calcular el índice de la subdivisión
                            subdiv_idx = int(click_x_in_beat // subdiv_width)


                            # --- Verificar que los índices calculados sean válidos ---
                            instrument_list = list(self.engine.patterns.keys())
                            if 0 <= inst_idx < len(instrument_list):
                                instrument_name = instrument_list[inst_idx]
                                if measure_idx < len(self.engine.patterns[instrument_name]) and \
                                   beat_idx < len(self.engine.patterns[instrument_name][measure_idx]) and \
                                   subdiv_idx < len(self.engine.patterns[instrument_name][measure_idx][beat_idx]):

                                    # print(f"Click mapeado a: Compás {measure_idx + 1}, Instrumento {instrument_name}, Beat {beat_idx + 1}, Subdiv {subdiv_idx + 1}")

                                    # --- ToggLEAR el estado de la celda ---
                                    current_state = self.engine.patterns[instrument_name][measure_idx][beat_idx][subdiv_idx]
                                    new_state = 1 if current_state == 0 else 0
                                    self.engine.patterns[instrument_name][measure_idx][beat_idx][subdiv_idx] = new_state

                                    # --- Actualizar eventos de audio y redibujar ---
                                    self.engine.generate_events()
                                    self._update_content_surface()


        '''
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Click izquierdo
            scroll_container_abs_rect = self.scroll_container.get_abs_rect()
            if scroll_container_abs_rect.collidepoint(event.pos):
                click_pos_in_container_visible_area = (event.pos[0] - scroll_container_abs_rect.x,
                                                      event.pos[1] - scroll_container_abs_rect.y)

                scroll_x_offset = 0
                if self.scroll_container.horiz_scroll_bar:
                    if hasattr(self.scroll_container.horiz_scroll_bar, 'scroll_position'):
                         scroll_x_offset = self.scroll_container.horiz_scroll_bar.scroll_position

                header_height = self.header_height
                total_drawable_height = self.header_height + max(0, self.current_content_draw_height)

                # --- Verificar si el click está dentro del área de dibujo total ---
                if click_pos_in_container_visible_area[1] < total_drawable_height:

                    # --- Si el click es en la cabecera (dentro de la altura de la cabecera) ---
                    if click_pos_in_container_visible_area[1] < header_height:
                         # Lógica de selección de compás (ya implementada con colisión)
                         for measure_idx in range(len(self.engine.measures)):
                             header_x_pos_content = measure_idx * self.measure_width
                             header_rect_in_container_view = pygame.Rect(
                                 header_x_pos_content - scroll_x_offset,
                                 0,
                                 self.measure_width,
                                 header_height
                             )

                             if header_rect_in_container_view.collidepoint(click_pos_in_container_visible_area):
                                  if measure_idx in self.selected_measures_indices:
                                      self.selected_measures_indices.remove(measure_idx)
                                  else:
                                      self.selected_measures_indices.append(measure_idx)
                                  self._update_content_surface()
                                  return # Salir del método una vez que se manejó el clic en un header

                    # --- Si el click es en el área del grid (debajo de la cabecera) ---
                    else:
                        # Calcular la posición del click relativa a la superficie de contenido total
                        # --- CORRECCIÓN HEURÍSTICA: Añadir un pequeño epsilon a la coordenada X ---
                        # Esto puede ayudar a mitigar problemas de punto flotante o pequeños desfases.
                        # sys.float_info.epsilon es un valor muy pequeño. Podrías necesitar un valor un poco mayor si el desfase es significativo.
                        epsilon = sys.float_info.epsilon * 100 # Multiplicamos epsilon para un efecto un poco mayor
                        click_pos_in_content_surface_x = click_pos_in_container_visible_area[0] + scroll_x_offset + epsilon
                        click_pos_in_content_surface = (click_pos_in_content_surface_x, click_pos_in_container_visible_area[1])


                        # Mapear la posición en content_surface a índices del grid
                        measure_idx = int(click_pos_in_content_surface[0] // self.measure_width)

                        # ... (resto del código para calcular inst_idx, beat_idx, subdiv_idx y actualizar estado) ...
                        # El resto de la lógica para mapear a inst_idx, beat_idx, subdiv_idx y
                        # actualizar el estado de la celda es correcta y no necesita cambios aquí.
                        # Asegúrate de que TODAS las partes que usan click_pos_in_content_surface_x
                        # usen la variable actualizada.

                        # Verificar si el índice de compás es válido
                        if 0 <= measure_idx < len(self.engine.measures):
                            # Calcular la posición Y relativa al inicio del área del grid (debajo de la cabecera)
                            click_y_in_grid_area = click_pos_in_content_surface[1] - self.header_height

                            # Obtener el número de instrumentos y calcular la altura de fila
                            num_instruments = len(self.engine.patterns.keys())
                            drawable_grid_area_height = max(0, self.current_content_draw_height)
                            inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40

                            # Calcular el índice del instrumento
                            inst_idx = int(click_y_in_grid_area // inst_row_height)

                            # Obtener beats y subdivs para ESTE compás y recalcular anchos
                            measure = self.engine.measures[measure_idx]
                            beats_per_measure = measure.get('length', 4)
                            subdivisions_per_beat = 16
                            if self.engine.patterns and list(self.engine.patterns.values()):
                                first_instrument_patterns = list(self.engine.patterns.values())[0]
                                if measure_idx < len(first_instrument_patterns) and beats_per_measure > 0:
                                    if 0 < len(first_instrument_patterns[measure_idx]):
                                        subdivisions_per_beat = len(first_instrument_patterns[measure_idx][0])
                                    subdivisions_per_beat = max(1, subdivisions_per_beat)

                            beat_width = self.measure_width / beats_per_measure if beats_per_measure > 0 else self.measure_width
                            subdiv_width = beat_width / subdivisions_per_beat if subdivisions_per_beat > 0 else beat_width

                            # Calcular la posición X dentro del compás
                            click_x_in_measure = click_pos_in_content_surface_x % self.measure_width # Usamos la X con epsilon

                            # Calcular el índice del beat
                            beat_idx = int(click_x_in_measure // beat_width)

                            # Calcular la posición X dentro del beat
                            click_x_in_beat = click_x_in_measure % beat_width

                            # Calcular el índice de la subdivisión
                            subdiv_idx = int(click_x_in_beat // subdiv_width)


                            # --- Verificar que los índices calculados sean válidos antes de acceder a patterns ---
                            instrument_list = list(self.engine.patterns.keys())
                            if 0 <= inst_idx < len(instrument_list):
                                instrument_name = instrument_list[inst_idx]
                                if measure_idx < len(self.engine.patterns[instrument_name]) and \
                                   beat_idx < len(self.engine.patterns[instrument_name][measure_idx]) and \
                                   subdiv_idx < len(self.engine.patterns[instrument_name][measure_idx][beat_idx]):

                                    # print(f"Click mapeado a: Compás {measure_idx + 1}, Instrumento {instrument_name}, Beat {beat_idx + 1}, Subdiv {subdiv_idx + 1}")

                                    # --- ToggLEAR el estado de la celda ---
                                    current_state = self.engine.patterns[instrument_name][measure_idx][beat_idx][subdiv_idx]
                                    new_state = 1 if current_state == 0 else 0
                                    self.engine.patterns[instrument_name][measure_idx][beat_idx][subdiv_idx] = new_state
                                    # print(f"Estado de celda actualizado a: {new_state}")

                                    # --- Actualizar eventos de audio y redibujar ---
                                    self.engine.generate_events()
                                    self._update_content_surface()

                                # else: print("DEBUG: Índices de patterns finales fuera de rango.")
                            # else: print("DEBUG: Índice de instrumento calculado fuera de rango.")
                        # else: print("DEBUG: Índice de compás calculado fuera de rango.")''' 