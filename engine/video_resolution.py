import pygame

# Lista de resoluciones soportadas
SUPPORTED_RESOLUTIONS = [(800, 600), (832, 624), (1024, 768), (1152, 872),
                         (1280, 720), (1280, 1024), (1360, 768), (1920, 1080)] #, (1280, 1024)]
DEFAULT_RESOLUTION = (1920, 1080)

def get_closest_resolution(available_resolution):
    """Encuentra la resolución soportada más cercana a la disponible."""
    best_match = DEFAULT_RESOLUTION
    min_distance_squared = float('inf')

    for supported in SUPPORTED_RESOLUTIONS:
        distance_squared = (available_resolution[0] - supported[0])**2 + (available_resolution[1] - supported[1])**2
        if distance_squared < min_distance_squared:
            min_distance_squared = distance_squared
            best_match = supported
        elif distance_squared == min_distance_squared:
            if supported == DEFAULT_RESOLUTION:
                best_match = DEFAULT_RESOLUTION

    print(f'\nLa resolucion mas cercana es: {best_match}')
    return best_match

def get_resolution():
    # Obtener la resolución disponible
    info = pygame.display.Info()
    available_resolution = (info.current_w, info.current_h)
    print(f"Resolución disponible: {available_resolution}")

    # Determinar la resolución a usar
    if available_resolution in SUPPORTED_RESOLUTIONS:
        current_resolution = available_resolution
    else:
        current_resolution = get_closest_resolution(available_resolution)
        print(f"Resolución no soportada. Usando la más cercana: {current_resolution}")
    ## PRUEBA
    #DEFAULT_RESOLUTION = SUPPORTED_RESOLUTIONS[0]

    return current_resolution



