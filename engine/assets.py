import os
import pygame

class AssetLoader:
    def __init__(self):
        self.tileset = None
        self.characters = {}
        self.tiles = {}
        self.enabled = False
        
        self.load_assets()
        
    def load_assets(self):
        try:
            tileset_path = 'assets/Modern tiles_Free/Interiors_free/48x48/Interiors_free_48x48.png'
            if os.path.exists(tileset_path):
                # We load the image. Pygame needs to be initialized.
                self.tileset = pygame.image.load(tileset_path).convert_alpha()
                self.enabled = True
                print("Loaded interior tileset successfully!")
                
                # Extract tiles based on coordinates in the Interiors sheet
                # Format: (column, row)
                self.tiles['vault_floor'] = self.get_tile(0, 0) # Grey tiled floor
                self.tiles['vault_wall'] = self.get_tile(12, 1)  # Steel metal divider/wall
                self.tiles['vault_door'] = self.get_tile(1, 6)   # Shutter/Sliding door
                self.tiles['terminal'] = self.get_tile(1, 14)   # Computer screen / console
                self.tiles['crate'] = self.get_tile(4, 23)      # Storage chest / container
                self.tiles['radiation'] = self.get_tile(6, 21)  # Waste pile / glowing generator part
                self.tiles['exit'] = self.get_tile(15, 23)     # Steel security hatch / gate
                
                # Wasteland tiles
                self.tiles['waste_floor'] = self.get_tile(0, 4)  # Wooden brown or sandy floor
                self.tiles['waste_wall'] = self.get_tile(4, 7)   # Brick ruined wall block
                self.tiles['waste_crate'] = self.get_tile(11, 23) # Rusted container
                self.tiles['waste_radiation'] = self.get_tile(6, 21) # Slime pile
                self.tiles['waste_exit'] = self.get_tile(15, 23) # Security hatch
            else:
                print("Warning: Tileset image not found. Running in procedural mode.")
                
            # Character models mapping
            chars = {
                'player': 'Adam',
                'overseer': 'Bob',
                'rusty': 'Alex',
                'moira': 'Amelia',
                'guard': 'Bob'
            }
            
            for role, name in chars.items():
                run_path = f'assets/Modern tiles_Free/Characters_free/{name}_run_16x16.png'
                idle_path = f'assets/Modern tiles_Free/Characters_free/{name}_idle_16x16.png'
                
                if os.path.exists(run_path) and os.path.exists(idle_path):
                    self.characters[role] = {
                        'run': pygame.image.load(run_path).convert_alpha(),
                        'idle': pygame.image.load(idle_path).convert_alpha()
                    }
                    print(f"Loaded character spritesheet for {role} ({name})")
        except Exception as e:
            print(f"Error loading assets: {e}. Running in procedural mode.")
            self.enabled = False

    def get_tile(self, tx, ty):
        if not self.tileset:
            return None
        rect = pygame.Rect(tx * 48, ty * 48, 48, 48)
        w, h = self.tileset.get_size()
        if rect.right <= w and rect.bottom <= h:
            # Subsurface creates a viewport reference into the sheet
            return self.tileset.subsurface(rect)
        return None

    def get_character_sprite(self, role, direction, anim_frame, is_moving=False):
        """
        Clips and upscales a 16x32 character frame from the spritesheet.
        direction: 'down', 'left', 'right', 'up'
        anim_frame: current frame index
        is_moving: whether running or idle
        """
        if role not in self.characters:
            return None
            
        sheet = self.characters[role]['run'] if is_moving else self.characters[role]['idle']
        
        # Determine direction offset
        # The sheet lays out directions horizontally: down, left, right, up
        dir_map = {'down': 0, 'left': 1, 'right': 2, 'up': 3}
        dir_idx = dir_map.get(direction, 0)
        
        frame_w, frame_h = 16, 32
        
        if is_moving:
            # Each direction has 6 running frames
            frame_x = (dir_idx * 6 + (anim_frame % 6)) * frame_w
            frame_y = 0
        else:
            # Idle has 1 frame per direction (down=0, left=16, right=32, up=48)
            # wait, let's verify if idle sheet is (64, 32)
            # if size is 64x32, and each frame is 16x32, there are 4 frames horizontally
            frame_x = dir_idx * frame_w
            frame_y = 0
            
        rect = pygame.Rect(frame_x, frame_y, frame_w, frame_h)
        w, h = sheet.get_size()
        if rect.right <= w and rect.bottom <= h:
            sub = sheet.subsurface(rect)
            # Upscale 3x to match 48px tile grid (48x96)
            return pygame.transform.scale(sub, (48, 96))
        return None
