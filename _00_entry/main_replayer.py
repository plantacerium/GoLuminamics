"""
File: replayer_ui.py
Creation Date: 2025-11-28
Last Updated: 2025-11-28
Version: 2.0.0
Description: Source file.
"""

import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                               QVBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit,
                               QLineEdit, QMessageBox, QFrame, QSlider, QComboBox)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPalette, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF, QTimer
from _03_ui.game_board import GameBoard
from _01_core_logic.recorder import GameRecorder
from _02_engines.laser import LaserCalculator2D

class CaptureChart(QWidget):
    """Visual area chart showing captures over time."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200) # Increased height
        self.setBackgroundRole(QPalette.Base)
        self.p1_data = []
        self.p2_data = []
        self.current_turn = 0
        
    def set_data(self, moves):
        """Parse moves to extract capture history."""
        self.p1_data = []
        self.p2_data = []
        
        for move in moves:
            # Use per-player captures if available (V2 logs)
            if 'p1_captures' in move and 'p2_captures' in move:
                self.p1_data.append(move['p1_captures'])
                self.p2_data.append(move['p2_captures'])
            else:
                # Fallback for legacy logs
                p1_caps = self.p1_data[-1] if self.p1_data else 0
                p2_caps = self.p2_data[-1] if self.p2_data else 0
                
                if 'captures' in move and move['captures']:
                    count = len(move['captures'])
                    if move.get('player') == 1:
                        p1_caps += count
                    else:
                        p2_caps += count
                
                self.p1_data.append(p1_caps)
                self.p2_data.append(p2_caps)
        
        self.update()

    def set_current_turn(self, turn_index):
        self.current_turn = turn_index
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1E1E24"))
        
        if not self.p1_data:
            painter.setPen(QColor("#808080"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Load game to see capture chart")
            return
            
        # Dimensions
        w = self.width()
        h = self.height()
        margin_x = 10
        margin_y = 20
        
        max_val = max(max(self.p1_data), max(self.p2_data))
        # Use minimum range of 20 for better visibility of small values
        if max_val < 20:
            max_val = 20
        else:
            # Add some headroom for larger values  
            max_val = max_val * 1.1
        
        count = len(self.p1_data)
        if count < 2: return
        
        # IMPORTANT: Only show data up to current turn (progressive reveal)
        visible_count = min(self.current_turn + 1, count) if self.current_turn > 0 else count
        
        step_x = (w - 2 * margin_x) / (count - 1)
        scale_y = (h - 2 * margin_y) / max_val
        
        # Helper to map data to point
        def get_point(index, value):
            x = margin_x + index * step_x
            y = h - margin_y - (value * scale_y)
            return QPointF(x, y)
            
        # Draw Gradients (Area Chart style) - More subtle
        # Modified to only show data up to current turn
        def draw_area(data, color_hex):
            if visible_count < 2:
                return
                
            path = QPainterPath()
            path.moveTo(get_point(0, 0))
            for i in range(visible_count):  # Only draw up to current turn
                path.lineTo(get_point(i, data[i]))
            path.lineTo(get_point(visible_count-1, 0))
            path.closeSubpath()
            
            color = QColor(color_hex)
            grad = QLinearGradient(0, 0, 0, h)
            # Reduced opacity for subtlety
            grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 60)) 
            grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            
            # Draw glow effect first (background layer)
            painter.setBrush(Qt.NoBrush)
            glow_pen = QPen(color, 6)
            glow_color = QColor(color)
            glow_color.setAlpha(80)
            glow_pen.setColor(glow_color)
            painter.setPen(glow_pen)
            for i in range(visible_count - 1):
                painter.drawLine(get_point(i, data[i]), get_point(i+1, data[i+1]))
            
            # Draw main line on top - bright and visible
            painter.setBrush(Qt.NoBrush)
            pen = QPen(color, 3)
            painter.setPen(pen)
            for i in range(visible_count - 1):  # Only draw up to current turn
                painter.drawLine(get_point(i, data[i]), get_point(i+1, data[i+1]))
            
            # Draw points at each data point for better visibility
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            for i in range(visible_count):
                point = get_point(i, data[i])
                painter.drawEllipse(point, 2, 2)

        draw_area(self.p1_data, "#00FF00") # P1 Bright Green
        draw_area(self.p2_data, "#00BFFF") # P2 Bright Blue (Deep Sky Blue)
        
        # Draw gridlines for reference
        painter.setPen(QPen(QColor("#303035"), 1, Qt.DashLine))
        step_count = 5
        for i in range(1, step_count):
            y_val = (max_val / step_count) * i
            y_pos = h - margin_y - (y_val * scale_y)
            painter.drawLine(margin_x, y_pos, w - margin_x, y_pos)
        
        # Draw Labels with better placement
        painter.setPen(QColor("#A0A0A0"))
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        
        # Y-axis labels (captures count)
        painter.drawText(2, margin_y + 10, f"{int(max_val)}")
        painter.drawText(2, h - margin_y - 5, "0")
        
        # X-axis label (turns)
        painter.drawText(w - 40, h - 5, f"Turn {count}")
        
        # Draw Current Turn Indicator
        if self.current_turn < count:
            cx = margin_x + self.current_turn * step_x
            painter.setPen(QPen(QColor("#FFC107"), 2))
            painter.drawLine(cx, margin_y, cx, h - margin_y)
            
            # Draw turn number
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(cx + 5, margin_y + 10, f"Turn {self.current_turn}")

class ReplayControls(QWidget):
    """Control panel for game replay."""
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Title
        self.layout.addWidget(QLabel("<h2>Game Replayer</h2>"))
        
        # Theme Selector
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Classic", "Neon", "Pastel", "Forest", "Real Stone"])
        theme_layout.addWidget(self.theme_combo)
        self.layout.addLayout(theme_layout)
        
        self.layout.addSpacing(10)
        
        # Load Game Button
        self.load_btn = QPushButton("Load Game File")
        self.layout.addWidget(self.load_btn)
        
        # Game Info
        self.info_label = QLabel("<i>No game loaded</i>")
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)
        
        self.layout.addSpacing(10)
        
        # Score Display
        self.score_label = QLabel("<b>Score:</b> P1: 0 | P2: 0")
        self.score_label.setStyleSheet("color: #FFC107; font-size: 16px;")
        self.layout.addWidget(self.score_label)
        
        self.layout.addSpacing(10)
        
        # Chart
        self.layout.addWidget(QLabel("<b>Capture History:</b>"))
        self.chart = CaptureChart()
        self.layout.addWidget(self.chart)
        
        self.layout.addSpacing(10)
        
        # Move Info Display (Expanded)
        self.layout.addWidget(QLabel("<b>Current Move:</b>"))
        self.move_display = QTextEdit()
        self.move_display.setReadOnly(True)
        self.move_display.setMinimumHeight(180) # Make it bigger
        self.layout.addWidget(self.move_display)
        
        self.layout.addSpacing(10)
        
        # Go to Step
        goto_layout = QHBoxLayout()
        goto_layout.addWidget(QLabel("Go to Step:"))
        self.step_input = QLineEdit()
        self.step_input.setPlaceholderText("#")
        self.step_input.setFixedWidth(50)
        goto_layout.addWidget(self.step_input)
        
        self.goto_btn = QPushButton("Go")
        self.goto_btn.setEnabled(False)
        goto_layout.addWidget(self.goto_btn)
        self.layout.addLayout(goto_layout)
        
        self.layout.addSpacing(10)
        
        # Playback Speed (Enhancement)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 1000) # ms delay
        self.speed_slider.setValue(300)
        self.speed_slider.setInvertedAppearance(True) # Left = Fast, Right = Slow? No, usually Left=Slow. 
        # Let's make Left=Slow (1000ms), Right=Fast (50ms)
        self.speed_slider.setInvertedAppearance(True) 
        speed_layout.addWidget(self.speed_slider)
        self.layout.addLayout(speed_layout)
        
        # Navigation Controls
        nav_layout = QHBoxLayout()
        
        self.first_btn = QPushButton("|◀")
        self.first_btn.setEnabled(False)
        nav_layout.addWidget(self.first_btn)
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)
        
        self.last_btn = QPushButton("▶|")
        self.last_btn.setEnabled(False)
        nav_layout.addWidget(self.last_btn)
        
        self.layout.addLayout(nav_layout)
        
        # Play/Pause Button (Modified)
        self.play_btn = QPushButton("Play / Pause")
        self.play_btn.setEnabled(False)
        self.layout.addWidget(self.play_btn)
        
        # Reset Button
        self.reset_btn = QPushButton("Reset Board")
        self.reset_btn.setEnabled(False)
        self.layout.addWidget(self.reset_btn)
        
        self.layout.addStretch()

class ReplayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoLuminamics - Game Replayer")
        self.resize(1400, 900) # Bigger window
        
        # Central Widget & Layout
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #202025;") # Ensure dark background
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20) # Add space above/below/sides
        layout.setSpacing(20)
        
        # Game Board (Stretch factor 3)
        self.board = GameBoard()
        self.board.stop_timer() # Disable game logic timer for replayer
        layout.addWidget(self.board, 3)
        
        # Replay Controls (Stretch factor 1)
        self.controls = ReplayControls()
        self.controls.setFixedWidth(350) # Wider controls
        layout.addWidget(self.controls, 1)
        
        # Game state
        self.game_data = None
        self.current_move_index = 0
        self.laser_calc = LaserCalculator2D(grid_size=19)
        
        # Playback Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_move)
        self.is_playing = False
        
        # Connect signals
        self.controls.load_btn.clicked.connect(self.load_game)
        self.controls.first_btn.clicked.connect(self.jump_to_first)
        self.controls.prev_btn.clicked.connect(self.previous_move)
        self.controls.next_btn.clicked.connect(self.next_move)
        self.controls.last_btn.clicked.connect(self.jump_to_last)
        self.controls.play_btn.clicked.connect(self.toggle_play)
        self.controls.reset_btn.clicked.connect(self.reset_replay)
        self.controls.goto_btn.clicked.connect(self.jump_to_step)
        self.controls.step_input.returnPressed.connect(self.jump_to_step)
        self.controls.goto_btn.clicked.connect(self.jump_to_step)
        self.controls.step_input.returnPressed.connect(self.jump_to_step)
        self.controls.speed_slider.valueChanged.connect(self.update_speed)
        self.controls.theme_combo.currentTextChanged.connect(self.board.set_theme)
        
        # Set default theme
        self.controls.theme_combo.setCurrentText("Real Stone")
        self.board.set_theme("Real Stone")
        
    def keyPressEvent(self, event):
        """Handle key shortcuts."""
        if not self.game_data:
            return
            
        if event.key() == Qt.Key_Right:
            self.next_move()
        elif event.key() == Qt.Key_Left:
            self.previous_move()
        elif event.key() == Qt.Key_Space:
            self.toggle_play()
        elif event.key() == Qt.Key_Home:
            self.jump_to_first()
        elif event.key() == Qt.Key_End:
            self.jump_to_last()
            
    def toggle_play(self):
        """Toggle auto-play."""
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.controls.play_btn.setText("Play")
        else:
            self.update_speed()
            self.timer.start()
            self.is_playing = True
            self.controls.play_btn.setText("Pause")
            
    def update_speed(self):
        """Update playback speed."""
        delay = self.controls.speed_slider.value()
        self.timer.setInterval(delay)
    
    def load_game(self):
        """Load a game file."""
        # Default to 'games' directory in current folder
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
            
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Game File",
            default_dir,
            "Game Files (*.json)"
        )
        
        if filename:
            try:
                self.game_data = GameRecorder.load_game(filename)
                
                # Protocol V2 Support: Normalize to legacy format
                if "turn_sequence" in self.game_data:
                    print("Detected Protocol V2 Log. Normalizing...")
                    self.game_data['moves'] = []
                    for turn in self.game_data['turn_sequence']:
                        action_data = turn.get('agent_action') or {}
                        params = action_data.get('params') or {}
                        
                        # Helper to get from params or action_data
                        def get_val(key, default=None):
                            return params.get(key, action_data.get(key, default))

                        move = {
                            "turn": turn.get('turn_id'),
                            "player": get_val('player', 1),
                            "action": action_data.get('type'),
                            "position": get_val('position'),
                            "stone_type": get_val('stone_type'),
                            "direction": get_val('direction'),
                            "angle": get_val('angle'),
                            "comment": " ".join(turn.get('event_log') or []),
                        }
                        
                        # Extract per-player captures directly from state_t
                        state_t = turn.get('state_t')
                        if state_t and 'player_captures' in state_t:
                            curr_caps = state_t['player_captures']
                            move['p1_captures'] = int(curr_caps.get("1", 0))
                            move['p2_captures'] = int(curr_caps.get("2", 0))
                        else:
                            move['p1_captures'] = 0
                            move['p2_captures'] = 0

                        self.game_data['moves'].append(move)
                    
                    # Normalize Metadata
                    if "metadata" in self.game_data:
                        settings = self.game_data['metadata'].get('game_settings', {})
                        self.game_data['players'] = [
                            settings.get('player1', 'Player 1'),
                            settings.get('player2', 'Player 2')
                        ]
                        
                        # Load theme if available
                        if "theme" in settings:
                            theme = settings["theme"]
                            # Block signal to avoid double update
                            self.controls.theme_combo.blockSignals(True)
                            self.controls.theme_combo.setCurrentText(theme)
                            self.controls.theme_combo.blockSignals(False)
                            self.board.set_theme(theme)
                    
                    self.game_data['total_turns'] = len(self.game_data['moves'])
                    # Ensure game_id exists
                    if 'game_id' not in self.game_data:
                        self.game_data['game_id'] = "V2_Log"
                        
                    # Extract Grid Size from first turn if available
                    if self.game_data.get('turn_sequence'):
                         first_turn = self.game_data['turn_sequence'][0]
                         state_t = first_turn.get('state_t', {})
                         self.game_data['grid_size'] = state_t.get('grid_size', 19)
                    else:
                         self.game_data['grid_size'] = 19

                # Validate game data structure
                if not self.game_data or 'moves' not in self.game_data:
                    raise KeyError("Invalid game file format: missing 'moves' data")
                
                # Load chart data to show full graph immediately
                self.controls.chart.set_data(self.game_data['moves'])
                
                # Update Board Grid Size
                grid_size = self.game_data.get('grid_size', 19)
                try:
                    self.board.set_grid_size(grid_size)
                except ValueError as e:
                    QMessageBox.warning(self, "Warning", f"Invalid grid size in replay: {e}. Using default.")
                
                # Reset to beginning (don't auto-play)
                self.reset_replay()
                self.update_game_info()
                self.enable_controls(True)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load game file:\n{str(e)}")
                self.game_data = None
                self.enable_controls(False)
    
    def check_and_show_victory(self):
        """Check if game is over and show victory screen."""
        if not self.board.board_state:
            return
            
        board = self.board.board_state
        
        # Check if game is over
        if board.game_over or self.current_move_index >= len(self.game_data['moves']):
            # Calculate final scores
            score = board.calculate_score()
            p1_total = score["player1"] + (board.get_captures(1) * 2)
            p2_total = score["player2"] + (board.get_captures(2) * 2)
            
            # Determine winner
            if board.winner:
                winner = board.winner
                reason = board.victory_reason
            else:
                # Determine by score
                if p1_total > p2_total:
                    winner = 1
                    reason = "Score Victory"
                elif p2_total > p1_total:
                    winner = 2
                    reason = "Score Victory"
                else:
                    winner = 0
                    reason = "Draw"
            
            # Show victory screen
            self.board.show_victory_screen(winner, reason, p1_total, p2_total)
    
    
    def update_game_info(self):
        """Update game information display."""
        if not self.game_data:
            return
        
        grid_size = self.game_data.get('grid_size', 19)
        
        info = f"""<b>Game ID:</b> {self.game_data.get('game_id', 'Unknown')}<br>
