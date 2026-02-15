# Playbook: The Battering Ram

## Game Mode Configuration
- **Mode**: Realtime (Velocity Based)
- **Energy**: Infinite
- **Grid Size**: 39x39
- **Focus**: Multi-Unit Movement & Laser Aggression

## Strategy Overview
**A column of Blockers leading a Prism.**

## Core Realtime Tactics
- formation: BLOCKER, BLOCKER, PRISM (in a line).
- movement: Move the column forward at full speed.
- laser: Fire the Prism through any gaps that open up.
- defense: The Blockers absorb all incoming fire.

## Execution Plan
1.  **Deployment**: Quickly establish the required unit formation.
2.  **Maneuver**: Execute the movement pattern defined in tactics.
3.  **Fire**: Spam lasers whenever the formation allows.
4.  **Adapt**: If formation breaks, fallback to "The_Total_Chaos_Engine" behavior until regrouped.

## AI Directives
- **SPEED**: Decision time must be < 100ms.
- **GROUPING**: Calculate moves for groups of stones, not just individuals.
- **AGGRESSION**: If a Laser shot is available, TAKE IT immediately.
