import pygame
import os
from .button import Button

PANEL_BG_COLOR = (50,50,50)
PANEL_BORDER_COLOR = (0,0,0)
PANEL_BORDER_THICKNESS = 2

class ControlPanel:
    def __init__(self,x, y, screen, engine, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.gui = gui
        # Cargar imagen de fondo del panel
        self.image = self.gui.load_image("cp_background")

        self.width = screen.get_width() * .25
        self.height = screen.get_height() * .18

        # Redimensionar imagen de fondo
        if self.image: # Verificar si la imagen se carg correctamente
             self.image = pygame.transform.scale(self.image, (int(self.width), int(self.height))) # Asegurar int para dimensiones
             self.rect = self.image.get_rect(topleft=(self.x, self.y))
        else:
             # Crear un rectngulo si la imagen no se carga, para que el panel tenga dimensiones
             self.rect = pygame.Rect(self.x, self.y, int(self.width), int(self.height))
             print("ADVERTENCIA: No se pudo cargar la imagen de fondo de ControlPanel. Usando rectngulo genrico.")

        # Lista para todos los botones interactivos (para manejar eventos)
        self.buttons = []

        # --- Estado de reproduccin ---
        # La aplicacin comienza por defecto en pausa
        self.is_playing = False # True si est reproduciendo, False si est pausado/detenido

        # Crear botones
        self._create_buttons()

        # --- Inicializar la imagen del botn PAUSE al inicio (estado por defecto: pausado) ---
        # Esto se hace despus de crear los botones para asegurar que self.pause_button existe
        # La lgica en update() ahora se encargar de esto.
        # if self.pause_button:
        #      self.pause_button.image = self.pause_button.hover_image_scaled # Establecer la imagen inicial de PAUSE a "on"


    def _create_buttons(self):
        # Definir dimensiones base para los botones de reproduccin (ajusta estos valores)
        # Estos son ejemplos, ajstalos para que se vean bien con tus imgenes y resolucin
        # Usamos los clculos originales de tu cdigo para mantener el layout que ya tenas
        play_pause_button_width = (self.width - 20) / 3
        play_pause_button_height = (self.height / 2) - 20
        button_y = self.y + 5 # Posicin Y para Play/Pause

        # BOTON PLAY
        # Cargar imgenes para el botn Play
        self.play_normal = self.gui.load_image("play_off")
        self.play_hover = self.gui.load_image("play_on")
        # Crear la instancia del botn Play
        play_button_x = self.x + 5 # Posicin X para Play
        self.play_button = Button(play_button_x, button_y,
                                  play_pause_button_width, play_pause_button_height,
                                  self.play_normal, self.play_hover, action=self._play)
        self.buttons.append(self.play_button) # Añadir a la lista de botones para manejo de eventos

        # BOTON PAUSE/STOP
        # Cargar imgenes para el botn Pause/Stop
        self.pause_normal = self.gui.load_image("pause_off")
        self.pause_hover = self.gui.load_image("pause_on")
        # Crear la instancia del botn Pause/Stop
        # Posicionar al lado del botn Play con un offset
        pause_button_x = self.x + ((self.width - 20) / 3) + 11 # Usar el offset de 11 de tu cdigo original
        self.pause_button = Button(pause_button_x, button_y, # Misma posicin Y que Play
                                   play_pause_button_width, play_pause_button_height,
                                   self.pause_normal, self.pause_hover, action=self._pause)
        self.buttons.append(self.pause_button) # Añadir a la lista de botones para manejo de eventos


        # BPM PANEL (Si es un botn visual, lo mantenemos aqu. Si solo es grfico, podra dibujarse directamente)
        # Cargar imagen para el panel BPM
        self.bpm_panel_image = self.gui.load_image("bpm_panel") # Renombrado para claridad
        # Crear instancia del botn BPM Panel (si es clickable)
        # --- Ajuste de tamaño y posicin del botn BPM Panel ---
        # Usamos los clculos y offsets de tu cdigo original
        bpm_panel_x = self.x + 4
        bpm_panel_y = self.y + (self.height / 2) - 13
        bpm_panel_width = self.play_button.width + self.pause_button.width # Usar los anchos ya calculados
        bpm_panel_height = (self.height / 2) + 6
        self.bpm_panel_button = Button(bpm_panel_x, bpm_panel_y,
                                       bpm_panel_width, bpm_panel_height,
                                       self.bpm_panel_image, None, action=None) # Accin None si no es clickable
        self.buttons.append(self.bpm_panel_button) # Añadir a la lista de botones


        # BOTON DOWNLOAD WAV
        # Cargar imagen para el botn Download
        self.download_wav_image = self.gui.load_image("download_wav") # Renombrado para claridad
        # Crear instancia del botn Download
        # --- Ajuste de tamaño y posicin del botn Download ---
        # Usamos los clculos y offsets de tu cdigo original
        download_button_x = self.x + 2*(((self.width - 20) / 3)) + 6
        download_button_y = self.y + (self.height / 2) - 13 # Misma posicin Y que BPM Panel
        download_button_width = ((self.width - 20) / 3)
        download_button_height = self.bpm_panel_button.height # Misma altura que BPM Panel
        self.download_wav_button = Button(download_button_x, download_button_y,
                                          download_button_width, download_button_height,
                                          self.download_wav_image, None, action=self._download_wav)
        self.buttons.append(self.download_wav_button) # Añadir a la lista de botones


    def handle_event(self, event):
        # Pasar el evento a cada botn. Button.handle_event actualizar is_hovered y ejecutar la accin al click.
        for button in self.buttons:
             button.handle_event(event)


    def update(self):
        # DIBUJO CONTROL PANEL EN PANTALLA (fondo)
        self.screen.fill(PANEL_BG_COLOR, self.rect)
        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, self.rect, PANEL_BORDER_THICKNESS)

        if self.image:
             self.screen.blit(self.image, self.rect)

        # --- DIBUJO BOTONES DE CONTROL PANEL ---
        # Iteramos sobre todos los botones interactivos
        for button in self.buttons:
            # --- Lógica para decidir qué imagen dibujar para Play y Pause ---
            if button == self.play_button:
                # Si est reproduciendo, Play est "encendido" permanentemente
                if self.is_playing:
                    button.image = button.hover_image_scaled # Play ON (imagen hover escalada)
                else:
                    # Si no est reproduciendo, Play est "apagado", pero puede tener hover temporal
                    if button.is_hovered:
                       button.image = button.hover_image_scaled # Play OFF pero con hover
                    else:
                       button.image = button.normal_image_scaled # Play OFF sin hover

            elif button == self.pause_button:
                # Si NO est reproduciendo (est pausado), Pause est "encendido" permanentemente
                if not self.is_playing:
                    button.image = button.hover_image_scaled # Pause ON (imagen hover escalada)
                else:
                    # Si est reproduciendo, Pause est "apagado", pero puede tener hover temporal
                    if button.is_hovered:
                       button.image = button.hover_image_scaled # Pause OFF pero con hover
                    else:
                       button.image = button.normal_image_scaled # Pause OFF sin hover

            else:
                # --- Lgica para otros botones (BPM, Download) ---
                # Para estos botones, el estado visual depende SOLO del hover.
                # Button.handle_event ya actualiz button.is_hovered.
                # Ahora, decidimos la imagen basndonos en is_hovered.
                if button.is_hovered and button.hover_image_scaled: # Usar imagen hover si existe y est hovered
                    button.image = button.hover_image_scaled
                else: # Si no est hovered o no hay imagen hover, usar la normal
                    button.image = button.normal_image_scaled


            # --- DIBUJAR el botn con la imagen que acabamos de establecer ---
            button.update(self.screen)
        
        self.is_playing = self.engine.is_playing()


    def _play(self):
        # Solo iniciar si no est reproduciendo ya
        if not self.engine.is_playing(): # Usar el estado del engine como fuente de verdad
            print("Accin: Iniciar Reproducción")
            self.engine.start()
            self.is_playing = True # Actualizar el estado local


    def _pause(self):
        # Solo detener si est reproduciendo
        if self.engine.is_playing(): # Usar el estado del engine como fuente de verdad
            print("Accin: Detener Reproducción")
            self.engine.stop()
            self.is_playing = False # Actualizar el estado local


    def _download_wav(self):            
        print("Acción: Descargar WAV")
        
        os.makedirs("exports", exist_ok=True)

        filename = os.path.join("exports", "export.wav")

        try:
            self.engine.export(filename)
            print(f"WAV exportado correctamente en: {filename}")
        except Exception as e:
            print(f"Error al exportar WAV: {e}")


