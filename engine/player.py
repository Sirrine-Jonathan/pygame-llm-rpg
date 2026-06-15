class Player:
    def __init__(self, name="Vault Dweller"):
        self.name = name
        
        # S.P.E.C.I.A.L. Stats
        self.special = {
            "Strength": 6,
            "Perception": 7,
            "Endurance": 5,
            "Charisma": 7,
            "Intelligence": 8,
            "Agility": 6,
            "Luck": 5
        }
        
        # Vitals
        self.max_hp = 100
        self.hp = 100
        self.max_rad = 100
        self.rad = 0  # Radiation
        
        # Progression
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        self.caps = 25
        
        # Position & World State
        self.x = 2
        self.y = 2
        self.current_area = "vault"  # "vault" or "wasteland"
        
        # Inventory: list of dicts {id, name, type, qty, value, desc, combat_val}
        self.inventory = [
            {
                "id": "vault_suit",
                "name": "Vault Jumpsuit",
                "type": "apparel",
                "qty": 1,
                "value": 10,
                "desc": "A snug-fitting blue jumpsuit with yellow lining. Size 38.",
                "combat_val": 5  # Damage resistance
            },
            {
                "id": "stimpak",
                "name": "Stimpak",
                "type": "aid",
                "qty": 2,
                "value": 20,
                "desc": "A chemical syringe that boosts cell regeneration. Heals 40 HP.",
                "combat_val": 40
            },
            {
                "id": "bobby_pin",
                "name": "Bobby Pin",
                "type": "misc",
                "qty": 3,
                "value": 5,
                "desc": "A simple hairpin. Useful for picking locks.",
                "combat_val": 0
            }
        ]
        
        # Equipped items
        self.equipped_weapon = None
        self.equipped_armor = "vault_suit"
        
    def add_item(self, item_id, name, item_type, qty=1, value=10, desc="", combat_val=0):
        # Check if item already exists in inventory
        for item in self.inventory:
            if item["id"] == item_id:
                item["qty"] += qty
                return
        
        # Add new item
        self.inventory.append({
            "id": item_id,
            "name": name,
            "type": item_type,
            "qty": qty,
            "value": value,
            "desc": desc,
            "combat_val": combat_val
        })

    def remove_item(self, item_id, qty=1):
        for item in self.inventory:
            if item["id"] == item_id:
                if item["qty"] > qty:
                    item["qty"] -= qty
                    return True
                elif item["qty"] == qty:
                    self.inventory.remove(item)
                    if self.equipped_weapon == item_id:
                        self.equipped_weapon = None
                    if self.equipped_armor == item_id:
                        self.equipped_armor = None
                    return True
        return False

    def has_item(self, item_id, qty=1):
        for item in self.inventory:
            if item["id"] == item_id:
                return item["qty"] >= qty
        return False

    def use_item(self, item_id):
        # Find item
        target_item = None
        for item in self.inventory:
            if item["id"] == item_id:
                target_item = item
                break
                
        if not target_item:
            return False, "Item not found in inventory."
            
        if target_item["type"] == "aid":
            if target_item["id"] == "stimpak":
                if self.hp >= self.max_hp:
                    return False, "Health is already full!"
                self.hp = min(self.max_hp, self.hp + target_item["combat_val"])
                self.remove_item(item_id, 1)
                return True, f"Used Stimpak. Healed {target_item['combat_val']} HP."
                
            elif target_item["id"] == "radaway":
                if self.rad == 0:
                    return False, "You have no radiation poisoning!"
                self.rad = max(0, self.rad - target_item["combat_val"])
                self.remove_item(item_id, 1)
                return True, f"Used RadAway. Cleared {target_item['combat_val']} Rads."
                
        elif target_item["type"] == "weapon":
            if self.equipped_weapon == item_id:
                self.equipped_weapon = None
                return True, f"Unequipped {target_item['name']}."
            else:
                self.equipped_weapon = item_id
                return True, f"Equipped {target_item['name']}."
                
        elif target_item["type"] == "apparel":
            if self.equipped_armor == item_id:
                self.equipped_armor = None
                return True, f"Unequipped {target_item['name']}."
            else:
                self.equipped_armor = item_id
                return True, f"Equipped {target_item['name']}."
                
        return False, "This item cannot be used directly."

    def take_damage(self, amount):
        # Calculate defense based on armor
        armor_defense = 0
        if self.equipped_armor:
            for item in self.inventory:
                if item["id"] == self.equipped_armor:
                    armor_defense = item["combat_val"]
                    break
        
        # Mitigate damage
        actual_damage = max(1, amount - armor_defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def take_radiation(self, amount):
        # Endurance mitigates radiation
        rad_resistance = self.special["Endurance"] * 0.5
        actual_rad = max(0.5, amount - rad_resistance)
        self.rad = min(self.max_rad, self.rad + actual_rad)
        
        # If radiation is maxed out, player dies or loses HP
        if self.rad >= self.max_rad:
            self.hp = 0
        return actual_rad

    def gain_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            # Increase stats slightly on level up
            self.max_hp += 10
            self.hp = self.max_hp
            leveled_up = True
        return leveled_up

    def get_attack_power(self):
        base_dmg = 5 + (self.special["Strength"] // 2)
        if self.equipped_weapon:
            for item in self.inventory:
                if item["id"] == self.equipped_weapon:
                    base_dmg += item["combat_val"]
                    break
        return base_dmg
