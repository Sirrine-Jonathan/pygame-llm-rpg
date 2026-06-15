import math
import struct
import random
import pygame

# Initialize sound system status
_mixer_enabled = False

def init_sound():
    global _mixer_enabled
    try:
        # Initialize mixer: 22050Hz, 16-bit, mono
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        _mixer_enabled = True
    except Exception as e:
        print(f"Warning: Could not initialize sound mixer: {e}. Running in silent mode.")
        _mixer_enabled = False

def generate_sound(wave_type="sine", freq_start=440.0, freq_end=440.0, duration=0.1, volume=0.3):
    if not _mixer_enabled:
        return None
    
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        # Linear frequency interpolation for sweeps (chirps)
        freq = freq_start + (freq_end - freq_start) * (i / num_samples)
        
        # Generate wave shape
        if wave_type == "sine":
            val = math.sin(2 * math.pi * freq * t)
        elif wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif wave_type == "triangle":
            val = 2.0 * abs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
        elif wave_type == "sawtooth":
            val = 2.0 * (t * freq - math.floor(t * freq + 0.5))
        elif wave_type == "noise":
            val = random.uniform(-1.0, 1.0)
        else:
            val = 0.0
            
        # Apply envelope (fade out at the end)
        fade_out = 1.0
        fade_samples = min(1000, num_samples // 4)
        if i > num_samples - fade_samples:
            fade_out = (num_samples - i) / fade_samples
            
        # Simple fade in to prevent clicks
        fade_in = 1.0
        if i < 100:
            fade_in = i / 100.0
            
        val *= fade_out * fade_in * volume
        
        # Clamp and convert to 16-bit signed int
        val = max(-1.0, min(1.0, val))
        samples.append(int(val * 32767))
        
    try:
        # Pack into little-endian 16-bit integers
        byte_data = struct.pack(f"<{len(samples)}h", *samples)
        return pygame.mixer.Sound(buffer=byte_data)
    except Exception:
        return None

# Pre-defined sound playing functions
def play_click():
    snd = generate_sound("square", 1200, 1200, 0.02, volume=0.1)
    if snd: snd.play()

def play_beep():
    snd = generate_sound("sine", 880, 880, 0.08, volume=0.15)
    if snd: snd.play()

def play_fail():
    snd = generate_sound("sawtooth", 180, 120, 0.25, volume=0.25)
    if snd: snd.play()

def play_shoot_laser():
    # Frequency sweep downwards for laser sound
    snd = generate_sound("sine", 2000, 400, 0.15, volume=0.2)
    if snd: snd.play()

def play_shoot_pipe():
    # Noise combined with quick pitch drop
    snd = generate_sound("noise", 800, 100, 0.1, volume=0.3)
    if snd: snd.play()

def play_hit():
    snd = generate_sound("noise", 150, 50, 0.15, volume=0.4)
    if snd: snd.play()

def play_heal():
    # Rising scale
    snd = generate_sound("sine", 300, 1200, 0.3, volume=0.25)
    if snd: snd.play()

def play_radiation_click():
    # Very short crackling noise burst
    snd = generate_sound("noise", 1000, 1000, 0.003, volume=0.4)
    if snd: snd.play()

def play_door_slide():
    snd = generate_sound("sawtooth", 120, 100, 0.5, volume=0.15)
    if snd: snd.play()

def play_level_up():
    if not _mixer_enabled:
        return
    # Play a quick progression of notes
    notes = [523.25, 659.25, 783.99, 1046.50] # C5, E5, G5, C6
    for freq in notes:
        snd = generate_sound("sine", freq, freq, 0.12, volume=0.25)
        if snd: 
            snd.play()
            pygame.time.delay(100)
