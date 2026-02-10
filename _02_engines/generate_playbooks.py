import os

playbooks_dir = "playbooks"
if not os.path.exists(playbooks_dir):
    os.makedirs(playbooks_dir)



strategies = [
    {
        "name": "The_Solar_Weaver",
        "desc": "Focus on creating a massive network of splitters to cover the 39x39 grid.",
        "tactics": "- Prioritize SPLITTERS to multiply beams.\n- Place stones at key triangular intervals.\n- Aim to illuminate the center 20x20 area efficiently."
    },
    {
        "name": "The_Obsidian_Wall",
        "desc": "Build a defensive line of mirrors to block opponent expansion.",
        "tactics": "- Use MIRRORS to reflect opponent lasers back at them.\n- Create a dense wall on rows 15-24.\n- Protect your emitters."
    },
    {
        "name": "The_Prism_Core",
        "desc": "Establish a central hub of prisms for rapid redirection.",
        "tactics": "- Rush the center (19,19).\n- Build a diamond shape of PRISMS.\n- Use this core to shoot lasers in 4 directions."
    },
    {
        "name": "The_Edge_Walker",
        "desc": "Control the perimeter to encircle the opponent.",
        "tactics": "- Move along the edges (x=0, x=38, y=0, y=38).\n- Shoot lasers inward from the rim.\n- Trap the opponent in the middle."
    },
    {
        "name": "The_Diagonal_Slash",
        "desc": "Dominate the main diagonals of the 39x39 board.",
        "tactics": "- Place stones on (x,x) and (x, 38-x).\n- Create a cross-board laser highway.\n- Sever the board in half."
    },
    {
        "name": "The_Infinite_Loop",
        "desc": "Create self-sustaining loops to maximize local brightness.",
        "tactics": "- Arrange 4 MIRRORS in a square.\n- Trap a laser inside for territory points.\n- Replicate this pattern across the grid."
    },
    {
        "name": "The_Splitter_Swarm",
        "desc": "Aggressive expansion using only splitters.",
        "tactics": "- Do not use Mirrors or Prisms unless necessary.\n- Exponential beam growth is the goal.\n- Overwhelm the opponent with beam count."
    },
    {
        "name": "The_Sniper_Nest",
        "desc": "Set up long-range protected firing positions.",
        "tactics": "- Build bunkers of MIRRORS.\n- Leave small openings for PRISM shots.\n- Target opponent stones specifically."
    },
    {
        "name": "The_Chaos_Field",
        "desc": "Entropy maximization. Random high-density placement.",
        "tactics": "- Place stones in non-linear patterns.\n- Confuse the opponent's prediction.\n- Create unpredictable reflection angles."
    },
    {
        "name": "The_Symmetry_Keeper",
        "desc": "Maintain perfect rotational symmetry.",
        "tactics": "- Mirror every opponent move if possible.\n- Maintain balance on the board.\n- Use the large space to create beautiful geometric patterns."
    },
    {
        "name": "The_Grid_Locker",
        "desc": "Divide the 39x39 board into smaller controlled sectors.",
        "tactics": "- Build internal walls every 10 cells.\n- Secure one sector at a time.\n- Achieve 100% control of sub-sectors before moving on."
    },
    {
        "name": "The_Turtle_Shell",
        "desc": "Slow, methodical expansion from the starting corner.",
        "tactics": "- Do not extend beyond your illuminated territory.\n- Solidify control before advancing.\n- 100% Territory requires 0% gaps."
    },
    {
        "name": "The_Vanguard_Rush",
        "desc": "Immediate aggression towards opponent spawn.",
        "tactics": "- Place stones deep in enemy territory early.\n- Disrupt their initial setup.\n- Fight on their land, not yours."
    },
    {
        "name": "The_Laser_Web",
        "desc": "Maximize beam intersections for stability.",
        "tactics": "- Create a 'net' pattern.\n- Ensure every stone is hit by at least two lasers.\n- Hard to disrupt."
    },
    {
        "name": "The_Void_Filler",
        "desc": "Rapidly fill empty space with low-cost structures.",
        "tactics": "- Identifiy largest dark areas.\n- Drop PRISMS to light them up.\n- Ignore combat, focus on lighting pixels."
    },
    {
        "name": "The_Mirror_Maze",
        "desc": "Create a complex path that is hard to trace.",
        "tactics": "- Use diverse rotation angles on MIRRORS.\n- Baffle the opponent's raycasting.\n- Hide your true target."
    },
    {
        "name": "The_Splitter_Chain",
        "desc": "Linear acceleration of beams.",
        "tactics": "- Line up SPLITTERS in a row.\n- Create a 'beam cannon' effect.\n- Blast through enemy defenses."
    },
    {
        "name": "The_Zone_Denial",
        "desc": "Prevent opponent from entering specific zones.",
        "tactics": "- Use lasers to cut off access routes.\n- blockade the center.\n- Force opponent to the edges."
    },
    {
        "name": "The_Hunter_Killer",
        "desc": "Prioritize stone destruction over territory.",
        "tactics": "- If a stone can be captured, capture it.\n- Value +2 points over territory.\n- Demoralize the opponent."
    },
    {
        "name": "The_Illuminati",
        "desc": "Pure focus on the Victory Condition (100% Territory).",
        "tactics": "- Every move must increase lit pixel count.\n- Do not block your own lasers.\n- Optimize for coverage area."
    }
]

template = """# Playbook: {name}

## Game Mode Configuration
- **Mode**: 100% Territory (Total Domination)
- **Energy**: Infinite
- **Score**: Infinite
- **Time Limit**: 60 Minutes
- **Grid Size**: 39x39

## Strategy Overview
**{desc}**

## Core Tactics
{tactics}

## Execution Plan for 39x39 Grid
1.  **Early Game (0-10 mins)**: Establish the pattern foundation. Do not worry about energy costs.
2.  **Mid Game (10-40 mins)**: Expand the pattern to cover at least 50% of the board.
3.  **Late Game (40-60 mins)**: Hunt down the remaining dark spots to reach 100% territory.

## AI Reasoning Guidelines
- Since Energy is Infinite, prefer placing stones over passing.
- The board is huge. Think in "sectors" rather than individual cells.
- Aggression is viable because replacement is free.
"""

for s in strategies:
    filename = os.path.join(playbooks_dir, f"{s['name']}.md")
    content = template.format(name=s['name'].replace("_", " "), desc=s['desc'], tactics=s['tactics'])
    with open(filename, "w", encoding='utf-8') as f:
        f.write(content)
    print(f"Generated {filename}")

print("Done generating 20 playbooks.")
