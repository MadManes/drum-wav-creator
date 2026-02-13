import pygame
from .button import Button

class InstrumentsPanel:
    def __init__(self,x, y, screen, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.gui = gui
        self.image = self.gui.load_image("inst_background")        
        self.width = screen.get_width() * .125
        self.height = screen.get_height() * .68
        self.image = pygame.transform.scale(self.image, (self.width, self.height)) ## IDEM RESPONSIVE!!!
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        pass

    def update(self):
        # DIBUJO CONTROL PANEL EN PANTALLA
        self.screen.blit(self.image, self.rect)
        # DIBUJO BOTONES DE CONTROL PANEL
        #for button in self.buttons:
        #    button.update(self.screen)

    def _play(self):
        pass

    def _pause(self):
        pass