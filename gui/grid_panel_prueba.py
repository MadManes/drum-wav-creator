import pygame
import pygame_gui
# from .button import Button # No parece que GridPanel necesite importar Button aquí

class GridPanel:
    def __init__(self, x, y, screen, engine, manager, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.manager = manager
        self.gui = gui

        # El tamaño y posición del panel en la ventana general
        self.width = screen.get_width() - x
        self.height = screen.get_height() * .68
        self.panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Cargar y escalar la imagen de fondo del panel (si es que el fondo es fijo)
        self.background_image = self.gui.load_image("grid_background.png")
        self.background_image = pygame.transform.scale(self.background_image, (self.panel_rect.width, self.panel_rect.height))

        # Creamos el ScrollingContainer. Su relative_rect es donde se coloca dentro de su contenedor.
        # Como GridPanel parece dibujarse directamente en la pantalla principal (en gui.py),
        # el relative_rect del scrolling_container será relativo a la esquina superior izquierda de la pantalla.
        # Si el scrolling_container debe ocupar toda el área de este GridPanel, su relative_rect es self.panel_rect.
        # Si hay un encabezado fijo dentro de GridPanel, ajusta la 'top' y 'height' del relative_rect.
        self.measure_header_height = self.panel_rect.height * .08 # Define esto si tienes un área de encabezado

        self.scrolling_container = pygame_gui.elements.UIScrollingContainer(
             relative_rect=pygame.Rect(self.panel_rect.left, self.panel_rect.top + self.measure_header_height,
                                       self.panel_rect.width, self.panel_rect.height - self.measure_header_height),
             manager=self.manager
         )

        # Dimensiones de un compás individual VISUAL dentro del scrolling container
        # Estas son las dimensiones de la Surface que crearás para cada compás.
        self.compas_visual_width = 150 # Puedes ajustar este valor
        self.compas_visual_height = self.panel_rect.height - self.measure_header_height # Alto igual al área de scroll
        self.margin_between_compases = 5 # Margen entre compases

        # Lista para mantener un registro de los elementos UIImage de cada compás
        # Guardar el índice del compás asociado a cada elemento es útil para eventos
        self.compas_elements = []
        self.total_content_width = 0 # Para llevar el registro del ancho total del contenido desplazable

        # Asumo que _create_buttons crea botones *dentro* de GridPanel, si son de pygame-gui,
        # puedes pasarle self.manager o incluso self.scrolling_container si deben ir dentro del área de scroll.
        self._create_buttons()

    # Método para dibujar un ÚNICO compás en una superficie dada
    # Ahora recibe el índice del compás
    def draw_single_measure(self, surface, measure_index):
        # surface: La Surface donde dibujar este compás (de tamaño self.compas_visual_width x self.compas_visual_height)
        # measure_index: El índice del compás en self.engine.measures

        # Obtener los datos relevantes del compás del engine
        if measure_index >= len(self.engine.measures):
            print(f"Error: Intentando dibujar compás con índice {measure_index}, pero solo hay {len(self.engine.measures)} compases.")
            return

        measure_data = self.engine.measures[measure_index]
        current_beats = measure_data.get('length', 4) # Usar .get con valor por defecto por seguridad

        # Dimensiones de las celdas dentro de la surface del compás
        rect_width = self.compas_visual_width / current_beats
        rect_height = surface.get_height() / len(self.engine.patterns) # Alto basado en el número de instrumentos

        for beat_idx in range(current_beats):
            # Obtener las subdivisiones para este beat de este compás y este instrumento (usando 'snare' como referencia si es válido)
            # Asegúrate de que los índices existan antes de acceder
            current_subdiv = 1 # Valor por defecto
            if 'snare' in self.engine.patterns and measure_index < len(self.engine.patterns['snare']) and beat_idx < len(self.engine.patterns['snare'][measure_index]):
                 current_subdiv = len(self.engine.patterns['snare'][measure_index][beat_idx]) or 1 # Usar 1 si la lista está vacía

            subdiv_width = rect_width / current_subdiv

            for subdiv_idx in range(current_subdiv):
                x_pos_relative_to_surface = int(round((beat_idx * rect_width) + (subdiv_idx * subdiv_width)))

                for inst_idx, inst in enumerate(self.engine.patterns):
                    # Verificar que los índices existan en self.engine.patterns antes de acceder al estado
                    state = 0 # Estado por defecto
                    if (inst in self.engine.patterns and
                        measure_index < len(self.engine.patterns[inst]) and
                        beat_idx < len(self.engine.patterns[inst][measure_index]) and
                        subdiv_idx < len(self.engine.patterns[inst][measure_index][beat_idx])):
                         state = self.engine.patterns[inst][measure_index][beat_idx][subdiv_idx]


                    cell_width = int(round(subdiv_width)) - 1
                    rect = pygame.Rect(
                        x_pos_relative_to_surface,
                        inst_idx * rect_height, # Posición vertical relativa al inicio del área de grid en la surface
                        cell_width,
                        rect_height
                    )

                    # Dibuja el rectángulo en la surface del compás
                    color = (255, 0, 0) if state else (200, 200, 200) if subdiv_idx != 0 else (150, 150, 150)
                    pygame.draw.rect(surface, color, rect)
                    # Opcional: Dibujar el borde si quieres que se vea la cuadrícula completa
                    pygame.draw.rect(surface, (100, 100, 100), rect, 1)


    # Este método se llamará desde MeasurePanel cuando se agregue un nuevo compás al engine
    def add_measure(self, measure_index): # <--- Ahora recibe el índice del compás
        # measure_index: El índice del compás que se acaba de agregar en self.engine.measures

        print(f"GridPanel.add_measure llamado para el índice: {measure_index}")

        # 1. Crea una Surface para este nuevo compás
        # Las dimensiones de esta surface son las dimensiones VISUALES de un compás en la pantalla
        compas_surface = pygame.Surface((self.compas_visual_width, self.compas_visual_height), pygame.SRCALPHA)
        compas_surface.fill((0, 0, 0, 0)) # Rellenar con transparente

        # 2. Dibuja el contenido del compás en su Surface usando el índice
        self.draw_single_measure(compas_surface, measure_index) # <--- Pasamos el índice aquí

        # 3. Calcula la posición horizontal para el nuevo compás dentro del scrolling container
        # Se coloca al final del contenido existente
        pos_x_in_container = self.total_content_width

        # 4. Crea un UIImage para la Surface del compás
        compas_element = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(pos_x_in_container, 0, self.compas_visual_width, self.compas_visual_height),
            image_surface=compas_surface,
            manager=self.manager,
            container=self.scrolling_container  # ¡Añadimos el UIImage al scrolling container!
        )

        # 5. Actualiza el ancho total del contenido desplazable
        self.total_content_width += self.compas_visual_width + self.margin_between_compases # Sumamos el ancho visual del compás y el margen

        # 6. Informa al scrolling_container las nuevas dimensiones totales del contenido
        # Esto es crucial para que active la barra de scroll si el ancho excede el área visible
        self.scrolling_container.set_scrollable_area_dimensions((self.total_content_width, self.compas_visual_height)) # El alto del área desplazable es el alto visual de un compás


        # Guarda la referencia al elemento UIImage y asóciala con el índice del compás si necesitas el mapeo inverso para eventos
        self.compas_elements.append({'index': measure_index, 'element': compas_element})

        print(f"Elemento UIImage para compás {measure_index} añadido al scrolling container. Ancho total contenido: {self.total_content_width}")


    # EL MÉTODO draw_grid YA NO SE LLAMA PARA DIBUJAR LOS COMPASES DESPLAZABLES.
    # El UIManager de pygame-gui se encarga de dibujarlos.
    # Puedes eliminar o refactorizar draw_grid si ya no tiene otra función.
    # Si tenías lógica para dibujar el "cabezal" de cada compás (el número, etc.),
    # eso podría ser parte del draw_single_measure o un elemento de UI separado.

    def _create_buttons(self):
        # Aquí crearías botones si GridPanel tuviera botones propios.
        # Si estos botones deben estar DENTRO del área de scroll, pásales self.scrolling_container como container.
        # Si son fijos del panel (fuera del área de scroll), no se lo pases.
        pass

    def handle_event(self, event):
         # Eventos para elementos de pygame-gui dentro del scrolling_container se manejan en el bucle principal a través del manager.
         # Aquí solo manejarías eventos específicos de GridPanel que no sean para los elementos de pygame-gui en el scroll.
         # Por ejemplo, si tienes botones fijos en GridPanel que no son de pygame-gui.

        # Ejemplo de cómo manejar clicks en los UIImage de compás (ESTA LÓGICA VA EN EL BUCLE PRINCIPAL DE gui.py):
        # if event.type == pygame_gui.UI_IMAGE_PRESSED:
        #     # Verifica si el elemento clickeado es uno de los UIImage de compás de este panel
        #     clicked_element_info = next((item for item in self.compas_elements if item['element'] == event.ui_element), None)
        #     if clicked_element_info:
        #         compas_index = clicked_element_info['index']
        #         # Obtener la posición del click relativa al UIImage clickeado
        #         click_pos_relative_to_image = (event.pos[0] - event.ui_element.get_screen_rect().left,
        #                                        event.pos[1] - event.ui_element.get_screen_rect().top)
        #         # Implementa lógica para calcular la celda (beat, subdiv, instrumento)
        #         # a partir de click_pos_relative_to_image y las dimensiones de las celdas VISUALES.
        #         # Luego, llama a self.engine.update_pattern(...) y **ACTUALIZA EL UIImage DE ESE COMPÁS**
        #         # (probablemente redibujando su surface y actualizando la image_surface del UIImage).
        #         # self.update_compas_visual(compas_index) # Necesitarías un método para esto

        # Si tienes botones NO gestionados por pygame-gui, mantén su manejo de eventos aquí:
        # for button in self.buttons:
        #     button.handle_event(event)
        pass # Elimina el manejo de eventos directo para la grilla aquí

    # Método opcional para actualizar la visualización de un compás después de cambiar su patrón
    def update_compas_visual(self, measure_index):
         # Encuentra el elemento UIImage correspondiente al índice del compás
         compas_info = next((item for item in self.compas_elements if item['index'] == measure_index), None)
         if compas_info:
             compas_element = compas_info['element']
             # Crea una nueva Surface para este compás con los datos actualizados
             updated_surface = pygame.Surface((self.compas_visual_width, self.compas_visual_height), pygame.SRCALPHA)
             updated_surface.fill((0, 0, 0, 0))
             self.draw_single_measure(updated_surface, measure_index)
             # Actualiza la imagen del UIImage
             compas_element.set_image(updated_surface)


    def update(self):
        # Dibuja el fondo fijo de tu panel si no es un elemento de pygame-gui
        self.screen.blit(self.background_image, self.panel_rect)

        # Si tienes otros elementos fijos en este panel (ej. encabezado de compases)
        # que no son elementos de pygame-gui ni están en el scrolling_container, dibújalos aquí.

        # Los elementos dentro del scrolling_container (los compases) los dibuja el manager
        # en el bucle principal con manager.draw_ui(screen).
        pass # Elimina la llamada a self.draw_grid() aquí