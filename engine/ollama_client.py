import json
import requests

class OllamaClient:
    def __init__(self, host="http://localhost:11434"):
        self.host = host
        self.enabled = False
        self.model = "llama3.2:latest"
        
        # Test connection and detect models
        self.detect_model()
        
    def detect_model(self):
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=1.5)
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    self.enabled = True
                    # Prioritize llama3.2, but fall back to whatever is available
                    if "llama3.2:latest" in models:
                        self.model = "llama3.2:latest"
                    elif "llama3.2" in models:
                        self.model = "llama3.2"
                    else:
                        self.model = models[0]
                    print(f"Ollama connected successfully. Using model: {self.model}")
                else:
                    print("Ollama connected, but no models found. Run 'ollama pull llama3.2'")
                    self.enabled = False
            else:
                self.enabled = False
        except Exception as e:
            print(f"Ollama offline or unreachable: {e}")
            self.enabled = False

    def query_npc(self, npc_profile, game_state, chat_history, player_message):
        """
        Sends dialogue to Ollama and returns structured JSON response.
        If Ollama is disabled/fails, returns a rule-based mock response.
        """
        if not self.enabled:
            return self._get_fallback_response(npc_profile["id"], game_state, chat_history, player_message)
            
        # Build prompt
        system_prompt = f"""You are an NPC in a Fallout-themed retro 2D RPG.
Your name: {npc_profile['name']}
Your role/description: {npc_profile['role']}
Your personality: {npc_profile['personality']}
Your lore/knowledge: {npc_profile['lore']}
Your goal/secret in this interaction: {npc_profile['secret']}

Current Game State:
- Player Name: {game_state['player_name']}
- Player HP: {game_state['player_hp']}/100
- Player Radiation (Rads): {game_state['player_rad']}/100
- Player Caps: {game_state['player_caps']}
- Player Inventory: {', '.join([f"{item['name']} (x{item['qty']})" for item in game_state['inventory']])}
- Quest Progress: {json.dumps(game_state['quests'])}

Respond in character. You must output a valid JSON object only. Do not include markdown code block formatting like ```json or ```. Output ONLY the JSON raw text.
The JSON object must follow this structure:
{{
  "reply": "Write your in-character spoken dialogue response here.",
  "mood": "Choose one of: neutral, happy, angry, suspicious, scared, sarcastic.",
  "action": "Trigger a game event. Choose ONLY from: NONE, GIVE_ITEM, TAKE_ITEM, GIVE_CAPS, TAKE_CAPS, START_COMBAT, ADVANCE_QUEST, HEAL_PLAYER.",
  "action_payload": "String payload for the action. For GIVE_ITEM/TAKE_ITEM use item_id (e.g. 'water_chip', 'plasma_pistol', 'stimpak'). For GIVE_CAPS/TAKE_CAPS use amount (e.g. '50'). For ADVANCE_QUEST use a trigger name (e.g. 'purifier_fixed', 'door_unlocked'). For HEAL_PLAYER use amount (e.g. '40'). Keep empty for NONE or START_COMBAT."
}}

CRITICAL ACTION RULES:
1. ONLY trigger GIVE_ITEM or GIVE_CAPS if the player has fulfilled a condition, earned it, or if it fits your character's generous nature in this context.
2. ONLY trigger ADVANCE_QUEST if the player has supplied the required item (e.g., they have the water_chip or fusion_core in their inventory and you are taking it) or solved a puzzle.
3. Trigger START_COMBAT if the player is hostile, insults you repeatedly, threatens you, or if you are a guard and they try to pass without permission.
"""

        # Format chat history for Ollama API
        messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history[-6:]: # Keep last 6 exchanges for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": player_message})
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            }
            
            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=8.0)
            if response.status_code == 200:
                result_json = response.json()
                content_str = result_json["message"]["content"].strip()
                
                # Double check if LLM wrapped in code blocks and clean it
                if content_str.startswith("```json"):
                    content_str = content_str[7:]
                if content_str.endswith("```"):
                    content_str = content_str[:-3]
                content_str = content_str.strip()
                
                parsed = json.loads(content_str)
                return parsed
            else:
                print(f"Ollama returned status {response.status_code}. Using fallback.")
                return self._get_fallback_response(npc_profile["id"], game_state, chat_history, player_message)
        except Exception as e:
            print(f"Error calling Ollama API: {e}. Using fallback.")
            return self._get_fallback_response(npc_profile["id"], game_state, chat_history, player_message)

    def _get_fallback_response(self, npc_id, game_state, chat_history, player_message):
        """Rule-based dialog fallback when Ollama is offline or fails."""
        msg_lower = player_message.lower()
        reply = "Sorry, my brain processor seems to be jammed..."
        action = "NONE"
        payload = ""
        mood = "neutral"
        
        if npc_id == "overseer":
            mood = "suspicious"
            if "hello" in msg_lower or "hi" in msg_lower:
                reply = "Greetings, citizen. What is your business in the Overseer's office? We must maintain order in Vault 404."
            elif "water" in msg_lower or "purifier" in msg_lower or "chip" in msg_lower:
                reply = "The water purifier is failing, yes. I have the spare parts, but I cannot trust just anyone. Bring me Rusty's report, or prove your loyalty."
                if any(i["id"] == "water_chip" for i in game_state["inventory"]):
                    reply = "Ah! You found the Water Chip! Outstanding work. Here is the Vault door keycard as promised. Now, secure our future."
                    action = "GIVE_ITEM"
                    payload = "vault_keycard"
                    # Also take water_chip
                    # Note: engine handles item transfers based on action
            elif "keycard" in msg_lower or "leave" in msg_lower or "gate" in msg_lower:
                reply = "Leave the Vault? Absolute madness! The Wasteland is a toxic death trap. I cannot allow it... unless you fix our water purifier first."
            elif "attack" in msg_lower or "fight" in msg_lower or "die" in msg_lower or "idiot" in msg_lower:
                reply = "Insolent rebel! Security, neutralize this threat!"
                action = "START_COMBAT"
                mood = "angry"
            else:
                reply = "Our primary directive is survival. Do not disrupt Vault operations."
                
        elif npc_id == "rusty":
            mood = "sarcastic"
            if "hello" in msg_lower or "hi" in msg_lower:
                reply = "Names Rusty. Don't stare at the skin, kid. It's just a little post-war tan. What do you need fixed?"
            elif "purifier" in msg_lower or "water" in msg_lower or "fix" in msg_lower:
                if game_state["quests"].get("water_purifier") == "completed":
                    reply = "Purifier's running clean now. Thanks to you, we aren't drinking radioactive sludge."
                elif any(i["id"] == "water_chip" for i in game_state["inventory"]):
                    reply = "Holy caps, you actually got a Water Chip! Let me plug this baby in. That fixes the water purifier! Go tell the Overseer, he'll have to let you out now."
                    action = "ADVANCE_QUEST"
                    payload = "purifier_fixed"
                else:
                    reply = "The main water purifier is fried. Need a Water Chip to fix it. Heard there might be one in the old storage crates, or Moira in the Wasteland might have one. Bring it to me."
            elif "plasma" in msg_lower or "weapon" in msg_lower:
                if game_state["player_caps"] >= 50:
                    reply = "I got a surplus Plasma Pistol. Clean lines, melting capability. Yours for 50 caps."
                    action = "TAKE_CAPS"
                    payload = "50"
                    # Note: engine will chain giving plasma pistol
                else:
                    reply = "You want this Plasma Pistol? It'll cost you 50 caps. Come back when you're loaded."
            else:
                reply = "Keep it moving, smoothskin. I've got machinery to calibrate."
                
        elif npc_id == "moira":
            mood = "happy"
            if "hello" in msg_lower or "hi" in msg_lower:
                reply = "Oh! Hello there! A real live Vault Dweller! I'm Moira, research assistant and trader. Welcome to my shop!"
            elif "buy" in msg_lower or "trade" in msg_lower or "stimpak" in msg_lower:
                if game_state["player_caps"] >= 15:
                    reply = "Sure! Here is a fresh Stimpak. Safe travels!"
                    action = "TAKE_CAPS"
                    payload = "15"
                else:
                    reply = "Stimpaks are 15 caps. You're a bit short, sweetie."
            elif "chip" in msg_lower or "water" in msg_lower:
                reply = "A Water Chip? Oh, I found one in a pile of junk near the ruins! I'd gladly trade it for some spare parts, or say, 30 caps?"
                if game_state["player_caps"] >= 30:
                    reply = "Perfect! Here's the Water Chip. Don't wash it in radioactive water, haha!"
                    action = "TAKE_CAPS"
                    payload = "30"
                    # Note: engine gives water_chip
                else:
                    reply = "I'll let you have the Water Chip for 30 caps. Let me know when you have the coin!"
            else:
                reply = "The Wasteland is a beautiful, scary place! Need any supplies or info?"
                
        elif npc_id == "guard":
            mood = "suspicious"
            if "hello" in msg_lower or "hi" in msg_lower:
                reply = "Halt. Sentinel Sterling, Brotherhood of Steel. State your business at the Vault Gate."
            elif "open" in msg_lower or "leave" in msg_lower or "pass" in msg_lower:
                if any(i["id"] == "vault_keycard" for i in game_state["inventory"]):
                    reply = "Vault Keycard detected. Access granted. Stand back as the vault door opens."
                    action = "ADVANCE_QUEST"
                    payload = "door_unlocked"
                else:
                    reply = "No one leaves the Vault without the Overseer's Keycard. Security protocols are absolute."
            elif "brotherhood" in msg_lower:
                reply = "We preserve technology to prevent humanity from burning itself out a second time."
            elif "attack" in msg_lower or "force" in msg_lower:
                reply = "Hostile action detected! Engaging target!"
                action = "START_COMBAT"
                mood = "angry"
            else:
                reply = "Move along. I am on duty."
                
        return {
            "reply": "[OFFLINE DIALOGUE] " + reply,
            "mood": mood,
            "action": action,
            "action_payload": payload
        }
