import pygame


class BasePopup:

    SIZES = {
        "small_menu": (300, 400),
        "small_alert": (400, 200),
        "confirm_new_project": (450, 220),
        "medium": (500, 400),
        "large": (900, 700)
    }

    def __init__(self, gui, size_type="medium"):
        self.gui = gui
        self.screen = gui.screen

        self.width, self.height = self.SIZES[size_type]

        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        self.rect = pygame.Rect(
            (self.screen_width - self.width) // 2,
            (self.screen_height - self.height) // 2,
            self.width,
            self.height
        )

        self.background_color = (60, 60, 60)
        self.border_color = (100, 100, 100)

        self.overlay = pygame.Surface((self.screen_width, self.screen_height))
        self.overlay.set_alpha(150)
        self.overlay.fill((0, 0, 0))

        # Botón cerrar
        self.close_image = gui.load_image("close_button_off")
        self.close_hover = gui.load_image("close_button_on")

        self.close_size = 24
        self.close_rect = pygame.Rect(
            self.rect.right - self.close_size - 10,
            self.rect.top + 10,
            self.close_size,
            self.close_size
        )

        self.is_close_hovered = False

        self.active = True

    # ------------------------

    def handle_event(self, event):

        if event.type == pygame.MOUSEMOTION:
            self.is_close_hovered = self.close_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                self.close()

    # ------------------------

    def draw(self):

        # Oscurecer fondo
        self.screen.blit(self.overlay, (0, 0))

        # Fondo popup
        pygame.draw.rect(self.screen, self.background_color, self.rect)
        pygame.draw.rect(self.screen, self.border_color, self.rect, 2)

        # Dibujar X
        image = self.close_hover if self.is_close_hovered else self.close_image
        image_scaled = pygame.transform.scale(image, (self.close_size, self.close_size))
        self.screen.blit(image_scaled, self.close_rect)

    # ------------------------

    def close(self):
        self.active = False
        self.gui.popup_manager.clear_popup()


class SmallMenuPopup(BasePopup):

    def __init__(self, gui):
        super().__init__(gui, "small_menu")

        self.font = pygame.font.SysFont("arial", 18)

        self.options = [
            "New Project",
            "Load Project",
            "Save Project As...",
            "Save Project"
        ]

        self.option_rects = []
        self.hover_index = None

        start_y = self.rect.top + 60
        spacing = 50

        for i in range(len(self.options)):
            rect = pygame.Rect(
                self.rect.left + 40,
                start_y + i * spacing,
                self.rect.width - 80,
                35
            )
            self.option_rects.append(rect)

    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.MOUSEMOTION:
            self.hover_index = None
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.hover_index = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self._handle_option(i)

    def _handle_option(self, index):

        if index == 0:
            self.close()

            if self.gui.project_is_saved:
                self.gui.reset_project()
            else:
                from .popups import ConfirmNewProjectPopup
                confirm_popup = ConfirmNewProjectPopup(self.gui)
                self.gui.popup_manager.open_popup(confirm_popup)

        elif index == 1:
            self.close()
            if self.gui.project_is_saved:                
                self.gui.load_project()
            else:
                from .popups import ConfirmLoadProjectPopup
                confirm_popup = ConfirmLoadProjectPopup(self.gui)
                self.gui.popup_manager.open_popup(confirm_popup)

        elif index == 2:
            self.close()
            self.gui.save_project_as()

        elif index == 3:  # Save Project
            self.close()
            self.gui.save_project()

    def draw(self):
        super().draw()

        for i, rect in enumerate(self.option_rects):

            color = (120, 120, 120) if i == self.hover_index else (80, 80, 80)

            pygame.draw.rect(self.screen, color, rect, border_radius=4)

            text_surface = self.font.render(self.options[i], True, (240, 240, 240))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)   


