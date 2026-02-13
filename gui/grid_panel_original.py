import pygame
import pygame_gui
from .button import Button

class GridPanel:
    def __init__(self,x, y, screen, engine, manager, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine
        self.manager = manager
        self.gui = gui
        
        self.image = self.gui.load_image("grid_background.png")        
        self.width = screen.get_width() - x
        self.height = screen.get_height() * .68
        self.image = pygame.transform.scale(self.image, (self.width, self.height)) ## IDEM RESPONSIVE!!!
        self.rect = self.image.get_rect(topleft=(self.x, self.y))        
        
        self.scrolling_container = pygame_gui.elements.UIScrollingContainer(relative_rect=self.rect, manager=self.manager)
                
        self.measure_width = self.width * 0.7
        self.measure_header_height = self.height * .08

        self.buttons = []
        self._create_buttons()

    #AGREGAR TODAS ESAS LINEAS DESPUES PARA LOS POPUPS
    #def draw_grid(self):
        #if self.is_save_popup_visible or self.is_load_popup_visible: # Si popup visible, oscurecer grid
        #    surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA) # Superficie transparente
        #    surface.fill((0, 0, 0, 150)) # Relleno negro semi-transparente
        #    self.screen.blit(surface, (0, 0)) # Dibujar encima de la pantalla
#
        #if not self.is_save_popup_visible and not self.is_load_popup_visible: # Dibujar grid solo si no hay popup
        #    x_base = self.left_panel_width - self.scroll_x
        #    y_start = 80
        #    self.measure_grid = []
        #    self.total_grid_width = len(self.engine.measures) * self.measure_width
        #    visible_width = self.screen.get_width() - self.left_panel_width
        #    self.max_scroll_x = max(0, self.total_grid_width - visible_width)

    def draw_grid(self):
        x_base = self.x 
        y_start = self.y + self.measure_header_height
        self.measure_grid = []
        self.total_grid_width = len(self.engine.measures) * self.measure_width
        visible_width = self.screen.get_width() - self.x
        self.max_scroll_x = max(0, self.total_grid_width - visible_width)
        for measure_idx, measure in enumerate(self.engine.measures):
            x = x_base + (measure_idx * self.measure_width)
            current_beats = measure['length']
            if x + self.measure_width > self.x and x < self.screen.get_width():
                # Rect de compas (sin cambios)
                #measure_rect = pygame.draw.rect(self.screen, (50, 50, 50), (x, y_start, self.measure_width, 400), 1)
                #border_color = (100, 100, 100) if measure_idx not in self.selected_measures else (255, 0, 0)
                #pygame.draw.rect(self.screen, border_color, measure_rect, 2)
                ## Rect de solapa (sin cambios)
                #tab_rect = pygame.Rect(x, y_start - 30, 50, 25)
                #pygame.draw.rect(self.screen, (100, 100, 100), tab_rect)
                #text = self.font.render(str(measure_idx + 1), True, (255, 255, 255))
                #self.screen.blit(text, (x + 5, y_start - 25))
                beat_width = self.measure_width / current_beats
                for beat_idx in range(current_beats):
                    current_subdiv = len(self.engine.patterns['snare'][measure_idx][beat_idx])
                    subdiv_width = beat_width / current_subdiv
                    for subdiv_idx in range(current_subdiv):
                        x_pos = int(round(x + (beat_idx * beat_width) + (subdiv_idx * subdiv_width)))
                        for inst_idx, inst in enumerate(self.engine.patterns):
                            if (measure_idx < len(self.engine.patterns[inst]) and
                                beat_idx < len(self.engine.patterns[inst][measure_idx]) and
                                subdiv_idx < len(self.engine.patterns[inst][measure_idx][beat_idx])):
                                state = self.engine.patterns[inst][measure_idx][beat_idx][subdiv_idx]
                                cell_width = int(round(subdiv_width)) - 1
                                rect = pygame.Rect(
                                    x_pos,
                                    y_start + inst_idx * ((self.height - self.measure_header_height) / 9),    ## height/9 era INSTRUMENT HEIGHT
                                    cell_width,
                                    (self.height - self.measure_header_height) / 9   ## IGUAL ERA.....
                                )
                                self.measure_grid.append((rect, (measure_idx, beat_idx, subdiv_idx, inst)))
                                color = (255, 0, 0) if state else (200, 200, 200) if subdiv_idx != 0 else (150,150,150)
                                pygame.draw.rect(self.screen, color, rect)
        

    def _create_buttons(self):
        pass
        ## BOTON PLAY
        #play_normal = self.gui.load_image("play_off.png")
        #play_hover = self.gui.load_image("play_on.png")
        ### VER POS X e Y CON EL REESCALADO Y EL RESPONSIVE
        #play_button = Button(5, self.y + 5, 
        #                     ((self.width - 20) / 3), (self.height / 2) - 20, 
        #                     play_normal, play_hover, action=self._play)
        #self.buttons.append(play_button)
#
        ## BOTON PAUSE
        #pause_normal = self.gui.load_image("pause_off.png")
        #pause_hover = self.gui.load_image("pause_on.png")
        ### VER POS X e Y CON EL REESCALADO Y EL RESPONSIVE
        #pause_button = Button(((self.width - 20) / 3) + 11, self.y + 5, 
        #                      ((self.width - 20) / 3), (self.height / 2) - 20, 
        #                      pause_normal, pause_hover, action=self._pause)
        #self.buttons.append(pause_button)
#
        ## BOTON DOWNLOAD WAV
        #download_wav = self.gui.load_image("download_wav.png")        
        ### VER POS X e Y CON EL REESCALADO Y EL RESPONSIVE
        #download_wav_button = Button(2 * ((self.width - 20) / 3) + 15, self.y + (self.height / 2) - 10, 
        #                             ((self.width - 20) / 3), (self.height / 2) + 6,
        #                             download_wav, None, action=self._download_wav)
        #self.buttons.append(download_wav_button)
#
        ## BPM PANEL: ESTO DEBERIA HACERLO EN UN MODULO APARTE?
        ## Porque por ahora no tiene botones, solo imprimo en pantalla el panel
        #bpm_panel = self.gui.load_image("bpm_panel.png")
        #bpm_panel_button = Button(4, self.y + (self.height / 2) - 10, 
        #                          (2 * (self.width - 20) / 3) + 7, (self.height / 2) + 6, 
        #                          bpm_panel, None, action=self._download_wav)  ## CAMBIAR Y ADAPTARLO A PANEL !!
        #self.buttons.append(bpm_panel_button)

    
    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:        
            for rect, data in self.measure_grid:
                if rect.collidepoint(pygame.mouse.get_pos()):
                    measure_idx, beat, subdiv_idx, inst = data
                    current = self.engine.patterns[inst][measure_idx][beat][subdiv_idx]
                    self.engine.update_pattern(inst, measure_idx, beat, subdiv_idx, 0 if current else 1)

    def update(self):
        # DIBUJO CONTROL PANEL EN PANTALLA
        self.screen.blit(self.image, self.rect)
        # DIBUJO BOTONES DE CONTROL PANEL
        self.draw_grid()
        #for button in self.buttons:
        #    button.update(self.screen)
        


    