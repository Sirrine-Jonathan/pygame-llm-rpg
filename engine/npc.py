import pygame

class NPC:
    def __init__(self, npc_id, name, area, x, y, role, personality, lore, secret, hp=80, max_hp=80, attack=8):
        self.id = npc_id
        self.name = name
        self.area = area
        self.x = x
        self.y = y
        
        # Dialogue system configuration
        self.role = role
        self.personality = personality
        self.lore = lore
        self.secret = secret
        self.chat_history = []  # List of {"role": "user"/"assistant", "content": "..."}
        
        # Combat stats
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.hostile = False
        
    def get_profile(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "personality": self.personality,
            "lore": self.lore,
            "secret": self.secret
        }

    def reset_chat(self):
        self.chat_history = []


class Enemy:
    def __init__(self, enemy_id, name, area, x, y, hp=30, max_hp=30, attack=6, xp_reward=25, loot=None):
        self.id = enemy_id
        self.name = name
        self.area = area
        self.x = x
        self.y = y
        
        # Combat stats
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.xp_reward = xp_reward
        self.loot = loot or []  # List of item dicts
        
        self.hostile = True
        
    def get_loot(self):
        return self.loot


def get_default_npcs():
    return [
        NPC(
            npc_id="overseer",
            name="Overseer Jacobe",
            area="vault",
            x=12,
            y=3,
            role="Supreme Leader of Vault 404",
            personality="Authoritarian, suspicious, paranoid, speaks with dry formality, believes the outside world is 100% uninhabitable.",
            lore="Knows that the Vault's water purifier is failing and that Vault 404 was designed as an experiment where the doors would never open. Has the only Vault Door Keycard in his desk.",
            secret="Wants the player to fix the water purifier. Will NEVER allow the player to leave unless they prove the purifier is running, or if they bribe/persuade him with high Charisma/Caps, or steal it, or kill him.",
            hp=100,
            max_hp=100,
            attack=10
        ),
        NPC(
            npc_id="rusty",
            name="Rusty",
            area="vault",
            x=4,
            y=11,
            role="Ghoulish Vault Mechanic",
            personality="Cynical, tired, sarcastic, but secretly helpful. Dislikes the Overseer's strict rules. Speaks in gruff slang.",
            lore="Knows all vault systems. Knows the water purifier needs a specific pre-war Water Chip to filter the radiation out. Has an old Plasma Pistol he's willing to sell.",
            secret="Wants the Water Chip to save the Vault. If player brings him the Water Chip, he will install it and give the player a customized Plasma Pistol as a reward. Can sell the Plasma Pistol for 50 caps.",
            hp=90,
            max_hp=90,
            attack=12
        ),
        NPC(
            npc_id="guard",
            name="Sentinel Sterling",
            area="vault",
            x=17,
            y=8,
            role="Brotherhood of Steel Gatekeeper",
            personality="Stoic, disciplined, unwavering, suspicious of anyone trying to exit. Speaks in military code.",
            lore="Guards the main Vault elevator gate. Knows that entering the Wasteland without a hazmat suit or high radiation tolerance is lethal. Has orders to shoot anyone attempting to force the door.",
            secret="Will open the gate only if the player possesses the Vault Keycard. Can be persuaded to step aside if the player has Intelligence >= 8 (by talking about reactor maintenance) or Charisma >= 7.",
            hp=120,
            max_hp=120,
            attack=15
        ),
        NPC(
            npc_id="moira",
            name="Moira",
            area="wasteland",
            x=6,
            y=6,
            role="Wasteland Merchant and Explorer",
            personality="Upbeat, bubbly, extremely optimistic despite the ruins, eccentric, speaks fast and laughs at weird things.",
            lore="Has traveled the ruins. Discovered a stockpile of pre-war technology in a nearby crate. Sells medical supplies and has a spare 'Water Chip' she salvaged from a broken vault.",
            secret="Will trade the Water Chip for 30 caps, or for 2 Stimpaks. Sells Stimpaks for 15 caps and RadAway for 15 caps.",
            hp=70,
            max_hp=70,
            attack=8
        )
    ]

def get_default_enemies():
    return [
        Enemy(
            enemy_id="radroach_1",
            name="Radroach",
            area="vault",
            x=4,
            y=7,
            hp=20,
            max_hp=20,
            attack=4,
            xp_reward=15,
            loot=[{"id": "bobby_pin", "name": "Bobby Pin", "type": "misc", "qty": 1, "value": 5, "desc": "Found inside the carcass."}]
        ),
        Enemy(
            enemy_id="radroach_2",
            name="Giant Radroach",
            area="vault",
            x=14,
            y=12,
            hp=25,
            max_hp=25,
            attack=5,
            xp_reward=20,
            loot=[{"id": "stimpak", "name": "Stimpak", "type": "aid", "qty": 1, "value": 20, "desc": "Tangled in the roach's legs.", "combat_val": 40}]
        ),
        Enemy(
            enemy_id="raider_1",
            name="Wasteland Raider",
            area="wasteland",
            x=14,
            y=6,
            hp=45,
            max_hp=45,
            attack=8,
            xp_reward=35,
            loot=[
                {"id": "10mm_pistol", "name": "10mm Pistol", "type": "weapon", "qty": 1, "value": 45, "desc": "A sturdy pre-war sidearm. +15 Damage.", "combat_val": 15},
                {"id": "caps", "name": "Bottle Caps", "type": "currency", "qty": 18, "value": 1, "desc": "Wasteland money."}
            ]
        ),
        Enemy(
            enemy_id="raider_2",
            name="Scavver Guard",
            area="wasteland",
            x=10,
            y=11,
            hp=50,
            max_hp=50,
            attack=9,
            xp_reward=40,
            loot=[
                {"id": "radaway", "name": "RadAway", "type": "aid", "qty": 1, "value": 20, "desc": "Clears 50 rads.", "combat_val": 50},
                {"id": "caps", "name": "Bottle Caps", "type": "currency", "qty": 22, "value": 1, "desc": "Wasteland money."}
            ]
        )
    ]
