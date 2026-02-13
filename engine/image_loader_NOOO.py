#### YA NO NECESITO ESTE MODULO EN ESTA VERSION. NO SE ESTA USANDO EN EL CODIGO

import pygame

def load_images():
    # EJEMPLO SOLO PARA TOOLBAR. DESPUES RESOLVER COMO CARGAR ABSOLUTAMENTE TODOO
    try:
        image = pygame.image.load("assets/images/toolbar/toolbar_2.png")
        width = image.get_width() // 3   ## VER LO DE RESPONSIVE!!
        height = image.get_height() // 3
        image = pygame.transform.scale(image, (width, height))
        rect = image.get_rect(topleft=(0, 0))
    except pygame.error as e:
        print(f'Error al cargar la imagen de toolbar: {e}')

    return image, rect