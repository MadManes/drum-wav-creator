import pygame
from .button import Button

class MeasurePanel:
    def __init__(self,x, y, screen, engine, gui):
        self.x = x
        self.y = y
        self.screen = screen
        self.engine = engine        
        self.gui = gui
        self.image = self.gui.load_image("cp_background.png")        
        self.width = screen.get_width() * .75
        self.height = screen.get_height() * .18
        self.image = pygame.transform.scale(self.image, (self.width, self.height)) ## IDEM RESPONSIVE!!!
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):               
        # BOTON ADD
        add_normal = self.gui.load_image("add_button.png")        
        
        add_button = Button(self.x + 25, self.y + 25, 
                            90, 90, 
                            add_normal, None, action=self._add_measure)
        self.buttons.append(add_button)

        # BOTON DEL
        del_normal = self.gui.load_image("del_button.png")

        del_button = Button(self.x + 165, self.y + 25, 
                            90, 90, 
                            del_normal, None, action=self._pause)
        self.buttons.append(del_button)     
        

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)
            

    def update(self):
        # DIBUJO CONTROL PANEL EN PANTALLA
        self.screen.blit(self.image, self.rect)
        # DIBUJO BOTONES DE CONTROL PANEL
        for button in self.buttons:
            button.update(self.screen)

    def _add_measure(self):
        print('PRESIONADO +')
        self.engine.add_measure()        

    def _pause(self):
        pass

    