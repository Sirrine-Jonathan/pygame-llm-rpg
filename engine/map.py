import pygame
from engine.sound import play_door_slide, play_radiation_click

# Tile Constants
TILE_SIZE = 48
COLS = 20
ROWS = 15

# Tile IDs
TILE_FLOOR = 0
TILE_WALL = 1
TILE_DOOR = 2
TILE_TERMINAL = 3
TILE_CRATE = 4
TILE_RADIATION = 5
TILE_EXIT = 6

class GameMap:
    def __init__(self):
        # Vault Map Grid (20x15)
        # 1=Wall, 0=Floor, 2=Door, 3=Terminal, 4=Crate, 5=Radiation, 6=Exit Gate
        self.vault_grid = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
            [1,0,3,0,1,0,0,0,0,0,0,1,0,0,0,1,1,1,0,1],
            [1,0,0,0,2,0,0,0,0,0,0,2,0,0,0,1,1,1,0,1],
            [1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,1],
            [1,0,4,0,0,1,0,5,5,0,1,0,0,4,0,1,0,0,0,1],
            [1,0,0,0,0,1,0,5,5,0,1,0,0,0,0,2,0,0,0,1],
            [1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,6,1],
            [1,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,1],
            [1,0,0,4,0,1,0,0,0,0,0,1,0,4,0,1,0,0,0,1],
            [1,0,0,0,0,1,0,0,0,0,0,1,0,0,0,2,0,0,0,1],
            [1,1,1,1,2,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ]
        
        # Wasteland Map Grid (20x15)
        self.wasteland_grid = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,6,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,1],
            [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,1],
            [1,0,0,0,1,0,0,1,1,0,0,1,1,0,0,0,1,0,0,1],
            [1,0,1,1,1,0,0,0,0,0,0,1,1,1,0,0,1,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,1,1,0,0,0,0,0,0,0,5,5,0,0,1],
            [1,0,4,0,0,0,1,1,0,0,0,1,1,1,0,5,5,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,0,0,0,0,0,0,0,4,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,1],
            [1,0,0,0,0,4,0,0,0,0,0,1,1,1,1,1,1,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ]
        
        # State of interactive elements
        # Format: (area, x, y)
        self.unlocked_doors = set()
        self.looted_crates = set()
        self.terminal_states = {}  # Store logs read status
        
        # Define crate contents
        self.crate_loot = {
            # Vault crates
            ("vault", 2, 6): [
                {"id": "stimpak", "name": "Stimpak", "type": "aid", "qty": 1, "value": 20, "desc": "A chemical syringe. Heals 40 HP.", "combat_val": 40},
                {"id": "caps", "name": "Bottle Caps", "type": "currency", "qty": 10, "value": 1, "desc": "Wasteland money."}
            ],
            ("vault", 13, 6): [
                {"id": "radaway", "name": "RadAway", "type": "aid", "qty": 1, "value": 20, "desc": "Clears 50 rads.", "combat_val": 50}
            ],
            ("vault", 3, 10): [
                {"id": "bobby_pin", "name": "Bobby Pin", "type": "misc", "qty": 2, "value": 5, "desc": "A lockpick pin."}
            ],
            ("vault", 13, 10): [
                {"id": "stimpak", "name": "Stimpak", "type": "aid", "qty": 1, "value": 20, "desc": "Heals 40 HP.", "combat_val": 40},
                {"id": "caps", "name": "Bottle Caps", "type": "currency", "qty": 15, "value": 1, "desc": "Wasteland money."}
            ],
            # Wasteland crates
            ("wasteland", 2, 7): [
                {"id": "water_chip", "name": "Water Chip", "type": "quest", "qty": 1, "value": 100, "desc": "A vital pre-war logic chip for water purification."}
            ],
            ("wasteland", 14, 10): [
                {"id": "10mm_pistol", "name": "10mm Pistol", "type": "weapon", "qty": 1, "value": 45, "desc": "A sturdy sidearm. +15 Damage.", "combat_val": 15},
                {"id": "caps", "name": "Bottle Caps", "type": "currency", "qty": 20, "value": 1, "desc": "Wasteland money."}
            ],
            ("wasteland", 5, 12): [
                {"id": "stimpak", "name": "Stimpak", "type": "aid", "qty": 2, "value": 20, "desc": "Heals 40 HP.", "combat_val": 40},
                {"id": "radaway", "name": "RadAway", "type": "aid", "qty": 1, "value": 20, "desc": "Clears 50 rads.", "combat_val": 50}
            ]
        }
        
        # Terminal lore logs
        self.terminal_logs = {
            ("vault", 2, 2): [
                "=== VAULT 404 SYSTEMS MONITOR ===",
                "Status: CRITICAL WARNING",
                "Water Purifier filter efficiency: 1.2% (FAILING)",
                "Estimated drinkable supply: 3 DAYS.",
                "Note: Main Vault door lock override is situated in the Overseer's private Terminal.",
                "DO NOT panic. Remain inside. The Wasteland is hazardous."
            ]
        }

    def get_grid(self, area):
        return self.vault_grid if area == "vault" else self.wasteland_grid

    def is_walkable(self, area, x, y):
        grid = self.get_grid(area)
        if x < 0 or x >= COLS or y < 0 or y >= ROWS:
            return False
            
        tile = grid[y][x]
        if tile == TILE_WALL:
            return False
        if tile == TILE_DOOR:
            # Check if door is unlocked
            return (area, x, y) in self.unlocked_doors
        return True

    def interact(self, area, x, y, player):
        """
        Attempts to interact with a tile.
        Returns a tuple: (success_bool, message_string, optional_data)
        """
        grid = self.get_grid(area)
        tile = grid[y][x]
        
        if tile == TILE_DOOR:
            coord = (area, x, y)
            if coord in self.unlocked_doors:
                return True, "The door is already open.", None
            
            # Locked door - check for keycard
            if player.has_item("vault_keycard") or area == "wasteland":
                self.unlocked_doors.add(coord)
                play_door_slide()
                return True, "You swipe the Vault Keycard. The metallic door slides open!", None
            else:
                # Can lockpick?
                if player.has_item("bobby_pin"):
                    # Quick check on lockpick
                    player.remove_item("bobby_pin", 1)
                    # Let's say lockpick is based on Agility + Luck
                    success_chance = (player.special["Agility"] + player.special["Luck"]) * 6
                    import random
                    if random.randint(1, 100) <= success_chance:
                        self.unlocked_doors.add(coord)
                        play_door_slide()
                        player.gain_xp(15)
                        return True, "Success! You picked the lock using a Bobby Pin (+15 XP).", None
                    else:
                        return False, "You snapped the Bobby Pin in the lock! Try again.", None
                else:
                    return False, "This heavy security door is locked. You need a Vault Keycard or a Bobby Pin to lockpick it.", None
                    
        elif tile == TILE_CRATE:
            coord = (area, x, y)
            if coord in self.looted_crates:
                return True, "This storage crate is empty.", None
                
            loot_items = self.crate_loot.get(coord, [])
            if not loot_items:
                return True, "You find nothing inside.", None
                
            # Add loot to player
            collected = []
            for item in loot_items:
                if item["id"] == "caps":
                    player.caps += item["qty"]
                    collected.append(f"{item['qty']} Bottle Caps")
                else:
                    player.add_item(
                        item_id=item["id"],
                        name=item["name"],
                        item_type=item["type"],
                        qty=item["qty"],
                        value=item["value"],
                        desc=item["desc"],
                        combat_val=item.get("combat_val", 0)
                    )
                    collected.append(f"{item['name']} (x{item['qty']})")
                    
            self.looted_crates.add(coord)
            player.gain_xp(10)
            return True, f"You searched the crate and found: {', '.join(collected)} (+10 XP).", None
            
        elif tile == TILE_TERMINAL:
            coord = (area, x, y)
            logs = self.terminal_logs.get(coord, ["=== TERMINAL ===", "No data logs found."])
            player.gain_xp(5)
            return True, "Accessing terminal logs...", {"type": "terminal", "logs": logs}
            
        return False, "", None

    def draw(self, surface, area, assets=None):
        grid = self.get_grid(area)
        for y in range(ROWS):
            for x in range(COLS):
                tile = grid[y][x]
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # Try drawing using sprite assets first
                if assets and assets.enabled:
                    drawn = self._draw_tile_from_assets(surface, area, tile, rect, (area, x, y), assets)
                    if drawn:
                        continue
                
                # Fallback to procedural drawing
                if area == "vault":
                    self._draw_vault_tile(surface, tile, rect, (area, x, y))
                else:
                    self._draw_wasteland_tile(surface, tile, rect, (area, x, y))

    def _draw_tile_from_assets(self, surface, area, tile, rect, coord, assets):
        key = None
        if area == "vault":
            if tile == TILE_FLOOR:
                key = 'vault_floor'
            elif tile == TILE_WALL:
                key = 'vault_wall'
            elif tile == TILE_DOOR:
                if coord in self.unlocked_doors:
                    # Draw floor underneath open door
                    if 'vault_floor' in assets.tiles:
                        surface.blit(assets.tiles['vault_floor'], rect)
                    # Draw a slight sliding panel on sides
                    pygame.draw.rect(surface, (100, 80, 20), (rect.x, rect.y, 6, TILE_SIZE))
                    pygame.draw.rect(surface, (100, 80, 20), (rect.x + TILE_SIZE - 6, rect.y, 6, TILE_SIZE))
                    return True
                else:
                    key = 'vault_door'
            elif tile == TILE_TERMINAL:
                if 'vault_floor' in assets.tiles:
                    surface.blit(assets.tiles['vault_floor'], rect)
                key = 'terminal'
            elif tile == TILE_CRATE:
                if 'vault_floor' in assets.tiles:
                    surface.blit(assets.tiles['vault_floor'], rect)
                if coord in self.looted_crates:
                    # Draw an open box look procedurally on floor
                    pygame.draw.rect(surface, (30, 20, 10), (rect.x + 8, rect.y + 8, TILE_SIZE-16, TILE_SIZE-16))
                    pygame.draw.rect(surface, (15, 10, 5), (rect.x + 10, rect.y + 10, TILE_SIZE-20, TILE_SIZE-20))
                    return True
                else:
                    key = 'crate'
            elif tile == TILE_RADIATION:
                key = 'radiation'
            elif tile == TILE_EXIT:
                key = 'exit'
        else: # wasteland
            if tile == TILE_FLOOR:
                key = 'waste_floor'
            elif tile == TILE_WALL:
                key = 'waste_wall'
            elif tile == TILE_CRATE:
                if 'waste_floor' in assets.tiles:
                    surface.blit(assets.tiles['waste_floor'], rect)
                if coord in self.looted_crates:
                    pygame.draw.rect(surface, (25, 18, 12), (rect.x + 8, rect.y + 8, TILE_SIZE-16, TILE_SIZE-16))
                    return True
                else:
                    key = 'waste_crate'
            elif tile == TILE_RADIATION:
                key = 'waste_radiation'
            elif tile == TILE_EXIT:
                key = 'waste_exit'
                
        if key and key in assets.tiles and assets.tiles[key]:
            surface.blit(assets.tiles[key], rect)
            return True
        return False

    def _draw_vault_tile(self, surface, tile, rect, coord):
        # Base floor color (dark industrial steel grey/green)
        pygame.draw.rect(surface, (20, 25, 22), rect)
        
        if tile == TILE_FLOOR:
            # Draw floor grid lines
            pygame.draw.rect(surface, (30, 40, 32), rect, 1)
        elif tile == TILE_WALL:
            # Steel wall panels
            pygame.draw.rect(surface, (50, 55, 60), rect)
            pygame.draw.rect(surface, (30, 35, 40), rect, 2)
            # Rivets in corners
            for cx, cy in [(4,4), (TILE_SIZE-5, 4), (4, TILE_SIZE-5), (TILE_SIZE-5, TILE_SIZE-5)]:
                pygame.draw.circle(surface, (90, 95, 100), (rect.x + cx, rect.y + cy), 2)
        elif tile == TILE_DOOR:
            if coord in self.unlocked_doors:
                # Open door - show frame
                pygame.draw.rect(surface, (30, 40, 32), rect, 1)
                pygame.draw.rect(surface, (100, 80, 20), (rect.x, rect.y, 6, TILE_SIZE))
                pygame.draw.rect(surface, (100, 80, 20), (rect.x + TILE_SIZE - 6, rect.y, 6, TILE_SIZE))
            else:
                # Closed door - hazard stripe sliding door
                pygame.draw.rect(surface, (80, 80, 80), rect)
                pygame.draw.rect(surface, (40, 40, 40), rect, 2)
                # Hazard stripes (yellow/black diagonal)
                for i in range(0, TILE_SIZE, 8):
                    pygame.draw.line(surface, (200, 160, 20), (rect.x + i, rect.y), (rect.x + i + 8, rect.y + TILE_SIZE), 3)
        elif tile == TILE_TERMINAL:
            # Computer screen desk
            pygame.draw.rect(surface, (40, 45, 50), rect)
            pygame.draw.rect(surface, (20, 20, 20), rect, 2)
            # Glowing green screen
            screen_rect = pygame.Rect(rect.x + 8, rect.y + 6, TILE_SIZE - 16, TILE_SIZE - 20)
            pygame.draw.rect(surface, (10, 30, 10), screen_rect)
            pygame.draw.rect(surface, (50, 200, 50), screen_rect, 1)
            # Green CRT phosphor cursor
            pygame.draw.rect(surface, (80, 255, 80), (rect.x + 12, rect.y + 12, 4, 6))
            # Keyboard
            pygame.draw.rect(surface, (20, 20, 20), (rect.x + 8, rect.y + TILE_SIZE - 10, TILE_SIZE - 16, 6))
        elif tile == TILE_CRATE:
            # Dark green military crate
            pygame.draw.rect(surface, (25, 45, 25), rect)
            pygame.draw.rect(surface, (10, 20, 10), rect, 2)
            if coord in self.looted_crates:
                # Looted / open lid
                pygame.draw.rect(surface, (40, 30, 20), (rect.x + 4, rect.y + 4, TILE_SIZE - 8, TILE_SIZE - 8))
            else:
                # Closed / secure bands
                pygame.draw.rect(surface, (150, 130, 50), (rect.x + 8, rect.y + 2, 4, TILE_SIZE - 4))
                pygame.draw.rect(surface, (150, 130, 50), (rect.x + TILE_SIZE - 12, rect.y + 2, 4, TILE_SIZE - 4))
        elif tile == TILE_RADIATION:
            # Toxic green slime / reactor core
            pygame.draw.rect(surface, (20, 50, 20), rect)
            # Yellow radioactive symbol
            center = rect.center
            pygame.draw.circle(surface, (220, 200, 20), center, 8)
            pygame.draw.circle(surface, (20, 50, 20), center, 3)
            # Propagate clicks randomly to simulate Geiger counter
            if pygame.time.get_ticks() % 120 < 4:
                # In real game we verify distance, but let it draw animations
                pass
        elif tile == TILE_EXIT:
            # Elevator / gate hatch
            pygame.draw.rect(surface, (30, 30, 45), rect)
            # Blue glowing rings
            pygame.draw.circle(surface, (50, 100, 255), rect.center, 18, 2)
            pygame.draw.circle(surface, (100, 180, 255), rect.center, 8, 1)

    def _draw_wasteland_tile(self, surface, tile, rect, coord):
        # Base wasteland color (orange-brown desert sand)
        pygame.draw.rect(surface, (115, 85, 50), rect)
        
        if tile == TILE_FLOOR:
            # Sand details / cracks
            pygame.draw.line(surface, (135, 105, 70), (rect.x + 4, rect.y + 10), (rect.x + 15, rect.y + 12))
            pygame.draw.line(surface, (100, 70, 35), (rect.x + 25, rect.y + 35), (rect.x + 30, rect.y + 30))
        elif tile == TILE_WALL:
            # Ruined brick walls / rocks
            pygame.draw.rect(surface, (70, 60, 50), rect)
            pygame.draw.rect(surface, (45, 35, 25), rect, 2)
            # Draw some rocky crevices
            pygame.draw.polygon(surface, (40, 30, 25), [
                (rect.x + 10, rect.y + 10),
                (rect.x + 38, rect.y + 15),
                (rect.x + 24, rect.y + 38)
            ])
        elif tile == TILE_DOOR:
            # Steel gate in ruins
            pygame.draw.rect(surface, (80, 75, 70), rect)
            pygame.draw.rect(surface, (40, 35, 30), rect, 2)
            pygame.draw.line(surface, (150, 150, 150), (rect.x + TILE_SIZE//2, rect.y), (rect.x + TILE_SIZE//2, rect.y + TILE_SIZE), 3)
        elif tile == TILE_CRATE:
            # Wooden rusted crate
            pygame.draw.rect(surface, (120, 80, 40), rect)
            pygame.draw.rect(surface, (60, 40, 20), rect, 2)
            if coord in self.looted_crates:
                pygame.draw.rect(surface, (30, 20, 10), (rect.x + 4, rect.y + 4, TILE_SIZE-8, TILE_SIZE-8))
            else:
                # Diagonal planks
                pygame.draw.line(surface, (60, 40, 20), (rect.x + 4, rect.y + 4), (rect.x + TILE_SIZE - 4, rect.y + TILE_SIZE - 4), 2)
        elif tile == TILE_RADIATION:
            # Glowing toxic sludge puddle
            pygame.draw.rect(surface, (60, 100, 30), rect)
            pygame.draw.circle(surface, (100, 180, 50), (rect.x + 24, rect.y + 24), 14)
            pygame.draw.circle(surface, (150, 230, 80), (rect.x + 18, rect.y + 18), 6)
        elif tile == TILE_EXIT:
            # Steel Vault entry door hatch on ground
            pygame.draw.rect(surface, (60, 65, 70), rect)
            pygame.draw.circle(surface, (30, 30, 30), rect.center, 20)
            pygame.draw.circle(surface, (180, 140, 10), rect.center, 12, 2) # Yellow warning ring
            # Vault door gear spokes
            for i in range(8):
                import math
                angle = i * (math.pi / 4)
                spoke_x = int(rect.centerx + 16 * math.cos(angle))
                spoke_y = int(rect.centery + 16 * math.sin(angle))
                pygame.draw.line(surface, (100, 105, 110), rect.center, (spoke_x, spoke_y), 3)
