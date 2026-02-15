#!/usr/bin/env python3
"""
Game Server for Rust RL Agent
-----------------------------
Provides a JSON IPC interface to the full Python game logic.

Protocol:
    Rust -> Python (stdin): {"command": "reset/step/get_valid_actions", ...}
    Python -> Rust (stdout): {"observation": [...], "reward": ..., "done": ..., ...}

Usage:
    python -m _00_entry.game_server
"""

import sys
import json
import math
from typing import Optional, Dict, Any, List, Tuple

from _01_core_logic.board_state import BoardState2D, StoneType, StoneData2D
from _02_engines.laser import LaserCalculator2D


class GameServer:
    """JSON IPC game server for RL training."""
    
    def __init__(self, grid_size: int = 19):
        self.grid_size = grid_size
        self.board: Optional[BoardState2D] = None
        self.laser_calc = LaserCalculator2D(grid_size)
        self.current_player = 1
        self.turn_count = 0
        self.max_turns = 500
        self.game_over = False
        self.winner = None
        self.victory_reason = None
        self.realtime_mode = False
        
    def reset(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Reset game to initial state with optional config."""
        if config is None:
            config = {}
            
        self.max_turns = config.get("max_turns", 500)
        
        self.board = BoardState2D(
            grid_size=self.grid_size,
            starting_energy=config.get("starting_energy", 20),
            territory_threshold=config.get("territory_threshold", 0.8),
            infinite_energy=config.get("infinite_energy", False),
            infinite_score=config.get("infinite_score", False)
        )
        self.realtime_mode = config.get("realtime_mode", False)
        self.current_player = 1
        self.turn_count = 0
        self.game_over = False
        self.winner = None
        self.victory_reason = None
        self.selection = [] # Store currently selected positions
        
        return {
            "observation": self._get_observation(),
            "info": {"grid_size": self.grid_size, "realtime_mode": self.realtime_mode}
        }
    
    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action and return result."""
        if self.board is None:
            return {"error": "Game not initialized. Call reset first."}
        
        if self.game_over:
            return {
                "observation": self._get_observation(),
                "reward": 0.0,
                "done": True,
                "info": {"winner": self.winner, "reason": self.victory_reason}
            }
        
        action_type = action.get("type", "pass")
        player = self.current_player
        success = False
        reward = 0.0
        turn_ended = True # Default to true for most actions
        
        if action_type == "select":
            # Handle selection - does not end turn
            positions = action.get("positions", [])
            # Validate positions are on board
            valid_positions = []
            for p in positions:
                if isinstance(p, list) and len(p) == 2:
                     x, y = p
                     if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                         valid_positions.append((x, y))
            
            self.selection = valid_positions
            success = True
            turn_ended = False
            
        elif action_type == "place":
            x, y = action.get("x", 0), action.get("y", 0)
            stone_type = action.get("stone_type", "PRISM")
            success = self.board.place_stone((x, y), stone_type, player)
            if success:
                self.board.reset_passes()
                reward = 0.01  # Small reward for valid placement
                
        elif action_type == "rotate":
            x, y = action.get("x", 0), action.get("y", 0)
            angle = action.get("angle", 0)
            stone = self.board.get_stone_at((x, y))
            if stone and stone.player == player:
                self.board.set_rotation_to((x, y), angle)
                success = True
                reward = 0.005  # Small reward for rotation
                
        elif action_type == "laser":
            x, y = action.get("x", 0), action.get("y", 0)
            dx, dy = action.get("dx", 1), action.get("dy", 0)
            # Fire laser and process captures
            paths = self.laser_calc.calculate_path(
                (x + 0.5, y + 0.5),
                (dx, dy),
                self.board.stones
            )
            captures = self.board.process_laser_captures(player, paths)
            if captures:
                reward = len(captures) * 0.5  # Reward per capture
            success = True
        
        elif action_type == "move":
            from_x = action.get("from_x", 0)
            from_y = action.get("from_y", 0)
            to_x = action.get("to_x", 0)
            to_y = action.get("to_y", 0)
            from_pos = (from_x, from_y)
            to_pos = (to_x, to_y)
            stone = self.board.get_stone_at(from_pos)
            if stone and stone.player == player:
                wrapped = self.board.move_stone(from_pos, to_pos)
                if wrapped is not None:
                    success = True
                    reward = 0.01
        
        elif action_type == "curve_move":
            from_x = action.get("from_x", 0)
            from_y = action.get("from_y", 0)
            cx = action.get("control_x", 0)
            cy = action.get("control_y", 0)
            ex = action.get("end_x", 0)
            ey = action.get("end_y", 0)
            from_pos = (from_x, from_y)
            control_points = [(cx, cy), (ex, ey)]
            stone = self.board.get_stone_at(from_pos)
            if stone and stone.player == player:
                final_pos = self.board.move_stone_along_curve(from_pos, control_points, player)
                if final_pos is not None:
                    success = True
                    reward = 0.02  # Slightly higher reward for curved movement
            
        elif action_type == "pass":
            self.board.pass_turn(player)
            success = True
            reward = -0.01  # Small penalty for passing
        
        # End turn
        if success:
            self.board.end_turn(player)
            self.turn_count += 1
            self.current_player = 3 - self.current_player  # Switch: 1->2, 2->1
        else:
            reward = -0.1  # Penalty for invalid action
        
        # Check victory conditions
        self._check_victory()
        
        # Add shaping reward based on score difference
        if not self.game_over:
            my_score = self._calculate_player_score(1 if player == 1 else 1)
            opp_score = self._calculate_player_score(2 if player == 1 else 2)
            reward += (my_score - opp_score) * 0.001
        
        # Terminal reward
        if self.game_over and self.winner is not None:
            if self.winner == player:
                reward += 10.0
            else:
                reward -= 10.0
        
        return {
            "observation": self._get_observation(),
            "reward": reward,
            "done": self.game_over,
            "info": {
                "current_player": self.current_player,
                "turn": self.turn_count,
                "winner": self.winner,
                "reason": self.victory_reason,
                "action_success": success
            }
        }
    
    def get_valid_actions(self) -> Dict[str, Any]:
        """Get list of valid actions for current player."""
        if self.board is None:
            return {"error": "Game not initialized"}
        
        valid = []
        player = self.current_player
        
        # Place actions
        if self.board.has_energy(player, 1):
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    if (x, y) not in self.board.stones:
                        for stone_type in ["PRISM", "MIRROR", "SPLITTER", "BLOCKER"]:
                            valid.append({
                                "type": "place",
                                "x": x, "y": y,
                                "stone_type": stone_type
                            })
        
        # Rotate actions (own stones only)
        for pos, stone in self.board.stones.items():
            if stone.player == player:
                for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                    valid.append({
                        "type": "rotate",
                        "x": pos[0], "y": pos[1],
                        "angle": angle
                    })
        
        # Move actions (realtime mode only)
        if self.realtime_mode:
            for pos, stone in self.board.stones.items():
                if stone.player == player:
                    # 8-directional moves with wrapping
                    directions = [
                        (0, -1), (0, 1), (-1, 0), (1, 0),
                        (-1, -1), (1, -1), (-1, 1), (1, 1)
                    ]
                    for dx, dy in directions:
                        nx = (pos[0] + dx) % self.grid_size
                        ny = (pos[1] + dy) % self.grid_size
                        if (nx, ny) not in self.board.stones:
                            valid.append({
                                "type": "move",
                                "from_x": pos[0], "from_y": pos[1],
                                "to_x": nx, "to_y": ny
                            })
                    
                    # Curve move actions (sample 2 random curves per stone)
                    import random
                    for _ in range(2):
                        angle = random.uniform(0, 2 * math.pi)
                        radius = random.randint(1, min(3, self.grid_size // 4))
                        cx = pos[0] + radius * math.cos(angle)
                        cy = pos[1] + radius * math.sin(angle)
                        ex = int(round(pos[0] + 2 * radius * math.cos(angle))) % self.grid_size
                        ey = int(round(pos[1] + 2 * radius * math.sin(angle))) % self.grid_size
                        if (ex, ey) not in self.board.stones:
                            valid.append({
                                "type": "curve_move",
                                "from_x": pos[0], "from_y": pos[1],
                                "control_x": round(cx, 1), "control_y": round(cy, 1),
                                "end_x": ex, "end_y": ey
                            })
        
        # Laser actions (from own stones)
        for pos, stone in self.board.stones.items():
            if stone.player == player:
                for direction in range(8):  # 8 directions
                    rad = direction * math.pi / 4
                    valid.append({
                        "type": "laser",
                        "x": pos[0], "y": pos[1],
                        "dx": math.cos(rad),
                        "dy": math.sin(rad)
                    })
        
        # Pass is always valid
        valid.append({"type": "pass"})
        
        return {"valid_actions": valid, "count": len(valid)}
    
    def _get_observation(self) -> List[float]:
        """Get flattened observation vector."""
        if self.board is None:
            return [0.0] * (self.grid_size * self.grid_size * 9)
        
        obs = []
        
        # Per-cell features: [empty, p1_prism, p1_mirror, p1_splitter, p1_blocker, p2_prism, p2_mirror, p2_splitter, p2_blocker]
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                cell = [0.0] * 9
                stone = self.board.stones.get((x, y))
                if stone is None:
                    cell[0] = 1.0  # Empty
                else:
                    idx = (stone.player - 1) * 4 + (stone.stone_type.value - 1) + 1
                    if idx < 9:
                        cell[idx] = 1.0
                obs.extend(cell)
        
        return obs
    
    def _calculate_player_score(self, player: int) -> int:
        """Calculate score for a player."""
        if self.board is None:
            return 0
        # Use board's calculate_score which handles territory
        scores = self.board.calculate_score()
        return scores.get(player, 0)
    
    def _check_victory(self):
        """Check for game end conditions."""
        if self.board is None:
            return
        
        # Check board's victory condition
        result = self.board.check_victory_condition()
        if result:
            self.game_over = True
            self.winner = result.get("winner")
            self.victory_reason = result.get("reason", "victory")
            return
        
        # Check max turns
        if self.turn_count >= self.max_turns:
            self.game_over = True
            self.victory_reason = "max_turns"
            # Determine winner by score
            s1 = self._calculate_player_score(1)
            s2 = self._calculate_player_score(2)
            if s1 > s2:
                self.winner = 1
            elif s2 > s1:
                self.winner = 2
            else:
                self.winner = None  # Draw


def main():
    """Main server loop - reads JSON from stdin, writes to stdout."""
    server = GameServer(grid_size=19)
    
    # Send ready signal
    print(json.dumps({"status": "ready", "version": "1.0.0"}), flush=True)
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            command = request.get("command", "")
            
            if command == "reset":
                config = request.get("config", None)
                response = server.reset(config)
            elif command == "step":
                action = request.get("action", {"type": "pass"})
                response = server.step(action)
            elif command == "get_valid_actions":
                response = server.get_valid_actions()
            elif command == "quit":
                print(json.dumps({"status": "goodbye"}), flush=True)
                break
            else:
                response = {"error": f"Unknown command: {command}"}
            
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON: {e}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
