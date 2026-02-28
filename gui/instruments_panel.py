import pygame

DIVIDER_COLOR = (255, 105, 180)  # estilo rosa como tu prueba
TEXT_COLOR = (200, 200, 200)

class InstrumentsPanel:
    def __init__(self, x, y, screen, gui, layout):
        self.x = x
        self.y = y
        self.screen = screen
        self.gui = gui
        self.layout = layout

        self.image = self.gui.load_image("inst_background")

        self.width = int(screen.get_width() * 0.125)
        self.height = int(screen.get_height() * 0.68)

        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

        # Si no pasan instrumentos, usar default        
        self.instruments = [
            "Crash 1",
            "Crash 2",
            "Cowbell",
            "Hi-Hat",
            "H-Tom",
            "Snare",
            "L-Tom",
            "Kick",
            "Closed Hi-Hat"
        ]
        
    # ---------------------------------------------------

    def update(self):
        self.screen.blit(self.image, self.rect)
        
        instrument_count = len(self.instruments)

        if instrument_count == 0:
            return

        header_height = self.layout.header_height
        drawable_height = (
            self.layout.content_height 
            - header_height
            - self.layout.bottom_space
        )

        row_height = drawable_height // instrument_count

        font_size = int(row_height * 0.4)
        font = pygame.font.SysFont("arial", font_size)

        for i, name in enumerate(self.instruments):

            row_y = self.y + header_height + i * row_height

            row_rect = pygame.Rect(
                self.x,
                int(row_y),
                self.width,
                int(row_height)
            )

            # Línea divisoria EXACTAMENTE alineada
            pygame.draw.line(
                self.screen,
                (255,105,180),
                (row_rect.left, row_rect.top),
                (row_rect.right, row_rect.top),
                2
            )            

            text_surface = font.render(name, True, (200,200,200))
            text_rect = text_surface.get_rect(
                midleft=(self.x + 10, row_rect.centery)
            )

            self.screen.blit(text_surface, text_rect)