import pygame
import pygame_gui

class MeasurePanel:
    def __init__(self, x, y, screen, engine, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.gui = gui
        self.manager = gui.manager

        #self.image = self.gui.load_image("cp_background") 
        self.width = screen.get_width() * .75
        self.height = screen.get_height() * .18
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # SI TUVIERA FONDO!!! (No iria el self rect de arriba porque se manejaria desde aca)
        #if self.image:
        #     self.image = pygame.transform.scale(self.image, (self.width, self.height))
        #     self.rect = self.image.get_rect(topleft=(self.x, self.y))
        #else:
        #     self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # SI TUVIERA FONDO!!!
        
        
        ## DEBUG PANELES
        #self.debug_panel = pygame_gui.elements.UIPanel(
        #    relative_rect=pygame.Rect(0, 0, 400, 300),
        #    manager=self.manager,
        #    starting_height=100,
        #    visible=True
        #)
        #self.debug_label = pygame_gui.elements.UILabel(
        #    relative_rect=pygame.Rect(10, 10, 380, 280),
        #    text="DEBUG: Paneles activos",
        #    manager=self.manager,
        #    container=self.debug_panel
        #)

        self.panel_container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.manager,
            starting_height=0,
            #object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanelContainer') # Opcional: asignar un object_id si lo usas en el tema
        )

        # Panel de información de selección
        self.info_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(20, 60, 300, 100),
            manager=self.manager,
            container=self.panel_container,
            starting_height=2,
            visible=False            
        )

        self.info_labels = {
            'beats': pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 10, 120, 25),
                text="Beats: --",
                manager=self.manager,
                container=self.info_panel
            ),
            'subdiv': pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 40, 120, 25),
                text="Subdiv: --",
                manager=self.manager,
                container=self.info_panel
            ),
            'bpm': pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(140, 10, 120, 25),
                text="BPM: --",
                manager=self.manager,
                container=self.info_panel
            ),
            'measures': pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(140, 40, 150, 25),
                text="Measures: --",
                manager=self.manager,
                container=self.info_panel
            )
        }

        # Panel de repetición
        self.repeat_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(25, 180, 300, 120),
            manager=self.manager,
            container=self.panel_container,
            starting_height=2,
            visible=True            
        )
        
        self.repeat_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(10, 10, 100, 30),
            manager=self.manager,
            container=self.repeat_panel,
            placeholder_text="Veces"
        )
        
        self.repeat_apply_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(120, 10, 80, 30),
            text="Repetir",
            manager=self.manager,
            container=self.repeat_panel
        )
        
        self.repeat_cancel_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(190, 10, 80, 30),
            text="Cancelar",
            manager=self.manager,
            container=self.repeat_panel
        )
        
        self.repeat_status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 50, 280, 60),
            text="Selecciona compases contiguos",   
            manager=self.manager,
            container=self.repeat_panel,
            object_id='#repeat_status_label'
        )


        # Input para Beats
        self.beats_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(25, 25, 80, 30),
            manager=self.manager,
            container=self.panel_container,
            initial_text=str(self.gui.input_values.get('beats', 4)), # Leer valor inicial de gui.input_values
            object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanel', object_id='#beats_input') # Asignar un object_id especfico
        )
        self.beats_input.set_allowed_characters('numbers')
        self.beats_input.set_text_length_limit(3)

        # Input para Subdivisions
        self.subdiv_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(25 + 80 + 10, 25, 80, 30),
            manager=self.manager,
            container=self.panel_container,
            initial_text=str(self.gui.input_values.get('subdivisions', 4)), # Leer valor inicial de gui.input_values
            object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanel', object_id='#subdiv_input') # Asignar un object_id especfico
        )
        self.subdiv_input.set_allowed_characters('numbers')
        self.subdiv_input.set_text_length_limit(3)

        # Botón Aceptar
        self.accept_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(25 + 80 + 10 + 80 + 10, 25, 100, 30),
            text="Aceptar",
            manager=self.manager,
            container=self.panel_container,
            #object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanel', object_id='#accept_button') # Opcional: asignar un object_id
        )

        # Botón ADD Measure
        add_button_rect = pygame.Rect(self.width - 100, self.height // 2 - 45, 90, 90)
        self.add_measure_button = pygame_gui.elements.UIButton(
            relative_rect=add_button_rect,
            text="ADD",
            manager=self.manager,
            container=self.panel_container,
            #object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanel', object_id='#add_button') # Opcional: asignar un object_id
        )

        # Botón DEL Measure
        del_button_rect = pygame.Rect(self.width - 200, self.height // 2 - 45, 90, 90)
        self.del_measure_button = pygame_gui.elements.UIButton(
            relative_rect=del_button_rect,
            text="DEL",
            manager=self.manager,
            container=self.panel_container,
            #object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanel', object_id='#del_button') # Opcional: asignar un object_id
        )


    def _update_info_panel(self):
        selected = self.gui.grid_panel.selected_measures_indices
        if not selected:
            self.info_panel.hide()
            self.repeat_panel.hide()
            return
            
        self.info_panel.show()
        
        # Obtener características comunes
        beats = set()
        subdivs = set()
        for idx in selected:
            beats.add(self.engine.measures[idx]['length'])
            subdivs.add(self.engine.measures[idx]['subdivisions'])
        
        # Actualizar labels
        beats_text = f"Beats: {beats.pop()}" if len(beats) == 1 else "Beats: Varios"
        subdiv_text = f"Subdiv: {subdivs.pop()}" if len(subdivs) == 1 else "Subdiv: Varios"
        bpm_text = f"BPM: {self.engine.bpm}"
        
        # Calcular rango de medidas si son consecutivas
        sorted_indices = sorted(selected)
        is_consecutive = all(sorted_indices[i] + 1 == sorted_indices[i+1] for i in range(len(sorted_indices)-1))
        
        measures_text = "Measures: --"
        if is_consecutive and len(selected) > 0:
            measures_text = f"Measures: {sorted_indices[0]+1} - {sorted_indices[-1]+1}"
        
        self.info_labels['beats'].set_text(beats_text)
        self.info_labels['subdiv'].set_text(subdiv_text)
        self.info_labels['bpm'].set_text(bpm_text)
        self.info_labels['measures'].set_text(measures_text)
        
        # Actualizar panel de repetición
        self.repeat_panel.show()
        self._update_repeat_panel_status(is_consecutive)

    def _update_repeat_panel_status(self, is_consecutive):
        if not is_consecutive:
            self.repeat_status_label.set_text("Selección no continua!\nSelecciona un bloque de compases contiguos")
            self.repeat_apply_btn.disable()
        else:
            self.repeat_status_label.set_text(f"Bloque seleccionado: {len(self.gui.grid_panel.selected_measures_indices)} compases")
            self.repeat_apply_btn.enable()


    def handle_event(self, event):        
        # Manejar eventos de la GUI (botones, inputs)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_measure_button:
                self._add_measure()
            if event.ui_element == self.accept_button:
                self._apply_beats_subdivs_to_selected()
            if event.ui_element == self.del_measure_button:
                 self._delete_selected_measures() # Llamar al mtodo interno para eliminar

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.repeat_apply_btn:
                self._handle_repeat_action()
            if event.ui_element == self.repeat_cancel_btn:
                self.gui.grid_panel.selected_measures_indices = []
                self._update_info_panel()


    def _handle_repeat_action(self):
        try:
            repeat_times = int(self.repeat_input.get_text())
            if repeat_times < 1:
                raise ValueError
        except ValueError:
            self.repeat_status_label.set_text("Error: Ingresa un número válido ≥1")
            return
            
        selected = sorted(self.gui.grid_panel.selected_measures_indices)
        start_idx = selected[0]
        end_idx = selected[-1]
        original_measures = self.engine.measures[start_idx:end_idx+1]
        
        # Duplicar patrones de instrumentos
        for _ in range(repeat_times):
            for i in range(start_idx, end_idx+1):
                self.engine.measures.insert(end_idx+1, self.engine.measures[i].copy())
                for inst in self.engine.patterns:
                    self.engine.patterns[inst].insert(end_idx+1, self.engine.patterns[inst][i].copy())
        
        # Actualizar UI
        self.engine.total_duration = self.engine.calculate_total_duration()
        self.engine.generate_events()
        self.gui.grid_panel._update_content_surface()
        self.repeat_status_label.set_text(f"¡Repetido {repeat_times} veces!")


    def draw(self, surface):
        ## NO ESTOY DIBUJANDO NADA POR AHORA CON ESTE METODO (antes dibujaba el fondo)
        # Dibuja el panel de fondo si hay imagen
        #if self.image:
        #     surface.blit(self.image, self.rect)
        pass

    def update(self):
        self._update_info_panel()

    # Método interno para añadir una medida (llama al engine)
    def _add_measure(self):
        beats_text = self.beats_input.get_text().strip()
        subdiv_text = self.subdiv_input.get_text().strip()
    
        try:
            beats = int(beats_text) if beats_text else 4
            subdivs = int(subdiv_text) if subdiv_text else 4
        except ValueError:
            return
    
        self.engine.add_measure(beats, subdivs)
        self.gui.grid_panel._update_content_surface()

    # Método interno para aplicar beats/subdivs a compases seleccionados (llamado por el botón Aceptar)
    def _apply_beats_subdivs_to_selected(self):
        beats_str = self.beats_input.get_text() # Leer directamente de los inputs
        subdivs_str = self.subdiv_input.get_text()

        try:
            new_beats = int(beats_str)
            new_subdivs = int(subdivs_str)
            if new_beats <= 0 or new_subdivs <= 0:
                 print("Advertencia: Beats y Subdivisiones deben ser mayores que 0.")
                 return

        except ValueError:
            print("Error: Valores de beats o subdivisiones no numricos. No se aplicarn los cambios.")
            return

        selected_indices = self.gui.grid_panel.selected_measures_indices

        if not selected_indices:
            print("Ningún compás seleccionado para modificar.")
            return

        # Aplicar los cambios a cada compás seleccionado
        for measure_idx in selected_indices:
            if 0 <= measure_idx < len(self.engine.measures):
                # Actualizar la longitud y las subdivisiones en la informacin de la medida en el engine
                self.engine.measures[measure_idx]['length'] = new_beats
                self.engine.measures[measure_idx]['subdivisions'] = new_subdivs

                # Actualizar la estructura del patrn para este compás en cada instrumento
                new_pattern_structure = [[0] * new_subdivs for _ in range(new_beats)]

                for inst in self.engine.patterns:
                    if measure_idx < len(self.engine.patterns[inst]):
                         # Reemplazamos completamente la lista del compás con la nueva estructura de ceros
                         # Usamos una reconstruccin explcita para asegurar una copia nueva
                         self.engine.patterns[inst][measure_idx] = [] # Vaciar la lista de beats
                         for beat_list in new_pattern_structure:
                              self.engine.patterns[inst][measure_idx].append(beat_list[:]) # Añadir copia de cada lista de subdivs


        # Recalcular duracin total y eventos en el engine y actualizar el grid
        self.engine.total_duration = self.engine.calculate_total_duration()
        self.engine.generate_events()
        self.gui.grid_panel._update_content_surface() # Notificar al grid para redibujarse

        # Limpiar la seleccin despus de aplicar los cambios
        self.gui.grid_panel.selected_measures_indices = []


    # Método interno para eliminar compases seleccionados (llama al engine)
    def _delete_selected_measures(self):
        selected = self.gui.grid_panel.selected_measures_indices

        if not selected:
            return

        self.engine.delete_measures(selected)
        self.gui.grid_panel.selected_measures_indices = []
        self.gui.grid_panel._update_content_surface()
