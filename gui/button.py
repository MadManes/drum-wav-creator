import pygame

class Button:
    def __init__(self, x, y, width, height, normal_image, hover_image=None, action=None):
        self.width = int(width) # Asegurar que las dimensiones son enteros para scale
        self.height = int(height)

        # --- MODIFICACIN CLAVE AQU: Escalar AMBAS imgenes en __init__ ---
        # Asegurar que las imgenes normal y hover existen antes de escalar
        if normal_image:
            self.normal_image_scaled = pygame.transform.scale(normal_image, (self.width, self.height))
        else:
            # Si la imagen normal no existe, crear una superficie vaca o manejar el error
            print(f"ADVERTENCIA: Imagen normal no proporcionada para botón en ({x}, {y})")
            self.normal_image_scaled = pygame.Surface((self.width, self.height), pygame.SRCALPHA) # Superficie transparente

        if hover_image:
            self.hover_image_scaled = pygame.transform.scale(hover_image, (self.width, self.height))
        else:
            # Si no hay imagen de hover, usar la imagen normal escalada
            self.hover_image_scaled = self.normal_image_scaled


        # La imagen actual que se dibujar. ControlPanel la establecer.
        self.image = self.normal_image_scaled

        # El rectngulo se basa en la imagen escalada
        self.rect = self.image.get_rect(topleft=(x, y))

        self.action = action
        self.is_hovered = False # Estado de hover, actualizado por handle_event

    def handle_event(self, event):
        # --- MODIFICACIN CLAVE AQU: Eliminar reescalado en handle_event ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos) and self.action: # event.button == 1 para clic izquierdo
                 self.action()
                 # No cambiar la imagen aqu, ControlPanel lo har en update

        elif event.type == pygame.MOUSEMOTION:
            # --- MODIFICACIN CLAVE AQU: Solo actualizar el estado is_hovered ---
            self.is_hovered = self.rect.collidepoint(event.pos)
            # No cambiar la imagen aqu, ControlPanel lo har en update


    def update(self, surface):
        # --- MODIFICACIN CLAVE AQU: Simplemente dibujar la imagen actual (ya establecida por ControlPanel) ---
        surface.blit(self.image, self.rect)

