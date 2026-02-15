"""
File: game_board.py
Creation Date: 2025-11-28
Last Updated: 2025-11-28
Version: 2.0.0
Description: Source file.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor, QPen, QRadialGradient, QPixmap, QPainter, QFont
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject, QTimer
from _01_core_logic.board_state import BoardState2D, StoneType
from _02_engines.laser import LaserCalculator2D
import os
import math
import json
from pathlib import Path

class GameBoard(QGraphicsView):
    """
    The main game board widget.
    Handles drawing the grid, stones, and lasers.
    """
    stone_placed = Signal(tuple, str)  # (x, y), stone_type
    stone_placed = Signal(tuple, str)  # (x, y), stone_type
    stone_rotated = Signal(tuple, float) # (x, y), angle
    laser_input = Signal(tuple, tuple, int) # pos, direction, player
    timer_updated = Signal(float, float, float, int) # p1_time, p2_time, move_time, total_limit
    game_over_signal = Signal() # New signal for time expiration
    
    # Color Themes
    THEMES = {
        "Classic": {
            "P1": (255, 50, 50),    # Red
            "P2": (50, 50, 255),    # Blue
            "Blocker": (40, 40, 40), # Dark Grey
            "Grid": (80, 80, 80),
            "Background": "#202025"
        },
        "Neon": {
            "P1": (255, 0, 255),    # Magenta
            "P2": (0, 255, 255),    # Cyan
            "Blocker": (10, 10, 20), # Deep Void
            "Grid": (40, 40, 60),
            "Background": "#050510"
        },
        "Pastel": {
            "P1": (255, 180, 180),  # Soft Red
            "P2": (180, 180, 255),  # Soft Blue
            "Blocker": (100, 100, 110), # Slate
            "Grid": (150, 150, 150),
            "Background": "#F0F0F5"
        },
        "Forest": {
            "P1": (255, 140, 0),    # Orange
            "P2": (50, 200, 50),    # Green
            "Blocker": (60, 45, 30), # Dark Wood
            "Grid": (60, 80, 60),
            "Background": "#152015"
        },
        "Real Stone": {
            "P1": "texture_ruby.png",
            "P2": "texture_sapphire.png",
            "Blocker": "texture_obsidian.png",
            "Grid": (60, 60, 60),
            "Background": "#1A1A1D"
        }
    }

    def __init__(self, board_state=None, territory_threshold=0.8, parent=None):
        super().__init__(parent)
        
        # Load UI configuration
        self._load_ui_config()
        
        # Store the territory threshold
        self.territory_threshold = territory_threshold
        
        if board_state is None:
            self.board_state = BoardState2D(self.grid_size, territory_threshold=territory_threshold)
        else:
            self.board_state = board_state

        self.laser_calc = LaserCalculator2D(self.grid_size)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.stone_items = {} # Stores QGraphicsItem for each stone at (x,y)
        self.laser_items = [] # Stores QGraphicsLineItem for laser paths
        self.aiming_arrow = None # Visual for current aiming direction
        self.victory_items = [] # Stores victory screen items for cleanup
        
        self.current_theme = "Classic" # Default theme
        
        # Interaction State
        self.drag_start_pos = None
        self.is_aiming = False
        self.aiming_source = None
        self.aiming_type = None
        
        # Rotation State
        self.is_rotating = False
        self.rotating_stone_pos = None

        # Selection State
        self.selected_stone_pos = None
        self.selection_item = None
        
        # Current stone type to place
        self.current_stone_type = "PRISM"
        self.current_player = 1
        
        self.texture_cache = {} # Cache for scaled textures
        
        self.texture_cache = {} # Cache for scaled textures
        
        # Timer
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.on_timer_tick)
        self.game_timer.start(100) # 100ms
        
        self._init_board()
        self._setup_view()
    
    def _load_ui_config(self):
        """Load UI configuration from JSON file with fallback to defaults."""
        try:
            config_path = Path(__file__).parent.parent / "_07_config" / "ui_config.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Load board settings
            board_config = config.get("board", {})
            self.grid_size = board_config.get("grid_size", 19)
            self.cell_size = board_config.get("cell_size", 35)
            self.margin_horizontal = board_config.get("margin_horizontal", 40)
            self.margin_vertical = board_config.get("margin_vertical", 30)
            
            # Load 3D effects configuration for Real Stones theme
            self.stone_3d_config = config.get("stones", {}).get("real_stone_3d_effects", {})
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # Fallback to default values if config fails
            print(f"Warning: Could not load ui_config.json ({e}), using defaults")
            self.grid_size = 19
            self.cell_size = 35
            self.margin_horizontal = 40
            self.margin_vertical = 30
            self.stone_3d_config = {}

    def set_theme(self, theme_name):
        """Set the visual theme."""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            # Update background
            theme = self.THEMES[theme_name]
            bg_color = theme["Background"]
            # We need to update the background brush. 
            # Since we use a texture or color, let's just set the background color for now 
            # or update the brush if we want to be fancy.
            # For simplicity, let's update the background rect color if it's a solid color theme,
            # or just trigger a redraw of stones.
            
            # Update stones
            for pos, item in self.stone_items.items():
                # We need to redraw the stone with new colors.
                # Since _draw_stone creates a new item, we can just remove and re-add?
                # Or better, update the brush of the existing item?
                # The item is a group or ellipse.
                # Let's just clear and redraw everything for simplicity or call _draw_stone again?
                # _draw_stone adds to scene.
                
                # Let's just update the board.
                pass
            
            # Force update of the view
            self.scene.update()
            
            # Actually, to properly update, we should probably clear and redraw stones.
            # But _draw_stone takes pos, type, player. We have that in board_state.
            
            # Re-draw all stones
            for pos in self.stone_items:
                self.scene.removeItem(self.stone_items[pos])
            self.stone_items.clear()
            
            for pos, stone in self.board_state.stones.items():
                self._draw_stone(pos, stone.type_name, stone.player)
                # Restore rotation
                self.rotate_stone_to(pos, stone.rotation_angle)



    def _init_board(self):
        """Initialize the board with wood texture and grid."""
        # Calculate sizes using separate horizontal/vertical margins
        board_pixel_size = (self.grid_size - 1) * self.cell_size
        total_scene_width = board_pixel_size + 2 * self.margin_horizontal
        total_scene_height = board_pixel_size + 2 * self.margin_vertical

        
        # Wood texture background - fills entire scene
        texture_path = Path(__file__).parent.parent / "assets" / "wood_texture.png"
        if texture_path.exists():
            pixmap = QPixmap(str(texture_path))
            # Scale texture to cover entire scene, maintaining aspect ratio
            max_dimension = max(total_scene_width, total_scene_height)
            scaled_pixmap = pixmap.scaled(
                max_dimension * 2,  # Scale larger to ensure coverage
                max_dimension * 2,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            
            # Create brush and set transform to center the growth rings at board center
            brush = QBrush(scaled_pixmap)
            
            # Calculate offset to center texture's center at scene center
            pixmap_center = scaled_pixmap.width() / 2
            scene_center_x = total_scene_width / 2
            scene_center_y = total_scene_height / 2
            offset_x = pixmap_center - scene_center_x
            offset_y = pixmap_center - scene_center_y
            
            # Set brush transform to offset the texture
            from PySide6.QtGui import QTransform
            transform = QTransform()
            transform.translate(-offset_x, -offset_y)
            brush.setTransform(transform)
        else:
            brush = QBrush(QColor("#D2691E"))
        
        # Background rectangle - covers entire scene
        bg_rect = self.scene.addRect(
            0, 0,
            total_scene_width, total_scene_height,
            Qt.NoPen, brush
        )
        bg_rect.setZValue(-2)
        
        # Grid lines - bolder and darker
        pen = QPen(QColor("#2C1810"), 2)
        
        # Vertical lines (19 lines from index 0 to 18)
        for i in range(self.grid_size):
            x = self.margin_horizontal + i * self.cell_size
            line = self.scene.addLine(
                x, self.margin_vertical,
                x, self.margin_vertical + board_pixel_size,
                pen
            )
            line.setZValue(-1)
        
        # Horizontal lines (19 lines from index 0 to 18)
        for i in range(self.grid_size):
            y = self.margin_vertical + i * self.cell_size
            line = self.scene.addLine(
                self.margin_horizontal, y,
                self.margin_horizontal + board_pixel_size, y,
                pen
            )
            line.setZValue(-1)
        
        # Star points
        star_pen = QPen(Qt.NoPen)
        star_brush = QBrush(QColor("#1A0D08"))
        
        star_positions = []
        center = (self.grid_size - 1) // 2
        
        if self.grid_size >= 13:
            # Standard 4-4 points for 13+ sizes
            corner_offset = 3
            points = [corner_offset, center, self.grid_size - 1 - corner_offset]
            
            for x in points:
                for y in points:
                    star_positions.append((x, y))
                    
        elif self.grid_size == 9:
            # 3-3 points for 9x9
            points = [2, 4, 6]
            for x in points:
                for y in points:
                    star_positions.append((x, y))
        
        for sx, sy in star_positions:
            x = self.margin_horizontal + sx * self.cell_size
            y = self.margin_vertical + sy * self.cell_size
            star = self.scene.addEllipse(
                x - 4, y - 4, 8, 8,
                star_pen, star_brush
            )
            star.setZValue(-1)
    
    def _setup_view(self):
        """Setup view properties."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        board_pixel_size = (self.grid_size - 1) * self.cell_size
        total_width = board_pixel_size + 2 * self.margin_horizontal
        total_height = board_pixel_size + 2 * self.margin_vertical
        
        self.setSceneRect(0, 0, total_width, total_height)
        # Removed fixed size to allow resizing
        
        # Initial fit
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        """Handle resize to keep board fitted."""
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
    
    def mousePressEvent(self, event):
        """Handle mouse interaction for placement, laser aiming, and rotation."""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.drag_start_scene = self.mapToScene(event.pos())
            self.is_aiming = False
            
            # Check if clicked on a stone or border
            grid_pos = self._get_grid_pos(self.drag_start_scene)
            
            if grid_pos:
                if grid_pos in self.board_state.stones:
                    self.aiming_source = grid_pos
                    self.aiming_type = "internal"
                else:
                    self.aiming_source = None
                    self.aiming_type = "placement"
            else:
                self.aiming_source = self._get_border_pos(self.drag_start_scene)
                self.aiming_type = "external" if self.aiming_source else None

        elif event.button() == Qt.RightButton:
            # Right click -> Start Rotation Drag
            scene_pos = self.mapToScene(event.pos())
            grid_pos = self._get_grid_pos(scene_pos)
            if grid_pos and grid_pos in self.board_state.stones:
                self.rotating_stone_pos = grid_pos
                self.is_rotating = True
                self.setCursor(Qt.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle aiming and rotation visuals."""
        if event.buttons() & Qt.LeftButton:
            if (event.pos() - self.drag_start_pos).manhattanLength() > 10:
                self.is_aiming = True
                self._update_aiming_visual(self.mapToScene(event.pos()))
        
        elif event.buttons() & Qt.RightButton and self.is_rotating:
            # Calculate angle from stone center to mouse
            stone_pos = self.rotating_stone_pos
            center_x = self.margin_horizontal + stone_pos[0] * self.cell_size
            center_y = self.margin_vertical + stone_pos[1] * self.cell_size
            
            mouse_pos = self.mapToScene(event.pos())
            dx = mouse_pos.x() - center_x
            dy = mouse_pos.y() - center_y
            
            angle = math.degrees(math.atan2(dy, dx))
            self.rotate_stone_to(self.rotating_stone_pos, angle)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Execute action on release."""
        if event.button() == Qt.LeftButton:
            self._clear_aiming_visual()
            
            if self.is_aiming and self.aiming_source:
                end_scene = self.mapToScene(event.pos())
                direction = self._calculate_direction(self.drag_start_scene, end_scene)
                if direction != (0, 0):
                    self.laser_input.emit(self.aiming_source, direction, self.current_player)
            
            elif not self.is_aiming and self.aiming_type == "placement":
                grid_pos = self._get_grid_pos(self.drag_start_scene)
                if grid_pos:
                    self.place_stone(grid_pos, self.current_stone_type, self.current_player)
            
            self.is_aiming = False
            self.aiming_source = None
            
        elif event.button() == Qt.RightButton:
            if self.is_rotating and self.rotating_stone_pos:
                # Emit final rotation
                stone = self.board_state.stones.get(self.rotating_stone_pos)
                if stone:
                    self.stone_rotated.emit(self.rotating_stone_pos, stone.rotation_angle)
            
            self.is_rotating = False
            self.rotating_stone_pos = None
            self.setCursor(Qt.ArrowCursor)
            
        super().mouseReleaseEvent(event)

    def _get_grid_pos(self, scene_pos):
        """Convert scene pos to grid coordinates."""
        gx = round((scene_pos.x() - self.margin_horizontal) / self.cell_size)
        gy = round((scene_pos.y() - self.margin_vertical) / self.cell_size)
        
        if 0 <= gx < self.grid_size and 0 <= gy < self.grid_size:
            return (gx, gy)
        return None

    def _get_border_pos(self, scene_pos):
        """Get closest border position for external laser.
        
        Enhanced with separate margins to allow easier top/bottom laser shooting.
        """
        # Logic to find closest edge point aligned with grid
        gx = round((scene_pos.x() - self.margin_horizontal) / self.cell_size)
        gy = round((scene_pos.y() - self.margin_vertical) / self.cell_size)
        
        # Check if aligned with a row/col but outside grid
        is_aligned_x = 0 <= gx < self.grid_size
        is_aligned_y = 0 <= gy < self.grid_size
        
        if is_aligned_x and not is_aligned_y:
            # Top or Bottom (now easier to click with larger vertical margins)
            if gy < 0: return (gx, -1)
            if gy >= self.grid_size: return (gx, self.grid_size)
            
        if is_aligned_y and not is_aligned_x:
            # Left or Right
            if gx < 0: return (-1, gy)
            if gx >= self.grid_size: return (self.grid_size, gy)
            
        return None

    def _calculate_direction(self, start, end):
        """Determine analog direction from drag."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0: return (0, 0)
        
        return (dx/length, dy/length)

    def _update_aiming_visual(self, end_pos):
        """Draw an arrow indicating laser direction."""
        if not self.aiming_arrow:
            self.aiming_arrow = self.scene.addLine(0,0,0,0, QPen(QColor("#FF0000"), 2, Qt.DashLine))
            self.aiming_arrow.setZValue(10)
            
        start_point = self.drag_start_scene
        
        # Analog direction
        direction = self._calculate_direction(start_point, end_pos)
        length = 50 # Fixed length visual
        
        end_point = QPointF(
            start_point.x() + direction[0] * length,
            start_point.y() + direction[1] * length
        )
        
        self.aiming_arrow.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        self.aiming_arrow.setVisible(True)

    def _clear_aiming_visual(self):
        """Clear the aiming arrow visual."""
        if self.aiming_arrow:
            self.aiming_arrow.setVisible(False)

    def place_stone(self, pos, stone_type_name="PRISM", player=1, rotation=0):
        """Place a stone at grid position."""
        if self.board_state.place_stone(pos, stone_type_name, player):
            self.board_state.stones[pos].set_rotation(rotation) # Set initial rotation
            self._draw_stone(pos, stone_type_name, player)
            self.rotate_stone_to(pos, rotation) # Apply visual rotation
            self.stone_placed.emit(pos, stone_type_name)
            self.end_turn()
            return True
        return False

    def _draw_stone(self, pos, stone_type_name, player):
        """Draw stone visual with 3D depth and optional texture."""
        x, y = pos
        center_x = self.margin_horizontal + x * self.cell_size
        center_y = self.margin_vertical + y * self.cell_size
        radius = self.cell_size / 2 - 2
        
        # Check if using textures (Real Stone theme)
        use_texture = False
        brush = None
        
        if self.current_theme in self.THEMES:
            theme = self.THEMES[self.current_theme]
            
            # Special handling for Real Stone theme to use different textures per type
            if self.current_theme == "Real Stone":
                use_texture = True
                texture_filename = None
                
                if stone_type_name == "MIRROR":
                    texture_filename = "texture_slate.png"
                elif stone_type_name == "SPLITTER":
                    texture_filename = "texture_gold.png"
                elif stone_type_name == "BLOCKER":
                    texture_filename = theme.get("Blocker", "texture_obsidian.png")
                else: # PRISM or others
                    # Use player specific gem
                    texture_filename = theme["P1"] if player == 1 else theme["P2"]
                
                # Fix: Assets are in root/assets
                texture_path = os.path.join(os.path.dirname(__file__), "..", "assets", texture_filename)
                
                if os.path.exists(texture_path):
                    # Texture Caching
                    cache_key = (texture_filename, int(radius * 2))
                    if cache_key in self.texture_cache:
                        scaled_pixmap = self.texture_cache[cache_key]
                    else:
                        pixmap = QPixmap(texture_path)
                        scaled_pixmap = pixmap.scaled(
                            int(radius * 2), int(radius * 2),
                            Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation
                        )
                        self.texture_cache[cache_key] = scaled_pixmap
                        
                    brush = QBrush(scaled_pixmap)
                else:
                    use_texture = False
            
            else:
                # Standard color/texture handling for other themes
                player_color = theme["P1"] if player == 1 else theme["P2"]
                
                # Check if color is actually a texture filename
                if isinstance(player_color, str) and player_color.endswith(".png"):
                    use_texture = True
                    # Fix: Assets are in root/assets
                    texture_path = os.path.join(os.path.dirname(__file__), "..", "assets", player_color)
                    
                    if os.path.exists(texture_path):
                        # Texture Caching
                        cache_key = (player_color, int(radius * 2))
                        if cache_key in self.texture_cache:
                            scaled_pixmap = self.texture_cache[cache_key]
                        else:
                            pixmap = QPixmap(texture_path)
                            scaled_pixmap = pixmap.scaled(
                                int(radius * 2), int(radius * 2),
                                Qt.KeepAspectRatioByExpanding,
                                Qt.SmoothTransformation
                            )
                            self.texture_cache[cache_key] = scaled_pixmap
                        brush = QBrush(scaled_pixmap)
                    else:
                        use_texture = False
        
        if not use_texture:
            # Create 3D depth gradient
            gradient = QRadialGradient(
                center_x - radius/3,
                center_y - radius/3, 
                radius * 1.8
            )
            
            if self.current_theme in self.THEMES:
                theme = self.THEMES[self.current_theme]
                
                if stone_type_name == "BLOCKER":
                    # BLOCKER always uses theme-specific Blocker color
                    blocker_color = theme.get("Blocker", (40, 40, 50))
                    if isinstance(blocker_color, tuple):
                        bc = QColor(*blocker_color)
                    else:
                        bc = QColor(40, 40, 50)  # Fallback if Blocker is a texture filename
                    gradient.setColorAt(0, bc.lighter(150))
                    gradient.setColorAt(0.3, bc.lighter(110))
                    gradient.setColorAt(0.7, bc.darker(130))
                    gradient.setColorAt(1, bc.darker(180))
                else:
                    # For PRISM/MIRROR/SPLITTER, use player color
                    base_color = theme["P1"] if player == 1 else theme["P2"]
                    if isinstance(base_color, tuple):
                        c = QColor(*base_color)
                    elif isinstance(base_color, str) and not base_color.endswith(".png"):
                        c = QColor(base_color)
                    else:
                        # Real Stone fallback - texture missing, use neutral color
                        c = QColor(180, 180, 180) if player == 2 else QColor(80, 80, 80)
                    
                    if stone_type_name == "PRISM":
                        gradient.setColorAt(0, c.lighter(180))
                        gradient.setColorAt(0.4, c.lighter(120))
                        gradient.setColorAt(0.8, c)
                        gradient.setColorAt(1, c.darker(140))
                    elif stone_type_name == "MIRROR":
                        gradient.setColorAt(0, QColor("#FFFFFF"))
                        gradient.setColorAt(0.3, QColor("#F0F0F0"))
                        gradient.setColorAt(0.7, QColor("#C0C0C0"))
                        gradient.setColorAt(1, QColor("#808080"))
                    elif stone_type_name == "SPLITTER":
                        gradient.setColorAt(0, QColor("#FFEB3B"))
                        gradient.setColorAt(0.4, QColor("#FFC107"))
                        gradient.setColorAt(0.8, QColor("#FF8F00"))
                        gradient.setColorAt(1, QColor("#E65100"))
                    else:
                        gradient.setColorAt(0, c.lighter(150))
                        gradient.setColorAt(1, c)
            else:
                gradient.setColorAt(0, QColor("#FFFFFF"))
                gradient.setColorAt(1, QColor("#E0E0E0"))
            
            brush = QBrush(gradient)
        
        # Main stone with proper black/white outlines
        # Player 1 = Black stones with black outline
        # Player 2 = White stones with white outline
        if player == 1:
            outline_color = QColor("#000000")  # Black outline for black stones
        else:
            outline_color = QColor("#FFFFFF")  # White outline for white stones
        outline_pen = QPen(outline_color, 3)
        
        # Create main stone item first to act as parent
        stone_group = self.scene.addEllipse(
            -radius, -radius, radius * 2, radius * 2,
            outline_pen,
            brush
        )
        stone_group.setPos(center_x, center_y)
        stone_group.setZValue(1)

        # Enhanced 3D effects for Real Stones theme (applies to ALL stone types)
        if self.current_theme == "Real Stone":
            effects_config = self.stone_3d_config
            
            # Shadow for 3D depth - Enhanced for Real Stones
            if effects_config.get("shadow", {}).get("enabled", True):
                shadow_config = effects_config.get("shadow", {})
                shadow_offset_x = shadow_config.get("offset_x", 3)
                shadow_offset_y = shadow_config.get("offset_y", 3)
                shadow_opacity = int(shadow_config.get("opacity", 0.4) * 255)
                
                shadow = QGraphicsEllipseItem(
                    -radius + shadow_offset_x, 
                    -radius + shadow_offset_y,
                    radius * 2, radius * 2,
                    stone_group  # Parent
                )
                shadow.setPen(Qt.NoPen)
                shadow.setBrush(QBrush(QColor(0, 0, 0, shadow_opacity)))
                shadow.setZValue(-0.5) # Behind the stone body
            
            # Specular highlight for 3D gloss
            if effects_config.get("specular", {}).get("enabled", True):
                spec_config = effects_config.get("specular", {})
                spec_offset_ratio = spec_config.get("position_offset_ratio", 0.25)
                spec_size_ratio = spec_config.get("size_ratio", 0.3)
                spec_opacity = int(spec_config.get("opacity", 0.6) * 255)
                spec_color = QColor(spec_config.get("color", "#FFFFFF"))
                spec_color.setAlpha(spec_opacity)
                
                spec_radius = radius * spec_size_ratio
                spec_gradient = QRadialGradient(
                    -radius * spec_offset_ratio,
                    -radius * spec_offset_ratio,
                    spec_radius * 2
                )
                spec_gradient.setColorAt(0, spec_color)
                spec_gradient.setColorAt(0.5, QColor(255, 255, 255, spec_opacity // 2))
                spec_gradient.setColorAt(1, QColor(255, 255, 255, 0))
                
                specular = QGraphicsEllipseItem(
                    -radius * spec_offset_ratio - spec_radius,
                    -radius * spec_offset_ratio - spec_radius,
                    spec_radius * 2,
                    spec_radius * 2,
                    stone_group
                )
                specular.setPen(Qt.NoPen)
                specular.setBrush(QBrush(spec_gradient))
                specular.setZValue(0.2)  # Above stone
            
            # Inner bevel effect for carved look
            if effects_config.get("bevel", {}).get("enabled", True):
                bevel_config = effects_config.get("bevel", {})
                highlight_strength = int(bevel_config.get("inner_highlight_strength", 0.3) * 255)
                shadow_strength = int(bevel_config.get("inner_shadow_strength", 0.2) * 255)
                
                # Inner highlight (top-left)
                inner_highlight = QGraphicsEllipseItem(
                    -radius, -radius,
                    radius * 2, radius * 2,
                    stone_group
                )
                highlight_grad = QRadialGradient(
                    -radius/2, -radius/2, radius * 1.5
                )
                highlight_grad.setColorAt(0, QColor(255, 255, 255, highlight_strength))
                highlight_grad.setColorAt(0.6, QColor(255, 255, 255, 0))
                inner_highlight.setPen(Qt.NoPen)
                inner_highlight.setBrush(QBrush(highlight_grad))
                inner_highlight.setZValue(0.1)
                
                # Inner shadow (bottom-right)
                inner_shadow = QGraphicsEllipseItem(
                    -radius, -radius,
                    radius * 2, radius * 2,
                    stone_group
                )
                shadow_grad = QRadialGradient(
                    radius/2, radius/2, radius * 1.5
                )
                shadow_grad.setColorAt(0, QColor(0, 0, 0, shadow_strength))
                shadow_grad.setColorAt(0.6, QColor(0, 0, 0, 0))
                inner_shadow.setPen(Qt.NoPen)
                inner_shadow.setBrush(QBrush(shadow_grad))
                inner_shadow.setZValue(0.1)
        
        else:
            # Standard shadow for non-Real Stone themes
            shadow_offset = 2
            shadow = QGraphicsEllipseItem(
                -radius + shadow_offset, 
                -radius + shadow_offset,
                radius * 2, radius * 2,
                stone_group  # Parent
            )
            shadow.setPen(Qt.NoPen)
            shadow.setBrush(QBrush(QColor(0, 0, 0, 60)))
            shadow.setZValue(-0.5) # Behind the stone body
        
        # Orientation indicator
        # Visual cue of plus sign and rotation line
        # Player 2 (White Stone) -> Black Indicator
        # Player 1 (Black Stone) -> White Indicator
        indicator_pen = QPen(QColor("#000000") if player == 2 else QColor("#FFFFFF"), 2)
        
        if stone_type_name in ["MIRROR", "SPLITTER", "PRISM"]:
             # Line indicating "forward" (up relative to stone rotation)
             # Disconnected from the plus sign and smaller
             line = QGraphicsLineItem(0, -12, 0, -radius + 4, stone_group)
             line.setPen(indicator_pen)
             line.setZValue(2)
             
             # Plus sign at center
             plus_size = 4
             h_line = QGraphicsLineItem(-plus_size, 0, plus_size, 0, stone_group)
             v_line = QGraphicsLineItem(0, -plus_size, 0, plus_size, stone_group)
             h_line.setPen(indicator_pen)
             v_line.setPen(indicator_pen)
             h_line.setZValue(2)
             v_line.setZValue(2)
        
        elif stone_type_name == "BLOCKER":
             # X cross to indicate absorption / blocking
             cross_size = 5
             x_line1 = QGraphicsLineItem(-cross_size, -cross_size, cross_size, cross_size, stone_group)
             x_line2 = QGraphicsLineItem(-cross_size, cross_size, cross_size, -cross_size, stone_group)
             blocker_pen = QPen(QColor("#FF4444") if player == 1 else QColor("#4444FF"), 2)
             x_line1.setPen(blocker_pen)
             x_line2.setPen(blocker_pen)
             x_line1.setZValue(2)
             x_line2.setZValue(2)
        
        self.stone_items[pos] = stone_group

    def rotate_stone_to(self, pos, angle):
        """Rotate stone to specific angle (degrees)."""
        if pos in self.stone_items:
            stone = self.board_state.stones[pos]
            stone.set_rotation(angle)
            
            item = self.stone_items[pos]
            item.setRotation(angle)

    def move_stone_visual(self, from_pos, to_pos):
        """Move a stone visual from one grid position to another.
        
        Args:
            from_pos: (x, y) source position
            to_pos: (x, y) destination position (already wrapped)
        """
        if from_pos in self.stone_items:
            # Remove old visual
            self.scene.removeItem(self.stone_items[from_pos])
            del self.stone_items[from_pos]
        
        # Redraw at new position
        stone = self.board_state.get_stone_at(to_pos)
        if stone:
            self._draw_stone(to_pos, stone.stone_type.name, stone.player)
            self.rotate_stone_to(to_pos, stone.rotation_angle)

    def shoot_laser(self, start_pos, direction, player=1):
        """Shoot a laser and visualize the path."""
        # Clear old lasers
        for item in self.laser_items:
            self.scene.removeItem(item)
        self.laser_items.clear()
        
        # Calculate path
        paths = self.laser_calc.calculate_path(
            (start_pos[0] + 0.5, start_pos[1] + 0.5),
            direction,
            self.board_state.stones
        )
        
        # Draw new lasers
        laser_color = QColor("#FF0000") if player == 1 else QColor("#0000FF")
        pen = QPen(laser_color, 4)
        pen.setCapStyle(Qt.RoundCap)
        
        for segment in paths:
            start_x = self.margin_horizontal + (segment[0][0] - 0.5) * self.cell_size
            start_y = self.margin_vertical + (segment[0][1] - 0.5) * self.cell_size
            end_x = self.margin_horizontal + (segment[1][0] - 0.5) * self.cell_size
            end_y = self.margin_vertical + (segment[1][1] - 0.5) * self.cell_size
            
            line = self.scene.addLine(start_x, start_y, end_x, end_y, pen)
            line.setZValue(5) # Top layer
            self.laser_items.append(line)
            
        # Return captured stones for game logic processing
        return self.board_state.process_laser_captures(player, paths)

    def highlight_stones(self, positions):
        """Highlight specific stones or cells."""
        self.clear_highlights()
        
        highlight_pen = QPen(QColor("#00FF00"), 3)
        highlight_brush = QBrush(QColor(0, 255, 0, 50))
        
        for pos in positions:
            x, y = pos
            center_x = self.margin_horizontal + x * self.cell_size
            center_y = self.margin_vertical + y * self.cell_size
            radius = self.cell_size / 2 - 2
            
            highlight = self.scene.addEllipse(
                center_x - radius - 2, 
                center_y - radius - 2, 
                (radius + 2) * 2, 
                (radius + 2) * 2,
                highlight_pen, 
                highlight_brush
            )
            highlight.setZValue(0.5) # Behind stone, above board
            
            # Store for cleanup - using a new attribute if needed or reusing selection_item list
            if not hasattr(self, 'highlight_items'):
                self.highlight_items = []
            self.highlight_items.append(highlight)

    def clear_highlights(self):
        """Clear all highlights."""
        if hasattr(self, 'highlight_items'):
            for item in self.highlight_items:
                self.scene.removeItem(item)
            self.highlight_items.clear()
    
    def on_timer_tick(self):
        """Update timers."""
        # This belongs in MainWindow really, or BoardState should track time?
        # For now just emitting signal based on some external or internal logic
        pass


        from _02_engines.laser import LaserCalculator2D
        # Use existing calculator
        paths = self.laser_calc.calculate_path(start_pos, direction, self.board_state.stones)
        
        # Draw paths
        laser_color = QColor("#FF0000") if player == 1 else QColor("#0000FF")
        pen = QPen(laser_color, 3)
        
        for path in paths:
            # Draw line segments
            if len(path) >= 2:
                for i in range(len(path) - 1):
                    p1 = path[i]
                    p2 = path[i+1]
                    
                    # Scale to scene
                    x1 = self.margin_horizontal + p1[0] * self.cell_size
                    y1 = self.margin_vertical + p1[1] * self.cell_size
                    x2 = self.margin_horizontal + p2[0] * self.cell_size
                    y2 = self.margin_vertical + p2[1] * self.cell_size
                    
                    line = self.scene.addLine(x1, y1, x2, y2, pen)
                    line.setZValue(5) # Above stones
                    self.laser_items.append(line)
        
        # Calculate captures (logic needed here or in board_state)
        # We delegate capture logic to board_state to keep it central
        captured = self.board_state.process_laser_captures(player, paths)
        
        # Update visuals for captured stones
        for pos in captured:
            if pos in self.stone_items:
                self.scene.removeItem(self.stone_items[pos])
                del self.stone_items[pos]
                
        return captured

    # --- Mouse & Keyboard Interaction ---

    def keyPressEvent(self, event):
        """Handle keyboard input for movement."""
        if not self.selected_stone_pos:
            super().keyPressEvent(event)
            return

        key = event.key()
        dx, dy = 0, 0
        
        if key in (Qt.Key_W, Qt.Key_Up):
            dy = -1
        elif key in (Qt.Key_S, Qt.Key_Down):
            dy = 1
        elif key in (Qt.Key_A, Qt.Key_Left):
            dx = -1
        elif key in (Qt.Key_D, Qt.Key_Right):
            dx = 1
        else:
            super().keyPressEvent(event)
            return

        self.move_selected_stone(dx, dy)

    def move_selected_stone(self, dx, dy):
        """Attempt to move the selected stone by delta (dx, dy)."""
        if not self.selected_stone_pos:
            return

        current_pos = self.selected_stone_pos
        stone = self.board_state.stones.get(current_pos)
        
        # Security check: only move own stones (unless in debug/replayer? assume standard rules)
        if not stone or stone.player != self.current_player:
            return

        # Calculate target position (wrapping logic handled by board_state, 
        # but we need to pass strict 'to' coordinate to move_stone if it handles wrapping, 
        # OR calculate wrapped 'to' coordinate here.
        # board_state.move_stone documentation says: "to_pos: target position (will be wrapped)"
        # So we can pass the raw coordinate.
        
        target_x = current_pos[0] + dx
        target_y = current_pos[1] + dy
        
        # Execute move in board logic
        new_pos = self.board_state.move_stone(current_pos, (target_x, target_y))
        
        if new_pos:
            # Update Visuals
            self.move_stone_visual(current_pos, new_pos)
            
            # Update Selection
            self.selected_stone_pos = new_pos
            self._update_selection_visual()
            
            # Emit signal/Take energy?
            # Creating a custom signal for movement might be useful for recording, 
            # but main_game records placements/lasers.
            # We should probably trigger an 'energy spend' or 'turn end' if this counts as a move.
            # IN REALTIME MODE: Movement costs nothing (time/velocity based).
            # IN TURN BASED: Movement usually takes a turn? The original rules say "Place" or "Rotate".
            # Moving is a new action introduced for RealTime/Advanced play.
            # For now, we assume this is allowed. If turn-based, it might consume the turn.
            
            # Let's emit a 'stone_moved' signal if we want main_game to record it?
            # Added signal at class level: stone_placed, stone_rotated... 
            # I should add 'stone_moved' signal.
            pass

    def mousePressEvent(self, event):
        """Handle mouse interaction for placement, laser aiming, selection, and rotation."""
        # Ensure we have focus for keyboard events
        self.setFocus()
        
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.drag_start_scene = self.mapToScene(event.pos())
            self.is_aiming = False
            
            # Check if clicked on a stone or border
            grid_pos = self._get_grid_pos(self.drag_start_scene)
            
            if grid_pos:
                if grid_pos in self.board_state.stones:
                    # Clicked on existing stone
                    stone = self.board_state.stones[grid_pos]
                    
                    # If it's our stone, select it
                    if stone.player == self.current_player:
                        self.selected_stone_pos = grid_pos
                        self._update_selection_visual()
                    else:
                        # Deselect if clicked opponent stone (or keep? let's deselect)
                        self.selected_stone_pos = None
                        self._update_selection_visual()
                        
                    self.aiming_source = grid_pos
                    self.aiming_type = "internal"
                else:
                    # Clicked on empty space
                    self.selected_stone_pos = None # Deselect
                    self._update_selection_visual()
                    
                    self.aiming_source = None
                    self.aiming_type = "placement"
            else:
                self.selected_stone_pos = None # Deselect
                self._update_selection_visual()
                
                self.aiming_source = self._get_border_pos(self.drag_start_scene)
                self.aiming_type = "external" if self.aiming_source else None

        elif event.button() == Qt.RightButton:
            # Right click -> Start Rotation Drag
            scene_pos = self.mapToScene(event.pos())
            grid_pos = self._get_grid_pos(scene_pos)
            if grid_pos and grid_pos in self.board_state.stones:
                self.rotating_stone_pos = grid_pos
                self.is_rotating = True
                self.setCursor(Qt.ClosedHandCursor)
                # Right click also selects? Maybe not to avoid conflict.
                # self.selected_stone_pos = grid_pos
                # self._update_selection_visual()

        # Call parent QGraphicsView mouse event to handle potential drag items if any (we don't use them heavily)
        # But we do need to call super implementation for general housekeeping
        super(QGraphicsView, self).mousePressEvent(event)   

    def _update_selection_visual(self):
        """Draw selection ring around selected stone."""
        # Check if we have a selection item already
        if hasattr(self, 'selection_item') and self.selection_item:
            self.scene.removeItem(self.selection_item)
            self.selection_item = None
            
        if self.selected_stone_pos:
            x, y = self.selected_stone_pos
            center_x = self.margin_horizontal + x * self.cell_size
            center_y = self.margin_vertical + y * self.cell_size
            radius = self.cell_size / 2 + 2 # Slightly larger than stone
            
            pen = QPen(QColor("#00FF00"), 3) # bright green selection
            pen.setStyle(Qt.DotLine)
            
            self.selection_item = self.scene.addEllipse(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                pen, Qt.NoBrush
            )
            self.selection_item.setZValue(10)


    
    def set_stone_type(self, stone_type):
        """Set the current stone type for placement."""
        self.current_stone_type = stone_type
        
    def end_turn(self):
        """Switch current player."""
        self.current_player = (self.current_player % 2) + 1
        self.reset_move_timer()

    def set_current_player(self, player):
        """Set the current player (for energy tracking)."""
        self.current_player = player
        # Reset move timer on turn switch (handled in end_turn usually, but safe here too)
        self.board_state.current_move_time_remaining = self.board_state.move_time_limit

    def on_timer_tick(self):
        """Handle timer tick."""
        if self.board_state.game_over:
            return
            
        delta = 0.1
        
        # Decrement Move Timer
        self.board_state.current_move_time_remaining -= delta
        
        # Decrement Total Timer
        if self.board_state.total_time_limit > 0:
            self.board_state.player_time_remaining[self.current_player] -= delta
            
        # Check Expiration
        if self.board_state.current_move_time_remaining <= 0:
            self.handle_time_expiration(f"Player {self.current_player} Move Time Expired")
            return
            
        if self.board_state.total_time_limit > 0 and self.board_state.player_time_remaining[self.current_player] <= 0:
            self.handle_time_expiration(f"Player {self.current_player} Total Time Expired")
            return
            
        # Emit update signal
        self.timer_updated.emit(
            self.board_state.player_time_remaining[1],
            self.board_state.player_time_remaining[2],
            self.board_state.current_move_time_remaining,
            self.board_state.total_time_limit
        )

    def handle_time_expiration(self, reason):
        """Handle time expiration."""
        self.board_state.game_over = True
        self.board_state.winner = 2 if self.current_player == 1 else 1
        self.board_state.victory_reason = reason
        self.game_over_signal.emit()

    def set_timer_settings(self, total_min, move_sec):
        """Update timer settings."""
        self.board_state.total_time_limit = total_min
        self.board_state.move_time_limit = move_sec
        
        # Reset current timers
        self.board_state.player_time_remaining = {
            1: total_min * 60.0,
            2: total_min * 60.0
        }
        self.board_state.current_move_time_remaining = float(move_sec)
        
    def reset_move_timer(self):
        """Reset the move timer."""
        self.board_state.current_move_time_remaining = float(self.board_state.move_time_limit)
        
    def stop_timer(self):
        """Stop the game timer (e.g. for replayer)."""
        if self.game_timer:
            self.game_timer.stop()
    
    def clear_board(self):
        """Clear all stones and lasers."""
        for item in self.stone_items.values():
            self.scene.removeItem(item)
        self.stone_items.clear()
        
        for item in self.laser_items:
            self.scene.removeItem(item)
        self.laser_items.clear()
        
        if self.aiming_arrow:
            self.scene.removeItem(self.aiming_arrow)
            self.aiming_arrow = None
        
        # Clear victory screen items
        for item in self.victory_items:
            self.scene.removeItem(item)
        self.victory_items.clear()
            
        self.board_state = BoardState2D(self.grid_size, territory_threshold=self.territory_threshold)
        self.current_player = 1

    def set_grid_size(self, new_size):
        """Set the grid size and reinitialize the board."""
        if new_size not in BoardState2D.GRID_SIZES:
            raise ValueError(f"Invalid grid size {new_size}. Must be one of {BoardState2D.GRID_SIZES}")
        
        # Update grid size
        self.grid_size = new_size
        self.laser_calc = LaserCalculator2D(new_size)
        
        # Clear ALL scene items (including grid, background, stones, lasers)
        self.scene.clear()
        self.stone_items.clear()
        self.laser_items.clear()
        self.victory_items.clear()
        self.aiming_arrow = None
        
        # Reinitialize board state with new size
        self.board_state = BoardState2D(new_size, territory_threshold=self.territory_threshold)
        self.current_player = 1
        
        # Redraw board with new grid
        self._init_board()
        
        # Recalculate scene rect and fit to view
        self._setup_view()

    def show_victory_screen(self, winner, reason, p1_score=0, p2_score=0):
        """Display a dramatic victory screen overlay with scores."""
        # Fix: Clear existing victory items first to avoid ghost overlays
        self.clear_victory_screen()
        
        # Create a semi-transparent dark overlay
        overlay = self.scene.addRect(
            self.scene.sceneRect(),
            Qt.NoPen,
            QBrush(QColor(0, 0, 0, 200))
        )
        overlay.setZValue(100)
        self.victory_items.append(overlay)
        
        # Victory Text
        text = f"PLAYER {winner} WINS!" if winner > 0 else "DRAW!"
        font = QFont("Impact", 48, QFont.Bold)
        text_item = self.scene.addText(text, font)
        text_item.setDefaultTextColor(QColor("#FFD700"))  # Gold color
        
        # Center the text
        rect = text_item.boundingRect()
        center_x = self.scene.width() / 2
        center_y = self.scene.height() / 2
        text_item.setPos(center_x - rect.width() / 2, center_y - rect.height() / 2 - 100)
        text_item.setZValue(101)
        self.victory_items.append(text_item)
        
        # Reason Text
        reason_font = QFont("Segoe UI", 24)
        reason_item = self.scene.addText(reason, reason_font)
        reason_item.setDefaultTextColor(QColor("#FFFFFF"))
        
        r_rect = reason_item.boundingRect()
        reason_item.setPos(center_x - r_rect.width() / 2, center_y - 20)
        reason_item.setZValue(101)
        self.victory_items.append(reason_item)
        
        # Score Text
        score_font = QFont("Segoe UI", 20)
        score_text = f"Final Score: P1: {p1_score}  -  P2: {p2_score}"
        score_item = self.scene.addText(score_text, score_font)
        score_item.setDefaultTextColor(QColor("#FFC107"))
        
        s_rect = score_item.boundingRect()
        score_item.setPos(center_x - s_rect.width() / 2, center_y + 40)
        score_item.setZValue(101)
        self.victory_items.append(score_item)

    def clear_victory_screen(self):
        """Clear only the victory screen overlay."""
        for item in self.victory_items:
            self.scene.removeItem(item)
        self.victory_items.clear()
