"""
File: ui_controls.py
Creation Date: 2025-11-28
Last Updated: 2025-11-28
Version: 2.0.0
Description: Source file.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QHBoxLayout, QRadioButton, QButtonGroup,
                               QMessageBox, QComboBox, QGroupBox, QGridLayout, QSpinBox, QScrollArea)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, Qt

class UIControls(QWidget):
    """
    Side panel for game controls.
    """
    command_entered = Signal(str)
    laser_shot = Signal(tuple, tuple)
    manual_place = Signal(tuple, int) # New signal for manual placement with rotation
    pass_turn = Signal()
    surrender = Signal()
    restart_game = Signal()
    save_game = Signal()
    grid_size_changed = Signal(int)
    theme_changed = Signal(str)
    victory_threshold_changed = Signal(float)
    timer_settings_changed = Signal(int, int) # total_min, move_sec
    infinite_energy_changed = Signal(bool)
    infinite_score_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(340) # Increased width for visibility
        
        # Main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for controls
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 25, 10) # Increased right margin for scrollbar clearance
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Title
        title = QLabel("Luminamics Go")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Theme Selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Classic", "Neon", "Pastel", "Forest", "Real Stone"])
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # Victory Threshold Selection
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Victory:")
        self.threshold_combo = QComboBox()
        self.threshold_combo.addItem("80% Territory", 0.8)
        self.threshold_combo.addItem("90% Territory", 0.9)
        self.threshold_combo.addItem("100% Territory", 1.0)
        self.threshold_combo.setCurrentIndex(0)  # Default to 80%
        self.threshold_combo.setToolTip("Territory % needed for auto-victory")
        self.threshold_combo.currentIndexChanged.connect(
            lambda: self.victory_threshold_changed.emit(self.threshold_combo.currentData())
        )
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_combo)
        threshold_layout.addWidget(self.threshold_combo)
        layout.addLayout(threshold_layout)

        # Grid Size Selection
        grid_size_layout = QHBoxLayout()
        grid_size_label = QLabel("Board Size:")
        self.grid_size_combo = QComboBox()
        # GRID_SIZES = [9, 13, 19, 23, 27, 31, 35, 39]
        for size in [9, 13, 19, 23, 27, 31, 35, 39]:
            self.grid_size_combo.addItem(f"{size}x{size}", size)
        self.grid_size_combo.setCurrentIndex(2)  # Default to 19x19
        self.grid_size_combo.setToolTip("Board grid size (requires restart)")
        self.grid_size_combo.currentIndexChanged.connect(
            lambda: self.grid_size_changed.emit(self.grid_size_combo.currentData())
        )
        grid_size_layout.addWidget(grid_size_label)
        grid_size_layout.addWidget(self.grid_size_combo)
        layout.addLayout(grid_size_layout)

        # Timer Settings
        timer_group = QGroupBox("Timer Settings")
        timer_layout = QGridLayout()
        
        # Total Time
        timer_layout.addWidget(QLabel("Total Time:"), 0, 0)
        self.total_time_combo = QComboBox()
        self.total_time_combo.addItem("Infinite", 0)
        self.total_time_combo.addItem("15 min", 15)
        self.total_time_combo.addItem("30 min", 30)
        self.total_time_combo.addItem("45 min", 45)
        self.total_time_combo.addItem("60 min", 60)
        self.total_time_combo.currentIndexChanged.connect(self.emit_timer_settings)
        timer_layout.addWidget(self.total_time_combo, 0, 1)
        
        # Move Time
        timer_layout.addWidget(QLabel("Move Time:"), 1, 0)
        self.move_time_spin = QSpinBox()
        self.move_time_spin.setRange(5, 300)
        self.move_time_spin.setValue(30)
        self.move_time_spin.setSuffix(" s")
        self.move_time_spin.valueChanged.connect(self.emit_timer_settings)
        timer_layout.addWidget(self.move_time_spin, 1, 1)
        
        timer_group.setLayout(timer_layout)
        layout.addWidget(timer_group)
        
        # Energy Settings
        from PySide6.QtWidgets import QCheckBox
        self.infinite_energy_check = QCheckBox("Infinite Energy")
        self.infinite_energy_check.setToolTip("When checked, stone placement doesn't consume energy")
        self.infinite_energy_check.stateChanged.connect(
            lambda state: self.infinite_energy_changed.emit(state == 2)  # 2 = Checked
        )
        layout.addWidget(self.infinite_energy_check)
        
        # Victory Settings
        self.infinite_score_check = QCheckBox("Infinite Score (No Mercy)")
        self.infinite_score_check.setToolTip("When checked, no mercy rule - victory by time & final score")
        self.infinite_score_check.stateChanged.connect(
            lambda state: self.infinite_score_changed.emit(state == 2)
        )
        layout.addWidget(self.infinite_score_check)
        
        # Score Board
        score_group = QGroupBox("Score")
        score_layout = QGridLayout()
        
        self.score_label = QLabel("Territory: 0 - 0")
        self.capture_label = QLabel("Captures: 0 - 0")
        self.energy_label_p1 = QLabel("P1 Energy: 20/20")
        self.energy_label_p2 = QLabel("P2 Energy: 20/20")
        
        score_layout.addWidget(self.score_label, 0, 0, 1, 2)
        score_layout.addWidget(self.capture_label, 1, 0, 1, 2)
        score_layout.addWidget(self.energy_label_p1, 2, 0)
        score_layout.addWidget(self.energy_label_p2, 2, 1)
        
        self.timer_label_p1 = QLabel("P1 Time: --:--")
        self.timer_label_p2 = QLabel("P2 Time: --:--")
        self.move_timer_label = QLabel("Move: 30s")
        self.move_timer_label.setAlignment(Qt.AlignCenter)
        self.move_timer_label.setStyleSheet("font-weight: bold; color: #FFD700;")
        
        score_layout.addWidget(self.timer_label_p1, 3, 0)
        score_layout.addWidget(self.timer_label_p2, 3, 1)
        score_layout.addWidget(self.move_timer_label, 4, 0, 1, 2)
        
        score_group.setLayout(score_layout)
        layout.addWidget(score_group)
        
        # Player Color Selection
        color_group = QGroupBox("Your Color")
        color_layout = QVBoxLayout()
        
        self.color_group_buttons = QButtonGroup(self)
        
        self.black_radio = QRadioButton("Play as Black (P1)")
        self.black_radio.setChecked(True) 
        self.color_group_buttons.addButton(self.black_radio)
        color_layout.addWidget(self.black_radio)
        
        self.white_radio = QRadioButton("Play as White (P2)")
        self.color_group_buttons.addButton(self.white_radio)
        color_layout.addWidget(self.white_radio)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Stone Selection
        stone_group = QGroupBox("Stone Type")
        stone_layout = QVBoxLayout()
        
        self.stone_type_group = QButtonGroup(self)
        
        self.prism_radio = QRadioButton("Prism (Black)")
        self.prism_radio.setChecked(True)
        self.stone_type_group.addButton(self.prism_radio)
        stone_layout.addWidget(self.prism_radio)
        
        self.mirror_radio = QRadioButton("Mirror (Silver)")
        self.stone_type_group.addButton(self.mirror_radio)
        stone_layout.addWidget(self.mirror_radio)
        
        self.splitter_radio = QRadioButton("Splitter (Gold)")
        self.stone_type_group.addButton(self.splitter_radio)
        stone_layout.addWidget(self.splitter_radio)
        
        stone_group.setLayout(stone_layout)
        layout.addWidget(stone_group)
        
        # Actions
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        self.pass_btn = QPushButton("Pass Turn")
        self.pass_btn.clicked.connect(self.pass_turn.emit)
        action_layout.addWidget(self.pass_btn)
        
        self.surrender_btn = QPushButton("Surrender")
        self.surrender_btn.clicked.connect(self.surrender.emit)
        action_layout.addWidget(self.surrender_btn)
        
        self.restart_btn = QPushButton("Restart Game")
        self.restart_btn.clicked.connect(self.restart_game.emit)
        action_layout.addWidget(self.restart_btn)
        
        self.save_btn = QPushButton("Save Game")
        self.save_btn.clicked.connect(self.save_game.emit)
        action_layout.addWidget(self.save_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Manual Placement
        placement_group = QGroupBox("Manual Placement")
        placement_layout = QGridLayout()
        
        placement_layout.addWidget(QLabel("X:"), 0, 0)
        self.place_x = QLineEdit()
        self.place_x.setPlaceholderText("0-18")
        self.place_x.setFixedWidth(40) # Compact input
        placement_layout.addWidget(self.place_x, 0, 1)
        
        placement_layout.addWidget(QLabel("Y:"), 0, 2)
        self.place_y = QLineEdit()
        self.place_y.setPlaceholderText("0-18")
        self.place_y.setFixedWidth(40) # Compact input
        placement_layout.addWidget(self.place_y, 0, 3)

        placement_layout.addWidget(QLabel("Rot:"), 0, 4)
        self.place_rotation = QLineEdit()
        self.place_rotation.setPlaceholderText("0-360")
        self.place_rotation.setFixedWidth(45) # Compact input
        placement_layout.addWidget(self.place_rotation, 0, 5)
        
        self.manual_place_btn = QPushButton("Place Stone")
        self.manual_place_btn.clicked.connect(self.on_manual_place)
        placement_layout.addWidget(self.manual_place_btn, 1, 0, 1, 6)
        
        placement_group.setLayout(placement_layout)
        layout.addWidget(placement_group)

        # Laser Control
        debug_group = QGroupBox("Laser Control")
        debug_layout = QGridLayout()
        
        debug_layout.addWidget(QLabel("Start (x,y):"), 0, 0)
        self.laser_start_input = QLineEdit()
        self.laser_start_input.setPlaceholderText("-1, 9")
        self.laser_start_input.setToolTip("Enter coordinates. (-1, y) for left edge, etc.")
        debug_layout.addWidget(self.laser_start_input, 0, 1)
        
        debug_layout.addWidget(QLabel("Dir (dx,dy):"), 1, 0)
        self.laser_dir_input = QLineEdit()
        self.laser_dir_input.setPlaceholderText("1, 0")
        debug_layout.addWidget(self.laser_dir_input, 1, 1)
        
        self.shoot_btn = QPushButton("Shoot Laser")
        self.shoot_btn.clicked.connect(self.on_shoot_laser)
        debug_layout.addWidget(self.shoot_btn, 2, 0, 1, 2)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()

    def update_energy(self, p1, p2):
        self.energy_label_p1.setText(f"P1 Energy: {p1}/20")
        self.energy_label_p2.setText(f"P2 Energy: {p2}/20")

    def update_score(self, p1, p2):
        self.score_label.setText(f"Territory: {p1} - {p2}")

    def update_captures(self, p1, p2):
        self.capture_label.setText(f"Captures: {p1} - {p2}")

    def on_shoot_laser(self):
        try:
            start = tuple(map(int, self.laser_start_input.text().split(',')))
            direction = tuple(map(int, self.laser_dir_input.text().split(',')))
            self.laser_shot.emit(start, direction)
        except ValueError:
            pass

    def on_manual_place(self):
        try:
            x = int(self.place_x.text())
            y = int(self.place_y.text())
            rotation = int(self.place_rotation.text()) if self.place_rotation.text() else 0
            self.manual_place.emit((x, y), rotation)
        except ValueError:
            pass
            
    def show_game_over(self, winner, reason, p1_score, p2_score):
        msg = QMessageBox(self)
        msg.setWindowTitle("Game Over")
        msg.setText(f"Player {winner} Wins!\nReason: {reason}\n\nFinal Score:\nP1: {p1_score}\nP2: {p2_score}")
        msg.exec()

    def get_selected_stone_type(self):
        """Get the currently selected stone type name."""
        if self.prism_radio.isChecked(): return "PRISM"
        if self.mirror_radio.isChecked(): return "MIRROR"
        if self.splitter_radio.isChecked(): return "SPLITTER"
        return "PRISM"
    
    def get_player_color(self):
        """Returns 1 for Black, 2 for White"""
        if self.black_radio.isChecked():
            return 1
        else:
            return 2
    
    def get_victory_threshold(self):
        """Returns the selected victory threshold as a float (0.8, 0.9, or 1.0)"""
        return self.threshold_combo.currentData()

    def get_grid_size(self):
        """Returns the selected grid size (9, 13, 19, 23, 27, 31, 35, or 39)"""
        return self.grid_size_combo.currentData()

    def emit_timer_settings(self):
        """Emit timer settings changed signal."""
        total_time = self.total_time_combo.currentData()
        move_time = self.move_time_spin.value()
        self.timer_settings_changed.emit(total_time, move_time)

    def update_timers(self, p1_time, p2_time, move_time, total_limit):
        """Update timer displays."""
        def format_time(seconds):
            if total_limit == 0: return "∞"
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m:02d}:{s:02d}"
            
        self.timer_label_p1.setText(f"P1 Time: {format_time(p1_time)}")
        self.timer_label_p2.setText(f"P2 Time: {format_time(p2_time)}")
        
        self.move_timer_label.setText(f"Move: {int(move_time)}s")
        if move_time <= 5:
            self.move_timer_label.setStyleSheet("font-weight: bold; color: #FF4444;")
        else:
            self.move_timer_label.setStyleSheet("font-weight: bold; color: #FFD700;")

