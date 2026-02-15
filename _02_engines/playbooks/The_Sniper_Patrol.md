# Playbook: The Sniper Patrol

## Game Mode Configuration
- **Mode**: Realtime (Velocity Based)
- **Energy**: Infinite
- **Grid Size**: 39x39
- **Focus**: Multi-Unit Movement & Laser Aggression

## Strategy Overview
**Mobile prisms hunting for targets.**

## Core Realtime Tactics
- units: 3 isolated Prisms.
- behavior: Patrol specific distinct zones (Top, Mid, Bot).
- action: Stop only to align a shot, fire, then resume patrolling.

## Execution Plan
1.  **Deployment**: Quickly establish the required unit formation.
2.  **Maneuver**: Execute the movement pattern defined in tactics.
3.  **Fire**: Spam lasers whenever the formation allows.
4.  **Adapt**: If formation breaks, fallback to "The_Total_Chaos_Engine" behavior until regrouped.

## AI Directives
- **SPEED**: Decision time must be < 100ms.
- **GROUPING**: Calculate moves for groups of stones, not just individuals.
- **AGGRESSION**: If a Laser shot is available, TAKE IT immediately.
