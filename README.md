# Vault 404: Wasteland Reclamation Utility
A retro post-apocalyptic RPG built using **Pygame** where the NPCs are powered by a **local Ollama LLM**. The game interface, graphics, sound effects, and menus are styled in the iconic, glowing green CRT style of the Fallout series' Pip-Boy.

---

## 🎮 Story & Setting
You are a Resident of **Vault 404**, an underground shelter designed to preserve humanity. However, a twin crisis threatens the vault:
1. **The Water Purifier has failed**, leaving only 3 days of clean supply.
2. **The Overseer has sealed the Vault doors**, refusing to let anyone exit to salvage parts.

To save Vault 404, you must explore the Vault quarters, interact with terminals, search storage crates, and talk to NPCs. If you manage to find the **Water Chip**, you can repair the purifier. If you get the **Vault Keycard**, you can escape into the toxic ruins of the **Wasteland**. 

---

## ⚙️ Features
- **Dynamic Local LLM NPCs**: Talk to NPCs using free-text chat! The game sends the NPC's profile, dialog history, and current game state (your inventory, caps, stats, quest progression) to your local Ollama model.
- **Structured Game Actions**: The LLM outputs JSON payloads, allowing the NPCs to dynamically decide when to:
  - **Give/Take items** (e.g., trading caps for a Stimpak, giving you a keycard).
  - **Advance quests** (e.g., recognizing you brought the Water Chip and fixing the purifier).
  - **Initiate turn-based combat** (if you insult or threaten them, they turn hostile and attack).
- **Fallout Pip-Boy CRT Aesthetic**: Dynamic screen scanlines, screen-glitch overlays, and rounded glass bezels simulate an old computer monitor.
- **Monochrome Vector Avatars**: Characters are drawn procedurally as glowing green wireframes representing their physical traits and current mood.
- **Procedural Sound Synthesis**: Features custom synth sound effects (laser fire, clicks, radiation crackling, level-up fanfares, door slides) generated mathematically on the fly, requiring no external `.wav` or `.mp3` assets.
- **Pip-Boy Interface**: Press `TAB` to open your wrist-worn Pip-Boy 3000 to manage your **STATS** (SPECIAL values, HP, Radiation), **INV** (use Stimpaks/RadAway, equip weapons), and **DATA** (track quest objectives).
- **V.A.T.S. Combat**: A tactical turn-based combat overlay with hit chances based on your **Perception** and **Luck** stats.

---

## 🚀 How to Run the Game

### Method 1: Local Virtual Environment (Recommended)
This is the easiest way to run the game, as it runs Pygame natively on your host system with full display and audio support.

1. **Set up and Run**:
   ```bash
   ./run.sh
   ```
   *This script will automatically check for Python 3, create a virtual environment (`.venv`), install all requirements, check if Ollama is running, and launch the game.*

### Method 2: Docker Compose
If you prefer to run both the game and a fresh Ollama instance inside isolated Docker containers:

1. **Enable local GUI connections** (On Linux/WSL):
   ```bash
   xhost +local:docker
   ```
2. **Build and Run**:
   ```bash
   docker compose up --build
   ```

---

## 🧠 Setting up Ollama
To activate the dynamic dialogue system:
1. Ensure the Ollama service is running on your system (defaults to `http://localhost:11434`).
2. Download the lightweight and fast `llama3.2` model (ideal for structured json and quick response times):
   ```bash
   ollama pull llama3.2
   ```

### ⚡ Offline Fallback Mode
If Ollama is not running or the model is not found, **the game will not crash**. It will display a warning and automatically load a **rule-based fallback dialogue engine** that parses keyphrases (like "hello", "purifier", "caps", "keycard") so the entire story and gameplay loop remains fully playable!

---

## 🕹️ Controls
- **Arrow Keys / WASD**: Move character around the grid map.
- **E**: Interact with adjacent objects (terminals, crates, closed doors).
- **TAB**: Open / Close the Pip-Boy interface.
- **1, 2, 3** (while inside Pip-Boy): Navigate between STAT, INV, and DATA tabs.
- **Enter**: Type dialogue message / Confirm selections / Advance screens.