class ConfirmNewProjectPopup(BasePopup):

    def __init__(self, gui):
        super().__init__(gui, "confirm_new_project")

        self.font = pygame.font.SysFont("arial", 20)

        self.message = "Do you want to save before creating a new project?"

        self.yes_rect = pygame.Rect(
            self.rect.centerx - 90,
            self.rect.bottom - 70,
            80,
            35
        )

        self.no_rect = pygame.Rect(
            self.rect.centerx + 10,
            self.rect.bottom - 70,
            80,
            35
        )

        self.hover_yes = False
        self.hover_no = False

    def draw(self):
        # Dibujar fondo base del popup
        super().draw()

        mouse_pos = pygame.mouse.get_pos()

        self.hover_yes = self.yes_rect.collidepoint(mouse_pos)
        self.hover_no = self.no_rect.collidepoint(mouse_pos)

        # --- Mensaje ---
        text_surface = self.font.render(self.message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
        self.screen.blit(text_surface, text_rect)

        # --- Botón YES ---
        yes_color = (70, 70, 70) if not self.hover_yes else (100, 100, 100)
        pygame.draw.rect(self.screen, yes_color, self.yes_rect, border_radius=6)

        yes_text = self.font.render("Yes", True, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=self.yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)

        # --- Botón NO ---
        no_color = (70, 70, 70) if not self.hover_no else (100, 100, 100)
        pygame.draw.rect(self.screen, no_color, self.no_rect, border_radius=6)

        no_text = self.font.render("No", True, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=self.no_rect.center)
        self.screen.blit(no_text, no_text_rect)


    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.MOUSEMOTION:
            self.hover_yes = self.yes_rect.collidepoint(event.pos)
            self.hover_no = self.no_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # YES (primero save) -> luego crear nuevo proyecto
            if self.yes_rect.collidepoint(event.pos):                
                self.gui.save_project()
                self.gui.reset_project()
                self.close()

            # NO → crear nuevo proyecto
            if self.no_rect.collidepoint(event.pos):
                self.gui.reset_project()
                self.close()

class ConfirmLoadProjectPopup(BasePopup):

    def __init__(self, gui):
        super().__init__(gui, "confirm_new_project")  # reutilizamos tamaño

        self.font = pygame.font.SysFont("arial", 20)

        self.message = "Do you want to save before loading another project?"

        self.yes_rect = pygame.Rect(
            self.rect.centerx - 90,
            self.rect.bottom - 70,
            80,
            35
        )

        self.no_rect = pygame.Rect(
            self.rect.centerx + 10,
            self.rect.bottom - 70,
            80,
            35
        )

        self.hover_yes = False
        self.hover_no = False

    def draw(self):
        super().draw()

        mouse_pos = pygame.mouse.get_pos()

        self.hover_yes = self.yes_rect.collidepoint(mouse_pos)
        self.hover_no = self.no_rect.collidepoint(mouse_pos)

        # --- Mensaje ---
        text_surface = self.font.render(self.message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
        self.screen.blit(text_surface, text_rect)

        # --- YES ---
        yes_color = (70, 70, 70) if not self.hover_yes else (100, 100, 100)
        pygame.draw.rect(self.screen, yes_color, self.yes_rect, border_radius=6)

        yes_text = self.font.render("Yes", True, (255, 255, 255))
        self.screen.blit(yes_text, yes_text.get_rect(center=self.yes_rect.center))

        # --- NO ---
        no_color = (70, 70, 70) if not self.hover_no else (100, 100, 100)
        pygame.draw.rect(self.screen, no_color, self.no_rect, border_radius=6)

        no_text = self.font.render("No", True, (255, 255, 255))
        self.screen.blit(no_text, no_text.get_rect(center=self.no_rect.center))

    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # YES → guardar como... primero, luego cargar
            if self.yes_rect.collidepoint(event.pos):
                self.gui.save_project_as()
                self.gui.load_project()
                self.close()

            # NO → cargar directamente
            if self.no_rect.collidepoint(event.pos):
                self.gui.load_project()
                self.close()
