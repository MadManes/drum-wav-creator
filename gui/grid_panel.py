import pygame

class GridPanel:
    def __init__(self, x, y, screen, engine, manager, gui, layout):        
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.manager = manager
        self.gui = gui
        self.layout = layout

        self.copy_highlight_color = (0, 200, 0)
        
        self.playback_line_color = (0, 200, 200)  # Turquesa
        self.playback_line_thickness = 2
        self.last_playback_position = 0
        self.manual_playback_x = 0  # posición absoluta en el contenido (no visible)
        self.is_dragging_playback = False
        self.playback_head_size = 8
        self.auto_follow_playback = True

        self.width = screen.get_width() - x
        self.height = screen.get_height() * 0.68
        self.measure_width = 600 # Ancho fijo para cada compás
        self.header_height = self.layout.header_height

        self.user_scrolling = False
        self.scrollbar_height = 20

        self.visible_area_rect = pygame.Rect(self.x, self.y, self.width, self.height - self.scrollbar_height)
        self.current_content_draw_height = self.layout.content_height

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
        self.block_selected = None

        self.loop_highlight = None      

        self._update_content_surface()

    
    def sync_engine_position(self):
        total_width = self._calculate_total_visual_width()
        total_duration = self.engine.get_total_duration()

        if total_width <= 0 or total_duration <= 0:
            return

        progress = self.manual_playback_x / total_width
        new_time = progress * total_duration

        self.engine.set_playback_position_seconds(new_time)


    def draw_playback_line(self, surface):

        total_width = self._calculate_total_visual_width()
        if total_width <= 0:
            return

        if self.engine.is_playing() and not self.is_dragging_playback:

            measure_idx, offset = self.engine.get_visual_position_data()

            measure_duration = self.engine.get_duration_of_measures(measure_idx, measure_idx)

            if measure_duration > 0:
                local_progress = offset / measure_duration
            else:
                local_progress = 0

            self.manual_playback_x = (
                measure_idx * self.measure_width
                + local_progress * self.measure_width
            )

        line_x = max(0, min(self.manual_playback_x, total_width))
        self.manual_playback_x = line_x

        # ---------------------------------
        #  DIBUJAR LINEA
        # ---------------------------------
        grid_top = self.visible_area_rect.y + self.header_height
        grid_bottom = (
            self.visible_area_rect.y
            + self.current_content_draw_height
            - self.layout.bottom_space // 2
        )
        
        
        screen_x = self.visible_area_rect.x + (line_x - self.scroll_x)
        
        if self.visible_area_rect.x <= screen_x <= self.visible_area_rect.right:
            pygame.draw.line(
                surface,
                self.playback_line_color,
                (screen_x, grid_top),
                (screen_x, grid_bottom),
                self.playback_line_thickness
            )
        
        # ---------------------------------
        #  AUTO FOLLOW (centrado y solo en reproducción)
        # ---------------------------------
        if self.engine.is_playing() and self.auto_follow_playback and not self.user_scrolling:
            center_offset = self.visible_area_rect.width // 2
            desired_scroll = line_x - center_offset
            self.scroll_x = max(0, min(desired_scroll, self.max_scroll_x))
            self._update_thumb_position()


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
        drawable_grid_area_height = (self.current_content_draw_height 
                                     - self.header_height
                                     - self.layout.bottom_space
                                     )
        inst_row_height = drawable_grid_area_height // num_instruments if num_instruments > 0 else 40
        
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
        return self.engine.get_measure_count() * self.measure_width


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


    def _draw_all_measures(self):        
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


    def _draw_loop_blocks_area(self):
        if not self.engine.loop_blocks:
            return

        block_rect_area = self._get_block_area_rect()
        block_area_top = block_rect_area.y
        block_height = block_rect_area.height

        for loop in self.engine.loop_blocks:
            start = loop.start
            end = loop.end

            x_start = start * self.measure_width
            x_end = (end + 1) * self.measure_width
            width = x_end - x_start

            rect = pygame.Rect(
                x_start,
                block_area_top,
                width,
                block_height
            )

            pygame.draw.rect(self.content_surface, (60, 100, 140), rect)
            pygame.draw.rect(self.content_surface, (0, 200, 255), rect, 2)

            text = self.gui.font.render("BLOCK", True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            self.content_surface.blit(text, text_rect)

    
    def _get_playback_click_area_screen(self):
        top = self.visible_area_rect.y + self.header_height
        bottom = (
            self.visible_area_rect.y
            + self.current_content_draw_height
            - self.layout.bottom_space // 2
        )
        return pygame.Rect(
            self.visible_area_rect.x,
            top,
            self.visible_area_rect.width,
            bottom - top
        )


    def _get_block_area_screen(self):
        top = (
            self.visible_area_rect.y
            + self.current_content_draw_height
            - self.layout.bottom_space // 2
        )
        bottom = self.scrollbar_track_rect.top

        return pygame.Rect(
            self.visible_area_rect.x,
            top,
            self.visible_area_rect.width,
            bottom - top
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
            self.block_selected = None
            pygame.draw.rect(self.content_surface, (255, 0, 0), selection_rect, 3)
        
        for loop in self.engine.loop_blocks:
            start = loop.start
            end = loop.end

            if measure_idx == start:
                pygame.draw.line(
                    self.content_surface,
                    (0, 255, 255),
                    (x_pos, 0),
                    (x_pos, self.visible_area_rect.height),
                    4
                )

            if measure_idx == end:
                pygame.draw.line(
                    self.content_surface,
                    (0, 255, 255),
                    (x_pos + self.measure_width, 0),
                    (x_pos + self.measure_width, self.visible_area_rect.height),
                    4
                )

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
        self._draw_loop_blocks_area()

    
    def _sync_engine_to_playback_position(self):
        total_width = self._calculate_total_visual_width()
        total_duration = self.engine.get_total_duration()

        if total_width <= 0 or total_duration <= 0:
            return

        progress = self.manual_playback_x / total_width
        new_time = progress * total_duration

        with self.engine.lock:
            self.engine.absolute_position = int(new_time * self.engine.SAMPLE_RATE)

    def _get_grid_top_y(self):
        return self.visible_area_rect.y + self.header_height
    
    def _get_grid_bottom_y(self):
        return (
            self.visible_area_rect.y
            + self.current_content_draw_height
            - self.layout.bottom_space
        )
    
    def _get_block_area_rect(self):
        block_area_top = (
            self.current_content_draw_height
            - self.layout.bottom_space
        )

        half_height = self.layout.bottom_space // 2

        return pygame.Rect(
            0,
            block_area_top + half_height,
            self.total_content_width,
            half_height - 5
        )

    
    def clear_selection(self):
        self.selected_measures_indices = []
        self._update_content_surface()
        self.block_selected = None


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


    # --- Método para manejar eventos (incluyendo scroll y clicks) ---
    def handle_event(self, event):        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # ------------------------------
            # CLICK SOBRE PLAYBACK LINE
            # ------------------------------

            mouse_x, mouse_y = event.pos

            line_screen_x = self.visible_area_rect.x + (self.manual_playback_x - self.scroll_x)

            line_rect = pygame.Rect(
                line_screen_x - 6,
                self.visible_area_rect.y + self.header_height,
                12,
                self.scrollbar_track_rect.top - (self.visible_area_rect.y + self.header_height)
            )

            if line_rect.collidepoint(mouse_x, mouse_y):
                self.is_dragging_playback = True
                self.auto_follow_playback = False
                return   

            # ------------------------------
            # CLICK EN ZONA VACÍA INFERIOR (solo ahí mover playback)
            # ------------------------------

            grid_bottom_y = (
                self.visible_area_rect.y
                + self.current_content_draw_height
                - self.layout.bottom_space
            )            
            
            
            # Manejar arrastre del thumb de la barra de scroll
            if self.max_scroll_x > 0 and self.scrollbar_thumb_rect.collidepoint(event.pos):            
                self.is_dragging_thumb = True
                self.user_scrolling = True
                self.auto_follow_playback = False
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
             
            elif self.visible_area_rect.collidepoint(event.pos):
                # ---------------------------------
                # CLICK EN BLOQUE
                # ---------------------------------
                block_area = self._get_block_area_screen()

                if block_area.collidepoint(event.pos):
                    click_x = event.pos[0] - self.visible_area_rect.x + self.scroll_x
                    measure_clicked = int(click_x // self.measure_width)

                    for loop in self.engine.loop_blocks:
                        if loop.start <= measure_clicked <= loop.end:
                            self.selected_measures_indices = list(
                                range(loop.start, loop.end + 1)
                            )
                            self.block_selected = loop
                            self._update_content_surface()
                            return                

                # -----------------------------------------
                # CALCULAR AREA REAL DEL GRID (igual que draw)
                # -----------------------------------------

                grid_top = self.visible_area_rect.y + self.header_height
                grid_bottom = (
                    self.visible_area_rect.y
                    + self.current_content_draw_height
                    - self.layout.bottom_space
                )

                # Si el click no está dentro del área real del grid → salir
                if not (grid_top <= event.pos[1] < grid_bottom):
                    return

                click_pos_in_visible_area = (
                    event.pos[0] - self.visible_area_rect.x,
                    event.pos[1] - self.visible_area_rect.y
                )

                click_pos_in_content_surface = (
                    click_pos_in_visible_area[0] + self.scroll_x,
                    click_pos_in_visible_area[1]
                )

                measure_idx = int(click_pos_in_content_surface[0] // self.measure_width)

                if 0 <= measure_idx < self.engine.get_measure_count():
                
                    # -----------------------------------------
                    # CALCULAR FILA EXACTAMENTE COMO EN DRAW
                    # -----------------------------------------

                    instruments = self.engine.get_instruments()
                    num_instruments = len(instruments)

                    drawable_grid_area_height = (
                        self.current_content_draw_height
                        - self.header_height
                        - self.layout.bottom_space
                    )

                    inst_row_height = (
                        drawable_grid_area_height // num_instruments
                        if num_instruments > 0 else 40
                    )

                    relative_y = event.pos[1] - grid_top
                    inst_idx = int(relative_y // inst_row_height)

                    beats = self.engine.get_measure_info(measure_idx)
                    beats_per_measure = beats.get('length', 4)

                    subdivisions_per_beat = self.engine.get_subdivisions(measure_idx)

                    beat_width = (
                        self.measure_width / beats_per_measure
                        if beats_per_measure > 0 else self.measure_width
                    )

                    subdiv_width = (
                        beat_width / subdivisions_per_beat
                        if subdivisions_per_beat > 0 else beat_width
                    )

                    click_x_in_measure = click_pos_in_content_surface[0] % self.measure_width

                    beat_idx = int(click_x_in_measure // beat_width)
                    click_x_in_beat = click_x_in_measure % beat_width
                    subdiv_idx = int(click_x_in_beat // subdiv_width)

                    if 0 <= inst_idx < len(instruments):
                        instrument_name = instruments[inst_idx]
                        self.engine.toggle_cell(instrument_name, measure_idx, beat_idx, subdiv_idx)
                        self._update_content_surface()
                        self.gui.mark_project_dirty()
                        return

            block_click_area = self._get_block_area_screen()

            if block_click_area.collidepoint(event.pos) and not self.engine.is_playing():
                click_visible_x = event.pos[0] - self.visible_area_rect.x
                self.manual_playback_x = click_visible_x + self.scroll_x
                self.auto_follow_playback = False
                return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging_playback:
                self.is_dragging_playback = False
                return
            if self.is_dragging_thumb:                  
                self.is_dragging_thumb = False
                self.user_scrolling = False
        elif event.type == pygame.MOUSEMOTION:
            # ------------------------------
            # DRAG PLAYBACK LINE
            # ------------------------------
            if self.is_dragging_playback:
                mouse_x = event.pos[0]
                visible_x = mouse_x - self.visible_area_rect.x
                self.manual_playback_x = visible_x + self.scroll_x
                return
            # ------------------------------
            # DRAG SCROLLBAR THUMB
            # ------------------------------
            if self.is_dragging_thumb:
                drag_delta_x = event.pos[0] - self.thumb_drag_start_x
                scrollbar_track_width = self.scrollbar_track_rect.width
                thumb_width = self.scrollbar_thumb_rect.width
                if (scrollbar_track_width - thumb_width) > 0:
                    scroll_delta_x = drag_delta_x * (
                        self.max_scroll_x / (scrollbar_track_width - thumb_width)
                    )
                else:
                    scroll_delta_x = 0
                new_scroll_x = self.scroll_start_on_drag + scroll_delta_x
                self.scroll_x = max(0, min(new_scroll_x, self.max_scroll_x))
                self._update_thumb_position()
                return
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:                            
                # Cancelar copy/paste
                if hasattr(self.gui.measure_panel, "waiting_for_paste"):
                    self.gui.measure_panel.waiting_for_paste = False
                    self.gui.measure_panel.copied_measure_index = None
                # Limpiar selección
                self.selected_measures_indices = []
                self._update_content_surface()
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

    