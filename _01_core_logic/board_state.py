"""
File: board_state_2d.py
Creation Date: 2025-11-28
Last Updated: 2025-11-28
Version: 2.0.0
Description: Source file.
"""

from PySide6.QtGui import QVector2D
from enum import Enum

class StoneType(Enum):
    PRISM = 1
    MIRROR = 2
    SPLITTER = 3
    BLOCKER = 4

class StoneData2D:
    """Represents a stone's logical state in 2D."""
    def __init__(self, stone_type=StoneType.PRISM, player=1):
        self.stone_type = stone_type
        self.rotation_angle = 0.0  # Rotation in degrees (0-360)
        self.player = player  # 1 or 2
        self.velocity = 1  # Moves per tick in realtime mode
    
    def set_rotation(self, angle):
        """Set rotation angle."""
        self.rotation_angle = angle % 360
    
    def get_rotation_radians(self):
        """Get rotation in radians."""
        import math
        return math.radians(self.rotation_angle)
    
    @property
    def type_name(self):
        """Get the string name of the stone type."""
        return self.stone_type.name

class BoardState2D:
    """Manages the logical state of the 2D game board."""
    
    # Available board sizes (user configurable)
    GRID_SIZES = [9, 13, 19, 23, 27, 31, 35, 39]
    
    def __init__(self, grid_size=19, starting_energy=10, territory_threshold=0.8,
                 infinite_energy=False, energy_cost=1, infinite_score=False):
        # Validate grid_size
        if grid_size not in self.GRID_SIZES:
            raise ValueError(f"Invalid grid_size {grid_size}. Must be one of {self.GRID_SIZES}")
        
        self.grid_size = grid_size
        self.stones = {}  # Map (x,y) -> StoneData2D
        self.laser_sources = []  # List of (pos, dir, player) tuples
        self.territory_threshold = territory_threshold # Victory condition threshold
        self.infinite_score = infinite_score  # When True, no mercy rule
        
        # Energy system
        self.infinite_energy = infinite_energy
        self.energy_cost = energy_cost
        self.starting_energy = starting_energy
        self.player_energy = {1: starting_energy, 2: starting_energy}
        self.max_energy = 20  # Energy cap
        
        # Capture tracking
        self.player_captures = {1: 0, 2: 0}
        
        # Game End State
        self.consecutive_passes = 0
        self.game_over = False
        self.winner = None
        self.victory_reason = ""

        # Timer System
        self.total_time_limit = 0  # 0 = Infinite, otherwise in minutes
        self.move_time_limit = 30  # Seconds per move
        self.player_time_remaining = {1: 0.0, 2: 0.0} # Seconds remaining for total time
        self.current_move_time_remaining = 30.0 # Seconds remaining for current move
    
    def to_dict(self):
        """Serialize board state to dictionary."""
        stones_data = {}
        for pos, stone in self.stones.items():
            key = f"{pos[0]},{pos[1]}"
            stones_data[key] = {
                "type": stone.stone_type.name,
                "player": stone.player,
                "rotation": stone.rotation_angle
            }
            
        return {
            "grid_size": self.grid_size,
            "territory_threshold": self.territory_threshold,
            "infinite_score": self.infinite_score,
            "infinite_energy": self.infinite_energy,
            "energy_cost": self.energy_cost,
            "player_energy": self.player_energy,
            "stones": stones_data,
            "player_captures": self.player_captures,
            "game_over": self.game_over,
            "winner": self.winner,
            "victory_reason": self.victory_reason,
            "total_time_limit": self.total_time_limit,
            "move_time_limit": self.move_time_limit,
            "player_time_remaining": self.player_time_remaining,
            "current_move_time_remaining": self.current_move_time_remaining
        }

    @classmethod
    def from_dict(cls, data):
        """Create BoardState2D from dictionary."""
        grid_size = data.get("grid_size", 19)
        territory_threshold = data.get("territory_threshold", 0.8)
        infinite_score = data.get("infinite_score", False)
        infinite_energy = data.get("infinite_energy", False)
        energy_cost = data.get("energy_cost", 1)
        board = cls(grid_size, territory_threshold=territory_threshold,
                    infinite_energy=infinite_energy, energy_cost=energy_cost,
                    infinite_score=infinite_score)
        
        # Restore energy
        board.player_energy = data.get("player_energy", {1: 10, 2: 10})
        # Handle JSON string keys
        if "1" in board.player_energy:
            board.player_energy[1] = board.player_energy.pop("1")
        if "2" in board.player_energy:
            board.player_energy[2] = board.player_energy.pop("2")
            
        board.player_captures = data.get("player_captures", {1: 0, 2: 0})
        if "1" in board.player_captures:
            board.player_captures[1] = board.player_captures.pop("1")
        if "2" in board.player_captures:
            board.player_captures[2] = board.player_captures.pop("2")
            
        board.game_over = data.get("game_over", False)
        board.winner = data.get("winner", None)
        board.victory_reason = data.get("victory_reason", "")
        
        # Restore timers
        board.total_time_limit = data.get("total_time_limit", 0)
        board.move_time_limit = data.get("move_time_limit", 30)
        board.player_time_remaining = data.get("player_time_remaining", {1: 0.0, 2: 0.0})
        # Handle JSON string keys for player_time_remaining
        if "1" in board.player_time_remaining:
            board.player_time_remaining[1] = board.player_time_remaining.pop("1")
        if "2" in board.player_time_remaining:
            board.player_time_remaining[2] = board.player_time_remaining.pop("2")
            
        board.current_move_time_remaining = data.get("current_move_time_remaining", 30.0)
        
        # Restore stones
        stones_data = data.get("stones", {})
        for key, stone_data in stones_data.items():
            x, y = map(int, key.split(','))
            pos = (x, y)
            
            stone_type_name = stone_data["type"]
            stone_type = StoneType[stone_type_name]
            player = stone_data["player"]
            rotation = stone_data["rotation"]
            
            stone = StoneData2D(stone_type, player)
            stone.rotation_angle = rotation
            board.stones[pos] = stone
            
        return board
    
    def clone(self):
        """Create a deep copy of the board state (faster than to_dict/from_dict)."""
        new_board = BoardState2D(self.grid_size, self.starting_energy, self.territory_threshold,
                                 self.infinite_energy, self.energy_cost, self.infinite_score)
        
        # Copy simple attributes
        new_board.player_energy = self.player_energy.copy()
        new_board.player_captures = self.player_captures.copy()
        new_board.game_over = self.game_over
        new_board.winner = self.winner
        new_board.victory_reason = self.victory_reason
        new_board.consecutive_passes = self.consecutive_passes
        
        # Copy timer state
        new_board.total_time_limit = self.total_time_limit
        new_board.move_time_limit = self.move_time_limit
        new_board.player_time_remaining = self.player_time_remaining.copy()
        new_board.current_move_time_remaining = self.current_move_time_remaining
        
        # Deep copy stones
        for pos, stone in self.stones.items():
            new_stone = StoneData2D(stone.stone_type, stone.player)
            new_stone.rotation_angle = stone.rotation_angle
            new_board.stones[pos] = new_stone
            
        # Copy laser sources
        new_board.laser_sources = self.laser_sources.copy()
        
        return new_board
    
    def place_stone(self, pos_tuple, stone_type_name="PRISM", player=1):
        """Place a stone at (x, y). Costs 1 energy."""
        x, y = pos_tuple
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            print(f"Position {pos_tuple} out of bounds")
            return False
        
        if pos_tuple in self.stones:
            print(f"Stone already at {pos_tuple}")
            return False
        
        # Check energy (skip if infinite)
        if not self.infinite_energy and not self.has_energy(player, self.energy_cost):
            print(f"Player {player} has insufficient energy")
            return False
        
        # Determine Type
        sType = StoneType.PRISM
        if stone_type_name == "MIRROR":
            sType = StoneType.MIRROR
        elif stone_type_name == "SPLITTER":
            sType = StoneType.SPLITTER
        elif stone_type_name == "BLOCKER":
            sType = StoneType.BLOCKER
        
        # Spend energy (if not infinite) and place stone
        if not self.infinite_energy:
            self.spend_energy(player, self.energy_cost)
        self.stones[pos_tuple] = StoneData2D(sType, player)
        self.reset_passes()  # Valid move resets pass counter
        self.check_victory_condition()  # Check for victory
        return True
    
    def rotate_stone(self, pos_tuple, angle):
        """Rotate stone at position by angle degrees (relative)."""
        if pos_tuple in self.stones:
            stone = self.stones[pos_tuple]
            stone.set_rotation(stone.rotation_angle + angle)
            return True
        return False
    
    def set_rotation_to(self, pos_tuple, angle):
        """Set stone rotation to absolute angle in degrees."""
        if pos_tuple in self.stones:
            stone = self.stones[pos_tuple]
            stone.set_rotation(angle)
            return True
        return False
    
    def get_stone_at(self, pos_tuple):
        """Get stone at position."""
        return self.stones.get(pos_tuple)
    
    def move_stone(self, from_pos, to_pos):
        """Move a stone from one position to another with board wrapping.
        
        Args:
            from_pos: (x, y) source position
            to_pos: (x, y) target position (will be wrapped)
        
        Returns:
            Wrapped (x, y) position if successful, None otherwise
        """
        if from_pos not in self.stones:
            return None
        
        # Wrap coordinates using modular arithmetic
        wrapped_x = to_pos[0] % self.grid_size
        wrapped_y = to_pos[1] % self.grid_size
        wrapped_pos = (wrapped_x, wrapped_y)
        
        # Cannot move to occupied cell
        if wrapped_pos in self.stones and wrapped_pos != from_pos:
            return None
        
        # Move the stone
        stone = self.stones.pop(from_pos)
        self.stones[wrapped_pos] = stone
        self.reset_passes()
        return wrapped_pos
    
    def move_stone_along_curve(self, from_pos, control_points, player):
        """Move a stone along a Bezier curve path.
        
        Args:
            from_pos: (x, y) starting position
            control_points: List of (x, y) control points defining the curve.
                           For quadratic Bezier: [control_point, end_point]
                           For cubic Bezier: [control1, control2, end_point]
            player: Player who owns the stone
        
        Returns:
            Final wrapped (x, y) position if successful, None otherwise
        """
        if from_pos not in self.stones:
            return None
        stone = self.stones[from_pos]
        if stone.player != player:
            return None
        
        # The final destination is the last control point
        if not control_points:
            return None
        
        end_point = control_points[-1]
        
        # Wrap the final position
        wrapped_x = int(round(end_point[0])) % self.grid_size
        wrapped_y = int(round(end_point[1])) % self.grid_size
        final_pos = (wrapped_x, wrapped_y)
        
        # Cannot move to occupied cell
        if final_pos in self.stones and final_pos != from_pos:
            return None
        
        # Move the stone to final position
        s = self.stones.pop(from_pos)
        self.stones[final_pos] = s
        self.reset_passes()
        return final_pos
    
    def add_laser_source(self, pos, direction, player=1):
        """Add a laser source with player ownership."""
        self.laser_sources.append((pos, direction, player))
    
    def clear_laser_sources(self):
        """Clear all laser sources."""
        self.laser_sources.clear()
    
    # Energy Management Methods
    
    def get_energy(self, player):
        """Get current energy for player."""
        return self.player_energy.get(player, 0)
    
    def has_energy(self, player, amount=None):
        """Check if player has enough energy. If infinite_energy, always True."""
        if self.infinite_energy:
            return True
        if amount is None:
            amount = self.energy_cost
        return self.get_energy(player) >= amount
    
    def spend_energy(self, player, amount):
        """Spend energy. Returns True if successful."""
        if not self.has_energy(player, amount):
            return False
        self.player_energy[player] -= amount
        return True
    
    def recharge_energy(self, player, amount):
        """Recharge energy (respects max cap)."""
        current = self.get_energy(player)
        self.player_energy[player] = min(current + amount, self.max_energy)
    
    def end_turn(self, player):
        """End turn: recharge energy."""
        # Base recharge: +2 per turn
        self.recharge_energy(player, 2)
    
    def process_laser_captures(self, player, laser_paths):
        """Process stone captures from laser beam.
        
        Args:
            player: Player shooting the laser (1 or 2)
            laser_paths: List of paths from LaserCalculator2D
        
        Returns:
            List of captured stone positions
        """
        captured_stones = []
        
        # Check all points along laser paths
        for path in laser_paths:
            for point in path:
                # Check if there's a stone at this position
                # Laser points are floats (intersections), need to round to nearest grid cell
                x, y = point
                grid_pos = (int(round(x)), int(round(y)))
                
                stone = self.get_stone_at(grid_pos)
                if stone and stone.player != player:
                    # Opponent stone hit by laser - capture it!
                    captured_stones.append(grid_pos)
        
        # Remove captured stones and update capture count
        for pos in captured_stones:
            if pos in self.stones:
                del self.stones[pos]
                self.player_captures[player] += 1
        
        return captured_stones
    
    def get_captures(self, player):
        """Get capture count for player."""
        return self.player_captures.get(player, 0)
    
    def pass_turn(self, player):
        """Handle player passing their turn."""
        self.consecutive_passes += 1
        self.end_turn(player)
        
        if self.consecutive_passes >= 2:
            self.game_over = True
            self.victory_reason = "Mutual Pass"
            self._determine_winner_by_score()
            return True
        return False
    
    def reset_passes(self):
        """Reset consecutive passes counter (call on valid move)."""
        self.consecutive_passes = 0
    
    def surrender(self, player):
        """Player surrenders the game."""
        self.game_over = True
        self.winner = 2 if player == 1 else 1
        self.victory_reason = f"Player {player} Surrendered"
    
    def check_victory_condition(self):
        """Check for Total Victory (Mercy Rule). Skipped if infinite_score is True."""
        if self.game_over:
            return
        
        # Skip mercy rule when infinite_score is enabled
        if self.infinite_score:
            return
            
        score = self.calculate_score()
        p1_score = score["player1"] + (self.player_captures[1] * 2)
        p2_score = score["player2"] + (self.player_captures[2] * 2)
        
        diff = abs(p1_score - p2_score)
        total_territory = score["player1"] + score["player2"] + score["contested"]
        
        # Condition 1: Score difference > 50
        if diff > 50:
            self.game_over = True
            self.winner = 1 if p1_score > p2_score else 2
            self.victory_reason = "Total Victory (Score Difference > 50)"
            return
            
        # Condition 2: > Territory Threshold Control (if at least 20 points on board)
        if total_territory > 20:
            p1_ratio = score["player1"] / total_territory
            p2_ratio = score["player2"] / total_territory
            
            if p1_ratio > self.territory_threshold:
                self.game_over = True
                self.winner = 1
                self.victory_reason = f"Total Victory (>{int(self.territory_threshold*100)}% Territory)"
            elif p2_ratio > self.territory_threshold:
                self.game_over = True
                self.winner = 2
                self.victory_reason = f"Total Victory (>{int(self.territory_threshold*100)}% Territory)"

    def _determine_winner_by_score(self):
        """Determine winner based on current score."""
        score = self.calculate_score()
        p1_final = score["player1"] + (self.player_captures[1] * 2)
        p2_final = score["player2"] + (self.player_captures[2] * 2)
        
        if p1_final > p2_final:
            self.winner = 1
        elif p2_final > p1_final:
            self.winner = 2
        else:
            self.winner = 0  # Tie
    
    def end_game_by_time(self):
        """End game due to time expiration. Winner determined by final score."""
        if self.game_over:
            return
            
        self.game_over = True
        self._determine_winner_by_score()
        
        score = self.calculate_score()
        p1_final = score["player1"] + (self.player_captures[1] * 2)
        p2_final = score["player2"] + (self.player_captures[2] * 2)
        
        if self.winner == 0:
            self.victory_reason = f"Time Expired - Draw ({p1_final} - {p2_final})"
        else:
            self.victory_reason = f"Time Expired - P{self.winner} Wins ({p1_final} - {p2_final})"
    
    def calculate_score(self):
        """Calculate territory score based on illuminated intersections."""
        from _02_engines.laser import LaserCalculator2D
        
        laser_calc = LaserCalculator2D(self.grid_size)
        
        # Track illuminated points per player
        player1_points = set()
        player2_points = set()
        
        # Calculate laser paths for each source
        for source_pos, source_dir, player in self.laser_sources:
            paths = laser_calc.calculate_path(source_pos, source_dir, self.stones)
            unique_points = laser_calc.get_unique_points(paths)
            
            if player == 1:
                player1_points.update(unique_points)
            else:
                player2_points.update(unique_points)
        
        # Handle contested territory
        contested = player1_points & player2_points
        player1_territory = player1_points - contested
        player2_territory = player2_points - contested
        
        return {
            "player1": len(player1_territory),
            "player2": len(player2_territory),
            "contested": len(contested),
            "player1_points": player1_territory,
            "player2_points": player2_territory,
            "contested_points": contested
        }
