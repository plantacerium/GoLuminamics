# 🎮 Luminamics Go 2D - Game Mechanics

## 📋 Core Game System

### Board Configuration
- **Grid Sizes**: Configurable (9×9, 13×13, 19×19, 23×23, 27×27, 31×31, 35×35, 39×39)
- **Default Size**: 19×19 intersections
- **Cell Size**: 35 pixels per cell
- **Coordinate System**: (x, y) tuples, 0 to (grid_size-1) for on-board positions
- **Direction Format**: Normalized (dx, dy) vectors for laser trajectories

### Player System
- **Player IDs**: 
  - Player 1 (Black) - ID: 1
  - Player 2 (White) - ID: 2
- **Turn System**: Alternating turns with pass option
- **Control**: Mouse-based placement, rotation, and laser aiming, with extensible keyboard shortcuts

---

## ⚡ Energy System

### Energy Rules
- **Starting Energy**: 10 per player (configurable)
- **Maximum Energy**: 20 (hard cap)
- **Energy Recharge**: +2 per turn
- **Stone Placement Cost**: 1 energy (configurable via `energy_cost`)
- **Laser Firing Cost**: 0 energy (free action)
- **Infinite Energy Mode**: Optional setting that removes energy costs entirely

### Energy Management
Energy is checked before actions, consumed after successful placement, and recharged at end of turn. When **Infinite Energy** is enabled via the UI, placement costs are ignored, allowing unlimited stone placement.

---

## ⏳ Timer & Clock System

### Time Controls
- **Total Game Timer**: Optional limit on total thinking time per player (configurable: 15m, 30m, 60m, or Infinite).
- **Move Timer**: Fixed time limit for each individual turn (default: 30 or 80 seconds).

### Action-Activated Clock Mechanics (Idle Protection)
1. **Startup Idle State**: Upon launching the UI or restarting a match, the game clock is completely paused in an idle state. Neither the Move Timer nor the Total Game Timer will decrement. This prevents unfair losses or accidental timeouts before players take action.
2. **Activation Triggers**: The clock automatically activates as soon as any game action occurs:
   - Placing a stone on an intersection
   - Rotating a stone
   - Firing a laser beam
   - Moving a stone (linear or Bézier curve)
   - Passing the turn
   - Clicking **START AI MATCH** in the Arena
3. **Turn Switching & Reset**: When a player completes their turn, their Move Timer resets to full capacity for the opponent.
4. **Pause & Resume**: Pausing an AI match immediately halts the countdown without resetting remaining seconds.
5. **Restarting**: Clicking **Restart Game** restores full initial timer allocations and returns the clock to its idle state.
6. **Expiration**:
   - **Move Timer**: If a player's move timer expires while active, the turn is automatically passed.
   - **Total Timer**: If a player's total thinking time reaches zero, the opponent wins by timeout.

---

## 🔮 Stone Types & Modern Bottom HUD

### Stone Selector Bottom HUD
Stone selection is managed via a sleek, horizontal dock located directly below the board:
- **Instant Hotkeys**: Press `1`, `2`, `3`, or `4` at any time to switch active piece types.
- **Visual Feedback**: The active button illuminates with a glowing border matching the stone's optical color.
- **Extensible Architecture**: Defined in `_03_ui/stone_hud.py` via `AVAILABLE_STONE_TYPES`. Developers can register new optical elements (such as Polarizers, Portals, or Sensors) with just a single dictionary entry.

### 1. Prism (Transmit / Refract)
- **Symbol**: ▲ | **Hotkey**: `1`
- **Energy Cost**: 1
- **Effect**: Transmits laser straight through or refracts at 45°/90° depending on alignment
- **Use Cases**: Creating direct laser networks, territory coverage
- **Strategic Value**: Essential for long-range illumination and captures

### 2. Mirror (Reflect)
- **Symbol**: ⬡ | **Hotkey**: `2`
- **Energy Cost**: 1
- **Effect**: Reflects laser at 90° based on stone rotation (0-360°)
- **Use Cases**: Redirecting lasers around obstacles, creating perimeter reflection loops
- **Strategic Value**: Highest tactical versatility through angle orientation

