# Playbook: The Serpent

## Game Mode Configuration
- **Mode**: 100% Territory (Total Domination)
- **Energy**: Infinite
- **Score**: Infinite
- **Time Limit**: 60 Minutes
- **Grid Size**: 39x39
- **Stone Types**: PRISM (transmit), MIRROR (reflect), SPLITTER (branch), BLOCKER (absorb)
- **Modes Available**: Turn-Based (classic), Realtime (velocity-based movement)

## Strategy Overview
**Master curved movement to outmaneuver predictable opponents.**

## Core Tactics
- Use CURVE_MOVE with Bézier control points for unpredictable paths.
- Curve around enemy blockers and defenses.
- Combine curved movement with laser shots for surprise attacks.
- Think in arcs, not straight lines.

## Execution Plan for 39x39 Grid
1.  **Early Game (0-10 mins)**: Establish the pattern foundation. Do not worry about energy costs.
2.  **Mid Game (10-40 mins)**: Expand the pattern to cover at least 50% of the board.
3.  **Late Game (40-60 mins)**: Hunt down the remaining dark spots to reach 100% territory.

## AI Reasoning Guidelines
- Since Energy is Infinite, prefer placing stones over passing.
- The board is huge. Think in "sectors" rather than individual cells.
- Aggression is viable because replacement is free.
- BLOCKER stones completely absorb lasers — use them for defense.
- In Realtime Mode, use MOVE and CURVE_MOVE to reposition strategically.
