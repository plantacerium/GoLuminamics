"""
File: game_replayer.py
Creation Date: 2025-11-28
Last Updated: 2025-11-28
Version: 2.0.0
Description: Source file.
"""

from _01_core_logic.recorder import GameRecorder
from _01_core_logic.board_state import BoardState2D
from _02_engines.laser import LaserCalculator2D

class GameReplayer:
    """Replay a saved game step by step."""
    
    def __init__(self, game_file):
        self.game_data = GameRecorder.load_game(game_file)
        self.current_move_index = 0
        self.board = BoardState2D(grid_size=19)
        self.laser_calc = LaserCalculator2D(grid_size=19)
    
    def print_game_info(self):
        """Print game metadata."""
        print("=" * 60)
        print(f"Game ID: {self.game_data['game_id']}")
        print(f"Date: {self.game_data['date']}")
        print(f"Players: {self.game_data['players'][0]} vs {self.game_data['players'][1]}")
        print(f"Total Turns: {self.game_data['total_turns']}")
        print("=" * 60)
        print()
    
    def replay_all(self):
        """Replay entire game with annotations."""
        self.print_game_info()
        
        for move in self.game_data['moves']:
            self.print_move(move)
            self.execute_move(move)
            print()
        
        print("=" * 60)
        print("Game replay complete!")
        print(f"Final board state: {len(self.board.stones)} stones placed")
        print("=" * 60)
    
    def print_move(self, move):
        """Print move details with comment."""
        turn = move['turn']
        player = move['player']
        action = move['action']
        comment = move.get('comment', '')
        
        player_name = self.game_data['players'][player - 1]
        
        print(f"Turn {turn}: {player_name} (Player {player})")
        print(f"  Action: {action.upper()}")
        
        if action == "place":
            pos = tuple(move['position'])
            stone_type = move['stone_type']
            print(f"  Position: {pos}")
            print(f"  Stone Type: {stone_type}")
        elif action == "laser":
            pos = tuple(move['position'])
            direction = tuple(move['direction'])
            print(f"  Start: {pos}")
            print(f"  Direction: {direction}")
        
        if comment:
            print(f"  Strategy: {comment}")
    
    def execute_move(self, move):
        """Execute move on the internal board state."""
        action = move['action']
        player = move['player']
        
        if action == "place":
            pos = tuple(move['position'])
            stone_type = move['stone_type']
            self.board.place_stone(pos, stone_type, player)
        elif action == "laser":
            pos = tuple(move['position'])
            direction = tuple(move['direction'])
            paths = self.laser_calc.calculate_path(pos, direction, self.board.stones)
            print(f"  -> Laser creates {len(paths)} beam path(s)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        game_file = sys.argv[1]
    else:
        # Try to find the most recent game file
        import glob
        game_files = glob.glob("games/*.json")
        if game_files:
            game_file = max(game_files, key=lambda x: x)
            print(f"Loading most recent game: {game_file}\n")
        else:
            print("No game files found. Run simulate_game.py first.")
            sys.exit(1)
    
    replayer = GameReplayer(game_file)
    replayer.replay_all()