### 3. Splitter (Branch)
- **Symbol**: ✦ | **Hotkey**: `3`
- **Energy Cost**: 1
- **Effect**: Splits an incoming laser beam into two simultaneous paths
- **Use Cases**: Exponential territory coverage, multi-target simultaneous captures
- **Strategic Value**: Multiplies board control from a single shot

### 4. Blocker (Absorb Wall)
- **Symbol**: █ | **Hotkey**: `4`
- **Energy Cost**: 1
- **Effect**: Completely absorbs laser rays on contact — no reflection, no transmission
- **Use Cases**: Denying enemy shooting lanes, shielding critical friendly clusters
- **Strategic Value**: Pure zone defense and shot interception

---

## ⛶ Collapsible Paneling & Focus Mode

### Architecture
The interface layout utilizes a horizontal `QSplitter` separating the central viewport, controls, and AI thought streamer:
- **Splitter Dragging**: Users can drag the vertical splitter bars to allocate custom screen real estate.
- **`⛶ Modo Solo Tablero` (Focus Mode / `F11`)**: A single click collapses both the Controls panel and the Thought Streamer panel to 0 width. The board and Bottom HUD dynamically expand to take 100% of the window for distraction-free gameplay.
- **Individual Sidebar Toggles**:
  - `[ ⚙️ Controles ]`: Toggles the configuration and match settings panel.
  - `[ 🧠 AI Thoughts ]`: Toggles the AI Thought Streamer panel in Arena mode.

---

## 🤖 AI Engines & MCP Protocol

### 1. Optical Monte Carlo Tree Search (MCTS) Engine
Located in `_02_engines/mcts.py`:
- **Optical Resonance Pruning**: Filters the vast action space (>11,000 moves on 19×19) down to 20–40 high-utility candidates based on ray tracing lines of sight and angular symmetry.
- **Ultra-Fast Cloning**: State memory cloning engine delivering over 420,000 board clones per second.
- **Search Rate**: Explores ~5,000 full game simulations per second.
- **CLI Usage**: Selectable in Arena mode via `--p1 mcts` or `--p2 mcts:500`.

### 2. Live UI ⇄ MCP Agent Bridge
Located in `_00_entry/live_bridge.py`:
- Embeds a local JSON/HTTP bridge on port `18989`.
- Allows AI coding agents (such as **Antigravity**) to read the visible board state (`luminamics_get_board_state`) and play moves (`luminamics_place_stone`, `luminamics_shoot_laser`) that render and animate directly on screen in real time.
- Streams the agent's inner tactical reasoning directly into the **AI Thought Streamer** HUD.

---

## 🎮 Controls Reference

| Action | Key / Input |
|:---|:---|
| **Select Prism** | `1` or Click on Bottom HUD |
| **Select Mirror** | `2` or Click on Bottom HUD |
| **Select Splitter** | `3` or Click on Bottom HUD |
| **Select Blocker** | `4` or Click on Bottom HUD |
| **Toggle Focus Mode** | `F11` or `⛶ Solo Tablero` button |
| **Toggle Controls** | `⚙️ Controles` button |
| **Toggle AI Thoughts** | `🧠 AI Thoughts` button |
| **Place Stone** | Left Click on empty intersection |
| **Rotate Stone** | Right Click & Drag on existing stone |
| **Fire Laser** | Drag from border / stone, or Space Bar |
| **Pass Turn** | `P` key or Pass button |
| **Undo Move** | `Ctrl+Z` |
| **Save Game** | `Ctrl+S` |
| **Surrender** | `Esc` → Surrender |

---

## 📝 Game Rules Summary

1. **Setup**: Configurable board (9×9 to 39×39, default 19×19), both players start with 10 energy. Clock remains idle until first move.
2. **Turns**: Alternate placing stones (1 energy, or free with Infinite Energy) or passing.
3. **Rotation**: Stones can be rotated 0-360° to direct laser reflections.
4. **Lasers**: Fire from board edges or stones, interacting with optical pieces.
5. **Captures**: Lasers destroy opponent stones (+2 points each).
6. **Territory**: Illuminated intersections count toward persistent score.
7. **Victory**: Mutual pass (highest score), total domination (unless Infinite Score enabled), timeout, or surrender.
8. **Energy**: +2 recharge per turn, max 20 (or unlimited with Infinite Energy).
