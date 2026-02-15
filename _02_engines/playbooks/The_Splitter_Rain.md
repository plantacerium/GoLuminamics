# Playbook: The Splitter Rain

## Game Mode Configuration
- **Mode**: Realtime (Velocity Based)
- **Energy**: Infinite
- **Grid Size**: 39x39
- **Focus**: Multi-Unit Movement & Laser Aggression

## Strategy Overview
**Drop splitters from the sky (top edge) and rain lasers downwards.**

## Core Realtime Tactics
- spawn: Place SPLITTERS at y=0 (top edge).
- movement: Move them downwards (y+) continuously.
- laser: Fire constantly downwards.
- result: A curtain of laser fire descending on the opponent.

## Execution Plan
1.  **Deployment**: Quickly establish the required unit formation.
2.  **Maneuver**: Execute the movement pattern defined in tactics.
3.  **Fire**: Spam lasers whenever the formation allows.
4.  **Adapt**: If formation breaks, fallback to "The_Total_Chaos_Engine" behavior until regrouped.

## AI Directives
- **SPEED**: Decision time must be < 100ms.
- **GROUPING**: Calculate moves for groups of stones, not just individuals.
- **AGGRESSION**: If a Laser shot is available, TAKE IT immediately.
