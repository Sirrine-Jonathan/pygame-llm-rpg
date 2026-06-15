import os
import sys
import pygame
from engine.game import GameEngine

def main():
    print("Initializing Vault 404 RPG Engine...")
    
    # Position pygame window in center of screen
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    
    # Initialize Pygame
    pygame.init()
    
    # Set Window Properties
    width, height = 960, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("VAULT 404: Wasteland Reclamation Utility (Pip-OS v3.0)")
    
    # Try setting custom icon or keep default
    try:
        # Create a simple icon surface (gear symbol)
        icon_surf = pygame.Surface((32, 32))
        icon_surf.fill((10, 15, 12))
        pygame.draw.circle(icon_surf, (80, 255, 100), (16, 16), 12, 3)
        pygame.draw.circle(icon_surf, (80, 255, 100), (16, 16), 4)
        pygame.display.set_icon(icon_surf)
    except Exception:
        pass
        
    # Instantiate Game Engine
    game = GameEngine(screen)
    
    # Main Game Loop
    try:
        while game.running:
            game.run_frame()
    except KeyboardInterrupt:
        print("\nForce closing game. Saving terminal state...")
    finally:
        pygame.quit()
        print("Vault 404 RPG successfully shutdown.")
        sys.exit(0)

if __name__ == "__main__":
    main()
