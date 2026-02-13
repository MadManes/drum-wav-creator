import pygame
import sys
# Asegúrate de que el archivo Button.py est accesible
from .button import Button
import pygame_gui # Importar pygame_gui si usaremos sus elementos


class Toolbar():
    # --- MODIFICACIN AQU: Aceptar el manager de pygame_gui ---
    def __init__(self, x, y, screen, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.gui = gui
        self.manager = gui.manager # Guardar la referencia al UIManager

        # Cargar imágenes de fondo de la toolbar (original y modo menú)
        self.original_image = self.gui.load_image("toolbar_title")
        # Asegrate de tener una imagen llamada "toolbar_menu_bg.png" (o el nombre que uses)
        self.menu_image = self.gui.load_image("toolbar_menu") # Imagen para el modo men

        # Verificar si las imgenes se cargaron correctamente antes de usarlas
        if not self.original_image:
             print("ADVERTENCIA: No se pudo cargar la imagen 'toolbar_2'. Usando una superficie genrica.")
             # Crear una superficie genrica si la imagen falla
             self.original_image = pygame.Surface((screen.get_width(), 50)) # Altura de ejemplo
             self.original_image.fill((100, 100, 100)) # Color de ejemplo

        # Usar la altura de la imagen original como base
        self.width = screen.get_width()
        self.height = self.original_image.get_height() // 3 # Usar la altura real de la imagen cargada

        # Redimensionar AMBAS imgenes a la altura y ancho de la toolbar
        self.original_image = pygame.transform.scale(self.original_image, (int(self.width), int(self.height))) # Asegurar int

        if self.menu_image: # Asegurarse de que la imagen del men se carg correctamente
             self.menu_image = pygame.transform.scale(self.menu_image, (int(self.width), int(self.height))) # Asegurar int
        else:
             # Si la imagen del men falla, usar la original para evitar errores
             print("ADVERTENCIA: No se pudo cargar la imagen 'toolbar_menu_bg'. Usando la imagen original.")
             self.menu_image = self.original_image

        # --- Imagen de fondo actual de la toolbar ---
        self.current_bg_image = self.original_image
        self.rect = self.current_bg_image.get_rect(topleft=(self.x, self.y))

        # Lista para los botones de control (minimizar, cerrar, y el nuevo botn de modo) - Custom Button
        self.control_buttons = []
        # Lista para los botones del men (File, Edit, Help, etc. - pygame_gui.elements.UIButton)
        self.menu_buttons = []

        # --- Estado del modo de la toolbar ---
        self.menu_mode_active = False # Comienza en modo control
        # --- Estado de hover de la toolbar completa ---
        self.is_toolbar_hovered = False # True si el ratn est sobre el rect de la toolbar

        # Crear todos los botones (control y men), pero solo manejaremos/dibujaremos los del modo actual
        self._create_buttons() # Crea los custom Buttons (control)
        self._create_menu_buttons() # Crea los pygame_gui Buttons (men)

        # Asegurarse de que la visibilidad inicial de los botones de men sea correcta (ocultos)
        self._update_button_visibility()


    def _create_buttons(self):
        # BOTON CERRAR
        close_normal = self.gui.load_image("close_button_off")
        close_hover = self.gui.load_image("close_button_on")
        # Usar dimensiones y posiciones relativas a la toolbar
        close_button_width = self.height * 0.8 # Ejemplo de tamaño relativo a la altura de la toolbar
        close_button_height = self.height * 0.8
        close_button_x = self.width - close_button_width - 5 # 5px de margen derecho
        close_button_y = (self.height - close_button_height) / 2 # Centrado verticalmente

        # --- MODIFICACIN CLAVE AQU: Pasar imgenes NO ESCALADAS al constructor de Button ---
        # Button se encargar de escalarlas a las dimensiones width/height proporcionadas
        close_button = Button(self.x + close_button_x, self.y + close_button_y, # Posicin absoluta
                                close_button_width, close_button_height,
                                close_normal, close_hover, action=self._close_app)
        self.control_buttons.append(close_button)
        
        
        # BOTON CERRAR
        #close_normal = self.gui.load_image("close_button_off")
        #close_hover = self.gui.load_image("close_button_on")
        ## Usar dimensiones y posiciones relativas a la toolbar
        #close_button_width = self.height * 0.8 # Ejemplo de tamaño relativo a la altura de la toolbar
        #close_button_height = self.height * 0.8
        #close_button_x = self.width - close_button_width - 5 # 5px de margen derecho
        #close_button_y = (self.height - close_button_height) / 2 # Centrado verticalmente
#
        #close_button = Button(self.x + close_button_x, self.y + close_button_y, # Posicin absoluta
        #                        close_button_width, close_button_height,
        #                        close_normal, close_hover, action=self._close_app)
        #self.control_buttons.append(close_button)

        # BOTON MINIMIZAR
        minimize_normal = self.gui.load_image("minimize_button_off")
        minimize_hover = self.gui.load_image("minimize_button_on")
        # Posicionar al lado del botn Cerrar
        minimize_button_width = self.height * 0.8
        minimize_button_height = self.height * 0.8
        minimize_button_x = close_button_x - minimize_button_width - 5 # 5px de espacio
        minimize_button_y = (self.height - minimize_button_height) / 2 # Centrado verticalmente

        minimize_button = Button(self.x + minimize_button_x, self.y + minimize_button_y,
                                  minimize_button_width, minimize_button_height,
                                  minimize_normal, minimize_hover, action=self._minimize_window)
        self.control_buttons.append(minimize_button)

        # --- Aadir el NUEVO BOTON DE MODO ---
        # Asumimos que est en la parte izquierda, aproximadamente 25% del ancho
        # Ajusta la posicin y tamaño segn tu diseo y la imagen del botn
        mode_toggle_normal = self.gui.load_image("menu_btn_normal") # Crea una imagen para este botn
        mode_toggle_hover = self.gui.load_image("menu_btn_hover")
        mode_toggle_button_width = self.height * 1.15 # Ejemplo de ancho
        mode_toggle_button_height = self.height * 1.15 # Altura similar a otros botones
        mode_toggle_button_x = self.width * 0.25 - mode_toggle_button_width / 2 # Centrado aprox. al 25%
        mode_toggle_button_y = (self.height - mode_toggle_button_height) / 2 # Centrado verticalmente


        self.mode_toggle_button = Button(self.x + mode_toggle_button_x, self.y + mode_toggle_button_y, # Posicin absoluta
                                         mode_toggle_button_width, mode_toggle_button_height,
                                         mode_toggle_normal, mode_toggle_hover, action=self._toggle_menu_mode)
        self.control_buttons.append(self.mode_toggle_button)

        # Puedes añadir otros botones de control si los tienes


    # --- NUEVO MÉTODO para crear los botones del modo menú (con pygame_gui) ---
    def _create_menu_buttons(self):
        # Estos botones solo sern visibles y manejados cuando self.menu_mode_active sea True

        # Ejemplo de botones de men (ajusta posiciones, tamaños y textos)
        # Usamos relative_rect relativo al CONTENEDOR del panel (la toolbar misma)
        button_height = self.height - 2 # Un poco ms pequeo que la altura de la toolbar
        button_y = 1 # Un poco separado del borde superior

        # Botn FILE
        file_button_rect = pygame.Rect(10, button_y, 80, button_height)
        file_button = pygame_gui.elements.UIButton(
            relative_rect=file_button_rect,
            text="File",
            manager=self.manager,
            container=self.manager.get_root_container(), # Dibuja sobre el root container
            anchors={'left': 'left', 'right': 'left', 'top': 'top', 'bottom': 'top'},
            visible=0 # Oculto inicialmente
        )
        # Ajustamos la posicin absoluta del botn para que est dentro de la toolbar
        file_button.set_position((self.rect.x + file_button_rect.x, self.rect.y + file_button_rect.y))
        self.menu_buttons.append(file_button)

        # Botn EDIT
        edit_button_rect = pygame.Rect(10 + 80 + 5, button_y, 80, button_height) # 5px de espacio
        edit_button = pygame_gui.elements.UIButton(
            relative_rect=edit_button_rect,
            text="Edit",
            manager=self.manager,
            container=self.manager.get_root_container(),
            anchors={'left': 'left', 'right': 'left', 'top': 'top', 'bottom': 'top'},
            visible=0 # Oculto inicialmente
        )
        edit_button.set_position((self.rect.x + edit_button_rect.x, self.rect.y + edit_button_rect.y))
        self.menu_buttons.append(edit_button)

        # Botn HELP
        help_button_rect = pygame.Rect(10 + 80 + 5 + 80 + 5, button_y, 80, button_height) # 5px de espacio
        help_button = pygame_gui.elements.UIButton(
            relative_rect=help_button_rect,
            text="Help",
            manager=self.manager,
            container=self.manager.get_root_container(),
            anchors={'left': 'left', 'right': 'left', 'top': 'top', 'bottom': 'top'},
            visible=0 # Oculto inicialmente
        )
        help_button.set_position((self.rect.x + help_button_rect.x, self.rect.y + help_button_rect.y))
        self.menu_buttons.append(help_button)

        # Puedes añadir ms botones de men aquí (Exit, etc.)

        # Necesitas almacenar una referencia a estos botones si quieres manejar sus eventos especficos ms tarde
        # Por ahora, se crean y se aaden a la lista menu_buttons


    # --- NUEVO MÉTODO para alternar entre los modos de la toolbar ---
    def _toggle_menu_mode(self):
        print("DEBUG: Alternando modo de toolbar")
        self.menu_mode_active = not self.menu_mode_active
        # Cuando el modo cambia, debemos actualizar la visibilidad de los botones
        self._update_button_visibility()


    # --- NUEVO MÉTODO para actualizar la visibilidad de los botones ---
    def _update_button_visibility(self):
        # --- MODIFICACIN CLAVE AQU: Solo iterar sobre los botones de pygame_gui ---
        # La visibilidad de los custom Buttons (self.control_buttons) se controla en handle_event y update
        if self.menu_mode_active:
            # Si el modo men est activo, mostrar botones de men
            for button in self.menu_buttons:
                # Los botones de pygame_gui s tienen set_visible
                button.visible = 1 # 1 para mostrar
        else:
            # Si el modo de control est activo, ocultar botones de men
            for button in self.menu_buttons:
                button.visible = 0 # 0 para ocultar


    def handle_event(self, event):
        # Manejar eventos de la GUI
        # --- MODIFICACIN AQU: Pasar eventos solo a los botones del modo activo ---
        if not self.menu_mode_active: # Si estamos en modo control
            # Pasar eventos solo a los botones de control personalizados
            for button in self.control_buttons:
                button.handle_event(event)
        else: # Si estamos en modo men
            # Los eventos para los botones de pygame_gui se manejan automticamente por self.manager.process_events(event) en gui.py
            # Si quieres manejar eventos de botones de pygame_gui especficos en la toolbar, hazlo aqu:
            # if event.type == pygame_gui.UI_BUTTON_PRESSED:
            #     if event.ui_element in self.menu_buttons:
            #         if event.ui_element.get_text() == "File":
            #             print("Clic en File")
            #             # Lgica del men File
            #         # etc.
            pass # No hacemos nada aqu para los botones de men de pygame_gui

        # --- MODIFICACIN AQU: Detectar si el ratn sale de la toolbar en MOUSEMOTION ---
        # Esto debe ocurrir independientemente del modo actual, para poder volver al modo control
        # si el ratn sale mientras est en modo men.
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.is_toolbar_hovered = self.rect.collidepoint(mouse_pos)
            # Si el modo men est activo Y el ratn ya NO colisiona con la toolbar
            if self.menu_mode_active and not self.rect.collidepoint(mouse_pos):
                print("DEBUG: Raton sali de la toolbar. Revertiendo modo menu.")
                # Alternar el modo de nuevo para volver al original
                self.menu_mode_active = False
                self._update_button_visibility() # Actualizar visibilidad de los botones
        
        # Manejar eventos de la GUI
        # Pasar eventos solo a los botones del modo activo (control o men)
        if not self.menu_mode_active: # Si estamos en modo control
            # Pasar eventos solo a los botones de control personalizados
            for button in self.control_buttons:
                button.handle_event(event)
        else: # Si estamos en modo men
            # Los eventos para los botones de pygame_gui se manejan automticamente por self.manager.process_events(event) en gui.py
            # Si quieres manejar eventos de botones de pygame_gui especficos en la toolbar, hazlo aquí:
            # if event.type == pygame_gui.UI_BUTTON_PRESSED:
            #     if event.ui_element in self.menu_buttons:
            #         if event.ui_element.get_text() == "File":
            #             print("Clic en File")
            #             # Lgica del men File
            #         # etc.
            pass # No hacemos nada aquí para los botones de men de pygame_gui



    def update(self):
        # --- MODIFICACIN CLAVE: Dibujar la imagen de fondo de la toolbar segn hover o modo activo ---
        if self.menu_mode_active:             
            self.current_bg_image = self.menu_image        
        else:
            # Si NO est en modo menu
            self.current_bg_image = self.original_image

        # DIBUJO TOOLBAR EN PANTALLA con la imagen de fondo decidida
        self.screen.blit(self.current_bg_image, self.rect)


        # DIBUJO BOTONES DEL MODO ACTIVO (solo tus Custom Buttons de control)
        # --- MODIFICACIN CLAVE AQU: Dibujar solo los botones de control si el modo men NO est activo ---
        if not self.menu_mode_active:
            for button in self.control_buttons:
                # --- Lógica para que los custom Buttons muestren su imagen de hover ---
                if button.is_hovered and button.hover_image_scaled: # Si est hovered y tiene imagen hover
                    button.image = button.hover_image_scaled # Usar imagen hover escalada
                else: # Si no est hovered o no tiene imagen hover
                    button.image = button.normal_image_scaled # Usar imagen normal escalada

                # Pasar la pantalla al mtodo update del botn para que se dibuje a s mismo
                button.update(self.screen)

        # Los botones de pygame_gui (self.menu_buttons) se dibujan automticamente por self.manager.draw_ui(self.screen) en gui.py


    def _close_app(self):
        print("\nCERRANDO EL PROGRAMA DESDE LA TOOLBAR")
        pygame.quit()
        sys.exit()

    def _minimize_window(self):
        print("\nMINIMIZANDO LA VENTANA DESDE LA TOOLBAR")
        pygame.display.iconify()

    # Define mtodos de accin para los botones del men de pygame_gui aquí si quieres
    # def _file_action(self):
    #     print("Accin de men: File")
    #     pass
    # def _edit_action(self):
    #     print("Accin de men: Edit")
    #     pass
    # def _help_action(self):
    #     print("Accin de men: Help")
    #     pass

