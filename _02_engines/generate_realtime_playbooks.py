import os

# Define the target directory
playbooks_dir = os.path.join(os.path.dirname(__file__), "playbooks")
if not os.path.exists(playbooks_dir):
    os.makedirs(playbooks_dir)

# Define the 20 new Realtime strategies
strategies = [
    {
        "name": "The_Sync_Swarm",
        "desc": "Move all units in unison to overwhelm a flank.",
        "tactics": "- synchronized_movement: Select 5+ stones and move them adjacent to each other.\n- direction: Push all units NORTH or SOUTH simultaneously.\n- laser_policy: Fire lasers from all capable units every 2 seconds.\n- goal: Create a moving wall of death."
    },
    {
        "name": "The_Orbiting_Death_Star",
        "desc": "Rotate a cluster of mirrors around a central prism emitter.",
        "tactics": "- formation: Central PRISM, surrounded by 4 MIRRORS.\n- action: Rotate the MIRRORS continuously to sweep the laser in a 360-degree arc.\n- movement: Slowly drift the entire formation towards the enemy center."
    },
    {
        "name": "The_Splitter_Rain",
        "desc": "Drop splitters from the sky (top edge) and rain lasers downwards.",
        "tactics": "- spawn: Place SPLITTERS at y=0 (top edge).\n- movement: Move them downwards (y+) continuously.\n- laser: Fire constantly downwards.\n- result: A curtain of laser fire descending on the opponent."
    },
    {
        "name": "The_Pincer_Maneuver",
        "desc": "Split forces into two distinct groups and attack from opposite sides.",
        "tactics": "- group_A: Move along x=0 (Left edge).\n- group_B: Move along x=38 (Right edge).\n- convergence: Both groups turn inward at y=20.\n- laser: Crossfire at the center point."
    },
    {
        "name": "The_Laser_Merry_Go_Round",
        "desc": "A continuous loop of stone swapping and firing.",
        "tactics": "- setup: 4 stones in a square.\n- action: Simultaneously move (swap) positions in a clockwise manner.\n- fire: Shoot lasers into the center of the square during movement."
    },
    {
        "name": "The_Battering_Ram",
        "desc": "A column of Blockers leading a Prism.",
        "tactics": "- formation: BLOCKER, BLOCKER, PRISM (in a line).\n- movement: Move the column forward at full speed.\n- laser: Fire the Prism through any gaps that open up.\n- defense: The Blockers absorb all incoming fire."
    },
    {
        "name": "The_Scatter_Bomb",
        "desc": "Explosive multi-directional expansion.",
        "tactics": "- start: All stones clustered in the center.\n- action: Simultaneously move all stones OUTWARDS in different directions.\n- laser: Fire randomly during the expansion to creating chaos."
    },
    {
        "name": "The_Grid_Sweeper",
        "desc": " Systematic laser sweeping line.",
        "tactics": "- formation: Line of MIRRORS at x=0.\n- movement: Move the entire line to x=38.\n- laser: Reflect lasers back and forth across the moving line."
    },
    {
        "name": "The_Turtle_Crawl",
        "desc": "Extremely slow, impenetrable advancement.",
        "tactics": "- formation: Dense 3x3 block of stones.\n- movement: Move 1 tile every 5 seconds, ensuring formation integrity.\n- laser: Short range blasts only."
    },
    {
        "name": "The_Sniper_Patrol",
        "desc": "Mobile prisms hunting for targets.",
        "tactics": "- units: 3 isolated Prisms.\n- behavior: Patrol specific distinct zones (Top, Mid, Bot).\n- action: Stop only to align a shot, fire, then resume patrolling."
    },
    {
        "name": "The_Mirror_Shuffle",
        "desc": "Constantly re-orienting mirrors to confuse enemy targeting.",
        "tactics": "- action: Every 1 second, rotate a random Mirror by 90 degrees.\n- action: Every 2 seconds, move a random Mirror by 1 tile.\n- goal: Make the board state impossible to predict."
    },
    {
        "name": "The_Vortex_Convergence",
        "desc": "Sucking all units towards the enemy base.",
        "tactics": "- target: Enemy Start (Spawn).\n- movement: All units move towards target using CURVE_MOVE.\n- laser: Focus fire on the target point."
    },
    {
        "name": "The_Wall_Of_Light",
        "desc": "A literal moving wall of laser beams.",
        "tactics": "- setup: Alternating PRISM and SPLITTER in a row.\n- laser: All fire parallel beams.\n- movement: Strafe the line sideways (perpendicular to beams)."
    },
    {
        "name": "The_Decoy_Dash",
        "desc": "Sacrificial runners drawing fire away from the main battery.",
        "tactics": "- decoys: 2 MIRRORS moving efficiently but harmlessly.\n- main: Static PRISMS lining up a shot.\n- goal: Force enemy AI to target moving stones."
    },
    {
        "name": "The_Phased_Assault",
        "desc": "Attack in waves.",
        "tactics": "- wave_1: Blockers move in to absorb fire.\n- wave_2: Prisms move in to fire.\n- wave_3: Mirrors move in to secure territory.\n- timing: 10 second delay between waves."
    },
    {
        "name": "The_Crossfire_Trap",
        "desc": "Luring the enemy into a pre-set kill zone.",
        "tactics": "- setup: Two Prisms facing each other with a gap in between.\n- bait: Move a vulnerable Mirror into the gap.\n- trap: Fire both Prisms when enemy enters to capture bait."
    },
    {
        "name": "The_Roaming_Triangle",
        "desc": "Three stones maintaining a strict geometric shape.",
        "tactics": "- shape: Equilateral triangle of Splitters.\n- movement: Rotate and Translate the entire triangle shape around the board.\n- laser: Fire inward to create a 'zone of death' inside the triangle."
    },
    {
        "name": "The_Blitzkrieg_Rush",
        "desc": "Maximum speed, minimum defense.",
        "tactics": "- speed: Maximize velocity.\n- target: Enemy infrastructure.\n- laser: Fire efficiently, do not stop to aim perfectly.\n- motto: Speed is life."
    },
    {
        "name": "The_Shadow_Stalker",
        "desc": "Hiding in the opponent's blind spots.",
        "tactics": "- analysis: Identify areas with NO enemy laser coverage.\n- movement: Move exclusively into those areas.\n- attack: Pop out, fire, move back into shadow."
    },
    {
        "name": "The_Total_Chaos_Engine",
        "desc": "Random usage of all available realtime actions.",
        "tactics": "- entropy: High.\n- behavior: 50% chance to Move, 30% chance to Fire, 20% chance to Rotate.\n- synchronization: None. Every unit acts independently."
    }
]