'''import pygame
from .button import Button

class ControlPanel:
    def __init__(self,x, y, screen, engine, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.gui = gui
        self.image = self.gui.load_image("cp_background")        
        self.width = screen.get_width() * .25
        self.height = screen.get_height() * .18
        
        self.image = pygame.transform.scale(self.image, (self.width, self.height)) ## IDEM RESPONSIVE!!!
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.buttons = []

        # --- Estado de reproduccin ---
        # La aplicacin comienza por defecto en pausa
        self.is_playing = False # True si est reproduciendo, False si est pausado/detenido

        self._create_buttons()

    def _create_buttons(self):

        # BOTON PLAY
        self.play_normal = self.gui.load_image("play_off")
        self.play_hover = self.gui.load_image("play_on")
        ## VER POS X e Y CON EL REESCALADO Y EL RESPONSIVE
        self.play_button = Button(self.x + 5, self.y + 5, 
                             ((self.width - 20) / 3), (self.height / 2) - 20, 
                             self.play_normal, self.play_hover, action=self._play)
        self.buttons.append(self.play_button)


        # BOTON PAUSE
        self.pause_normal = self.gui.load_image("pause_off")
        self.pause_hover = self.gui.load_image("pause_on")
        ## VER POS X e Y CON EL REESCALADO Y EL RESPONSIVE
        self.pause_button = Button(self.x + ((self.width - 20) / 3) + 6, self.y + 5, 
                              ((self.width - 20) / 3), (self.height / 2) - 20, 
                              self.pause_normal, self.pause_hover, action=self._pause)
        self.buttons.append(self.pause_button)


        # BPM PANEL: ESTO DEBERIA HACERLO EN UN MODULO APARTE?
        # Porque por ahora no tiene botones, solo imprimo en pantalla el panel
        self.bpm_panel = self.gui.load_image("bpm_panel")
        self.bpm_panel_button = Button(self.x + 5, self.y + (self.height / 2) - 13, 
                                  self.play_button.width + self.pause_button.width, (self.height / 2) + 6, 
                                  self.bpm_panel, None, action=self._download_wav)  ## CAMBIAR Y ADAPTARLO A PANEL !!
        self.buttons.append(self.bpm_panel_button)


        # BOTON DOWNLOAD WAV
        self.download_wav = self.gui.load_image("download_wav")        
        ## VER POS X e Y CON EL REESCALADO Y EL RESPONSIVE
        self.download_wav_button = Button(self.x + 2*(((self.width - 20) / 3)) + 6, self.y + (self.height / 2) - 13, 
                                     ((self.width - 20) / 3), self.bpm_panel_button.height,
                                     self.download_wav, None, action=self._download_wav)
        self.buttons.append(self.download_wav_button)        

    
    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)


    def update(self):
        # DIBUJO CONTROL PANEL EN PANTALLA
        self.screen.blit(self.image, self.rect)
        # DIBUJO BOTONES DE CONTROL PANEL
        for button in self.buttons:
            button.update(self.screen)

    def _play(self):
        self.engine.start()
        

    def _pause(self):
        self.engine.stop()

    def _download_wav(self):
        pass'''