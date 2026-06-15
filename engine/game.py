import threading
import pygame
from engine.player import Player
from engine.map import GameMap, TILE_SIZE, TILE_RADIATION, TILE_EXIT
from engine.npc import get_default_npcs, get_default_enemies, NPC, Enemy
from engine.ui import UIManager, COLOR_GREEN, COLOR_ALERT_RED, COLOR_BG_BLACK
from engine.ollama_client import OllamaClient
from engine.combat import CombatSystem
from engine.sound import init_sound, play_click, play_beep, play_radiation_click, play_level_up, play_door_slide
from engine.assets import AssetLoader

class GameEngine:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Audio Initialization
        init_sound()
        
        # Game Components
        self.player = Player()
        self.map = GameMap()
        self.npcs = get_default_npcs()
        self.enemies = get_default_enemies()
        self.ui = UIManager(960, 720)
        self.ollama_client = OllamaClient()
        self.assets = AssetLoader()
        
        # Active Quests
        self.quests = {
            "water_purifier": {
                "name": "Save the Water Supply",
                "desc": "The main water purifier is failing. Find a replacement Water Chip and deliver it to Rusty in the Vault generator room.",
                "status": "active"
            },
            "escape_vault": {
                "name": "Escape Vault 404",
                "desc": "Find a way to open the vault gate and escape into the Wasteland. You need the Overseer's Keycard to operate the terminal controls.",
                "status": "active"
            }
        }
        
        # Engine States: "bootstrap", "intro", "explore", "pipboy", "dialog", "dialog_thinking", "combat", "terminal", "death", "victory"
        self.state = "bootstrap"
        
        # Start Ollama Bootstrap Check
        from engine.bootstrap import OllamaBootstrap
        self.bootstrap = OllamaBootstrap()
        self.bootstrap.start_check()
        
        # Character Creation Vars
        self.intro_name = "Dweller"
        self.intro_special_points = 12
        self.intro_special = {
            "Strength": 5,
            "Perception": 5,
            "Endurance": 5,
            "Charisma": 5,
            "Intelligence": 5,
            "Agility": 5,
            "Luck": 5
        }
        self.intro_cursor = 0
        
        # Active Systems
        self.active_npc = None
        self.active_combat = None
        self.active_terminal_logs = None
        
        # Threading for Ollama requests (prevents UI freezing)
        self.llm_response = None
        self.llm_thread = None
        self.thinking_timer = 0
        
        # Movement Direction
        self.player_dir = "down" # "up", "down", "left", "right"
        
        # Notification Log (visible on explorer HUD)
        self.notifications = []
        self.notification_timer = 0

    def add_notification(self, text):
        self.notifications.append(text)
        if len(self.notifications) > 3:
            self.notifications.pop(0)
        self.notification_timer = pygame.time.get_ticks() + 4000

    def get_game_state_payload(self):
        """Prepares state snapshot to send to the LLM."""
        return {
            "player_name": self.player.name,
            "player_hp": self.player.hp,
            "player_rad": self.player.rad,
            "player_caps": self.player.caps,
            "inventory": [
                {"id": item["id"], "name": item["name"], "qty": item["qty"]}
                for item in self.player.inventory
            ],
            "quests": {
                qid: quest["status"] for qid, quest in self.quests.items()
            }
        }

    def start_dialogue(self, npc):
        self.active_npc = npc
        self.state = "dialog"
        play_beep()
        
        # Set initial greeting
        greeting = f"Greetings, Vault Dweller. I am {npc.name}. What brings you to this part of the facility?"
        if npc.id == "overseer":
            greeting = "Resident. You are disrupting important Vault administration. State your request clearly, or return to your quarters immediately."
        elif npc.id == "rusty":
            greeting = "Hey, smoothskin. Water system's leaking radiation like a sieve. Got a spare Water Chip, or just wasting my breath?"
        elif npc.id == "moira":
            greeting = "Oh! Wow, a real Vault Dweller! Look at that neat little blue suit. Welcome to my trading post! Looking to buy something, or got stories to swap?"
        elif npc.id == "guard":
            greeting = "Halt. Vault gate security protocol active. No passage to the Wasteland without explicit Overseer clearance."
            
        npc.reset_chat()
        npc.chat_history.append({"role": "assistant", "content": greeting})
        self.ui.set_typewriter_text(greeting)
        self.ui.input_text = ""

    def process_player_dialog_input(self):
        msg = self.ui.input_text.strip()
        if not msg:
            return
            
        self.ui.input_text = ""
        self.active_npc.chat_history.append({"role": "user", "content": msg})
        
        # Enter thinking state
        self.state = "dialog_thinking"
        self.llm_response = None
        self.thinking_timer = pygame.time.get_ticks()
        
        # Spawn LLM query thread
        self.llm_thread = threading.Thread(
            target=self._query_llm_worker,
            args=(self.active_npc, msg)
        )
        self.llm_thread.daemon = True
        self.llm_thread.start()

    def _query_llm_worker(self, npc, user_msg):
        profile = npc.get_profile()
        state = self.get_game_state_payload()
        history = npc.chat_history[:-1] # Exclude the user message we just sent (client adds it)
        
        response = self.ollama_client.query_npc(profile, state, history, user_msg)
        self.llm_response = response

    def handle_llm_response(self):
        if self.llm_response is None:
            return
            
        resp = self.llm_response
        self.llm_response = None
        self.state = "dialog"
        
        reply_text = resp.get("reply", "...")
        action = resp.get("action", "NONE")
        payload = resp.get("action_payload", "")
        
        # Append response to chat history
        self.active_npc.chat_history.append({"role": "assistant", "content": reply_text})
        self.ui.set_typewriter_text(reply_text)
        
        # Execute NPC Action
        self.execute_npc_action(action, payload)

    def execute_npc_action(self, action, payload):
        if action == "GIVE_ITEM":
            # Give player item
            item_details = self.get_item_data(payload)
            if item_details:
                self.player.add_item(**item_details)
                self.add_notification(f"Gained Item: {item_details['name']}")
                play_level_up()
                
        elif action == "TAKE_ITEM":
            # Take item from player
            if self.player.remove_item(payload, 1):
                self.add_notification(f"Lost Item: {payload.replace('_', ' ').title()}")
                play_click()
                
        elif action == "GIVE_CAPS":
            try:
                amt = int(payload)
                self.player.caps += amt
                self.add_notification(f"Gained Caps: +{amt}")
                play_level_up()
            except ValueError:
                pass
                
        elif action == "TAKE_CAPS":
            try:
                amt = int(payload)
                if self.player.caps >= amt:
                    self.player.caps -= amt
                    self.add_notification(f"Lost Caps: -{amt}")
                    play_click()
                    
                    # Special Chain: If buying the water_chip or plasma_pistol
                    if self.active_npc.id == "moira" and not self.player.has_item("water_chip"):
                        self.player.add_item("water_chip", "Water Chip", "quest", 1, 100, "A water purification circuit board.")
                        self.add_notification("Acquired Water Chip from Moira")
                    elif self.active_npc.id == "rusty" and not self.player.has_item("plasma_pistol"):
                        self.player.add_item("plasma_pistol", "Plasma Pistol", "weapon", 1, 80, "Melts targets into goo. +25 Damage.", 25)
                        self.add_notification("Acquired Plasma Pistol from Rusty")
            except ValueError:
                pass
                
        elif action == "START_COMBAT":
            self.add_notification(f"{self.active_npc.name} has turned hostile!")
            self.active_npc.hostile = True
            self.active_combat = CombatSystem(self.player, self.active_npc)
            self.state = "combat"
            
        elif action == "ADVANCE_QUEST":
            if payload == "purifier_fixed":
                if self.quests["water_purifier"]["status"] != "completed":
                    self.quests["water_purifier"]["status"] = "completed"
                    self.player.remove_item("water_chip", 1)
                    # Reward player
                    self.player.gain_xp(100)
                    self.player.add_item("plasma_pistol", "Plasma Pistol", "weapon", 1, 80, "Melts targets into goo. +25 Damage.", 25)
                    self.add_notification("Water Purifier Fixed! (+100 XP)")
                    self.add_notification("Rusty gave you: Plasma Pistol")
                    play_level_up()
                    
            elif payload == "door_unlocked":
                if self.quests["escape_vault"]["status"] != "completed":
                    self.quests["escape_vault"]["status"] = "completed"
                    self.player.remove_item("vault_keycard", 1)
                    # Open the gate!
                    self.map.unlocked_doors.add(("vault", 18, 8))
                    self.player.gain_xp(100)
                    self.add_notification("Vault Door Security Override Active! (+100 XP)")
                    play_level_up()
                    play_door_slide()
                    
        elif action == "HEAL_PLAYER":
            self.player.hp = self.player.max_hp
            self.player.rad = 0
            self.add_notification("Health restored and radiation purged!")
            play_level_up()

    def get_item_data(self, item_id):
        items = {
            "vault_keycard": {
                "item_id": "vault_keycard",
                "name": "Vault Door Keycard",
                "item_type": "quest",
                "qty": 1,
                "value": 50,
                "desc": "A heavy security passcard stamped with the Vault 404 gear symbol."
            },
            "stimpak": {
                "item_id": "stimpak",
                "name": "Stimpak",
                "item_type": "aid",
                "qty": 1,
                "value": 20,
                "desc": "Heals 40 HP.",
                "combat_val": 40
            },
            "radaway": {
                "item_id": "radaway",
                "name": "RadAway",
                "item_type": "aid",
                "qty": 1,
                "value": 20,
                "desc": "Removes 50 Radiation.",
                "combat_val": 50
            },
            "water_chip": {
                "item_id": "water_chip",
                "name": "Water Chip",
                "item_type": "quest",
                "qty": 1,
                "value": 100,
                "desc": "A computer circuit board used to control purification pumps."
            }
        }
        return items.get(item_id)

    def handle_explore_movement(self, dx, dy):
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        area = self.player.current_area
        
        # Track orientation
        if dx > 0: self.player_dir = "right"
        elif dx < 0: self.player_dir = "left"
        elif dy > 0: self.player_dir = "down"
        elif dy < 0: self.player_dir = "up"
        
        # Check NPC collisions first
        for npc in self.npcs:
            if npc.area == area and npc.x == new_x and npc.y == new_y:
                if npc.hostile:
                    # Attack!
                    self.active_combat = CombatSystem(self.player, npc)
                    self.state = "combat"
                else:
                    # Talk!
                    self.start_dialogue(npc)
                return
                
        # Check Enemy collisions
        for enemy in self.enemies:
            if enemy.area == area and enemy.x == new_x and enemy.y == new_y and enemy.hp > 0:
                self.active_combat = CombatSystem(self.player, enemy)
                self.state = "combat"
                return
                
        # Check Map Collisions
        if self.map.is_walkable(area, new_x, new_y):
            self.player.x = new_x
            self.player.y = new_y
            
            # Post-move tile events
            grid = self.map.get_grid(area)
            tile = grid[new_y][new_x]
            
            # 1. Radiation Check
            if tile == TILE_RADIATION:
                actual_rad = self.player.take_radiation(3.0)
                self.add_notification(f"WARNING: Radiation detected! (+{actual_rad:.1f} Rads)")
                play_radiation_click()
                if self.player.hp <= 0:
                    self.state = "death"
                    
            # 2. Transition Gate Exit
            elif tile == TILE_EXIT:
                play_door_slide()
                if area == "vault":
                    self.player.current_area = "wasteland"
                    self.player.x = 1
                    self.player.y = 1
                    self.add_notification("Leaving Vault 404... Entering Wasteland")
                    
                    # Verify Escape Quest
                    if self.quests["escape_vault"]["status"] == "completed":
                        # If player exits vault, checking win scenario
                        if self.quests["water_purifier"]["status"] == "completed":
                            self.state = "victory"
                else:
                    self.player.current_area = "vault"
                    self.player.x = 18
                    self.player.y = 8
                    self.add_notification("Entering Vault 404 security corridor")
        else:
            # Check if wall or locked door and let the player interact automatically
            grid = self.map.get_grid(area)
            if 0 <= new_x < len(grid[0]) and 0 <= new_y < len(grid):
                tile = grid[new_y][new_x]
                if tile == TILE_DOOR:
                    success, msg, _ = self.map.interact(area, new_x, new_y, self.player)
                    self.add_notification(msg)

    def handle_explore_interaction(self):
        # Look ahead based on orientation
        target_x = self.player.x
        target_y = self.player.y
        
        if self.player_dir == "up": target_y -= 1
        elif self.player_dir == "down": target_y += 1
        elif self.player_dir == "left": target_x -= 1
        elif self.player_dir == "right": target_x += 1
        
        area = self.player.current_area
        success, msg, data = self.map.interact(area, target_x, target_y, self.player)
        
        if success:
            if data and data.get("type") == "terminal":
                self.active_terminal_logs = data["logs"]
                self.state = "terminal"
                play_beep()
            else:
                self.add_notification(msg)
        else:
            if msg:
                self.add_notification(msg)
            else:
                self.add_notification("Nothing to interact with here.")

    def run_frame(self):
        # Tick clock
        self.clock.tick(30)
        
        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            self.process_events(event)
            
        # Update system state
        self.update()
        
        # Render scene
        self.render()

    def process_events(self, event):
        if self.state == "bootstrap":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Let user bypass to offline mode if not ready/installed
                    if self.bootstrap.status in ["not_installed", "not_running", "offline_fallback"]:
                        self.state = "intro"
                        play_level_up()
                elif event.key == pygame.K_o:
                    if self.bootstrap.status in ["not_installed", "not_running"]:
                        self.bootstrap.open_download_page()

        elif self.state == "intro":
            self.handle_intro_events(event)
            
        elif self.state == "explore":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.handle_explore_movement(0, -1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.handle_explore_movement(0, 1)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.handle_explore_movement(-1, 0)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.handle_explore_movement(1, 0)
                elif event.key == pygame.K_e:
                    self.handle_explore_interaction()
                elif event.key == pygame.K_TAB:
                    self.state = "pipboy"
                    play_click()
                    
        elif self.state == "pipboy":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.state = "explore"
                play_click()
            else:
                self.ui.handle_pipboy_input(event, self.player)
                
        elif self.state == "dialog":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "explore"
                    play_click()
                elif event.key == pygame.K_RETURN:
                    self.process_player_dialog_input()
                elif event.key == pygame.K_BACKSPACE:
                    self.ui.input_text = self.ui.input_text[:-1]
                else:
                    # Limit input text length
                    if len(self.ui.input_text) < 40 and event.unicode.isprintable():
                        self.ui.input_text += event.unicode
                        
        elif self.state == "combat":
            self.active_combat.handle_input(event)
            if self.active_combat.outcome is not None and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.resolve_combat_conclusion()
                    
        elif self.state == "terminal":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    self.state = "explore"
                    play_click()
                    
        elif self.state == "death":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.__init__(self.screen) # Full reset
                play_level_up()
                
        elif self.state == "victory":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.running = False

    def handle_intro_events(self, event):
        stats = list(self.intro_special.keys())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.intro_cursor = (self.intro_cursor - 1) % len(stats)
                play_click()
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.intro_cursor = (self.intro_cursor + 1) % len(stats)
                play_click()
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                stat = stats[self.intro_cursor]
                if self.intro_special[stat] > 1:
                    self.intro_special[stat] -= 1
                    self.intro_special_points += 1
                    play_click()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                stat = stats[self.intro_cursor]
                if self.intro_special_points > 0:
                    self.intro_special[stat] += 1
                    self.intro_special_points -= 1
                    play_click()
            elif event.key == pygame.K_BACKSPACE:
                self.intro_name = self.intro_name[:-1]
            elif event.key == pygame.K_RETURN:
                # Confirm character creation
                self.player.name = self.intro_name if self.intro_name.strip() else "Vault Dweller"
                self.player.special = self.intro_special.copy()
                self.state = "explore"
                play_level_up()
            else:
                if len(self.intro_name) < 14 and event.unicode.isalnum():
                    self.intro_name += event.unicode

    def resolve_combat_conclusion(self):
        outcome = self.active_combat.outcome
        enemy = self.active_combat.enemy
        
        if outcome == "victory":
            # Remove enemy / hostile NPC from map
            if isinstance(enemy, Enemy):
                self.enemies.remove(enemy)
            elif isinstance(enemy, NPC):
                self.npcs.remove(enemy)
                # If they were the Overseer, make sure we drop keycard
                if enemy.id == "overseer":
                    self.player.add_item(**self.get_item_data("vault_keycard"))
                    self.add_notification("You found the Vault Keycard on the Overseer's body!")
                    
            self.state = "explore"
            play_level_up()
        elif outcome == "escaped":
            self.state = "explore"
        elif outcome == "defeat":
            self.state = "death"
            
        self.active_combat = None

    def update(self):
        if self.state == "bootstrap":
            if self.bootstrap.status == "ready":
                self.ollama_client.detect_model()
                self.state = "intro"
                play_level_up()
            return

        # Geiger Counter periodic ticking near radiation zones
        area = self.player.current_area
        grid = self.map.get_grid(area)
        
        # Check if adjacent to radiation
        has_nearby_rad = False
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                check_x = self.player.x + ox
                check_y = self.player.y + oy
                if 0 <= check_x < len(grid[0]) and 0 <= check_y < len(grid):
                    if grid[check_y][check_x] == TILE_RADIATION:
                        has_nearby_rad = True
                        break
                        
        if has_nearby_rad and pygame.time.get_ticks() % 100 < 15:
            # Play a random geiger counter click
            import random
            if random.random() < 0.4:
                play_radiation_click()
                
        # LLM thread checker
        if self.state == "dialog_thinking":
            self.handle_llm_response()
            
        # Combat updates
        if self.state == "combat":
            self.active_combat.update()

    def render(self):
        self.screen.fill((10, 12, 10))
        
        if self.state == "bootstrap":
            self.ui.draw_bootstrap_screen(self.screen, self.bootstrap)
            
        elif self.state == "intro":
            self.ui.draw_intro_screen(self.screen, self.intro_name, self.intro_special_points, self.intro_special, self.intro_cursor)
            
        elif self.state == "explore":
            # Draw game map tiles
            self.map.draw(self.screen, self.player.current_area, self.assets)
            
            # Draw NPCs
            for npc in self.npcs:
                if npc.area == self.player.current_area:
                    self._draw_character(npc.x, npc.y, "npc", npc.id)
                    
            # Draw Enemies
            for enemy in self.enemies:
                if enemy.area == self.player.current_area and enemy.hp > 0:
                    self._draw_character(enemy.x, enemy.y, "enemy", enemy.id)
                    
            # Draw Player
            self._draw_character(self.player.x, self.player.y, "player")
            
            # HUD overlay
            self.ui.draw_hud(self.screen, self.player)
            self._draw_notifications()
            
        elif self.state == "pipboy":
            self.ui.draw_pipboy(self.screen, self.player, self.quests)
            
        elif self.state == "dialog":
            self.ui.draw_dialogue(self.screen, self.active_npc, self.assets)
            
        elif self.state == "dialog_thinking":
            self.ui.draw_dialogue(self.screen, self.active_npc, self.assets)
            # Draw glowing loading message over input
            think_cycle = (pygame.time.get_ticks() // 250) % 4
            dots = "." * think_cycle
            loading_msg = f"ACCESSING VAULT MAINFRAME{dots}"
            # Render a block over input field
            pygame.draw.rect(self.screen, COLOR_BG_BLACK, (45, self.height_control() - 75, 800, 30))
            self.ui.draw_text(self.screen, loading_msg, 50, self.height_control() - 72, self.ui.font_medium, color=COLOR_GREEN)
            
        elif self.state == "combat":
            self.ui.draw_combat(self.screen, self.active_combat)
            
        elif self.state == "terminal":
            self.ui.draw_terminal(self.screen, self.active_terminal_logs)
            
        elif self.state == "death":
            self.ui.draw_death_screen(self.screen)
            
        elif self.state == "victory":
            self._draw_victory_screen()
            
        # Layer CRT phosphor filter lines
        self.ui.draw_crt_effects(self.screen)
        
        pygame.display.flip()

    def height_control(self):
        return 720 # standard height used for coords mapping

    def _draw_character(self, x, y, char_type, char_id=None):
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        center = rect.center
        
        # Draw from pixel art assets if available
        if self.assets and self.assets.enabled:
            role = None
            direction = 'down'
            if char_type == "player":
                role = 'player'
                direction = self.player_dir
            elif char_type == "npc":
                role = char_id
                direction = 'down'
                
            if role and role in self.assets.characters:
                sprite = self.assets.get_character_sprite(role, direction, 0, False)
                if sprite:
                    # Draw aligned to bottom of grid square
                    self.screen.blit(sprite, (rect.x, rect.y - 48))
                    return
        
        if char_type == "player":
            # Vault suit character (blue outfit with yellow stripes)
            pygame.draw.circle(self.screen, (30, 80, 220), center, 14) # Blue body
            # Yellow vault lining
            pygame.draw.line(self.screen, (220, 200, 20), (center[0]-5, center[1]-8), (center[0]-5, center[1]+8), 3)
            pygame.draw.circle(self.screen, (230, 180, 140), (center[0], center[1]-10), 8) # Head/Skin
            pygame.draw.circle(self.screen, (80, 50, 20), (center[0], center[1]-13), 6) # Hair (brown)
            
        elif char_type == "npc":
            if char_id == "overseer":
                # Older overseer (dark blue vault suit, white hair, sitting feel or strict)
                pygame.draw.circle(self.screen, (20, 50, 180), center, 14)
                pygame.draw.circle(self.screen, (235, 190, 160), (center[0], center[1]-10), 8)
                pygame.draw.circle(self.screen, (240, 240, 240), (center[0], center[1]-13), 6) # White hair
                
            elif char_id == "rusty":
                # Rusty (brown rags, ghoulish yellow-brown skin)
                pygame.draw.circle(self.screen, (100, 75, 45), center, 14)
                pygame.draw.circle(self.screen, (160, 140, 90), (center[0], center[1]-10), 8)
                
            elif char_id == "guard":
                # Power armor guard (bulky silver grey metallic circle)
                pygame.draw.circle(self.screen, (120, 125, 130), center, 16)
                pygame.draw.rect(self.screen, (80, 85, 90), (center[0]-10, center[1]-8, 20, 16), 2)
                # Visor glowing red
                pygame.draw.line(self.screen, COLOR_ALERT_RED, (center[0]-6, center[1]-10), (center[0]+6, center[1]-10), 2)
                
            elif char_id == "moira":
                # Moira (tan shirt, orange/red scarf, brown hair)
                pygame.draw.circle(self.screen, (140, 110, 80), center, 14)
                pygame.draw.circle(self.screen, (245, 200, 170), (center[0], center[1]-10), 8)
                pygame.draw.circle(self.screen, (120, 40, 10), (center[0], center[1]-13), 7) # Auburn hair
                
        elif char_type == "enemy":
            if "radroach" in char_id:
                # Crawling brown insect shape
                pygame.draw.ellipse(self.screen, (90, 60, 30), (rect.x + 8, rect.y + 14, 32, 20))
                # Legs
                for i in [-6, 0, 6]:
                    pygame.draw.line(self.screen, (60, 40, 20), (center[0] + i, center[1]), (center[0] + i*1.8, rect.y + 36), 2)
                # Antennae
                pygame.draw.line(self.screen, (90, 60, 30), (rect.x + 10, rect.y + 16), (rect.x + 2, rect.y + 4), 1)
                pygame.draw.line(self.screen, (90, 60, 30), (rect.x + 22, rect.y + 16), (rect.x + 14, rect.y + 4), 1)
            else:
                # Raider (spiky red hair, leather harness, combat stance)
                pygame.draw.circle(self.screen, (70, 70, 70), center, 14)
                pygame.draw.circle(self.screen, (225, 180, 145), (center[0], center[1]-10), 8)
                # Spiky mohawk
                pygame.draw.line(self.screen, (200, 40, 20), (center[0], center[1]-18), (center[0], center[1]-12), 4)

    def _draw_notifications(self):
        if not self.notifications:
            return
            
        now = pygame.time.get_ticks()
        if now > self.notification_timer:
            self.notifications = []
            return
            
        y = 75
        for note in self.notifications:
            self.ui.draw_text(self.screen, f">> {note.upper()}", 30, y, self.ui.font_small, color=COLOR_GREEN_BRIGHT)
            y += 20

    def _draw_victory_screen(self):
        self.screen.fill((5, 15, 5))
        pygame.draw.rect(self.screen, COLOR_GREEN, (20, 20, self.width_control() - 40, 680), 2)
        
        self.ui.draw_text(self.screen, "=== EXODUS PROTOCOL: COMPLETE ===", 100, 150, self.ui.font_large, color=COLOR_GREEN_BRIGHT)
        
        self.ui.draw_text(self.screen, "You successfully activated the water purification chips.", 100, 240, self.ui.font_medium)
        self.ui.draw_text(self.screen, "Vault 404's citizens will survive for decades to come.", 100, 275, self.ui.font_medium)
        self.ui.draw_text(self.screen, "Stepping past Sentinel Sterling, you look out at the horizon.", 100, 310, self.ui.font_medium)
        self.ui.draw_text(self.screen, "The blinding light of the Wasteland sun warms your face...", 100, 345, self.ui.font_medium)
        
        self.ui.draw_text(self.screen, "THE END.", 100, 430, self.ui.font_large, color=COLOR_GREEN_BRIGHT)
        self.ui.draw_text(self.screen, "PRESS ENTER TO RETIRE FROM VAULT SERVICE...", 100, 520, self.ui.font_medium)

    def width_control(self):
        return 960
