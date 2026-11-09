# 🌟 GoLuminamics

<div align="center">

**A Strategic Board Game Where Light Becomes Your Path to Victory**

**Made with ❤️ and ☕ by the GoLuminamics Team**

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/plantacerium)

⭐ **Star us on GitHub** if you enjoy the game! ⭐
</div>


## 🎯 What is GoLuminamics?

GoLuminamics is a **strategic territory control game** that combines the depth of Go with the physics of light. Place optical stones (prisms, mirrors, splitters, blockers) on a configurable board (9×9 to 39×39) and fire laser beams to illuminate territory, reflect rays, and capture opponent pieces.

### ✨ Key Features

- 🔮 **Four Optical Stone Types**: Prisms (transmit/refract), Mirrors (reflect), Splitters (branch into two), Blockers (defensive wall).
- 🧩 **Modern Bottom HUD**: Quick-access horizontal piece selector with key shortcuts (`1`-`4`) and glowing active indicators. Easily extensible for custom pieces!
- ⛶ **Collapsible Panels & Focus Mode**: Drag to customize widths with `QSplitter`, toggle sidebars individually, or activate **"⛶ Solo Tablero"** to collapse all sidebars and expand the board to 100% of the screen.
- ⚡ **Real-Time Laser Physics**: Watch beams bounce, split, and illuminate the board in real time.
- ⏱️ **Action-Activated Clock**: Timers remain safely idle on startup—countdown begins only when a player takes an action or starts an AI match.
- 🌲 **Optical MCTS Engine**: Built-in Monte Carlo Tree Search engine with optical resonance pruning, running ~5,000 simulations per second.
- 🤖 **Live UI ⇄ MCP Agent Bridge**: Play against AI agents (like **Antigravity**) directly from chat via Model Context Protocol (MCP 2.x) with live screen animation!
- 🧠 **AI Arena with Thought Streamer**: Watch LLM agents (Ollama / Gemma / LLaMA / MCTS) battle in real time with an interactive HUD streaming their inner thoughts.
- 📐 **Adjustable Board Size**: 9×9 to 39×39 grids for different game lengths.
- ♾️ **Flexible Game Modes**: Infinite energy, infinite score (no mercy rule), and customizable timers.
- 💾 **Game Recording & Replayer**: Save and replay every match step by step.

---

## 🖼️ Screenshots

<div align="center">

### Main Game Board
![Game Board](assets/screenshots/Board_Game.JPG)
*Strategic stone placement with laser beam visualization*

### Main Replayer Board
![Replayer Board](assets/screenshots/Board_Replayer.JPG)

### Victory Screen
![Replayer Board](assets/screenshots/Board_Victory.JPG)

</div>

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the game (Human vs Human with Bottom HUD & Focus Mode)
python -m _00_entry.main_game

# Launch the AI Arena (Spectator Mode with Thought Streamer & MCP mode)
python -m _00_entry.arena_ui

# Launch the Replayer
python -m _00_entry.main_replayer

# Launch the Native MCP Server (for AI Assistants & IDEs)
python mcp_server.py
```

---

## 🤖 Playing with AI: Arena, MCTS & Antigravity MCP

### 1. Playing Against Antigravity (Live MCP Mode)
1. Open the Arena:
   ```bash
   python _00_entry/arena_ui.py
   ```
2. Click the purple button **`[ 🤖 AI MCP (Jugar contra Antigravity) ]`** in the control panel.
3. In your Antigravity chat, simply ask:
   > *"Antigravity, haz tu jugada"* or *"Antigravity, calcula con MCTS y dispara el láser"*
4. Antigravity will inspect your active board state via the local bridge (`127.0.0.1:18989`), compute the move, and execute it live on your screen while streaming its tactical thoughts into the Thought Streamer HUD!

### 2. High-Speed Optical MCTS Engine (No Ollama Needed)
You can pit the built-in Monte Carlo Tree Search engine against Ollama models or run an MCTS vs MCTS tournament:
```bash
# MCTS Engine vs Ollama Gemma 3
python _00_entry/arena_ui.py --p1 mcts --p2 gemma3:4b

# MCTS vs MCTS Tournament (Pure mathematical optical search at 5,000 sims/sec)
python _00_entry/arena_ui.py --p1 mcts:500 --p2 mcts:500 --auto-start
```

### 3. Model Context Protocol (MCP 2.x) Tools
The server exposes 13 tools via stdio:
- `luminamics_get_board_state`: Real-time ASCII board, piece list, energies, captures, and scores (synced with live UI when open).
- `luminamics_mcts_recommend_move`: Executes Monte Carlo Tree Search with optical resonance pruning and returns the optimal tactical move.
- `luminamics_simulate_laser`: Ray-casting sandbox to simulate reflections and captures before playing.
- `luminamics_place_stone`, `luminamics_rotate_stone`, `luminamics_shoot_laser`, `luminamics_move_stone`, `luminamics_pass_turn`.
- `luminamics_list_playbooks`, `luminamics_read_playbook`: 50+ strategy playbooks from Grandmasters.

---

## 🎮 How to Play

### Game Objective
Control more territory than your opponent by strategically placing stones and firing lasers to illuminate the board.

### Stone Types (Bottom HUD)

| Stone | Symbol | Hotkey | Effect | Strategic Role |
|:---|:---:|:---:|:---|:---|
| **Prism** | ▲ | `1` | Transmits / refracts laser at 45° or 90° | Path builder & directional splitter |
| **Mirror** | ⬡ | `2` | Reflects laser at 90° | Perimeter bounces & redirecting into enemy stones |
| **Splitter** | ✦ | `3` | Branches laser into two simultaneous beams | Exponential territory coverage & multi-line attacks |
| **Blocker** | █ | `4` | Absorbs laser beams completely (wall) | Defensive zone denial & intercepting enemy shots |

### Controls

| Action | Key / Mouse |
|:---|:---|
| **Select Prism** | `1` or Click on Bottom HUD |
| **Select Mirror** | `2` or Click on Bottom HUD |
| **Select Splitter** | `3` or Click on Bottom HUD |
| **Select Blocker** | `4` or Click on Bottom HUD |
| **Place Stone** | Left Click on empty intersection |
| **Rotate Stone** | Right Click & Drag on stone |
| **Fire Laser** | Drag from border / stone, or Space Bar |
| **Toggle Focus Mode (Solo Tablero)** | `F11` or Click `⛶ Solo Tablero` button |
| **Pass Turn** | `P` key or Pass button |
| **Undo Move** | `Ctrl+Z` |
| **Save Game** | `Ctrl+S` |
| **Surrender** | `Esc` → Surrender |

### Timer & Clock Rules
- **Idle at Startup**: The game timer stays safely paused at match initialization. Players have unlimited time to select settings and plan their opening move.
- **Action-Activated**: As soon as either player places a stone, rotates a stone, fires a laser, passes, or starts an AI match, the clock activates.
- **Move Timer**: Resets to full limit (e.g. 30s or 80s) on each turn change.
- **Pause & Resume**: Pausing the AI match pauses the clock; restarting resets the clock to idle.

---

## 📜 License

This project is licensed under the GPL V3 License - see the [LICENSE](LICENSE) file for details.
For information about third-party dependencies, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
