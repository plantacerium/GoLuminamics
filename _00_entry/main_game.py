"""
File: main.py
Creation Date: 2025-11-28
Last Updated: 2025-11-29
Version: 2.1.0
Description: Source file.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from _03_ui.game_board import GameBoard
from _03_ui.controls import UIControls
from _01_core_logic.recorder import GameRecorder

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoLuminamics")
        self.resize(1200, 800)
        
        # recorder initialized later after board

        
        # Set dark background to reduce white space
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1A1D;
            }
            QWidget {
                background-color: #1A1A1D;
            }
        """)
        
        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20) # Add space above/below
        layout.setSpacing(20)
        
        # Controls (create first to get initial threshold)
        self.controls = UIControls()
        
        # Game Board (with initial threshold from controls)
        initial_threshold = self.controls.get_victory_threshold()
        self.board = GameBoard(territory_threshold=initial_threshold)
        
        # Initialize Recorder
        self.recorder = GameRecorder(player1_name="Player 1", player2_name="Player 2", grid_size=self.board.grid_size)
        
        layout.addWidget(self.board, stretch=1)
        layout.addWidget(self.controls, stretch=0)
        
        # Connect signals
        self.controls.splitter_radio.toggled.connect(lambda: self.board.set_stone_type(self.controls.get_selected_stone_type()))
        self.controls.mirror_radio.toggled.connect(lambda: self.board.set_stone_type(self.controls.get_selected_stone_type()))
        self.controls.prism_radio.toggled.connect(lambda: self.board.set_stone_type(self.controls.get_selected_stone_type()))
        self.controls.blocker_radio.toggled.connect(lambda: self.board.set_stone_type(self.controls.get_selected_stone_type()))
        
        # Connect theme and victory threshold signals
        self.controls.theme_changed.connect(self.board.set_theme)
        self.controls.victory_threshold_changed.connect(self.handle_threshold_change)
        self.controls.grid_size_changed.connect(self.handle_grid_size_change)
        self.controls.infinite_energy_changed.connect(self.handle_infinite_energy_change)
        self.controls.infinite_score_changed.connect(self.handle_infinite_score_change)
        
        # Connect stone placement to update energy display
        self.board.stone_placed.connect(self.on_stone_placed)
        self.board.stone_rotated.connect(self.on_stone_rotated)
        self.board.laser_input.connect(self.handle_laser_mouse)
        self.controls.manual_place.connect(self.handle_manual_place) # Connect manual placement
        
        # Connect control signals
        self.controls.pass_turn.connect(self.handle_pass)
        self.controls.surrender.connect(self.handle_surrender)
        self.controls.restart_game.connect(self.handle_restart)
        self.controls.save_game.connect(self.handle_save_game)
        self.controls.command_entered.connect(self.handle_command)
        self.controls.laser_shot.connect(self.handle_laser_mouse)
        
        # Connect timer signals
        self.controls.timer_settings_changed.connect(self.board.set_timer_settings)
        self.board.timer_updated.connect(self.controls.update_timers)
        self.board.game_over_signal.connect(self.check_game_over)
        
        # Initialize timer settings
        self.controls.emit_timer_settings()
        
        # Initial energy display
        self.update_energy_display()
        
    def _record_action(self, action_type, params, description):
        """Helper to record an action to the log."""
        # Calculate reward (simple score difference for now)
        score = self.board.board_state.calculate_score()
        p1_score = score["player1"]
        p2_score = score["player2"]
        # Reward is from perspective of current player (who just moved)
        reward = 0.0 
        
        self.recorder.record_step(
            turn_id=self.recorder.current_turn,
            state_t=self.board.board_state.to_dict(), # Note: This is post-state.
            agent_action={"type": action_type, "params": params},
            reward_t=reward,
            terminal=self.board.board_state.game_over,
            event_log=[description, f"Score: P1={p1_score}, P2={p2_score}"]
        )
    
    def on_stone_placed(self, pos, stone_type):
        """Handle stone placement updates."""
        self.update_energy_display()
        
        # Record the move
        # Note: The player has already switched in GameBoard.place_stone
        # The player who placed the stone is the *previous* player.
        player_who_moved = 1 if self.board.current_player == 2 else 2
        
        self._record_action(
            "place", 
            {"position": pos, "stone_type": stone_type, "player": player_who_moved},
            f"Player {player_who_moved} placed {stone_type} at {pos}"
        )
        
        self.check_game_over()
    
    def on_stone_rotated(self, pos, angle):
        """Handle stone rotation updates."""
        # Record the rotation
        # Rotation is a free action, but we should record who did it?
        # Usually the current player, but technically you can only rotate your own stones?
        # Board logic doesn't strictly enforce "only your turn" for rotation in UI (it might),
        # but let's assume valid rotation.
        
        stone = self.board.board_state.get_stone_at(pos)
        player = stone.player if stone else self.board.current_player
        
        self._record_action(
            "rotate",
            {"position": pos, "angle": angle, "player": player},
            f"Player {player} rotated stone at {pos} to {angle:.1f}°"
        )

    def check_game_over(self):
        """Check if game has ended."""
        if self.board.board_state.game_over:
            score = self.board.board_state.calculate_score()
            p1_caps = self.board.board_state.get_captures(1)
            p2_caps = self.board.board_state.get_captures(2)
            
            p1_final = score["player1"] + (p1_caps * 2)
            p2_final = score["player2"] + (p2_caps * 2)
            
            # Show victory screen with scores (no popup)
            self.board.show_victory_screen(
                self.board.board_state.winner, 
                self.board.board_state.victory_reason,
                p1_final,
                p2_final
            )
            
    def handle_pass(self):
        """Handle pass turn."""
        if self.board.board_state.game_over:
            return
            
        player = self.board.current_player
        self.board.board_state.pass_turn(player)
        print(f"Player {player} passed.")
        
        self._record_action("pass", {"player": player}, f"Player {player} passed turn")
        
        self.board.end_turn() # Switch player
        self.update_energy_display()
        self.check_game_over()
        
    def handle_surrender(self):
        """Handle surrender."""
        if self.board.board_state.game_over:
            return
            
        player = self.board.current_player
        self.board.board_state.surrender(player)
        
        self._record_action("surrender", {"player": player}, f"Player {player} surrendered")
        
        self.check_game_over()
        
    def handle_restart(self):
        """Restart the game."""
        # Re-initialize board
        self.board.clear_board()
        
        # Re-apply timer settings from UI
        self.controls.emit_timer_settings()
        
        # Reset recorder
        self.recorder = GameRecorder(player1_name="Player 1", player2_name="Player 2", grid_size=self.board.grid_size)
        
        self.update_energy_display()
        self.controls.update_score(0, 0)
        self.controls.update_captures(0, 0)
        print("Game Restarted")
    
    def handle_threshold_change(self, new_threshold):
        """Handle victory threshold change from UI."""
        self.board.territory_threshold = new_threshold
        self.board.board_state.territory_threshold = new_threshold
        print(f"Victory threshold changed to {int(new_threshold * 100)}% territory control")
    
    def handle_grid_size_change(self, new_size):
        """Handle grid size change from UI."""
        if new_size != self.board.board_state.grid_size:
            # Confirm with user since this restarts the game
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "Change Board Size",
                f"Changing to {new_size}x{new_size} will restart the game. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.board.set_grid_size(new_size)
                self.handle_restart()
                print(f"Grid size changed to {new_size}x{new_size}")
            else:
                # Reset combo to current size
                current_size = self.board.board_state.grid_size
                index = self.controls.grid_size_combo.findData(current_size)
                self.controls.grid_size_combo.blockSignals(True)
                self.controls.grid_size_combo.setCurrentIndex(index)
                self.controls.grid_size_combo.blockSignals(False)
    
    def handle_infinite_energy_change(self, enabled):
        """Handle infinite energy toggle from UI."""
        self.board.board_state.infinite_energy = enabled
        if enabled:
            print("Infinite Energy enabled")
        else:
            print("Infinite Energy disabled")
        self.update_energy_display()
    
    def handle_infinite_score_change(self, enabled):
        """Handle infinite score toggle from UI."""
        self.board.board_state.infinite_score = enabled
        if enabled:
            print("Infinite Score enabled (no mercy rule)")
        else:
            print("Infinite Score disabled (mercy rule active)")
        
    def handle_manual_place(self, pos):
        """Handle manual stone placement from UI inputs."""
        if self.board.board_state.game_over:
            return
            
        stone_type = self.controls.get_selected_stone_type()
        player = self.controls.get_player_color()
        
        # Check if it's correct player's turn
        if player != self.board.current_player:
            QMessageBox.warning(self, "Wrong Turn", f"It is Player {self.board.current_player}'s turn!")
            return

        self.board.place_stone(pos, stone_type, player)
        
    def handle_save_game(self):
        """Save the current game state."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Game", "", "JSON Files (*.json)")
        if file_name:
            try:
                # Save theme in metadata
                if "game_settings" not in self.recorder.metadata:
                    self.recorder.metadata["game_settings"] = {}
                self.recorder.metadata["game_settings"]["theme"] = self.board.current_theme
                
                # Use the recorder to save the full log
                self.recorder.save_game(file_name)
                print(f"Game saved to {file_name}")
            except Exception as e:
                print(f"Error saving game: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save game: {str(e)}")

    def update_energy_display(self):
        """Update energy display in UI."""
        p1_energy = self.board.board_state.get_energy(1)
        p2_energy = self.board.board_state.get_energy(2)
        self.controls.update_energy(p1_energy, p2_energy)
    
    def handle_command(self, text):
        """Handle command input."""
        print(f"Command: {text}")
        # Parse: stone(x,y) [TYPE]
        if text.startswith("stone("):
            try:
                parts = text.split()
                coords = parts[0][6:-1]  # Extract "x,y" from "stone(x,y)"
                x, y = map(int, coords.split(','))
                
                stone_type = "PRISM"
                if len(parts) > 1:
                    stone_type = parts[1].upper()
                
                self.board.place_stone((x, y), stone_type)
            except Exception as e:
                print(f"Error parsing command: {e}")
    
    def handle_laser_mouse(self, start, direction, player):
        """Handle laser input from mouse."""
        try:
            captured = self.board.shoot_laser(start, direction, player)
            
            # Record the move
            self._record_action(
                "laser",
                {"position": start, "direction": direction, "player": player, "captures": captured},
                f"Player {player} fired laser from {start} capturing {len(captured)} stones"
            )
            
            # Update score display
            score_data = self.board.board_state.calculate_score()
            self.controls.update_score(score_data["player1"], score_data["player2"])
            
            # Update capture display
            p1_captures = self.board.board_state.get_captures(1)
            p2_captures = self.board.board_state.get_captures(2)
            self.controls.update_captures(p1_captures, p2_captures)
            
            # Show capture notification
            if captured:
                print(f"Player {self.board.current_player} captured {len(captured)} stone(s) at {captured}!")
                
            self.check_game_over()
        except Exception as e:
            print(f"Error shooting laser: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Dark Theme Stylesheet
    app.setStyleSheet("""
        QMainWindow { background-color: #202025; }
        QWidget { color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
        QLabel { color: #E0E0E0; }
        QLineEdit { 
            background-color: #303035; 
            color: #FFFFFF; 
            border: 1px solid #505055; 
            border-radius: 4px; 
            padding: 5px; 
        }
        QPushButton { 
            background-color: #404045; 
            color: #FFFFFF; 
            border: none; 
            border-radius: 4px; 
            padding: 8px; 
        }
        QPushButton:hover { background-color: #505055; }
        QPushButton:pressed { background-color: #606065; }
        QComboBox {
            background-color: #303035;
            color: #FFFFFF;
            border: 1px solid #505055;
            border-radius: 4px;
            padding: 5px;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            border-left-width: 1px;
            border-left-color: #505055;
            border-left-style: solid;
        }
        QRadioButton { color: #E0E0E0; }
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
        }
        QRadioButton::indicator:unchecked {
            background-color: #303035;
            border: 2px solid #505055;
            border-radius: 9px;
        }
        QRadioButton::indicator:checked {
            background-color: #007ACC;
            border: 2px solid #007ACC;
            border-radius: 9px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
