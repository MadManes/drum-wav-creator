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

        # --- Estado de reproducción ---
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


        # BOTON POWER (EXIT)
        self.power_normal = self.gui.load_image("power_off")
        self.power_hover = self.gui.load_image("power_on")

        power_button_x = self.pause_button.rect.right + 6  # pequeño espacio fijo
        power_button_y = button_y

        self.power_button = Button(
            power_button_x,
            power_button_y,
            play_pause_button_width,
            play_pause_button_height,
            self.power_normal,
            self.power_hover,
            action=self._exit_program
        )

        self.buttons.append(self.power_button)


        # BPM PANEL (Si es un botn visual, lo mantenemos aqu. Si solo es grfico, podra dibujarse directamente)
        # Cargar imagen para el panel BPM
        self.bpm_panel_image = self.gui.load_image("bpm_panel") # Renombrado para claridad
        
        # ==========================
        # BPM PANEL (ANCHO EXACTO)
        # ==========================

        bpm_panel_x = self.play_button.rect.left
        bpm_panel_y = self.y + (self.height / 2) - 13

        # Distancia REAL entre play.left y pause.right
        bpm_panel_width = self.pause_button.rect.right - self.play_button.rect.left

        bpm_panel_height = (self.height / 2) + 6

        self.bpm_panel_button = Button(
            bpm_panel_x,
            bpm_panel_y,
            bpm_panel_width,
            bpm_panel_height,
            self.bpm_panel_image,
            None,
            action=None
        )

        self.buttons.append(self.bpm_panel_button)        

        panel_rect = self.bpm_panel_button.rect

        # Rect negro donde va el número
        self.bpm_value_rect = pygame.Rect(
            panel_rect.x + panel_rect.width * 0.06,
            panel_rect.y + panel_rect.height * 0.38,
            panel_rect.width * 0.6,
            panel_rect.height * 0.56
        )

        panel_rect = self.bpm_panel_button.rect

        arrow_area_x = panel_rect.x + panel_rect.width * 0.6402
        arrow_area_width = panel_rect.width * 0.22
        
        arrow_width = arrow_area_width * 0.65
        arrow_height = panel_rect.height * 0.55
        
        arrow_x = arrow_area_x + (arrow_area_width - arrow_width) / 2
        
        # FLECHA UP
        self.bpm_up_rect = pygame.Rect(
            arrow_x,
            panel_rect.y + panel_rect.height * 0.18,
            arrow_width,
            arrow_height
        )
        
        # FLECHA DOWN
        self.bpm_down_rect = pygame.Rect(
            arrow_x,
            panel_rect.y + panel_rect.height * 0.58,
            arrow_width,
            arrow_height
        )

        # BOTON DOWNLOAD WAV
        # Cargar imagen para el botn Download
        self.download_wav_image = self.gui.load_image("download_wav") # Renombrado para claridad
        # Crear instancia del botn Download
        # --- Ajuste de tamaño y posicin del botn Download ---
        # Usamos los clculos y offsets de tu cdigo original
        download_button_x = self.power_button.rect.x
        download_button_width = self.power_button.rect.width
        download_button_height = self.bpm_panel_button.rect.height
        download_button_y = bpm_panel_y
        self.download_wav_button = Button(
            download_button_x,
            download_button_y,
            download_button_width,
            download_button_height,
            self.download_wav_image,
            None,
            action=self._download_wav
        )
        self.buttons.append(self.download_wav_button) # Añadir a la lista de botones

    
    def _exit_program(self):
        pygame.quit()
        exit()


    def handle_event(self, event):
        # Pasar el evento a cada botn. Button.handle_event actualizar is_hovered y ejecutar la accin al click.
        for button in self.buttons:
             button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.bpm_up_rect.collidepoint(event.pos):
                self.engine.bpm += 1

            if self.bpm_down_rect.collidepoint(event.pos):
                if self.engine.bpm > 20:
                    self.engine.bpm -= 1


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

        # Solo dibujar si existe el panel
        if hasattr(self, "bpm_panel_button"):
        
            # Número BPM
            font_size = int(self.bpm_value_rect.height * 0.8)
            bpm_font = pygame.font.SysFont("arial", font_size)
            bpm_text = bpm_font.render(f"{self.engine.bpm}", True, (0, 255, 255))
            bpm_text_rect = bpm_text.get_rect(center=self.bpm_value_rect.center)
            self.screen.blit(bpm_text, bpm_text_rect)
            # Flecha UP
            #pygame.draw.rect(self.screen, (60, 60, 60), self.bpm_up_rect, border_radius=4)
            up_text = bpm_font.render("▲", True, (255, 255, 255))
            self.screen.blit(up_text, up_text.get_rect(center=self.bpm_up_rect.center))
            # Flecha DOWN
            #pygame.draw.rect(self.screen, (60, 60, 60), self.bpm_down_rect, border_radius=4)
            down_text = bpm_font.render("▼", True, (255, 255, 255))
            self.screen.blit(down_text, down_text.get_rect(center=self.bpm_down_rect.center))
        
        self.is_playing = self.engine.is_playing()


    def _play(self):
        # Solo iniciar si no est reproduciendo ya
        if not self.engine.is_playing(): # Usar el estado del engine como fuente de verdad            
            self.engine.start()
            self.is_playing = True # Actualizar el estado local


    def _pause(self):
        # Solo detener si est reproduciendo
        if self.engine.is_playing(): # Usar el estado del engine como fuente de verdad            
            self.engine.stop()
            self.is_playing = False # Actualizar el estado local


    def _download_wav(self):
        os.makedirs("exports", exist_ok=True)

        filename = os.path.join("exports", "export.wav")

        try:
            self.engine.export(filename)
            print(f"WAV exportado correctamente en: {filename}")
        except Exception as e:
            print(f"Error al exportar WAV: {e}")


