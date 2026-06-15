import pygame
import math
from engine.sound import play_click, play_beep

# Color Definitions (Retro Pip-Boy Phosphor Green)
COLOR_BG_BLACK = (10, 15, 12)
COLOR_GREEN_DARK = (20, 80, 25)
COLOR_GREEN = (40, 200, 60)
COLOR_GREEN_BRIGHT = (80, 255, 100)
COLOR_ALERT_RED = (255, 60, 60)
COLOR_RAD_YELLOW = (220, 200, 20)

class UIManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Load fonts
        self.font_large = self._get_mono_font(32)
        self.font_medium = self._get_mono_font(22)
        self.font_small = self._get_mono_font(16)
        self.font_tiny = self._get_mono_font(12)
        
        # Cache CRT overlays
        self.scanline_surface = self._create_scanlines()
        self.bezel_surface = self._create_bezel()
        
        # Typewriter text scroll effect
        self.typewriter_text = ""
        self.typewriter_index = 0
        self.typewriter_delay = 1  # ticks between chars
        self.typewriter_timer = 0
        
        # Dialog text input buffer
        self.input_text = ""
        self.cursor_blink = True
        self.cursor_timer = 0
        
        # Selected tab for Pip-Boy
        self.pipboy_tab = "STAT"  # "STAT", "INV", "DATA"
        self.inv_selected_idx = 0
        self.data_selected_idx = 0
        
    def _get_mono_font(self, size):
        # Find monospace fonts
        font_names = ["courier", "couriernew", "lucidaconsole", "monospace", "consolas"]
        for name in font_names:
            f = pygame.font.match_font(name)
            if f:
                return pygame.font.Font(f, size)
        return pygame.font.Font(None, size)

    def _create_scanlines(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Vertical overlay of dark lines
        for y in range(0, self.height, 3):
            # A very subtle dark line
            pygame.draw.line(surf, (0, 0, 0, 50), (0, y), (self.width, y))
        return surf

    def _create_bezel(self):
        # A vignette border that simulates a curved CRT glass screen
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Outer screen frame
        border_width = 16
        pygame.draw.rect(surf, (0, 0, 0, 255), (0, 0, self.width, border_width))
        pygame.draw.rect(surf, (0, 0, 0, 255), (0, 0, border_width, self.height))
        pygame.draw.rect(surf, (0, 0, 0, 255), (0, self.height - border_width, self.width, border_width))
        pygame.draw.rect(surf, (0, 0, 0, 255), (self.width - border_width, 0, border_width, self.height))
        
        # Rounded corners inside the bezel
        radius = 28
        # Top Left
        pygame.draw.rect(surf, (0, 0, 0, 255), (border_width, border_width, radius, radius))
        pygame.draw.circle(surf, (0, 0, 0, 0), (border_width + radius, border_width + radius), radius)
        # Top Right
        pygame.draw.rect(surf, (0, 0, 0, 255), (self.width - border_width - radius, border_width, radius, radius))
        pygame.draw.circle(surf, (0, 0, 0, 0), (self.width - border_width - radius, border_width + radius), radius)
        # Bottom Left
        pygame.draw.rect(surf, (0, 0, 0, 255), (border_width, self.height - border_width - radius, radius, radius))
        pygame.draw.circle(surf, (0, 0, 0, 0), (border_width + radius, self.height - border_width - radius), radius)
        # Bottom Right
        pygame.draw.rect(surf, (0, 0, 0, 255), (self.width - border_width - radius, self.height - border_width - radius, radius, radius))
        pygame.draw.circle(surf, (0, 0, 0, 0), (self.width - border_width - radius, self.height - border_width - radius), radius)
        
        # Add a green glow around the inner bezel
        bezel_rect = pygame.Rect(border_width, border_width, self.width - 2*border_width, self.height - 2*border_width)
        pygame.draw.rect(surf, (40, 200, 60, 40), bezel_rect, 2)
        
        return surf

    def draw_crt_effects(self, surface):
        surface.blit(self.scanline_surface, (0, 0))
        # Draw screen flicker / overlay
        flicker = math.sin(pygame.time.get_ticks() / 15.0) * 2 + 3
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((40, 200, 60, int(flicker)))
        surface.blit(overlay, (0, 0))
        # Bezel overlay
        surface.blit(self.bezel_surface, (0, 0))

    def draw_text(self, surface, text, x, y, font, color=COLOR_GREEN, shadow=True):
        if shadow:
            # Draw shadow for glow effect
            shadow_surf = font.render(text, True, (color[0]//4, color[1]//4, color[2]//4))
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                surface.blit(shadow_surf, (x + ox, y + oy))
        
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, (x, y))

    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            width, _ = font.size(test_line)
            if width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def set_typewriter_text(self, text):
        self.typewriter_text = text
        self.typewriter_index = 0
        self.typewriter_timer = pygame.time.get_ticks()

    def update_typewriter(self):
        if self.typewriter_index < len(self.typewriter_text):
            now = pygame.time.get_ticks()
            if now >= self.typewriter_timer:
                self.typewriter_index += 1
                self.typewriter_timer = now + self.typewriter_delay
                # Play typing tick sound occasionally
                if self.typewriter_index % 3 == 0:
                    play_click()

    def get_visible_dialogue(self):
        return self.typewriter_text[:self.typewriter_index]

    def draw_hud(self, surface, player):
        # Bottom status panel
        panel_y = self.height - 75
        pygame.draw.rect(surface, (15, 20, 18), (16, panel_y, self.width - 32, 60))
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (16, panel_y, self.width - 32, 60), 1)
        
        # Player name & Level
        self.draw_text(surface, f"{player.name.upper()} - LVL {player.level}", 30, panel_y + 10, self.font_medium)
        
        # HP Bar
        hp_pct = max(0, min(1.0, player.hp / player.max_hp))
        hp_bar_width = 180
        self.draw_text(surface, f"HP: {player.hp}/{player.max_hp}", 300, panel_y + 10, self.font_small)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (300, panel_y + 30, hp_bar_width, 14))
        pygame.draw.rect(surface, COLOR_GREEN, (300, panel_y + 30, int(hp_bar_width * hp_pct), 14))
        pygame.draw.rect(surface, COLOR_GREEN_BRIGHT, (300, panel_y + 30, hp_bar_width, 14), 1)
        
        # Radiation Bar
        rad_pct = max(0, min(1.0, player.rad / player.max_rad))
        rad_bar_width = 120
        rad_color = COLOR_RAD_YELLOW if player.rad > 0 else COLOR_GREEN
        self.draw_text(surface, f"RADS: {int(player.rad)}%", 500, panel_y + 10, self.font_small, color=rad_color)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (500, panel_y + 30, rad_bar_width, 14))
        pygame.draw.rect(surface, rad_color, (500, panel_y + 30, int(rad_bar_width * rad_pct), 14))
        pygame.draw.rect(surface, COLOR_GREEN_BRIGHT, (500, panel_y + 30, rad_bar_width, 14), 1)
        
        # Caps & Weapon
        self.draw_text(surface, f"CAPS: {player.caps}", 650, panel_y + 10, self.font_small)
        weapon_name = "UNARMED"
        if player.equipped_weapon:
            for item in player.inventory:
                if item["id"] == player.equipped_weapon:
                    weapon_name = item["name"]
                    break
        self.draw_text(surface, f"WEAPON: {weapon_name}", 650, panel_y + 30, self.font_small)
        
        # Hint text
        self.draw_text(surface, "TAB: PIP-BOY | E: INTERACT | ARROWS: MOVE", 20, 24, self.font_tiny)

    def draw_pipboy(self, surface, player, active_quests):
        # Draw base Pip-Boy screen
        surface.fill(COLOR_BG_BLACK)
        
        # Pip-Boy Header
        pygame.draw.line(surface, COLOR_GREEN, (30, 60), (self.width - 30, 60), 2)
        self.draw_text(surface, "PIP-BOY 3000", 40, 32, self.font_large)
        
        # Tabs
        tab_x = 350
        for tab in ["STAT", "INV", "DATA"]:
            tab_color = COLOR_GREEN_BRIGHT if self.pipboy_tab == tab else COLOR_GREEN_DARK
            self.draw_text(surface, f"[{tab}]", tab_x, 34, self.font_medium, color=tab_color)
            tab_x += 100
            
        # Draw Content based on selected tab
        if self.pipboy_tab == "STAT":
            self._draw_pipboy_stat(surface, player)
        elif self.pipboy_tab == "INV":
            self._draw_pipboy_inv(surface, player)
        elif self.pipboy_tab == "DATA":
            self._draw_pipboy_data(surface, player, active_quests)
            
        # Footer
        pygame.draw.line(surface, COLOR_GREEN, (30, self.height - 60), (self.width - 30, self.height - 60), 2)
        self.draw_text(surface, "PRESS TAB TO CLOSE PIP-BOY", 40, self.height - 48, self.font_small)

    def _draw_pipboy_stat(self, surface, player):
        # Left Panel - SPECIAL
        self.draw_text(surface, "=== S.P.E.C.I.A.L. ===", 60, 90, self.font_medium)
        special_y = 125
        for stat, val in player.special.items():
            stat_name = stat.upper()
            self.draw_text(surface, f"{stat_name:<15}: {val}", 60, special_y, self.font_small)
            # Draw tiny bar for stat
            pygame.draw.rect(surface, COLOR_GREEN_DARK, (220, special_y + 2, 80, 10))
            pygame.draw.rect(surface, COLOR_GREEN, (220, special_y + 2, int(8 * val), 10))
            special_y += 26
            
        # Right Panel - Vitals & Progression
        self.draw_text(surface, "=== PLAYER STATUS ===", 380, 90, self.font_medium)
        self.draw_text(surface, f"NAME  : {player.name.upper()}", 380, 125, self.font_small)
        self.draw_text(surface, f"LEVEL : {player.level}", 380, 155, self.font_small)
        
        # XP Progress Bar
        xp_pct = max(0, min(1.0, player.xp / player.xp_to_next))
        self.draw_text(surface, f"XP    : {player.xp}/{player.xp_to_next}", 380, 185, self.font_small)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (380, 205, 300, 14))
        pygame.draw.rect(surface, COLOR_GREEN, (380, 205, int(300 * xp_pct), 14))
        pygame.draw.rect(surface, COLOR_GREEN_BRIGHT, (380, 205, 300, 14), 1)
        
        # Detailed HP/Rad stats
        self.draw_text(surface, f"HEALTH: {player.hp}/{player.max_hp} HP", 380, 240, self.font_small)
        self.draw_text(surface, f"RADS  : {int(player.rad)}/100 RAD", 380, 270, self.font_small)
        self.draw_text(surface, f"CAPS  : {player.caps} Bottle Caps", 380, 300, self.font_small)
        
        # Draw vault boy outline / radar animation in the empty space
        self._draw_vector_vault_boy(surface, 550, 320)

    def _draw_vector_vault_boy(self, surface, cx, cy):
        # A simple vector vault boy head doing thumbs up!
        # Head
        pygame.draw.circle(surface, COLOR_GREEN, (cx, cy), 20, 2)
        # Hair (wavy)
        pygame.draw.arc(surface, COLOR_GREEN, (cx-22, cy-22, 44, 25), 0, math.pi, 2)
        # Smile
        pygame.draw.arc(surface, COLOR_GREEN, (cx-10, cy-5, 20, 15), math.pi, 2*math.pi, 2)
        # Eyes
        pygame.draw.circle(surface, COLOR_GREEN, (cx-6, cy-4), 2)
        pygame.draw.circle(surface, COLOR_GREEN, (cx+6, cy-4), 2)
        # Thumbs up body line
        pygame.draw.line(surface, COLOR_GREEN, (cx, cy+20), (cx, cy+50), 2)
        pygame.draw.line(surface, COLOR_GREEN, (cx, cy+30), (cx-20, cy+30), 2) # Arm
        pygame.draw.circle(surface, COLOR_GREEN, (cx-22, cy-2), 6, 2) # Thumb up hand

    def _draw_pipboy_inv(self, surface, player):
        self.draw_text(surface, "=== INVENTORY ===", 60, 90, self.font_medium)
        
        if not player.inventory:
            self.draw_text(surface, "NO ITEMS HELD", 60, 130, self.font_small)
            return
            
        # Limit item selection range
        self.inv_selected_idx = max(0, min(self.inv_selected_idx, len(player.inventory) - 1))
        
        # Scrollable list
        start_y = 130
        list_height = 8 # Display max 8 items
        scroll_start = max(0, self.inv_selected_idx - list_height + 2)
        
        for i in range(scroll_start, min(len(player.inventory), scroll_start + list_height)):
            item = player.inventory[i]
            equipped = ""
            if player.equipped_weapon == item["id"] or player.equipped_armor == item["id"]:
                equipped = "[E] "
            
            item_text = f"{equipped}{item['name']} (x{item['qty']})"
            color = COLOR_GREEN_BRIGHT if i == self.inv_selected_idx else COLOR_GREEN
            self.draw_text(surface, item_text, 60, start_y, self.font_small, color=color)
            start_y += 28
            
        # Draw selected item details
        selected_item = player.inventory[self.inv_selected_idx]
        self.draw_text(surface, "=== ITEM SPECIFICATIONS ===", 420, 90, self.font_medium)
        self.draw_text(surface, f"NAME : {selected_item['name']}", 420, 130, self.font_small)
        self.draw_text(surface, f"TYPE : {selected_item['type'].upper()}", 420, 160, self.font_small)
        self.draw_text(surface, f"VALUE: {selected_item['value']} caps", 420, 190, self.font_small)
        
        # Wrap description
        desc_lines = self.wrap_text(selected_item["desc"], self.font_small, 320)
        desc_y = 220
        for line in desc_lines:
            self.draw_text(surface, line, 420, desc_y, self.font_small)
            desc_y += 22
            
        # Use instructions
        action_desc = "USE ITEM / EQUIP WEAPON"
        if selected_item["type"] == "misc" or selected_item["type"] == "quest":
            action_desc = "CANNOT BE ACTIVATED DIRECTLY"
            
        self.draw_text(surface, "UP/DOWN: SCROLL | ENTER: " + action_desc, 420, self.height - 90, self.font_tiny)

    def _draw_pipboy_data(self, surface, player, active_quests):
        self.draw_text(surface, "=== ACTIVE QUESTS ===", 60, 90, self.font_medium)
        
        quests = list(active_quests.items())
        if not quests:
            self.draw_text(surface, "NO CURRENT OBJECTIVES", 60, 130, self.font_small)
            return
            
        self.data_selected_idx = max(0, min(self.data_selected_idx, len(quests) - 1))
        
        # List quests
        start_y = 130
        for i, (q_id, quest) in enumerate(quests):
            color = COLOR_GREEN_BRIGHT if i == self.data_selected_idx else COLOR_GREEN
            self.draw_text(surface, f"- {quest['name']}", 60, start_y, self.font_small, color=color)
            start_y += 28
            
        # Selected Quest Details
        selected_qid, selected_q = quests[self.data_selected_idx]
        self.draw_text(surface, "=== OBJECTIVES DATA ===", 420, 90, self.font_medium)
        self.draw_text(surface, f"STATUS: {selected_q['status'].upper()}", 420, 130, self.font_small)
        
        desc_lines = self.wrap_text(selected_q["desc"], self.font_small, 320)
        desc_y = 160
        for line in desc_lines:
            self.draw_text(surface, line, 420, desc_y, self.font_small)
            desc_y += 22

    def handle_pipboy_input(self, event, player):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.pipboy_tab = "STAT"
                play_click()
            elif event.key == pygame.K_2:
                self.pipboy_tab = "INV"
                play_click()
            elif event.key == pygame.K_3:
                self.pipboy_tab = "DATA"
                play_click()
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                tabs = ["STAT", "INV", "DATA"]
                idx = tabs.index(self.pipboy_tab)
                self.pipboy_tab = tabs[(idx - 1) % len(tabs)]
                play_click()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                tabs = ["STAT", "INV", "DATA"]
                idx = tabs.index(self.pipboy_tab)
                self.pipboy_tab = tabs[(idx + 1) % len(tabs)]
                play_click()
                
            # Scroll item/quests
            if self.pipboy_tab == "INV" and player.inventory:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.inv_selected_idx = (self.inv_selected_idx - 1) % len(player.inventory)
                    play_click()
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.inv_selected_idx = (self.inv_selected_idx + 1) % len(player.inventory)
                    play_click()
                elif event.key == pygame.K_RETURN:
                    # Action
                    item_id = player.inventory[self.inv_selected_idx]["id"]
                    success, msg = player.use_item(item_id)
                    play_beep()
                    # Return message block later if UI supports it, but stats update immediately
            elif self.pipboy_tab == "DATA":
                # Quests can scroll
                pass

    def draw_dialogue(self, surface, npc, assets=None):
        # Split dialogue screen
        surface.fill(COLOR_BG_BLACK)
        
        # Border
        pygame.draw.rect(surface, COLOR_GREEN, (20, 20, self.width - 40, self.height - 40), 2)
        
        # Draw NPC Avatar Box (Left top)
        avatar_rect = pygame.Rect(40, 40, 240, 200)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, avatar_rect, 1)
        self._draw_vector_npc_avatar(surface, npc.id, avatar_rect)
        
        # Draw actual pixel art portrait if assets are available
        if assets and assets.enabled and npc.id in assets.characters:
            sprite = assets.get_character_sprite(npc.id, 'down', 0, False)
            if sprite:
                # Upscale 16x32 by 5x (which is 80x160) for a large avatar display
                portrait = pygame.transform.scale(sprite, (80, 160))
                px = avatar_rect.centerx - 40
                py = avatar_rect.centery - 80
                surface.blit(portrait, (px, py))
        
        # Draw NPC Details Box (Right top)
        self.draw_text(surface, f"NPC NAME : {npc.name.upper()}", 300, 40, self.font_medium)
        self.draw_text(surface, f"ROLE     : {npc.role}", 300, 75, self.font_small)
        self.draw_text(surface, f"SPELLIN' : {npc.personality.split(',')[0]}", 300, 105, self.font_small)
        
        # Mood Radar
        mood = "neutral"
        self.draw_text(surface, f"SCAN MOOD: {mood.upper()}", 300, 135, self.font_small, color=COLOR_GREEN_BRIGHT)
        
        # Divider line
        pygame.draw.line(surface, COLOR_GREEN, (40, 260), (self.width - 40, 260), 2)
        
        # Dialogue Subtitle Box
        dialogue_text = self.get_visible_dialogue()
        wrapped_lines = self.wrap_text(dialogue_text, self.font_medium, self.width - 80)
        
        y_pos = 280
        for line in wrapped_lines:
            self.draw_text(surface, line, 50, y_pos, self.font_medium)
            y_pos += 26
            
        # Prompt Box at the bottom
        pygame.draw.line(surface, COLOR_GREEN, (40, self.height - 100), (self.width - 40, self.height - 100), 1)
        self.draw_text(surface, "ENTER YOUR RESPONSE (TYPE FREE TEXT):", 50, self.height - 90, self.font_tiny)
        
        # Blinking cursor for typing
        cursor_str = "_" if self.cursor_blink else " "
        self.draw_text(surface, f"> {self.input_text}{cursor_str}", 50, self.height - 70, self.font_medium, color=COLOR_GREEN_BRIGHT)
        
        # Update typewriter and cursor blinking
        self.update_typewriter()
        now = pygame.time.get_ticks()
        if now - self.cursor_timer >= 500:
            self.cursor_blink = not self.cursor_blink
            self.cursor_timer = now

    def _draw_vector_npc_avatar(self, surface, npc_id, rect):
        cx = rect.centerx
        cy = rect.centery
        
        # Standard green CRT radar grid behind avatar
        for r in range(10, 80, 20):
            pygame.draw.circle(surface, (15, 45, 20), (cx, cy), r, 1)
        pygame.draw.line(surface, (15, 45, 20), (rect.x, cy), (rect.x + rect.width, cy), 1)
        pygame.draw.line(surface, (15, 45, 20), (cx, rect.y), (cx, rect.y + rect.height), 1)
        
        if npc_id == "overseer":
            # Strict Overseer: square head, slick hair, glasses
            pygame.draw.polygon(surface, COLOR_GREEN, [
                (cx-25, cy-20), (cx+25, cy-20), (cx+25, cy+25), (cx-25, cy+25)
            ], 2) # Head
            pygame.draw.line(surface, COLOR_GREEN, (cx-35, cy-22), (cx+35, cy-22), 3) # Slick hair top
            pygame.draw.line(surface, COLOR_GREEN, (cx-35, cy-22), (cx-25, cy+5), 2) # Hair side
            pygame.draw.line(surface, COLOR_GREEN, (cx+35, cy-22), (cx+25, cy+5), 2)
            # Glasses
            pygame.draw.rect(surface, COLOR_GREEN, (cx-18, cy-5, 12, 8), 1)
            pygame.draw.rect(surface, COLOR_GREEN, (cx+6, cy-5, 12, 8), 1)
            pygame.draw.line(surface, COLOR_GREEN, (cx-6, cy-1), (cx+6, cy-1), 2)
            # Strict thin mouth
            pygame.draw.line(surface, COLOR_GREEN, (cx-10, cy+15), (cx+10, cy+15), 2)
            
        elif npc_id == "rusty":
            # Ghoul: gaunt features, hollow cheeks, patch hair
            pygame.draw.polygon(surface, COLOR_GREEN, [
                (cx-18, cy-25), (cx+18, cy-25), (cx+22, cy), (cx+15, cy+30), (cx-15, cy+30), (cx-22, cy)
            ], 2) # Gaunt face
            # Hollow eyes (big dark circles)
            pygame.draw.circle(surface, COLOR_GREEN, (cx-8, cy-5), 5, 1)
            pygame.draw.circle(surface, COLOR_GREEN, (cx+8, cy-5), 5, 1)
            pygame.draw.line(surface, COLOR_GREEN, (cx-9, cy-5), (cx-7, cy-5), 2) # Small glowing pupils
            pygame.draw.circle(surface, COLOR_GREEN, (cx+7, cy-5), 1)
            # Scars / wrinkles
            pygame.draw.line(surface, COLOR_GREEN, (cx-15, cy-18), (cx-5, cy-18), 1)
            pygame.draw.line(surface, COLOR_GREEN, (cx+5, cy-18), (cx+15, cy-18), 1)
            pygame.draw.line(surface, COLOR_GREEN, (cx-18, cy+10), (cx-10, cy+8), 1)
            # Rotten smile / missing teeth (segmented line)
            pygame.draw.line(surface, COLOR_GREEN, (cx-12, cy+18), (cx+12, cy+18), 2)
            pygame.draw.line(surface, COLOR_GREEN, (cx-6, cy+15), (cx-6, cy+21), 1)
            pygame.draw.line(surface, COLOR_GREEN, (cx+6, cy+15), (cx+6, cy+21), 1)
            
        elif npc_id == "guard":
            # Power Armor Helmet: bulky, triangular visor, vents
            pygame.draw.polygon(surface, COLOR_GREEN, [
                (cx-30, cy-25), (cx+30, cy-25), (cx+35, cy+5), (cx+20, cy+35), (cx-20, cy+35), (cx-35, cy+5)
            ], 2) # Helmet shell
            # T-shaped dark visor
            pygame.draw.polygon(surface, COLOR_GREEN, [
                (cx-20, cy-10), (cx+20, cy-10), (cx+15, cy), (cx+4, cy), (cx+3, cy+12), (cx-3, cy+12), (cx-4, cy), (cx-15, cy)
            ], 2)
            # Tubes / respirator filters in the lower jaw corners
            pygame.draw.circle(surface, COLOR_GREEN, (cx-20, cy+25), 8, 2)
            pygame.draw.circle(surface, COLOR_GREEN, (cx+20, cy+25), 8, 2)
            # Grid vents in the mouth shield
            for x_offset in [-6, 0, 6]:
                pygame.draw.line(surface, COLOR_GREEN, (cx+x_offset, cy+18), (cx+x_offset, cy+32), 1)
                
        elif npc_id == "moira":
            # Moira: bubbly round head, curly hair, goggles
            pygame.draw.circle(surface, COLOR_GREEN, (cx, cy+5), 22, 2) # Head
            # Curly hair loops around the head
            for angle in range(0, 180, 30):
                rad = math.radians(angle)
                hx = int(cx + 25 * math.cos(rad))
                hy = int(cy + 5 - 25 * math.sin(rad))
                pygame.draw.circle(surface, COLOR_GREEN, (hx, hy), 6, 1)
            # Goggles on forehead
            pygame.draw.circle(surface, COLOR_GREEN, (cx-10, cy-12), 8, 2)
            pygame.draw.circle(surface, COLOR_GREEN, (cx+10, cy-12), 8, 2)
            pygame.draw.line(surface, COLOR_GREEN, (cx-2, cy-12), (cx+2, cy-12), 2)
            # Big happy smile
            pygame.draw.arc(surface, COLOR_GREEN, (cx-12, cy+2, 24, 14), math.PI if hasattr(math, "PI") else 3.14159, 2*3.14159, 2)
            # Bright eyes
            pygame.draw.circle(surface, COLOR_GREEN, (cx-7, cy+1), 2)
            pygame.draw.circle(surface, COLOR_GREEN, (cx+7, cy+1), 2)
            
        else:
            # Default / Alien face
            pygame.draw.circle(surface, COLOR_GREEN, (cx, cy), 20, 2)
            pygame.draw.line(surface, COLOR_GREEN, (cx-10, cy-5), (cx-5, cy-5), 2)
            pygame.draw.line(surface, COLOR_GREEN, (cx+5, cy-5), (cx+10, cy-5), 2)
            pygame.draw.line(surface, COLOR_GREEN, (cx-10, cy+8), (cx+10, cy+8), 2)

    def draw_combat(self, surface, combat):
        # Combat Arena Interface
        surface.fill(COLOR_BG_BLACK)
        
        # Border
        pygame.draw.rect(surface, COLOR_GREEN, (20, 20, self.width - 40, self.height - 40), 2)
        
        # Combat Title Header
        self.draw_text(surface, "V.A.T.S. ENGAGEMENT INTERFACE", 40, 32, self.font_large, color=COLOR_ALERT_RED)
        pygame.draw.line(surface, COLOR_ALERT_RED, (30, 60), (self.width - 30, 60), 2)
        
        # Player Stats (Left Side)
        player_rect = pygame.Rect(40, 80, 240, 160)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, player_rect, 1)
        self.draw_text(surface, "PLAYER STATS", 50, 90, self.font_medium)
        self.draw_text(surface, f"NAME  : {combat.player.name.upper()}", 50, 120, self.font_small)
        self.draw_text(surface, f"LEVEL : {combat.player.level}", 50, 145, self.font_small)
        
        # Health Bar
        hp_pct = max(0.0, min(1.0, combat.player.hp / combat.player.max_hp))
        self.draw_text(surface, f"HP: {combat.player.hp}/{combat.player.max_hp}", 50, 175, self.font_tiny)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (50, 195, 200, 10))
        pygame.draw.rect(surface, COLOR_GREEN, (50, 195, int(200 * hp_pct), 10))
        
        # Rads Bar
        rad_pct = max(0.0, min(1.0, combat.player.rad / combat.player.max_rad))
        rad_color = COLOR_RAD_YELLOW if combat.player.rad > 0 else COLOR_GREEN
        self.draw_text(surface, f"RADS: {int(combat.player.rad)}%", 50, 210, self.font_tiny, color=rad_color)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (50, 225, 200, 8))
        pygame.draw.rect(surface, rad_color, (50, 225, int(200 * rad_pct), 8))
        
        # Enemy Stats (Right Side)
        enemy_rect = pygame.Rect(self.width - 280, 80, 240, 160)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, enemy_rect, 1)
        self.draw_text(surface, "TARGET PROFILE", self.width - 270, 90, self.font_medium)
        self.draw_text(surface, f"NAME : {combat.enemy.name.upper()}", self.width - 270, 120, self.font_small)
        
        enemy_hp_pct = max(0.0, min(1.0, combat.enemy.hp / combat.enemy.max_hp))
        self.draw_text(surface, f"HP: {combat.enemy.hp}/{combat.enemy.max_hp}", self.width - 270, 155, self.font_tiny)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, (self.width - 270, 175, 200, 10))
        pygame.draw.rect(surface, COLOR_ALERT_RED, (self.width - 270, 175, int(200 * enemy_hp_pct), 10))
        
        # Combat Logs (Center/Lower)
        log_rect = pygame.Rect(40, 260, self.width - 80, 200)
        pygame.draw.rect(surface, COLOR_GREEN_DARK, log_rect, 1)
        self.draw_text(surface, "TACTICAL SITREP:", 50, 270, self.font_tiny)
        
        log_y = 295
        for log in combat.logs:
            # Highlight warning alerts in red
            color = COLOR_ALERT_RED if "hit you" in log or "DEFEAT" in log else COLOR_GREEN
            if "VICTORY" in log: color = COLOR_GREEN_BRIGHT
            self.draw_text(surface, log, 50, log_y, self.font_small, color=color)
            log_y += 24
            
        # Action Menu (At the bottom)
        menu_y = self.height - 150
        pygame.draw.line(surface, COLOR_GREEN, (40, menu_y), (self.width - 40, menu_y), 1)
        
        actions = combat.get_actions()
        col_w = (self.width - 80) // 4
        
        for i, action in enumerate(actions):
            act_x = 40 + i * col_w
            # Highlight selection
            color = COLOR_GREEN_BRIGHT if i == combat.selected_action else COLOR_GREEN_DARK
            self.draw_text(surface, f"[{action}]" if i == combat.selected_action else action, act_x + 10, menu_y + 20, self.font_small, color=color)
            
        # Quick prompts
        if combat.outcome is not None:
            prompt_text = "COMBAT CONCLUDED. PRESS ENTER TO CONTINUE..."
            self.draw_text(surface, prompt_text, 40, self.height - 60, self.font_medium, color=COLOR_GREEN_BRIGHT)
        else:
            self.draw_text(surface, "LEFT/RIGHT/UP/DOWN: CHOOSE | ENTER: EXECUTE COMMAND", 40, self.height - 60, self.font_tiny)

    def draw_terminal(self, surface, logs):
        surface.fill(COLOR_BG_BLACK)
        pygame.draw.rect(surface, COLOR_GREEN, (30, 30, self.width - 60, self.height - 60), 2)
        
        log_y = 60
        for line in logs:
            self.draw_text(surface, line, 60, log_y, self.font_medium)
            log_y += 35
            
        self.draw_text(surface, "PRESS ENTER OR ESCAPE TO EXIT TERMINAL SYSTEM", 60, self.height - 80, self.font_small, color=COLOR_GREEN_BRIGHT)

    def draw_intro_screen(self, surface, player_name, special_points, temp_special, cursor_idx):
        surface.fill(COLOR_BG_BLACK)
        pygame.draw.rect(surface, COLOR_GREEN, (20, 20, self.width - 40, self.height - 40), 2)
        
        # Boot sequence
        self.draw_text(surface, "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM", 40, 40, self.font_medium)
        self.draw_text(surface, "COPYRIGHT 2075-2077 ROBCO CORP", 40, 65, self.font_tiny)
        self.draw_text(surface, "=== VAULT 404 RESIDENT REGISTRATION ===", 40, 95, self.font_large, color=COLOR_GREEN_BRIGHT)
        
        # Name Input
        self.draw_text(surface, f"ENTER RESIDENT NAME: {player_name}_", 40, 150, self.font_medium)
        
        # SPECIAL Distributor
        self.draw_text(surface, f"DISTRIBUTE S.P.E.C.I.A.L. POINTS ({special_points} REMAINING):", 40, 200, self.font_medium)
        
        stats = list(temp_special.keys())
        y_pos = 240
        for i, stat in enumerate(stats):
            color = COLOR_GREEN_BRIGHT if i == cursor_idx else COLOR_GREEN
            stat_name = stat.upper()
            val = temp_special[stat]
            self.draw_text(surface, f"{stat_name:<15}: {val}  (<- / -> to adjust)", 60, y_pos, self.font_medium, color=color)
            y_pos += 26
            
        self.draw_text(surface, "PRESS ENTER TO CONFIRM REGISTRATION AND ENTER VAULT", 40, self.height - 70, self.font_medium, color=COLOR_GREEN_BRIGHT)

    def draw_death_screen(self, surface):
        surface.fill((15, 0, 0)) # Red tint black
        pygame.draw.rect(surface, COLOR_ALERT_RED, (20, 20, self.width - 40, self.height - 40), 2)
        
        self.draw_text(surface, "=== DIED IN THE WASTELAND ===", self.width//2 - 250, self.height//2 - 60, self.font_large, color=COLOR_ALERT_RED)
        
        self.draw_text(surface, "Vault 404 security logs record your vital signs at 0.00%.", self.width//2 - 260, self.height//2, self.font_medium)
        self.draw_text(surface, "Humanity's reclamation has failed this time.", self.width//2 - 260, self.height//2 + 30, self.font_medium)
        
        self.draw_text(surface, "PRESS ENTER TO TRY AGAIN", self.width//2 - 160, self.height//2 + 100, self.font_medium, color=COLOR_GREEN_BRIGHT)

    def draw_bootstrap_screen(self, surface, bootstrap):
        surface.fill(COLOR_BG_BLACK)
        pygame.draw.rect(surface, COLOR_GREEN, (20, 20, self.width - 40, self.height - 40), 2)
        
        # Header
        self.draw_text(surface, "ROBCO INDUSTRIES NEURAL BOOTSTRAP UTILITY", 40, 40, self.font_medium)
        self.draw_text(surface, "SYSTEM RECLAMATION INITIALIZATION PROTOCOL", 40, 65, self.font_tiny)
        pygame.draw.line(surface, COLOR_GREEN, (30, 85), (self.width - 30, 85), 2)
        
        status = bootstrap.status
        
        if status == "checking":
            self.draw_text(surface, "PINGING LOCAL NEURAL PROCESSORS...", 40, 150, self.font_large)
            self.draw_text(surface, "Locating Ollama host service on port 11434...", 40, 200, self.font_small)
            # Animated spinner
            dots = "." * ((pygame.time.get_ticks() // 200) % 4)
            self.draw_text(surface, f"CONNECTING{dots}", 40, 240, self.font_medium, color=COLOR_GREEN_BRIGHT)
            
        elif status == "starting":
            self.draw_text(surface, "OLLAMA OFFLINE. STARTING SERVICE...", 40, 150, self.font_large)
            self.draw_text(surface, "Running background service daemon 'ollama serve'...", 40, 200, self.font_small)
            self.draw_text(surface, "Waiting for local port binding to complete...", 40, 230, self.font_small)
            # Animated spinner
            dots = "." * ((pygame.time.get_ticks() // 200) % 4)
            self.draw_text(surface, f"INITIALIZING CORE SYSTEM{dots}", 40, 280, self.font_medium, color=COLOR_GREEN_BRIGHT)
            
        elif status == "pulling":
            self.draw_text(surface, "DOWNLOADING COGNITIVE ENGINES (llama3.2)...", 40, 150, self.font_large, color=COLOR_GREEN_BRIGHT)
            self.draw_text(surface, "This is an automated setup step to download the 2.0GB LLM brain model.", 40, 190, self.font_small)
            self.draw_text(surface, "Please remain connected to the network. Do not close this terminal.", 40, 215, self.font_small)
            
            # Progress Bar
            progress = bootstrap.progress
            self.draw_text(surface, f"Progress: {progress:.1f}%", 40, 270, self.font_medium)
            
            bar_w = self.width - 160
            pygame.draw.rect(surface, COLOR_GREEN_DARK, (80, 310, bar_w, 20))
            pygame.draw.rect(surface, COLOR_GREEN, (80, 310, int(bar_w * (progress / 100.0)), 20))
            pygame.draw.rect(surface, COLOR_GREEN_BRIGHT, (80, 310, bar_w, 20), 1)
            
        elif status in ["not_installed", "not_running"]:
            self.draw_text(surface, "NEURAL INTERFACE WARNING", 40, 150, self.font_large, color=COLOR_ALERT_RED)
            
            # Draw warning box
            pygame.draw.rect(surface, COLOR_ALERT_RED, (40, 190, self.width - 80, 150), 1)
            
            lines = [
                f"STATUS: {bootstrap.error_msg}",
                "",
                "1. Game will fall back to Offline (Static) Dialogue Mode.",
                "2. To experience full dynamic LLM conversations, download and start Ollama.",
                "   Website: https://ollama.com"
            ]
            y_pos = 205
            for line in lines:
                self.draw_text(surface, line, 50, y_pos, self.font_small, color=COLOR_ALERT_RED)
                y_pos += 24
                
            self.draw_text(surface, "PRESS ENTER: CONTINUE TO CHARACTER REGISTRATION (OFFLINE MODE)", 40, self.height - 120, self.font_medium, color=COLOR_GREEN_BRIGHT)
            self.draw_text(surface, "PRESS  O   : OPEN OLLAMA DOWNLOAD PAGE IN BROWSER", 40, self.height - 85, self.font_medium)
            
        elif status == "offline_fallback":
            self.draw_text(surface, "BOOTSTRAP EXCEPTION DETECTED", 40, 150, self.font_large, color=COLOR_ALERT_RED)
            self.draw_text(surface, bootstrap.error_msg, 40, 200, self.font_small, color=COLOR_ALERT_RED)
            self.draw_text(surface, "PRESS ENTER TO RUN IN OFFLINE BACKUP MODE...", 40, 300, self.font_medium, color=COLOR_GREEN_BRIGHT)
