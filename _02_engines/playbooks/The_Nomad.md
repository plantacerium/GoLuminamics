# Playbook: The Nomad

## Game Mode Configuration
- **Mode**: 100% Territory (Total Domination)
- **Energy**: Infinite
- **Score**: Infinite
- **Time Limit**: 60 Minutes
- **Grid Size**: 39x39
- **Stone Types**: PRISM (transmit), MIRROR (reflect), SPLITTER (branch), BLOCKER (absorb)
- **Modes Available**: Turn-Based (classic), Realtime (velocity-based movement)

## Strategy Overview
**In Realtime Mode, constantly reposition stones for tactical advantage.**

## Core Tactics
- Use MOVE actions to shift stones closer to enemy territory.
- Move in all 8 directions including diagonals.
- Exploit board wrapping to flank from the opposite edge.
- Keep stones mobile — never stay static.

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
