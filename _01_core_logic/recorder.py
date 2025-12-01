import json
import datetime
from pathlib import Path

class GameRecorder:
    """
    Records game moves and saves to JSON with strategic annotations.
    Updated for Protocol V2: Supports Replayable JSON Log schema for DRL and LLM training.
    """
    
    def __init__(self, player1_name="Player 1", player2_name="Player 2", metadata=None):
        self.game_id = f"2d_game_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.players = [player1_name, player2_name]
        
        # Protocol V2 Schema Fields
        self.log_version = "2.0.0"
        self.metadata = metadata if metadata else {
            "random_seed": None,
            "game_settings": {
                "player1": player1_name,
                "player2": player2_name
            }
        }
        self.turn_sequence = []
        self.current_turn = 1
    
    def record_step(self, turn_id, state_t, agent_action, reward_t, terminal, event_log):
        """
        Record a discrete time step/transition for DRL/LLM training.
        
        Args:
            turn_id (int): Sequential turn number.
            state_t (object): Standardized observation of the board before action.
            agent_action (object): The discrete action taken.
            reward_t (float): Immediate numerical reward.
            terminal (bool): Whether the game ended.
            event_log (list): Human-readable strings for SFT.
        """
        step_data = {
            "turn_id": turn_id,
            "state_t": state_t,
            "agent_action": agent_action,
            "reward_t": reward_t,
            "terminal": terminal,
            "event_log": event_log
        }
        self.turn_sequence.append(step_data)
        self.current_turn = turn_id + 1

    def record_move(self, player, action, position=None, stone_type=None, direction=None, angle=None, comment="", captures=None):
        """
        Legacy method for recording moves. 
        Adapts to the new schema by creating a partial turn entry.
        """
        # Construct a legacy-style action object
        agent_action = {
            "player": player,
            "type": action,
            "position": list(position) if position else None,
            "stone_type": stone_type,
            "direction": list(direction) if direction else None,
            "angle": angle
        }
        
        # Construct a simple event log
        event_log = [f"{player} performed {action}"]
        if comment:
            event_log.append(comment)
        if captures:
            event_log.append(f"Captured {len(captures)} stones")

        self.record_step(
            turn_id=self.current_turn,
            state_t={}, # Legacy calls don't provide state, placeholder
            agent_action=agent_action,
            reward_t=0.0, # Legacy calls don't provide reward
            terminal=False,
            event_log=event_log
        )
    
    def save_game(self, filename=None):
        """Save game to JSON file following the Replayable JSON Log schema."""
        if filename is None:
            filename = f"games/{self.game_id}.json"
        
        # Ensure games directory exists
        Path("games").mkdir(exist_ok=True)
        
        game_data = {
            "log_version": self.log_version,
            "metadata": self.metadata,
            "turn_sequence": self.turn_sequence
        }
        
        with open(filename, 'w') as f:
            json.dump(game_data, f, indent=2)
        
        print(f"Game saved to {filename}")
        return filename
    
    @staticmethod
    def load_game(filename):
        """Load a game from JSON file."""
        with open(filename, 'r') as f:
            return json.load(f)
