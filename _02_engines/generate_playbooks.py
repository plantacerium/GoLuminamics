import os

playbooks_dir = os.path.join(os.path.dirname(__file__), "playbooks")
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
    },
    {
        "name": "The_Fortress",
        "desc": "Use BLOCKER stones to create impenetrable defensive walls.",
        "tactics": "- Place BLOCKERS to absorb enemy lasers completely.\n- Create fortress walls around your territory.\n- Use BLOCKERS as shields for your SPLITTER networks.\n- No laser passes through a BLOCKER — total absorption."
    },
    {
        "name": "The_Nomad",
        "desc": "In Realtime Mode, constantly reposition stones for tactical advantage.",
        "tactics": "- Use MOVE actions to shift stones closer to enemy territory.\n- Move in all 8 directions including diagonals.\n- Exploit board wrapping to flank from the opposite edge.\n- Keep stones mobile — never stay static."
    },
    {
        "name": "The_Serpent",
        "desc": "Master curved movement to outmaneuver predictable opponents.",
        "tactics": "- Use CURVE_MOVE with Bézier control points for unpredictable paths.\n- Curve around enemy blockers and defenses.\n- Combine curved movement with laser shots for surprise attacks.\n- Think in arcs, not straight lines."
    },
    {
        "name": "The_Wraith",
        "desc": "Exploit board wrapping to appear behind enemy lines.",
        "tactics": "- Move stones to the board edge, wrap to the opposite side.\n- Place BLOCKERs at your edge to protect your flank.\n- Use wrap-around to create impossible-to-trace laser paths.\n- Strike from where the opponent least expects."
    },
    # --- NEW LASER STRATEGIES (5) ---
    {
        "name": "The_Prism_Lance",
        "desc": "Long-range beaming using aligned Prisms.",
        "tactics": "- Align 3+ PRISMS in a straight line.\n- Use a MIRROR at the end to correct the final angle.\n- Create a beam that traverses the entire board length.\n- Snipe high-value targets across the map."
    },
    {
        "name": "The_Ricochet_Trap",
        "desc": "Geometric traps using Mirrors to hit blind spots.",
        "tactics": "- Place MIRRORS at obfuscated angles.\n- Calculate double-bounces to hit behind enemy walls.\n- Use the board edge as a virtual mirror (if mechanics allow) or just use standard reflection.\n- Catch the enemy off-guard with non-cardinal attacks."
    },
    {
        "name": "The_Scatter_Shot",
        "desc": "Using a Splitter close to the emitter for wide-angle denial.",
        "tactics": "- Place a SPLITTER immediately in front of your Laser Source.\n- Create two divergent beams instantly.\n- Deny a large cone of area to the opponent.\n- Force the opponent to defend two fronts."
    },
    {
        "name": "The_Beam_Surgeon",
        "desc": "Precise, surgical shots to snipe enemy stones without blocked by own.",
        "tactics": "- Use minimal stones to keep firing lines clear.\n- Rotate stones precisely to thread the needle.\n- Target enemy Mirrors first to disable their defense.\n- Prioritize safe shots over risky captures."
    },
    {
        "name": "The_Photon_Cage",
        "desc": "Using 4 mirrors to create a localized loop or killing zone.",
        "tactics": "- Construct a box of 4 MIRRORS facing inward.\n- Trap an enemy stone inside if possible.\n- Or use it to generate infinite local points (if loops are allowed).\n- Create a 'death zone' where any entry is destroyed."
    },

    # --- NEW MOVEMENT STRATEGIES (10) ---
    {
        "name": "The_Rolling_Phalanx",
        "desc": "Advancing a line of Blockers/Mirrors uniformly.",
        "tactics": "- Form a wall of BLOCKERS side-by-side.\n- Move them all forward 1 step per turn (Realtime).\n- Push the enemy back physically.\n- Crush their territory with a moving wall."
    },
    {
        "name": "The_Orbital_Strike",
        "desc": "Rotating stones around a target to find a firing angle.",
        "tactics": "- Choose a target enemy stone.\n- Move your PRISM/MIRROR in a circle around it.\n- Stop when a clear line of fire opens up.\n- Shoot and then move again."
    },
    {
        "name": "The_Hit_and_Run",
        "desc": "Move into firing position, fire, then retreat.",
        "tactics": "- Keep stones safe in your territory.\n- Dash out (Move) to a firing spot.\n- Shoot the laser.\n- Dash back (Move) to safety before they can retaliate.\n- Guerrilla warfare."
    },
    {
        "name": "The_Warp_Jungler",
        "desc": "Heavy use of edge-wrapping to traverse the board instantly.",
        "tactics": "- constantly move between x=0 and x=38.\n- Appear on the left, then instantly on the right.\n- Disorient the opponent's spatial awareness.\n- Maintain high velocity to stay unpredictable."
    },
    {
        "name": "The_Curve_Ball",
        "desc": "Using Bézier curves to move stones around obstacles.",
        "tactics": "- Do not move in straight lines.\n- Use CURVE_MOVE to arc around BLOCKERS.\n- Flank shielded enemies from the side.\n- Use movement as a weapon."
    },
    {
        "name": "The_Shadow_Dancer",
        "desc": "Constantly moving stones to stay in 'dark' tiles to avoid detection/hits.",
        "tactics": "- Analyze the board for unlit 'dark' tiles.\n- Move stones ONLY into these safe zones.\n- If a tile becomes lit, move immediately.\n- Survival is the highest priority."
    },
    {
        "name": "The_Swap_Tactics",
        "desc": "Swapping positions of a Mirror and a Prism to change beam behavior.",
        "tactics": "- Place a MIRROR and a PRISM near each other.\n- Physically move them to swap their locations.\n- Instantly change a reflection to a transmission.\n- Trick the opponent into a false sense of security."
    },
    {
        "name": "The_Aggressive_Ram",
        "desc": "Moving Blockers directly adjacent to enemy Emitters.",
        "tactics": "- Rush a BLOCKER across the board.\n- Park it right in front of the enemy Laser Source.\n- Completely neutralize their offensive capability.\n- Force them to waste moves destroying your cheap blocker."
    },
    {
        "name": "The_Kiting_Guard",
        "desc": "Keeping a defensive stone at exactly range 2 from enemy advancers.",
        "tactics": "- Maintain a safe distance from enemy 'Phalanx'.\n- Retreat as they advance, but stay in laser range.\n- Punish their overextension.\n- Draw them into a trap deep in your territory."
    },
    {
        "name": "The_Chaos_Shuffle",
        "desc": "Randomly shuffling stone positions to prevent enemy lock-on.",
        "tactics": "- Every turn, move a random stone by 1 tile.\n- Ensure no stone stays static for > 3 turns.\n- Prevent the enemy from pre-calculating shots.\n- Create a shifting, noisy battlefield."
    }
]

template = """# Playbook: {name}

## Game Mode Configuration
- **Mode**: 100% Territory (Total Domination)
- **Energy**: Infinite
- **Score**: Infinite
- **Time Limit**: 60 Minutes
- **Grid Size**: 39x39
- **Stone Types**: PRISM (transmit), MIRROR (reflect), SPLITTER (branch), BLOCKER (absorb)
- **Modes Available**: Turn-Based (classic), Realtime (velocity-based movement)

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
- BLOCKER stones completely absorb lasers — use them for defense.
- In Realtime Mode, use MOVE and CURVE_MOVE to reposition strategically.
"""

for s in strategies:
    filename = os.path.join(playbooks_dir, f"{s['name']}.md")
    content = template.format(name=s['name'].replace("_", " "), desc=s['desc'], tactics=s['tactics'])
    with open(filename, "w", encoding='utf-8') as f:
        f.write(content)
    print(f"Generated {filename}")

print(f"Done generating {len(strategies)} playbooks.")
