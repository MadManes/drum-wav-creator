class PopupManager:

    def __init__(self, gui):
        self.gui = gui
        self.active_popup = None

    def open_popup(self, popup):
        self.active_popup = popup
        # Pausa global
        if self.gui.engine.is_playing():
            self.gui.engine.stop()
        # Estado visual
        if hasattr(self.gui, "control_panel"):
            self.gui.control_panel.is_playing = False
        if hasattr(self.gui, "toolbar"):
            self.gui.toolbar.menu_mode_active = False
            self.gui.toolbar._update_button_visibility()

    def clear_popup(self):
        self.active_popup = None

    def has_active_popup(self):
        return self.active_popup is not None

    def handle_event(self, event):
        if self.active_popup:
            self.active_popup.handle_event(event)

    def draw(self, screen):
        if self.active_popup:
            self.active_popup.draw()
