"""
File: laser_calculator_2d.py
Creation Date: 2025-11-28
Last Updated: 2025-11-28
Version: 2.0.0
Description: Source file.
"""

import math

class LaserCalculator2D:
    """Calculate 2D laser paths using ray tracing."""
    def __init__(self, grid_size=19):
        self.grid_size = grid_size
        self.max_bounces = 20 # Reduced for performance with ray tracing
        self.stone_radius = 0.4 # Matches GameBoard radius (cell_size * 0.4 normalized to 1.0 cell)

    def calculate_path(self, start_pos, start_dir, stone_map):
        """
        Calculate laser path using ray casting with branching support.
        Returns list of paths, each path is a list of (x, y) tuples.
        """
        from _01_core_logic.board_state import StoneType
        
        all_paths = []
        
        # Normalize start direction
        length = math.sqrt(start_dir[0]**2 + start_dir[1]**2)
        if length == 0: return []
        start_dir_norm = (start_dir[0]/length, start_dir[1]/length)
        
        # Queue: (current_pos, current_dir, current_path, bounce_count)
        # current_path is a list of points visited so far for this ray segment
        queue = [(start_pos, start_dir_norm, [start_pos], 0)]
        
        while queue:
            curr_pos, curr_dir, curr_path, depth = queue.pop(0)
            
            if depth > self.max_bounces:
                all_paths.append(curr_path)
                continue
                
            # Cast Ray
            nearest_hit = None
            min_dist = float('inf')
            hit_object = None
            hit_pos = None
            
            # 1. Stones
            for s_pos, s_data in stone_map.items():
                # Avoid self-intersection (source)
                if (s_pos[0]-curr_pos[0])**2 + (s_pos[1]-curr_pos[1])**2 < 0.01: continue
                
                Lx = curr_pos[0] - s_pos[0]
                Ly = curr_pos[1] - s_pos[1]
                a = 1
                b = 2 * (Lx * curr_dir[0] + Ly * curr_dir[1])
                c = (Lx**2 + Ly**2) - self.stone_radius**2
                disc = b**2 - 4*a*c
                
                if disc >= 0:
                    sqrt_disc = math.sqrt(disc)
                    t1 = (-b - sqrt_disc)/2
                    t2 = (-b + sqrt_disc)/2
                    t = float('inf')
                    if t1 > 0.001: t = t1
                    elif t2 > 0.001: t = t2
                    
                    if t < min_dist:
                        min_dist = t
                        hit_object = s_data
                        hit_pos = (curr_pos[0] + t*curr_dir[0], curr_pos[1] + t*curr_dir[1])
            
            # 2. Walls
            # Expanded bounds to allow sources at -1 and grid_size (19) to fire into the board
            bounds = (-1.5, self.grid_size + 0.5)
            # X planes
            if curr_dir[0] != 0:
                t1 = (bounds[0] - curr_pos[0]) / curr_dir[0]
                t2 = (bounds[1] - curr_pos[0]) / curr_dir[0]
                if t1 > 0.001 and t1 < min_dist: min_dist, hit_object, hit_pos = t1, 'wall', (bounds[0], curr_pos[1] + t1*curr_dir[1])
                if t2 > 0.001 and t2 < min_dist: min_dist, hit_object, hit_pos = t2, 'wall', (bounds[1], curr_pos[1] + t2*curr_dir[1])
            # Y planes
            if curr_dir[1] != 0:
                t1 = (bounds[0] - curr_pos[1]) / curr_dir[1]
                t2 = (bounds[1] - curr_pos[1]) / curr_dir[1]
                if t1 > 0.001 and t1 < min_dist: min_dist, hit_object, hit_pos = t1, 'wall', (curr_pos[0] + t1*curr_dir[0], bounds[0])
                if t2 > 0.001 and t2 < min_dist: min_dist, hit_object, hit_pos = t2, 'wall', (curr_pos[0] + t2*curr_dir[0], bounds[1])
            
            if hit_object:
                # Add segment to path
                # We need to create a NEW list for the path to avoid modifying paths in the queue if we branch?
                # Actually, curr_path is unique to this queue item.
                # But if we branch, we need copies.
                
                new_path = curr_path + [hit_pos]
                
                if hit_object == 'wall':
                    all_paths.append(new_path)
                    continue
                
                # Hit Stone
                stone = hit_object
                
                # Flat surface normal based on rotation
                rot_rad = math.radians(stone.rotation_angle)
                nx = math.cos(rot_rad)
                ny = math.sin(rot_rad)
                
                # Dot product to see if we hit front or back
                dot = curr_dir[0]*nx + curr_dir[1]*ny
                
                # Reflection Vector
                rx = curr_dir[0] - 2 * dot * nx
                ry = curr_dir[1] - 2 * dot * ny
                reflect_dir = (rx, ry)
                
                # Transmission Vector (Straight through)
                trans_dir = curr_dir
                # Offset to exit stone
                trans_start = (hit_pos[0] + trans_dir[0]*1.0, hit_pos[1] + trans_dir[1]*1.0) 
                
                if stone.stone_type == StoneType.BLOCKER:
                    # Absorb - laser stops here completely
                    all_paths.append(new_path)
                    
                elif stone.stone_type == StoneType.MIRROR:
                    # Reflect
                    queue.append((hit_pos, reflect_dir, new_path, depth + 1))
                    
                elif stone.stone_type == StoneType.PRISM:
                    # Transmit
                    queue.append((trans_start, trans_dir, new_path, depth + 1))
                    
                elif stone.stone_type == StoneType.SPLITTER:
                    # Reflect AND Transmit
                    queue.append((hit_pos, reflect_dir, new_path, depth + 1))
                    queue.append((trans_start, trans_dir, new_path, depth + 1))
                    
            else:
                # Hit nothing (shouldn't happen with walls, but safe fallback)
                all_paths.append(curr_path)
        
        return all_paths

    def get_unique_points(self, paths):
        """Get unique grid points intersected by paths."""
        unique_points = set()
        for path in paths:
            for i in range(len(path)-1):
                p1 = path[i]
                p2 = path[i+1]
                
                # Walk the line and add integer coordinates
                dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                steps = int(dist * 2) # 2 steps per cell size
                if steps == 0: steps = 1
                
                for s in range(steps+1):
                    t = s / steps
                    x = int(round(p1[0] + (p2[0]-p1[0])*t))
                    y = int(round(p1[1] + (p2[1]-p1[1])*t))
                    if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                        unique_points.add((x,y))
        return unique_points
