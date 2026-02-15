# Playbook: The Laser Merry Go Round

## Game Mode Configuration
- **Mode**: Realtime (Velocity Based)
- **Energy**: Infinite
- **Grid Size**: 39x39
- **Focus**: Multi-Unit Movement & Laser Aggression

## Strategy Overview
**A continuous loop of stone swapping and firing.**

## Core Realtime Tactics
- setup: 4 stones in a square.
- action: Simultaneously move (swap) positions in a clockwise manner.
- fire: Shoot lasers into the center of the square during movement.

## Execution Plan
1.  **Deployment**: Quickly establish the required unit formation.
2.  **Maneuver**: Execute the movement pattern defined in tactics.
3.  **Fire**: Spam lasers whenever the formation allows.
4.  **Adapt**: If formation breaks, fallback to "The_Total_Chaos_Engine" behavior until regrouped.

## AI Directives
- **SPEED**: Decision time must be < 100ms.
- **GROUPING**: Calculate moves for groups of stones, not just individuals.
- **AGGRESSION**: If a Laser shot is available, TAKE IT immediately.
