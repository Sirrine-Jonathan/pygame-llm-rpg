import random
import pygame
from engine.sound import play_hit, play_shoot_laser, play_shoot_pipe, play_heal, play_fail, play_level_up

class CombatSystem:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy  # Can be an Enemy or an NPC
        self.active = True
        
        # Combat logs (displays last 4 entries)
        self.logs = [
            f"COMMENCING COMBAT: {player.name} vs {enemy.name}!",
            "Select action from the terminal below."
        ]
        
        self.turn = "player"  # "player" or "enemy"
        self.selected_action = 0  # Index of menu option
        self.outcome = None  # "victory", "defeat", "escaped"
        self.delay_timer = 0  # Timer for turn sequence delays
        self.loot_collected = []

    def get_actions(self):
        actions = []
        
        # Action 1: Attack
        weapon_name = "Fists"
        if self.player.equipped_weapon:
            for item in self.player.inventory:
                if item["id"] == self.player.equipped_weapon:
                    weapon_name = item["name"]
                    break
        actions.append(f"ATTACK ({weapon_name})")
        
        # Action 2: Stimpak
        stimpak_qty = 0
        for item in self.player.inventory:
            if item["id"] == "stimpak":
                stimpak_qty = item["qty"]
                break
        actions.append(f"USE STIMPAK ({stimpak_qty})")
        
        # Action 3: RadAway
        radaway_qty = 0
        for item in self.player.inventory:
            if item["id"] == "radaway":
                radaway_qty = item["qty"]
                break
        actions.append(f"USE RADAWAY ({radaway_qty})")
        
        # Action 4: Flee
        actions.append("RUN AWAY")
        
        return actions

    def add_log(self, text):
        self.logs.append(text)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def handle_input(self, event):
        if self.turn != "player" or self.outcome is not None:
            return
            
        actions = self.get_actions()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_action = (self.selected_action - 1) % len(actions)
                play_shoot_pipe() # Quick tick sound or click (wait, play click or let it click)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_action = (self.selected_action + 1) % len(actions)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.execute_player_action()

    def execute_player_action(self):
        if self.selected_action == 0:
            # Attack
            # Calculate hit chance (based on Perception and Luck)
            hit_chance = 65 + self.player.special["Perception"] * 3 + self.player.special["Luck"] * 2
            hit_chance = min(95, max(30, hit_chance))
            
            if random.randint(1, 100) <= hit_chance:
                # Hit! Calculate damage
                dmg = self.player.get_attack_power()
                # Luck can trigger critical hit
                crit_chance = self.player.special["Luck"] * 3
                is_crit = random.randint(1, 100) <= crit_chance
                if is_crit:
                    dmg = int(dmg * 1.5)
                    self.add_log(f"CRITICAL HIT! You strike {self.enemy.name}!")
                
                self.enemy.hp = max(0, self.enemy.hp - dmg)
                self.add_log(f"You hit {self.enemy.name} for {dmg} damage! ({self.enemy.hp}/{self.enemy.max_hp} HP)")
                
                # Sound
                if self.player.equipped_weapon == "plasma_pistol":
                    play_shoot_laser()
                else:
                    play_shoot_pipe()
            else:
                self.add_log(f"You missed {self.enemy.name}!")
                play_fail()
                
            # Check if enemy dead
            if self.enemy.hp <= 0:
                self.resolve_victory()
            else:
                self.turn = "enemy"
                self.delay_timer = pygame.time.get_ticks() + 1000 # 1 second delay
                
        elif self.selected_action == 1:
            # Use Stimpak
            success, msg = self.player.use_item("stimpak")
            self.add_log(msg)
            if success:
                play_heal()
                self.turn = "enemy"
                self.delay_timer = pygame.time.get_ticks() + 1000
            else:
                play_fail()
                
        elif self.selected_action == 2:
            # Use RadAway
            success, msg = self.player.use_item("radaway")
            self.add_log(msg)
            if success:
                play_heal()
                self.turn = "enemy"
                self.delay_timer = pygame.time.get_ticks() + 1000
            else:
                play_fail()
                
        elif self.selected_action == 3:
            # Flee
            # Escape chance based on Agility
            escape_chance = 40 + self.player.special["Agility"] * 5
            if random.randint(1, 100) <= escape_chance:
                self.add_log("You managed to escape the battle!")
                self.outcome = "escaped"
                play_heal() # Soft sound
            else:
                self.add_log("Escape failed! The enemy blocks your way.")
                play_fail()
                self.turn = "enemy"
                self.delay_timer = pygame.time.get_ticks() + 1000

    def update(self):
        # Handle enemy turn after delay
        if self.turn == "enemy" and self.outcome is None:
            now = pygame.time.get_ticks()
            if now >= self.delay_timer:
                self.execute_enemy_action()

    def execute_enemy_action(self):
        # Enemy attacks
        hit_chance = 70
        if random.randint(1, 100) <= hit_chance:
            # Enemy hit
            raw_dmg = self.enemy.attack
            # Add small random variation
            raw_dmg += random.randint(-2, 2)
            raw_dmg = max(1, raw_dmg)
            
            actual_dmg = self.player.take_damage(raw_dmg)
            self.add_log(f"{self.enemy.name} attacks and hits you for {actual_dmg} damage!")
            play_hit()
        else:
            self.add_log(f"{self.enemy.name} swings at you and misses!")
            play_heal() # Soft swoosh or silence
            
        # Check if player dead
        if self.player.hp <= 0:
            self.resolve_defeat()
        else:
            self.turn = "player"

    def resolve_victory(self):
        self.outcome = "victory"
        xp_gain = getattr(self.enemy, "xp_reward", 30)
        self.add_log(f"VICTORY! You defeated {self.enemy.name}!")
        self.add_log(f"Gained {xp_gain} XP.")
        
        # Loot enemy
        loot_items = getattr(self.enemy, "loot", [])
        if loot_items:
            for item in loot_items:
                if item["id"] == "caps":
                    self.player.caps += item["qty"]
                    self.loot_collected.append(f"{item['qty']} Bottle Caps")
                else:
                    self.player.add_item(
                        item_id=item["id"],
                        name=item["name"],
                        item_type=item["type"],
                        qty=item["qty"],
                        value=item["value"],
                        desc=item["desc"],
                        combat_val=item.get("combat_val", 0)
                    )
                    self.loot_collected.append(item["name"])
            self.add_log(f"Looted: {', '.join(self.loot_collected)}")
        
        # Check level up
        if self.player.gain_xp(xp_gain):
            self.add_log(f"LEVEL UP! You are now Level {self.player.level}!")
            play_level_up()
            
    def resolve_defeat(self):
        self.outcome = "defeat"
        self.add_log("DEFEAT... You succumbed to your wounds.")
        play_fail()