<b>Players:</b> {self.game_data['players'][0]} vs {self.game_data['players'][1]}<br>
<b>Grid Size:</b> {grid_size}x{grid_size}<br>
<b>Total Moves:</b> {self.game_data['total_turns']}<br>
<b>Current:</b> Move {self.current_move_index} of {len(self.game_data['moves'])}"""
        
        self.controls.info_label.setText(info)
        self.controls.chart.set_current_turn(self.current_move_index) # Update chart indicator
        self.update_score_display()
    
    def update_score_display(self):
        """Calculate and display current score."""
        if not self.board.board_state:
            return
            
        score = self.board.board_state.calculate_score()
        p1_caps = self.board.board_state.get_captures(1)
        p2_caps = self.board.board_state.get_captures(2)
        
        # Total score = Territory + (Captures * 2)
        p1_total = score["player1"] + (p1_caps * 2)
        p2_total = score["player2"] + (p2_caps * 2)
        
        # Highlight leader
        if p1_total > p2_total:
            color = "#4CAF50"
        elif p2_total > p1_total:
            color = "#2196F3"
        else:
            color = "#FFC107"
            
        text = f"<b>Score:</b> P1: {p1_total} | P2: {p2_total}<br>"
        text += f"<small>(Territory: {score['player1']}-{score['player2']}, Captures: {p1_caps}-{p2_caps})</small>"
        
        self.controls.score_label.setText(text)
        self.controls.score_label.setStyleSheet(f"color: {color}; font-size: 14px;")

    def update_move_display(self):
        """Update current move information."""
        if not self.game_data or self.current_move_index >= len(self.game_data['moves']):
            if self.current_move_index > 0:
                 self.controls.move_display.setText("<i>End of Game</i>")
            else:
                 self.controls.move_display.setText("<i>No move to display</i>")
            return
        
        # Clear victory screen if not at the end
        if self.current_move_index < len(self.game_data['moves']):
            self.board.clear_victory_screen()
        
        move = self.game_data['moves'][self.current_move_index]
        player_name = self.game_data['players'][move['player'] - 1]
        
        text = f"""
        <div style='font-size: 14px;'>
        <b>Turn {move['turn']}: {player_name}</b><br>
        <b>Action:</b> <span style='color: #FFC107;'>{move['action'].upper()}</span><br>
        """
        
        if move['action'] == 'place':
            text += f"<b>Position:</b> {tuple(move['position'])}<br>"
            text += f"<b>Stone Type:</b> {move['stone_type']}<br>"
        elif move['action'] == 'laser':
            text += f"<b>Start:</b> {tuple(move['position'])}<br>"
            text += f"<b>Direction:</b> {tuple(move['direction'])}<br>"
        elif move['action'] == 'rotate':
            text += f"<b>Position:</b> {tuple(move['position'])}<br>"
            text += f"<b>New Angle:</b> {move['angle']:.1f}°<br>"
        
        if move.get('comment'):
            text += f"<br><b>Strategy:</b><br><i style='color: #AAAAAA;'>{move['comment']}</i>"
            
        text += "</div>"
        
        self.controls.move_display.setHtml(text)
        self.update_game_info()
    
    def execute_move(self, move):
        """Execute a move on the board."""
        action = move['action']
        player = move['player']
        
        if action == 'place':
            pos = tuple(move['position'])
            stone_type = move['stone_type']
            rotation = move.get('angle', 0) or 0
            self.board.place_stone(pos, stone_type, player, rotation=rotation)
        elif action == 'laser':
            pos = tuple(move['position'])
            direction = tuple(move['direction'])
            self.board.shoot_laser(pos, direction, player) # Pass player for correct scoring
        elif action == 'pass':
            self.board.board_state.pass_turn(player)
            self.board.end_turn()
        elif action == 'surrender':
            self.board.board_state.surrender(player)
        elif action == 'rotate':
            pos = tuple(move['position'])
            angle = move['angle']
            self.board.rotate_stone_to(pos, angle)
            # Also update logical state
            stone = self.board.board_state.get_stone_at(pos)
            if stone:
                stone.rotation_angle = angle
    
    def next_move(self):
        """Execute next move."""
        if not self.game_data or self.current_move_index >= len(self.game_data['moves']):
            if self.is_playing:
                self.toggle_play() # Stop at end
            # Check if game is over and show victory screen
            self.check_and_show_victory()
            return
        
        move = self.game_data['moves'][self.current_move_index]
        self.execute_move(move)
        self.current_move_index += 1
        self.update_move_display()
        
        # Check if this was the last move
        if self.current_move_index >= len(self.game_data['moves']):
            self.check_and_show_victory()
    
    def previous_move(self):
        """Go back one move (requires reset and replay)."""
        if self.is_playing:
            self.toggle_play() # Stop if playing
            
        if self.current_move_index > 0:
            target_index = self.current_move_index - 1
            self.reset_replay()
            for _ in range(target_index):
                self.next_move()
            # Clear victory screen if not at end
            if self.current_move_index < len(self.game_data['moves']):
                self.board.clear_victory_screen()
    
    def jump_to_first(self):
        """Jump to first move."""
        self.reset_replay()
    
    def jump_to_last(self):
        """Jump to last move."""
        self.reset_replay()
        while self.current_move_index < len(self.game_data['moves']):
            self.next_move()
        self.check_and_show_victory()
            
    def jump_to_step(self):
        """Jump to specific step number."""
        try:
            step = int(self.controls.step_input.text())
            if not self.game_data:
                return
                
            total_moves = len(self.game_data['moves'])
            if step < 0: step = 0
            if step > total_moves: step = total_moves
            
            # Optimize direction
            if step < self.current_move_index:
                self.reset_replay()
                target = step
            else:
                target = step
                
            while self.current_move_index < target:
                self.next_move()
                
            self.update_move_display()
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid step number.")
    
    def play_all(self):
        """Play all remaining moves (Deprecated by Play/Pause)."""
        # Kept for compatibility if needed, but UI now uses toggle_play
        self.toggle_play()
    
    def reset_replay(self):
        """Reset the board and replay state."""
        self.board.clear_board()
        self.current_move_index = 0
        if self.game_data:
            self.update_move_display()
    
    def enable_controls(self, enabled):
        """Enable or disable navigation controls."""
        self.controls.first_btn.setEnabled(enabled)
        self.controls.prev_btn.setEnabled(enabled)
        self.controls.next_btn.setEnabled(enabled)
        self.controls.last_btn.setEnabled(enabled)
        self.controls.play_btn.setEnabled(enabled)
        self.controls.reset_btn.setEnabled(enabled)
        self.controls.goto_btn.setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Dark Theme Stylesheet (same as main.py)
    app.setStyleSheet("""
        QMainWindow { background-color: #202025; }
        QWidget { color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
        QLabel { color: #E0E0E0; }
        QPushButton { 
            background-color: #404045; 
            color: #FFFFFF; 
            border: none; 
            border-radius: 4px; 
            padding: 8px; 
        }
        QPushButton:hover { background-color: #505055; }
        QPushButton:pressed { background-color: #606065; }
        QPushButton:disabled { background-color: #303035; color: #808080; }
        QTextEdit {
            background-color: #303035;
            color: #E0E0E0;
            border: 1px solid #505055;
            border-radius: 4px;
            padding: 5px;
        }
        QLineEdit {
            background-color: #303035;
            color: #E0E0E0;
            border: 1px solid #505055;
            border-radius: 4px;
            padding: 5px;
        }
    """)
    
    window = ReplayerWindow()
    window.show()
    sys.exit(app.exec())
