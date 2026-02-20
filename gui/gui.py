import pygame
import pygame_gui
import sys
import os
from resource_path import resource_path
from .toolbar import Toolbar
from .control_panel import ControlPanel
from .measure_panel import MeasurePanel
from .instruments_panel import InstrumentsPanel
from .grid_panel import GridPanel
from .footer_panel import FooterPanel
from .popup_manager import PopupManager

### PRUEBA DESPUES BORRAR
from core.audio_engine import AudioEngine

class DrumGUI:
    def __init__(self, engine, resolution):
        self.engine = engine        
        self.popup_manager = PopupManager(self)
        self.screen_width = resolution[0]
        self.screen_height = resolution[1]
        
        pygame.display.set_caption("Drum Wav Creator (pro sequencer)")
        # El UIManager debe tener las dimensiones de la ventana completa
        self.manager = pygame_gui.UIManager((self.screen_width, self.screen_height))

        self.clock = pygame.time.Clock()
        # self.font se usa en otros paneles para dibujar texto directamente
        self.font = pygame.font.SysFont('Arial', 20)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.NOFRAME)

        self.assets = {}
        self.panels = []

        # Este diccionario se actualizará con los valores de los inputs de beats y subdivs
        # Se inicializa aquí y se accede desde MeasurePanel y se actualiza en el bucle de eventos
        self.input_values = {'beats': '4', 'subdivisions': '4'}

        self.project_is_saved = True


    def load_image(self, name):
        img_path = os.path.join("assets", "images", f"{name}.png")
        img_full_path = resource_path(img_path)
        if name not in self.assets:
            try:                
                self.assets[name] = pygame.image.load(img_full_path).convert_alpha()
            except pygame.error as e:
                print(f'Error al cargar la imagen "{name}": {e}')
                
                return None

        return self.assets.get(name) # Usar .get para devolver None si la imagen no se cargó


    def create_panels(self):        

        ## TOOLBAR        
        self.toolbar = Toolbar(0, 0, self.screen, self)
        self.panels.append(self.toolbar)

        ## CONTROL PANEL        
        self.control_panel = ControlPanel(0, self.toolbar.height, self.screen, self.engine, self)
        self.panels.append(self.control_panel)

        ## MEASURE PANEL        
        self.measure_panel = MeasurePanel(self.screen_width * .25, self.toolbar.height, self.screen, self.engine, self)
        self.panels.append(self.measure_panel)

        ## INSTRUMENTS PANEL        
        self.instruments_panel = InstrumentsPanel(0, self.toolbar.height + self.control_panel.height, self.screen, self)
        self.panels.append(self.instruments_panel)

        ## GRID PANEL (Este SÍ usa pygame-gui UIManager para eventos, aunque el scroll sea manual)
        # Asegurarse de pasar el manager a GridPanel
        self.grid_panel = GridPanel(self.instruments_panel.width, self.toolbar.height + self.control_panel.height,
                                    self.screen, self.engine, self.manager, self)
        self.panels.append(self.grid_panel)

        ## FOOTER PANEL
        # Asumimos dibujado manual a menos que uses widgets de pygame-gui en él.
        self.footer_panel = FooterPanel(0,
                                        self.toolbar.height +
                                        self.control_panel.height +
                                        self.instruments_panel.height,
                                        self.screen, self)
        self.panels.append(self.footer_panel)

    def reset_project(self):
        self.engine.stop()

        # limpiar medidas
        self.engine.measures.clear()

        # crear medida inicial
        initial_beats = int(self.input_values['beats'])
        initial_subdiv = int(self.input_values['subdivisions'])
        self.engine.add_measure(initial_beats, initial_subdiv)

        # actualizar grid visual
        self.grid_panel._update_content_surface()

        self.project_is_saved = True

        if hasattr(self, "grid_panel"):
            self.grid_panel.clear_selection()

        if hasattr(self, "control_panel"):
            self.control_panel.is_playing = False

    def run(self):
        running = True        
        self.create_panels() # Crea todos los paneles al inicio        

        # --- Añadir la medida inicial aquí, después de crear los paneles y enlazar grid_panel al engine ---
        initial_beats = int(self.input_values['beats'])
        initial_subdiv = int(self.input_values['subdivisions'])
        self.engine.add_measure(initial_beats, initial_subdiv)

        self.grid_panel._update_content_surface()

        while running:
            time_delta = self.clock.tick(60)/1000.0 # Manejar el tiempo (60 FPS)

            # --- Bucle de Eventos ---
            for event in pygame.event.get():
                if self.popup_manager.has_active_popup():
                    self.popup_manager.handle_event(event)
                    continue

                if event.type == pygame.QUIT:
                    running = False
                    self.engine.stop() # Asegurarse de detener el audio al salir

                # 1. Pasar TODOS los eventos al UIManager primero
                # Esto permite que los elementos de pygame-gui respondan (clicks en botones, texto en inputs, scroll, etc.)
                self.manager.process_events(event)

                # --- 2. Manejar eventos específicos de pygame_gui que requieren lógica central de la GUI ---
                # Capturar cambios en los inputs de beats y subdivisions y actualizar self.input_values
                if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
                    # Verificar si el evento proviene del input de beats usando su object_id
                    if event.ui_element.get_object_ids()[-1] == '#beats_input': # Comparamos con el último object_id
                        self.input_values['beats'] = event.text # Capturar el nuevo texto del input
                      

                    # Verificar si el evento proviene del input de subdivisions usando su object_id
                    elif event.ui_element.get_object_ids()[-1] == '#subdiv_input': # Comparamos con el último object_id
                        self.input_values['subdivisions'] = event.text # Capturar el nuevo texto del input                      

                # 3. Manejar eventos de Pygame "puros" o eventos para tus widgets personalizados
                # Pasamos el evento a cada panel para que maneje sus propios elementos no-pygame_gui
                
                # Primero el grid (porque modifica selección)
                if hasattr(self.grid_panel, 'handle_event'):
                    self.grid_panel.handle_event(event)
                
                for panel in self.panels:
                    if panel is self.grid_panel:
                        continue                     
                    if hasattr(panel, 'handle_event'):
                        panel.handle_event(event)

            if not self.popup_manager.has_active_popup():
                # --- Fase de Actualización ---
                # Actualizar el estado del UIManager y sus elementos (posiciones, scroll interno de pygame-gui si aún se usara, etc.)
                self.manager.update(time_delta)
                # Si otros paneles tuvieran lógica de update manual (no de dibujado), se llamarían aquí.

            # --- Fase de Dibujado ---
            # Esta sección redibuja la pantalla en cada frame            
            self.screen.fill((60, 60, 60)) # Limpiar la pantalla con un color de fondo
            
            # --- DIBUJAR CADA PANEL LLAMANDO A draw() O update() SI draw() NO EXISTE ---
            # Itera sobre la lista de paneles y llama a su método de dibujo manual.
            # GridPanel tiene draw(), otros paneles como Toolbar/ControlPanel tienen update() que dibuja.
            for panel in self.panels:
                if hasattr(panel, 'draw'):
                    # Si el panel tiene un método draw dedicado (como GridPanel)
                    panel.draw(self.screen)
                if hasattr(panel, 'update'):                    
                    # Si el panel dibuja dentro de su método update (como Toolbar, ControlPanel)
                    # Asumimos que update() dibuja directamente a self.screen que guarda el panel.
                    panel.update() # <-- Llamar a update() para dibujar
            
            # 2. Dibujar todos los elementos de pygame-gui
            # Esto dibujará los botones, inputs, paneles UIPanel, etc., que son gestionados por el manager.
            # Se dibujan ENCIMA de lo que dibujaste manualmente en el paso anterior.
            self.manager.draw_ui(self.screen)
            
            self.popup_manager.draw(self.screen)

            # 3. Actualizar la pantalla completa de Pygame para mostrar todo lo dibujado
            pygame.display.update()

        # Al salir del bucle, limpia Pygame
        pygame.quit()
        sys.exit()


# La llamada a gui.run() en main.py inicia el bucle principal.
# El resto del código en main.py después de gui.run() no se ejecutará hasta que gui.run() termine.