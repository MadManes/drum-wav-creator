import soundfile as sf
import librosa
import numpy as np
import os
from resource_path import resource_path

SAMPLE_RATE = 44100  ## Ya lo estoy usando en un par de lugares, deberia tenerlo en un modulo constants?

# Cargar sonidos
def load_sound(file, volume=1.0):

    sound_path = os.path.join("assets", "sounds", f"{file}.wav") # Asume que tus sonidos estn en 'assets/sounds'
#     try:
#         data, samplerate = sf.read(sound_path, dtype='float32')
#         # soundfile lee como (frames, channels) para stereo, (frames,) para mono.
#         # Necesitas asegurarte de que todos tus clips sean consistentes (ej. siempre stereo)
#         if len(data.shape) == 1:
#             data = np.column_stack((data, data)) # Convertir mono a stereo duplicando canal
#         elif data.shape[1] > 2:
#              data = data[:, :2] # Tomar solo los primeros 2 canales si tiene ms
#         return data # Retorna el array de numpy
#     except FileNotFoundError:
#         print(f"Advertencia: Archivo de sonido no encontrado: {sound_path}")
#         # Retornar un array vaco o sonido de error
#         return np.zeros((100, self.CHANNELS), dtype=np.float32) # Ejemplo: sonido mudo corto
    
    # Usa resource_path para obtener la ruta correcta, ya sea en desarrollo o empaquetado
    sound_full_path = resource_path(sound_path)

    try:
        data, sr = sf.read(sound_full_path, dtype='float32')
        if sr != SAMPLE_RATE:
            data = librosa.resample(data, orig_sr=sr, target_sr=SAMPLE_RATE)
        if data.ndim == 1:
            data = np.column_stack((data, data))

        final_data = data * volume

        return final_data
    
    except FileNotFoundError:
        print(f'Advertencia: Archivo de sonido no encontrado_ {sound_path}')

        # Retornar un array vaco o sonido de error
        return np.zeros((100, 2), dtype=np.float32) # Ejemplo: sonido mudo corto, el 2 es por los dos canales
    except Exception as e: # Capturar otros posibles errores de soundfile (archivos corruptos, etc.)
        print(f'Error al leer o procesar el archivo de sonido {sound_full_path}: {e}')
        return np.zeros((SAMPLE_RATE, 2), dtype=np.float32)

# Cargar instrumentos y sus ganancias o volumenes y podrian ser mas cosas...

def load_instruments():
    sounds = {
        'crash 1': load_sound('crash_1', 0.5),
        'crash 2': load_sound('crash_2', 0.7),
        'cowbell': load_sound('cowbell', 0.8),
        'Op. hihat': load_sound('op_hihat', 0.5),
        'H. tom': load_sound('h_tom', 1.4),
        'snare': load_sound('snare', 1.3),
        'F. tom': load_sound('f_tom', 1.5),
        'kick': load_sound('kick', 1.5),
        'F. hihat': load_sound('f_hihat', 0.8)
    }

    print("\n CARGADO INSTRUMENTOS")

    return sounds

#def load_instruments():
#    sounds = {
#        'crash 1': load_sound('assets/sounds/crash_1.wav', 0.5),
#        'crash 2': load_sound('assets/sounds/crash_2.wav', 0.7),
#        'cowbell': load_sound('assets/sounds/cowbell.wav', 0.8),
#        'Op. hihat': load_sound('assets/sounds/op_hihat.wav', 0.5),
#        'H. tom': load_sound('assets/sounds/h_tom.wav', 1.4),
#        'snare': load_sound('assets/sounds/snare.wav', 1.3),
#        'F. tom': load_sound('assets/sounds/f_tom.wav', 1.5),
#        'kick': load_sound('assets/sounds/kick.wav', 1.5),
#        'F. hihat': load_sound('assets/sounds/f_hihat.wav', 0.8)
#    }
#
#    print("\n CARGADO INSTRUMENTOS")
#
#    return sounds