template = """# Playbook: {name}

## Game Mode Configuration
- **Mode**: Realtime (Velocity Based)
- **Energy**: Infinite
- **Grid Size**: 39x39
- **Focus**: Multi-Unit Movement & Laser Aggression

## Strategy Overview
**{desc}**

## Core Realtime Tactics
{tactics}

## Execution Plan
1.  **Deployment**: Quickly establish the required unit formation.
2.  **Maneuver**: Execute the movement pattern defined in tactics.
3.  **Fire**: Spam lasers whenever the formation allows.
4.  **Adapt**: If formation breaks, fallback to "The_Total_Chaos_Engine" behavior until regrouped.

## AI Directives
- **SPEED**: Decision time must be < 100ms.
- **GROUPING**: Calculate moves for groups of stones, not just individuals.
- **AGGRESSION**: If a Laser shot is available, TAKE IT immediately.
"""

# Generate the files
for s in strategies:
    filename = os.path.join(playbooks_dir, f"{s['name']}.md")
    content = template.format(name=s['name'].replace("_", " "), desc=s['desc'], tactics=s['tactics'])
    with open(filename, "w", encoding='utf-8') as f:
        f.write(content)
    print(f"Generated Realtime Playbook: {filename}")

print(f"Successfully generated {len(strategies)} Realtime playbooks.")
