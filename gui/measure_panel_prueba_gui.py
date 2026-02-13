import pygame
import pygame_gui
# No necesitamos importar tu clase Button si vamos a usar los widgets de pygame-gui
# from .button import Button

class MeasurePanel:
    def __init__(self, x, y, screen, engine, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.gui = gui # Referencia a la GUI principal que tiene el manager
        self.manager = gui.manager # Obtenemos el manager de la GUI principal

        self.image = self.gui.load_image("cp_background.png")
        self.width = screen.get_width() * .75
        self.height = screen.get_height() * .18
        self.image = pygame.transform.scale(self.image, (self.width, self.height)) ## IDEM RESPONSIVE!!!
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

        # Creamos un contenedor para los widgets de pygame-gui dentro de este panel
        # Esto es opcional pero ayuda a organizar y posicionar widgets relativos al panel.
        # El relative_rect del contenedor será relativo a la pantalla.
        self.panel_container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect, # El contenedor ocupa la misma área que el panel visual
            manager=self.manager,
            # Puedes añadir un object_id si quieres aplicar theming específico a este panel
            # object_id=pygame_gui.core.ObjectID(class_id='@MeasurePanelContainer')
        )


        # --- Widgets de pygame-gui ---

        # Input para Beats
        self.beats_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(25, 25, 80, 30), # Posición relativa al panel_container
            manager=self.manager,
            container=self.panel_container, # El input está dentro de nuestro contenedor de panel
            initial_text=str(self.gui.input_values.get('beats', 4)), # Usar valor inicial del diccionario de GUI
            # Puedes añadir un object_id para theming específico
            # object_id=pygame_gui.core.ObjectID(class_id='@BeatsInput')
        )
        # Limitar a dígitos y longitud si es necesario
        self.beats_input.set_allowed_characters('numbers')
        self.beats_input.set_text_length_limit(2) # Por ejemplo, hasta 99 beats

        # Input para Subdivisions
        self.subdiv_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(25 + 80 + 10, 25, 80, 30), # Posición al lado del input de beats + margen
            manager=self.manager,
            container=self.panel_container, # El input está dentro de nuestro contenedor de panel
            initial_text=str(self.gui.input_values.get('subdivisions', 16)), # Usar valor inicial del diccionario de GUI
            # object_id=pygame_gui.core.ObjectID(class_id='@SubdivInput')
        )
        self.subdiv_input.set_allowed_characters('numbers')
        self.subdiv_input.set_text_length_limit(2) # Por ejemplo, hasta 99 subdivisiones

        # Botón Aceptar (para aplicar cambios a compases seleccionados - la lógica vendrá después)
        self.accept_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(25 + 80 + 10 + 80 + 10, 25, 100, 30), # Posición al lado del input de subdiv
            text="Aceptar",
            manager=self.manager,
            container=self.panel_container, # El botón está dentro de nuestro contenedor de panel
            # object_id=pygame_gui.core.ObjectID(class_id='@AcceptButton')
        )


        # Tu botón ADD (pygame-gui)
        add_button_rect = pygame.Rect(self.width - 100, self.height // 2 - 45, 90, 90)
        self.add_measure_button = pygame_gui.elements.UIButton(
            relative_rect=add_button_rect,
            text="ADD", # Texto simple por ahora
            manager=self.manager,
            container=self.panel_container,
            # object_id=pygame_gui.core.ObjectID(class_id='@AddMeasureButton')
        )

        # Tu botón DEL (pygame-gui)
        del_button_rect = pygame.Rect(self.width - 200, self.height // 2 - 45, 90, 90)
        self.del_measure_button = pygame_gui.elements.UIButton(
            relative_rect=del_button_rect,
            text="DEL", # Texto simple por ahora
            manager=self.manager,
            container=self.panel_container,
            # object_id=pygame_gui.core.ObjectID(class_id='@DelMeasureButton')
        )


    def handle_event(self, event):
        # Cuando usas pygame-gui, la mayor parte del manejo de eventos para los
        # widgets de pygame-gui ocurre dentro de manager.process_events().
        # Aquí, puedes manejar eventos de pygame-gui que te interesen
        # (como clics en botones de pygame-gui) o eventos de Pygame "puros"
        # que este panel necesite procesar.

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_measure_button:
                print('PRESIONADO BOTÓN ADD (pygame-gui)')
                # Llamar a la lógica para añadir un compás
                self._add_measure() # Llama a tu método existente

            if event.ui_element == self.accept_button:
                 print('PRESIONADO BOTÓN ACEPTAR (pygame-gui)')
                 # Aquí irá la lógica para aplicar beats/subdivs a compases seleccionados (paso 3)
                 self._apply_beats_subdivs_to_selected() # Método que crearemos después

            ## Añadir aca manejo para del_measure_button

        # Manejar eventos de cambio de texto en los inputs
        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == self.beats_input:
                print(f"Beats input changed to: {event.text}")
                # Validar y guardar el valor en el diccionario de la GUI
                self.gui.input_values['beats'] = event.text # Guardar el texto actual
                # Opcional: Añadir validación aquí si necesitas que el valor sea un número en un rango

            if event.ui_element == self.subdiv_input:
                print(f"Subdivisions input changed to: {event.text}")
                # Validar y guardar el valor en el diccionario de la GUI
                self.gui.input_values['subdivisions'] = event.text # Guardar el texto actual
                # Opcional: Añadir validación aquí

        # Si MeasurePanel tiene que manejar algún otro evento de Pygame que no sea de pygame-gui,
        # lo harías aquí.
        # for button in self.buttons: # Ya no necesitamos esto si usamos widgets de pygame-gui
        #      button.handle_event(event)


    def update(self):
        # En este enfoque, el dibujado de los widgets de pygame-gui dentro de este panel
        # lo maneja el UIManager en el bucle principal (gui.py::run).
        # Solo necesitas dibujar la imagen de fondo de tu panel si no usas un UIPanel
        # con una imagen de fondo (aunque UIPanel ya maneja el dibujado de su fondo).

        # Si usas UIPanel como contenedor, el dibujado de su fondo ya está cubierto por manager.draw_ui()
        # self.screen.blit(self.image, self.rect) # Comentar si usas UIPanel con fondo

        # Si tus botones ADD/DEL antiguos no usaban pygame-gui y los sigues dibujando aquí,
        # necesitarías mantener esa parte del código de dibujado.
        # for button in self.buttons: # Comentar si usas widgets de pygame-gui
        #      button.update(self.screen)

        pass # La mayor parte del trabajo de dibujado lo hace pygame-gui

    # Tu método para añadir un compás (llamado por el botón ADD ahora)
    def _add_measure(self):
        # La lógica para obtener los valores de beats y subdivs ya usa self.gui.input_values
        # Asegúrate de que los valores en self.gui.input_values son numéricos antes de llamar a engine.add_measure
        # Esto implica que la validación de los inputs debe ocurrir antes o dentro de engine.add_measure.
        print(f'Llamando a engine.add_measure con input_values: {self.gui.input_values}')
        self.engine.add_measure()

    # Método placeholder para la lógica de aceptar (paso 3)
    def _apply_beats_subdivs_to_selected(self):
        print(f"Intentando aplicar beats/subdivs: {self.gui.input_values}")

        # 1. Obtener los valores de beats y subdivisiones de los inputs
        # Ya están actualizados en self.gui.input_values por los eventos UI_TEXT_ENTRY_CHANGED
        beats_str = self.gui.input_values.get('beats', '4')
        subdivs_str = self.gui.input_values.get('subdivisions', '16')

        try:
            new_beats = int(beats_str)
            new_subdivs = int(subdivs_str)

            # Opcional: Validar los valores en los rangos permitidos
            # new_beats = max(2, min(new_beats, 7))
            # new_subdivs = max(1, min(new_subdivs, 16))

        except ValueError:
            print("Error: Valores de beats o subdivisiones no numéricos. No se aplicarán los cambios.")
            return # Salir del método si los valores no son válidos


        # 2. Obtener los índices de los compases seleccionados desde grid_panel
        selected_indices = self.gui.grid_panel.selected_measures_indices
        print(f"Compases seleccionados: {selected_indices}")

        if not selected_indices:
            print("Ningún compás seleccionado para modificar.")
            return # Salir si no hay compases seleccionados

        # 3. Iterar sobre los compases seleccionados y actualizar la estructura de datos del engine
        for measure_idx in selected_indices:
            if 0 <= measure_idx < len(self.engine.measures):
                print(f"Modificando Compás {measure_idx + 1} a {new_beats} beats y {new_subdivs} subdivisiones.")

                # Actualizar la longitud (beats) en la estructura de measures
                self.engine.measures[measure_idx]['length'] = new_beats

                # Actualizar la estructura de patterns para este compás
                # Esto es lo más delicado: creamos una nueva estructura vacía
                # con las nuevas dimensiones para cada instrumento en este compás.
                # NOTA: Esto BORRARÁ cualquier patrón existente en los compases modificados.
                # Preservar patrones existentes requiere lógica adicional (mapeo de celdas).
                for inst in self.engine.patterns:
                    if measure_idx < len(self.engine.patterns[inst]):
                        # Reemplazar la estructura de beats/subdivs para este compás
                        self.engine.patterns[inst][measure_idx] = [[0] * new_subdivs for _ in range(new_beats)]
                    else:
                        print(f"Advertencia: Índice de medida {measure_idx} fuera de rango para instrumento {inst}. Saltando.")


        # 4. Regenerar los eventos de audio después de modificar los patrones
        self.engine.generate_events()
        # Calcular la nueva duración total, ya que el número de beats puede haber cambiado
        self.engine.total_duration = self.engine.calculate_total_duration()


        # 5. Indicar al grid_panel que debe redibujarse para mostrar los cambios
        # Esto recalculará el ancho total y redibujará los compases modificados.
        self.gui.grid_panel._update_content_surface()

        # Opcional: Limpiar la selección después de aplicar los cambios
        self.gui.grid_panel.selected_measures_indices = []
        # Forzar un nuevo redibujado para quitar el recuadro rojo
        self.gui.grid_panel._update_content_surface()