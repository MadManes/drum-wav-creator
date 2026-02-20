import pygame

class GridPanel:
    def __init__(self, x, y, screen, engine, manager, gui):
        # ... (código __init__) ...
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.manager = manager
        self.gui = gui

        self.copy_highlight_color = (0, 200, 0)

        self.playback_line_color = (0, 200, 200)  # Turquesa
        self.playback_line_thickness = 2
        self.last_playback_position = 0

        self.width = screen.get_width() - x
        self.height = screen.get_height() * 0.68
        self.measure_width = 600 # Ancho fijo para cada compás
        self.header_height = 30 # Altura fija de la cabecera del compás

        self.user_scrolling = False
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
        self.editing_repeat = None # Índice del compás en edición
        self.repeat_input_text = "" # texto temporal (default vacío)
        self.repeat_input_rects = {} # rectángulos por compás

        self._update_content_surface()


    def draw_playback_line(self, surface):

        total_duration = self.engine.get_total_duration()
        if total_duration <= 0 or not self.engine.is_playing():
            return

        current_time = self.engine.get_current_playback_time()
        beat_duration = self.engine.calculate_beat_duration()

        accumulated_time = 0
        accumulated_x = 0
        line_x = 0

        # Buscar en qué compás (incluyendo repeticiones) estamos
        for measure in self.engine.measures:

            beats = measure.get("length", 4)
            repeat = measure.get("repeat", 1)

            single_measure_duration = beats * beat_duration
            total_measure_duration = single_measure_duration * repeat

            if current_time < accumulated_time + total_measure_duration:

                time_inside_block = current_time - accumulated_time

                # Tiempo dentro del compás físico
                time_inside_single = time_inside_block % single_measure_duration

                progress_in_measure = time_inside_single / single_measure_duration

                line_x = accumulated_x + (progress_in_measure * self.measure_width)
                break

            accumulated_time += total_measure_duration
            accumulated_x += self.measure_width

        # Convertir a coordenada visible
        visible_line_x = line_x - self.scroll_x

        # 🎥 AUTO-SCROLL (restaurado correctamente)
        if self.engine.is_playing() and not self.user_scrolling:

            scroll_margin = self.visible_area_rect.width * 0.5

            if visible_line_x > self.visible_area_rect.width - scroll_margin:
                self.scroll_x = min(
                    self.max_scroll_x,
                    line_x - self.visible_area_rect.width + scroll_margin
                )
                self._update_thumb_position()

            elif visible_line_x < scroll_margin:
                self.scroll_x = max(
                    0,
                    line_x - scroll_margin
                )
                self._update_thumb_position()

            visible_line_x = line_x - self.scroll_x

        # Dibujar línea
        total_width = self._calculate_total_visual_width()

        if 0 <= line_x <= total_width:
            pygame.draw.line(
                surface,
                self.playback_line_color,
                (visible_line_x + self.visible_area_rect.x,
                 self.visible_area_rect.y + 30),
                (visible_line_x + self.visible_area_rect.x,
                 self.visible_area_rect.bottom),
                self.playback_line_thickness
            )



    def _draw_measure_content(self, surface, measure_idx, x_base):        
        y_start = self.header_height

        if measure_idx >= self.engine.get_measure_count():            
            return

        beats = self.engine.get_measure_info(measure_idx)


        beats_per_measure = beats.get('length', 4)        

        subdivisions_per_beat = self.engine.get_subdivisions(measure_idx)        

        beat_width = self.measure_width / beats_per_measure if beats_per_measure > 0 else self.measure_width
        subdiv_width = beat_width / subdivisions_per_beat if subdivisions_per_beat > 0 else beat_width

        instruments = self.engine.get_instruments()
        num_instruments = len(instruments)
        drawable_grid_area_height = max(0, self.current_content_draw_height - self.header_height)
        inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40
        
        for beat_idx in range(beats_per_measure):
            beat_x_base = x_base + (beat_idx * beat_width)
            for subdiv_idx in range(subdivisions_per_beat):
                x_pos = beat_x_base + (subdiv_idx * subdiv_width)

                for inst_idx, inst in enumerate(instruments):
                    y_pos = y_start + inst_idx * inst_row_height
                    rect = pygame.Rect(x_pos, y_pos, subdiv_width - 1, inst_row_height - 1)

                    state = 0 # Estado por defecto es 0 (apagado)
                    
                    state = self.engine.get_cell_state(inst, measure_idx, beat_idx, subdiv_idx)


                    color = (200, 0, 0) if state == 1 else (80, 80, 80)
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (100,100,100), rect, 1)

    
    def _calculate_total_visual_width(self):
        total = 0
        for measure in self.engine.measures:
            repeat = measure.get("repeat", 1)
            total += self.measure_width * repeat
        return total


    def _recalculate_dimensions(self):
        self.total_content_width = self.engine.get_measure_count() * self.measure_width

    def _ensure_surface_size(self):
        new_surface_width = max(self.visible_area_rect.width, self.total_content_width)
        new_surface_height = self.visible_area_rect.height

        if self.content_surface is None or \
           self.content_surface.get_size() != (new_surface_width, new_surface_height):

            self.content_surface = pygame.Surface(
                (new_surface_width, new_surface_height),
                pygame.SRCALPHA
            )

        self.content_surface.fill((35, 35, 35, 255))

    def _apply_repeat_input(self):
        if self.editing_repeat is None:
            return
        try:
            value = int(self.repeat_input_text)
        except:
            value = 1

        if value >= 2:
            self.engine.set_measure_repeat(self.editing_repeat, value)
        else:
            self.engine.set_measure_repeat(self.editing_repeat, 1)

        self.editing_repeat = None
        self.repeat_input_text = ""

        self._update_content_surface()


    def _draw_all_measures(self):
        self.repeat_input_rects.clear()
        for measure_idx in range(self.engine.get_measure_count()):
            x_pos = measure_idx * self.measure_width

            self._draw_measure_header(measure_idx, x_pos)
            self._draw_measure_content(self.content_surface, measure_idx, x_pos)
            self._draw_measure_selection(measure_idx, x_pos)

    def _draw_measure_header(self, measure_idx, x_pos):
        measure = self.engine.get_measure_info(measure_idx)
        if not measure:
            return

        header_rect = pygame.Rect(
            x_pos,
            0,
            self.measure_width,
            self.header_height
        )

        pygame.draw.rect(self.content_surface, (50, 50, 50), header_rect)
        pygame.draw.rect(self.content_surface, (255, 255, 0), header_rect, 2)

        # Texto del número de compás
        text = self.gui.font.render(
            f"Compás {measure_idx + 1}",
            True,
            (255, 255, 255)
        )

        text_rect = text.get_rect(center=header_rect.center)
        self.content_surface.blit(text, text_rect)

        # -------------------------
        # INPUT DE REPETICIÓN
        # -------------------------

        repeat_value = measure.get("repeat", 1)

        input_width = 35
        input_height = 18

        input_x = x_pos + self.measure_width - input_width - 5
        input_y = 5

        input_rect = pygame.Rect(input_x, input_y, input_width, input_height)

        # Guardamos rect para detectar clicks
        self.repeat_input_rects[measure_idx] = input_rect

        pygame.draw.rect(self.content_surface, (40, 40, 40), input_rect, border_radius=3)
        pygame.draw.rect(self.content_surface, (120, 120, 120), input_rect, 1, border_radius=3)

        if self.editing_repeat != measure_idx:
            text_value = str(repeat_value) if repeat_value > 1 else ""

            text_surface = self.gui.font.render(
                text_value,
                True,
                (220, 220, 220)
            )

            self.content_surface.blit(
                text_surface,
                (input_rect.x + 5, input_rect.y + 1)
            )


    def _draw_measure_selection(self, measure_idx, x_pos):
        selection_rect = pygame.Rect(
            x_pos,
            0,
            self.measure_width,
            self.visible_area_rect.height
        )

        # Si es el compás copiado  verde
        if hasattr(self.gui.measure_panel, "copied_measure_index"):
            if measure_idx == self.gui.measure_panel.copied_measure_index:
                pygame.draw.rect(self.content_surface, self.copy_highlight_color, selection_rect, 3)
                return

        # Si está seleccionado normalmente  rojo
        if measure_idx in self.selected_measures_indices:
            pygame.draw.rect(self.content_surface, (255, 0, 0), selection_rect, 3)


    def _update_scroll_limits(self):
        self.max_scroll_x = max(
            0,
            self.total_content_width - self.visible_area_rect.width
        )

        self.scroll_x = max(0, min(self.scroll_x, self.max_scroll_x))
        self._update_thumb_position()

    
    def _update_content_surface(self):
        self._recalculate_dimensions()
        self._ensure_surface_size()
        self._draw_all_measures()
        self._update_scroll_limits()

    
    def clear_selection(self):
        self.selected_measures_indices = []
        self._update_content_surface()


    def draw(self, surface):        
        pygame.draw.rect(surface, (35, 35, 35), self.visible_area_rect)

        blit_area_in_content = pygame.Rect(self.scroll_x, 0, self.visible_area_rect.width, self.visible_area_rect.height)
        surface.blit(self.content_surface, self.visible_area_rect.topleft, area=blit_area_in_content)

        if self.max_scroll_x > 0:
            pygame.draw.rect(surface, (50, 50, 50), self.scrollbar_track_rect)
             
            if self.scrollbar_thumb_rect.width > 0 and self.scrollbar_thumb_rect.height > 0:
                pygame.draw.rect(surface, (100, 100, 100), self.scrollbar_thumb_rect)
                pygame.draw.rect(surface, (150, 150, 150), self.scrollbar_thumb_rect, 1)            

        self.draw_playback_line(surface)

        # Dibujar input activo encima (dinámico)
        if self.editing_repeat is not None:
        
            measure_idx = self.editing_repeat
            x_pos = measure_idx * self.measure_width - self.scroll_x
        
            input_width = 35
            input_height = 18
        
            input_x = self.visible_area_rect.x + x_pos + self.measure_width - input_width - 5
            input_y = self.visible_area_rect.y + 5
        
            input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        
            pygame.draw.rect(surface, (40, 40, 40), input_rect, border_radius=3)
            pygame.draw.rect(surface, (0, 200, 200), input_rect, 1, border_radius=3)
        
            text_surface = self.gui.font.render(
                self.repeat_input_text,
                True,
                (255, 255, 255)
            )
        
            surface.blit(
                text_surface,
                (input_rect.x + 5, input_rect.y + 1)
            )



    # --- Método para manejar eventos (incluyendo scroll y clicks) ---
    def handle_event(self, event):        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:             
            if hasattr(self.gui, 'measure_panel'):
                self.gui.measure_panel._update_info_panel()

            clicked_input = False

            # Si presiona en input de repetición de compás
            if self.visible_area_rect.collidepoint(event.pos):

                click_pos_in_visible = (
                    event.pos[0] - self.visible_area_rect.x,
                    event.pos[1] - self.visible_area_rect.y
                )

                click_pos_in_content = (
                    click_pos_in_visible[0] + self.scroll_x,
                    click_pos_in_visible[1]
                )

                # Si presiona en input de repetición
                for idx, rect in self.repeat_input_rects.items():
                    if rect.collidepoint(click_pos_in_content):
                    
                        self.editing_repeat = idx

                        measure = self.engine.get_measure_info(idx)
                        current_repeat = measure.get("repeat", 1)

                        self.repeat_input_text = "" if current_repeat == 1 else str(current_repeat)

                        clicked_input = True

                        return
                
                # --- Si estaba editando y clickeó fuera del input ---
                if self.editing_repeat is not None and not clicked_input:
                    self.editing_repeat = None
                    self.repeat_input_text = ""
            
            # Manejar arrastre del thumb de la barra de scroll
            if self.max_scroll_x > 0 and self.scrollbar_thumb_rect.collidepoint(event.pos):            
                self.is_dragging_thumb = True
                self.user_scrolling = True
                self.thumb_drag_start_x = event.pos[0]
                self.scroll_start_on_drag = self.scroll_x                
                return # Consumir el evento si es un clic en el thumb
            

            

            # --- Lógica de SELECCIÓN de compás (clic en cabecera) ---            

            if self.visible_area_rect.collidepoint(event.pos) and \
               event.pos[1] < self.visible_area_rect.y + self.header_height:
                                
                click_pos_in_visible_area = (event.pos[0] - self.visible_area_rect.x,
                                           event.pos[1] - self.visible_area_rect.y)
                click_pos_in_content_surface = (click_pos_in_visible_area[0] + self.scroll_x,
                                              click_pos_in_visible_area[1])                
                header_height = self.header_height  
                
                for measure_idx in range(self.engine.get_measure_count()):
                    header_rect_content = pygame.Rect(measure_idx * self.measure_width, 0, self.measure_width, self.header_height)
                    if header_rect_content.collidepoint(click_pos_in_content_surface):
                        # ---- MODO PEGAR ----
                        if self.gui.measure_panel.waiting_for_paste:
                            source_idx = self.gui.measure_panel.copied_measure_index                            

                            if source_idx is not None:
                                insert_idx = measure_idx
                                self.engine.duplicate_measure(source_idx, insert_idx)

                            self.gui.measure_panel.waiting_for_paste = False
                            self.gui.measure_panel.copied_measure_index = None

                            self.selected_measures_indices = []
                            self._update_content_surface()
                            return
                        if measure_idx in self.selected_measures_indices:
                            self.selected_measures_indices.remove(measure_idx)                            
                        else:
                            self.selected_measures_indices.append(measure_idx)                            
                        self._update_content_surface()

                        return # Consumir el evento
             
            elif self.visible_area_rect.collidepoint(event.pos) and \
                 event.pos[1] >= self.visible_area_rect.y + self.header_height and \
                 event.pos[1] < self.visible_area_rect.bottom:
                
                click_pos_in_visible_area = (event.pos[0] - self.visible_area_rect.x,
                                             event.pos[1] - self.visible_area_rect.y)

                click_pos_in_content_surface = (click_pos_in_visible_area[0] + self.scroll_x,
                                                click_pos_in_visible_area[1])                

                measure_idx = int(click_pos_in_content_surface[0] // self.measure_width)

                if 0 <= measure_idx < self.engine.get_measure_count():
                    click_y_in_grid_area = click_pos_in_content_surface[1] - self.header_height
                    num_instruments = len(self.engine.get_instruments())
                    drawable_grid_area_height = max(0, self.current_content_draw_height - self.header_height)
                    inst_row_height = drawable_grid_area_height / num_instruments if num_instruments > 0 else 40

                    inst_idx = int(click_y_in_grid_area // inst_row_height)

                    beats = self.engine.get_measure_info(measure_idx)

                    beats_per_measure = beats.get('length', 4)
                    
                    # --- Lógica de cálculo de Subdivisions por beat para mapeo de clic ---
                    subdivisions_per_beat = self.engine.get_subdivisions(measure_idx)
                    
                    beat_width = self.measure_width / beats_per_measure if beats_per_measure > 0 else self.measure_width
                    subdiv_width = beat_width / subdivisions_per_beat if subdivisions_per_beat > 0 else beat_width

                    click_x_in_measure = click_pos_in_content_surface[0] % self.measure_width

                    beat_idx = int(click_x_in_measure // beat_width)
                    click_x_in_beat = click_x_in_measure % beat_width
                    subdiv_idx = int(click_x_in_beat // subdiv_width)                    

                    # --- Lógica de ToggLEAR el estado de la celda ---
                    instrument_list = self.engine.get_instruments()
                    if 0 <= inst_idx < len(instrument_list):
                        instrument_name = instrument_list[inst_idx]
                        # Verificar que los índices calculados existan en la estructura ACTUAL del patrón.
                        self.engine.toggle_cell(instrument_name, measure_idx, beat_idx, subdiv_idx)
                        self._update_content_surface()
                        return


        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging_thumb:                  
                self.is_dragging_thumb = False
                self.user_scrolling = False


        elif event.type == pygame.MOUSEMOTION and self.is_dragging_thumb:
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
        
        elif event.type == pygame.KEYDOWN:            
            if event.key == pygame.K_RETURN:
                self._apply_repeat_input()
                return
            
            elif event.key == pygame.K_ESCAPE:
                # Cancelar edición de repeat si estaba
                if self.editing_repeat is not None:
                    self.editing_repeat = None
                    self.repeat_input_text = ""
                # Cancelar copy/paste
                if hasattr(self.gui.measure_panel, "waiting_for_paste"):
                    self.gui.measure_panel.waiting_for_paste = False
                    self.gui.measure_panel.copied_measure_index = None
                # Limpiar selección
                self.selected_measures_indices = []
                self._update_content_surface()
                return
            elif event.key == pygame.K_BACKSPACE:
                self.repeat_input_text = self.repeat_input_text[:-1]
                return
            elif event.unicode.isdigit():
                self.repeat_input_text += event.unicode
                return        
        

    def update(self):
        pass

    # Método para actualizar la posición y tamaño del thumb
    def _update_thumb_position(self):        
        # Asegurarse de que el track de la barra de scroll tiene ancho positivo y hay contenido para scrollear
        if self.scrollbar_track_rect.width > 0 and self.max_scroll_x > 0:             
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

        else:
            # Si no hay scrollbar (contenido cabe en el área visible), hacer el thumb invisible            
            self.scrollbar_thumb_rect.width = 0
            self.scrollbar_thumb_rect.height = self.scrollbar_height # Mantener la altura por si acaso
            self.scrollbar_thumb_rect.x = self.scrollbar_track_rect.x # Moverlo al inicio por si acaso
            self.scrollbar_thumb_rect.y = self.scrollbar_track_rect.y

    