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
- **Control**: Mouse-based placement, rotation, and laser aiming

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

## ⏳ Timer System

### Time Controls
- **Total Game Timer**: Optional limit on total thinking time per player (configurable: 15m, 30m, 60m, or Infinite).
- **Move Timer**: Fixed time limit for each individual turn (default: 30 seconds).

### Timer Mechanics
1. **Countdown**: Timers decrement in real-time while it is the player's turn.
2. **Move Time**: Resets to the full limit (e.g., 30s) at the start of each turn.
3. **Expiration**:
   - **Move Timer**: If the move timer expires, the turn is automatically passed.
   - **Total Timer**: If the total time limit is reached, the player loses the match.

---

## 🔮 Stone Types

### Prism (Transmit)
- **Symbol**: 🔺
- **Energy Cost**: 1
- **Effect**: Transmits laser straight through, continues path
- **Use Cases**: Creating direct laser paths, territory coverage
- **Strategic Value**: Essential for long-range illumination and captures

### Mirror (Reflect)
- **Symbol**: 📐
- **Energy Cost**: 1
- **Effect**: Reflects laser at angle based on stone rotation
- **Rotation**: 0-360° adjustable
- **Use Cases**: Redirecting lasers, creating defensive walls, complex paths
- **Strategic Value**: Highest tactical flexibility through rotation

### Splitter (Branch)
- **Symbol**: 💎
- **Energy Cost**: 1
- **Effect**: Splits laser into two beams, branching the path
- **Use Cases**: Maximizing territory coverage, multi-target captures
- **Strategic Value**: Territory maximization and area control

---

## 🌟 Laser System

### Laser Physics
- **Entry Points**: Board edges (coordinates -1 or 19)
- **Path Calculation**: Real-time physics using LaserCalculator2D
- **Interactions**: 
  - Prism: Continue straight through
  - Mirror: Reflect at angle (depends on rotation)
  - Splitter: Branch into two paths
- **Termination**: Board edge or path limit reached

### Laser Effects
- **Territory Illumination**: Illuminated intersections count as territory
- **Stone Captures**: Lasers hitting opponent stones destroy them (+2 points each)
- **Visual Feedback**: Neon-style beam rendering with glow effects
- **Path Display**: Full path visualization showing all reflections and splits

---

## 🏆 Scoring System

### Score Components
1. **Territory Points**: Each illuminated intersection counts
2. **Capture Points**: Each captured opponent stone worth +2 points
3. **Contested Territory**: Intersections illuminated by both players don't count for either

### Score Calculation
```
Player Score = Territory Illuminated + (Captures × 2)
```

Scoring is dynamic and recalculated after each laser shot. The replayer system tracks score progression over time.

---

## 🎯 Victory Conditions

### 1. Mutual Pass Victory
- **Trigger**: Both players pass sequentially
- **Winner**: Player with highest score
- **Reason**: "Score Victory"

### 2. Total Victory (Mercy Rule)
- **Trigger 1**: Score difference > 50 points
- **Trigger 2**: Control > Territory Threshold (configurable: 80%, 90%, or 100%)
- **Default Setting**: 80% territory control
- **Winner**: Dominant player
- **Reason**: "Total Domination"
- **Configuration**: Adjustable via "Victory" dropdown in game setup
- **Note**: Can be disabled with **Infinite Score** mode

### 3. Time-Based Victory
- **Trigger**: Total time expires (when timer is set)
- **Winner**: Player with highest score at time of expiration
- **Reason**: "Time Expired"
- **Note**: Primary victory mode when **Infinite Score** is enabled

### 4. Surrender
- **Trigger**: Player chooses to surrender (Esc → Surrender)
- **Winner**: Opponent
- **Reason**: "Opponent Surrendered"

### Infinite Score Mode
When **Infinite Score (No Mercy)** is enabled:
- Mercy rule conditions (score difference >50, territory threshold) are disabled
- Game continues until time expires, mutual pass, or surrender
- Victory determined by final score comparison

---

## 🎨 Visual Themes

### Classic Theme
- **Player 1**: Red stones with red lasers
- **Player 2**: Blue stones with blue lasers
- **Style**: Solid color fills with depth shadows

### Neon Theme
- **Player 1**: Magenta stones with glowing effects
- **Player 2**: Cyan stones with glowing effects
- **Style**: Vibrant neon colors, enhanced glow

### Pastel Theme
- **Player 1**: Soft red stones
- **Player 2**: Soft blue stones
- **Style**: Muted, gentle color palette

### Forest Theme
- **Player 1**: Orange stones
- **Player 2**: Green stones
- **Style**: Nature-inspired earthy tones

### Real Stones Theme
- **Prism P1**: Ruby texture (`texture_ruby.png`)
- **Prism P2**: Sapphire texture (`texture_sapphire.png`)
- **Mirror**: Slate texture (`texture_slate.png`)
- **Splitter**: Gold texture (`texture_gold.png`)
- **Outlines**: P1=Black, P2=White
- **Style**: Photorealistic stone textures with depth and rotation cues (notch/line)

---

## 🎮 Controls

### Mouse Controls
| Action | Input |
|--------|-------|
| Place Stone | Left Click on intersection |
| Rotate Stone | Right Click and Drag on stone |
| Aim Laser | Click and drag from edge |
| Release Laser | Release mouse button |
| Manual Placement | Use side panel (X, Y, Rotation) |

### Keyboard Controls
| Action | Key |
|--------|-----|
| Rotate Stone | R key |
| Fire Laser | Space bar |
| Pass Turn | P key |
| Undo Move | Ctrl+Z |
| Save Game | Ctrl+S |
| Surrender | Esc → Surrender |

### Replayer Controls
| Action | Key/Button |
|--------|------------|
| Next Move | Right Arrow / → button |
| Previous Move | Left Arrow / ← button |
| Play/Pause | Space / Play button |
| Jump to First | Home / ⏮ button |
| Jump to Last | End / ⏭ button |
| Speed Control | Slider (0.5x - 2.0x) |

---

## 📊 Game Recording System

### Recording Features
- **Auto-Save**: Games automatically saved to `games/` directory
- **Format**: JSON with metadata and move history
- **Data Captured**:
  - Player names and strategies
  - Complete move sequence (placements, rotations, lasers)
  - Timestamps
  - Final score and victory reason
  - Capture history

### Replay Features
- **Visual Timeline**: Capture chart showing score progression
- **Move-by-Move**: Step through entire game history
- **Speed Control**: Adjustable playback speed
- **Game Info**: Displays current turn, score, and move details

---


## 📝 Game Rules Summary

1. **Setup**: Configurable board (9×9 to 39×39, default 19×19), both players start with 10 energy
2. **Turns**: Alternate placing stones (1 energy, or free with Infinite Energy) or passing
3. **Rotation**: Stones can be rotated 0-360° for mirrors
4. **Lasers**: Fire from board edges, interact with stones
5. **Captures**: Lasers destroy opponent stones (+2 points each)
6. **Territory**: Illuminated intersections count toward score
7. **Victory**: Time expires, mutual pass (highest score), total domination (unless Infinite Score enabled), or surrender
8. **Energy**: +2 recharge per turn, max 20 (or unlimited with Infinite Energy)

