import pygame
from core.audio_engine import AudioEngine
import engine.sound_loader as sl
import engine.video_resolution as vr
from gui.gui import DrumGUI


if __name__ == "__main__":    
    pygame.init()
    sounds = sl.load_instruments()   # Cargo instrumentos
    engine = AudioEngine(sounds)     # creo engine pasando sonidos    
    resolution = vr.get_resolution()
    gui = DrumGUI(engine, resolution)    
    gui.run()    
    pygame.quit()