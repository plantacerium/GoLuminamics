import sys
import os
import random
import time
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QCheckBox, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import QTimer

# Reutilizamos la ventana principal existente
from _00_entry.main_game import MainWindow
# Importamos nuestros agentes IA
from _02_engines.ai_player import AIAgent

class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_file = open(filename, "a", encoding='utf-8')
        self.enabled = True

    def write(self, message):
        try:
            if self.enabled:
                self.terminal.write(message)
                self.log_file.write(message)
                self.log_file.flush() # Ensure it's written immediately
        except Exception:
             pass # Prevent crashes on logging errors

    def flush(self):
        if self.enabled:
            self.terminal.flush()
            self.log_file.flush()

class ArenaWindow(MainWindow):
    def __init__(self, p1_model="gemma3:4b", p2_model="gemma3:4b", use_all_playbooks=True):
        super().__init__()
        
        # --- CONFIGURAR LOGGING ---
        if not os.path.exists("logs"):
            os.makedirs("logs")
        log_filename = f"logs/match_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        self.logger = DualLogger(log_filename)
        sys.stdout = self.logger
        print(f"=== INICIO DE REGISTRO EN: {log_filename} ===")
        
        self.setWindowTitle("GoLuminamics - AI Arena")
        
        # Configurar agentes
        # use_all_playbooks determina si cargamos 1 o 20 estrategias
        self.p1_agent = AIAgent(1, p1_model, mechanics_path="MECHANICS.md", use_all_playbooks=use_all_playbooks)
        self.p2_agent = AIAgent(2, p2_model, mechanics_path="MECHANICS.md", use_all_playbooks=use_all_playbooks)
        self.agents = {1: self.p1_agent, 2: self.p2_agent}
        
        # Timer para el bucle de juego
        self.turn_timer = QTimer(self)
        self.turn_timer.timeout.connect(self.play_next_turn)
        # NO iniciamos el timer automáticamente
        
        self.is_thinking = False
        
        # Iniciar modo infinito de energía por defecto
        self.board.board_state.infinite_energy = True
        self.update_energy_display()

        # --- AÑADIR BOTÓN DE START Y CHECKBOX DE LOG ---
        self.ai_match_container = QWidget()
        ai_match_layout = QHBoxLayout(self.ai_match_container)
        ai_match_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_btn = QPushButton("START AI MATCH")
        self.start_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007ACC; 
                font-weight: bold; 
                font-size: 14px; 
                padding: 10px;
            }
            QPushButton:hover { background-color: #009DFF; }
        """)
        self.start_btn.clicked.connect(self.toggle_match)
        ai_match_layout.addWidget(self.start_btn, 4) # Weight 4
        
        self.log_check = QCheckBox("Log")
        self.log_check.setChecked(True)
        self.log_check.setToolTip("Enable/Disable logging to file")
        self.log_check.setStyleSheet("color: #CCC; font-weight: bold; margin-left: 5px;")
        self.log_check.stateChanged.connect(self.handle_logging_toggle)
        ai_match_layout.addWidget(self.log_check, 1) # Weight 1
        
        # --- REALTIME MODE CHECKBOX ---
        self.realtime_check = QCheckBox("Realtime")
        self.realtime_check.setChecked(False)
        self.realtime_check.setToolTip("Realtime mode: velocity-based movement, no turns, clock starts on Start")
        self.realtime_check.setStyleSheet("color: #7FDBFF; font-weight: bold; margin-left: 5px;")
        self.realtime_check.stateChanged.connect(self.handle_realtime_toggle)
        ai_match_layout.addWidget(self.realtime_check, 1)
        
        self.realtime_mode = False
        self.realtime_elapsed = 0.0  # Seconds elapsed since match start
        
        # Insertar el contenedor en el panel de controles
        self.controls.add_extra_action_button(self.ai_match_container, index=0)
        
        print(f"Arena Inicializada. Modelos: {p1_model} vs {p2_model}. All Playbooks: {use_all_playbooks}")

    def toggle_match(self):
        if self.turn_timer.isActive():
            self.stop_match()
        else:
            self.start_match()

    def handle_realtime_toggle(self, state):
        """Toggle realtime mode on/off."""
        self.realtime_mode = (state == 2)
        mode_name = "REALTIME" if self.realtime_mode else "TURN-BASED"
        print(f"Mode changed to: {mode_name}")
        if self.realtime_mode:
            print("  - Velocity-based movement enabled")
            print("  - Clock starts on START AI MATCH only")
            print("  - Both players act simultaneously")

    def start_match(self):
        print("Iniciando partida IA...")
        if self.realtime_mode:
            self.realtime_elapsed = 0.0
            self.turn_timer.start(500)  # 500ms realtime ticks
            print("REALTIME: 500ms tick, both players each tick")
        else:
            self.turn_timer.start(2000)  # 2s per turn (classic)
        self.start_btn.setText("PAUSE AI MATCH")
        self.start_btn.setStyleSheet("background-color: #CC7A00; font-weight: bold; padding: 10px;")

    def stop_match(self):
        print("Pausando partida IA...")
        self.turn_timer.stop()
        self.start_btn.setText("RESUME AI MATCH")
        self.start_btn.setStyleSheet("background-color: #007ACC; font-weight: bold; padding: 10px;")

    def handle_restart(self):
        """Sobreescribimos restart para detener la IA."""
        super().handle_restart()
        self.stop_match()
        self.start_btn.setText("START AI MATCH")
        print("Juego reiniciado. IA detenida.")

    def handle_grid_size_change(self, new_size):
        """Sobreescribimos cambio de grid para detener la IA."""
        # Llamamos al original que pregunta al usuario
        super().handle_grid_size_change(new_size)
        # Si el grid cambió, paramos
        if self.board.board_state.grid_size == new_size:
            self.stop_match()
            self.start_btn.setText("START AI MATCH")

    def handle_infinite_score_change(self, enabled):
        """Override to disable 'Pass' button when No Mercy is active."""
        super().handle_infinite_score_change(enabled)
        self.controls.pass_btn.setEnabled(not enabled)
        if enabled:
            print("INFO: Pass Turn disabled for 'No Mercy' ruleset.")
        else:
            print("INFO: Pass Turn re-enabled.")

    def handle_logging_toggle(self, state):
        """Habilita o deshabilita el registro en archivo y consola."""
        is_enabled = (state == 2) # 2 is Qt.Checked
        if hasattr(self, 'logger'):
            status = "HABILITADO" if is_enabled else "DESHABILITADO"
            if not is_enabled:
                print(f"=== REGISTRO {status} ===")
            
            self.logger.enabled = is_enabled
            
            if is_enabled:
                print(f"=== REGISTRO {status} ===")

    def play_next_turn(self):
        if self.board.board_state.game_over:
            self.turn_timer.stop()
            self.start_btn.setText("MATCH FINISHED")
            self.start_btn.setEnabled(False)
            print("Juego terminado. Guardando partida...")
            self.auto_save_game()
            return
            
        if self.is_thinking:
            return

        self.is_thinking = True
        QApplication.processEvents()
        
        try:
            if self.realtime_mode:
                # REALTIME: Both players act each tick
                self.realtime_elapsed += 0.5  # 500ms per tick
                for pid in [1, 2]:
                    self._play_one_agent(pid)
            else:
                # CLASSIC: Alternating turns
                current_pid = self.board.current_player
                self._play_one_agent(current_pid)
                
        except Exception as e:
            print(f"Error en turno de IA: {e}")
            if not self.realtime_mode:
                self.handle_pass()
        finally:
            self.is_thinking = False

    def _play_one_agent(self, current_pid):
        """Execute one AI agent's turn (used by both classic and realtime modes)."""
        agent = self.agents[current_pid]
        
        if not self.realtime_mode:
            print(f"Turno de IA Jugador {current_pid} ({agent.model_name})...")
        
        class DummyServer:
            def __init__(self, board_state, grid_size, realtime_mode):
                self.board = board_state
                self.grid_size = grid_size
                self.realtime_mode = realtime_mode
                
            def get_valid_actions(self):
                valid = []
                # Place actions (sample)
                empty_cells = []
                for y in range(self.grid_size):
                    for x in range(self.grid_size):
                        if (x, y) not in self.board.stones:
                            empty_cells.append((x,y))
                
                sample_cells = random.sample(empty_cells, min(10, len(empty_cells))) if len(empty_cells) > 0 else []
                for (x, y) in sample_cells:
                    for st in ["PRISM", "MIRROR", "SPLITTER", "BLOCKER"]:
                        valid.append({"type": "place", "x": x, "y": y, "stone_type": st})
                        
                # Rotate actions
                for pos, stone in self.board.stones.items():
                    if stone.player == current_pid: 
                        valid.append({"type": "rotate", "x": pos[0], "y": pos[1], "angle": 90})
                        
                        # Move actions (all 8 directions + wrapping)
                        if self.realtime_mode:
                            directions = [
                                (0, -1), (0, 1), (-1, 0), (1, 0),  # Cardinal
                                (-1, -1), (1, -1), (-1, 1), (1, 1)  # Diagonal
                            ]
                            for dx, dy in directions:
                                nx = (pos[0] + dx) % self.grid_size
                                ny = (pos[1] + dy) % self.grid_size
                                if (nx, ny) not in self.board.stones:
                                    valid.append({"type": "move", "from_x": pos[0], "from_y": pos[1], "to_x": nx, "to_y": ny})
                            
                            # Curve move actions (quadratic Bezier with random control point)
                            import math
                            for _ in range(2):  # 2 random curve options per stone
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
                        
                return {"valid_actions": valid}

        # The Grid Size se pasa actualizado aquí cada turno
        dummy_server = DummyServer(self.board.board_state, self.board.grid_size, self.realtime_mode)
        
        # RETRY LOOP (Max 3 attempts to avoid passing)
        max_retries = 3
        action_success = False
        
        for attempt in range(max_retries):
            # Only print retry attempts after first
            if attempt > 0:
                print(f"Intento {attempt+1}/{max_retries} para Agente {current_pid}...")
            
            action = agent.get_move(dummy_server)
            
            if not action:
                print(f"IA no devolvió JSON válido (Intento {attempt+1}).")
                continue
                
            if action.get("type") == "pass":
                if self.realtime_mode:
                    # In realtime mode, pass is acceptable (stone stays still)
                    break
                print(f"IA intentó pasar turno (Intento {attempt+1}). Forzando reintento...")
                continue

            if "thought" in action:
                print(f"💭 PENSAMIENTO ({agent.model_name}): {action['thought']}")
            
            # Try to execute
            if self.execute_ai_move(action):
                action_success = True
                break
            else:
                print(f"Movimiento {action.get('type')} fallido (Intento {attempt+1}).")
        
        if not action_success and not self.realtime_mode:
            if self.board.board_state.infinite_score:
                print("INFO: 'No Mercy' activo. Forzando movimiento aleatorio en lugar de pasar.")
                valid_actions = dummy_server.get_valid_actions().get("valid_actions", [])
                if valid_actions:
                    fallback_action = random.choice(valid_actions)
                    print(f"RESURRECCIÓN: Ejecutando acción aleatoria {fallback_action.get('type')}")
                    self.execute_ai_move(fallback_action)
                else:
                    print("CRÍTICO: No hay movimientos posibles. Pasando turno.")
                    self.handle_pass()
            else:
                print("IA falló todas las opciones o insistió en pasar. Pasando turno.")
                self.handle_pass()

    def execute_ai_move(self, action):
        """Traduce el JSON de la IA a acciones de la UI. Retorna True si éxito."""
        try:
            action_type = action.get("type")
            
            if action_type == "place":
                x = int(action.get("x", 0))
                y = int(action.get("y", 0))
                stone_type = action.get("stone_type", "PRISM").upper()
                
                limit = self.board.board_state.grid_size
                if 0 <= x < limit and 0 <= y < limit:
                    self.controls.set_stone_type(stone_type) 
                    if self.board.place_stone((x, y), stone_type, self.board.current_player):
                        return True
                print(f"Colocación inválida en {x}, {y} (Límite: {limit})")
                return False

            elif action_type == "rotate":
                x = int(action.get("x", 0))
                y = int(action.get("y", 0))
                angle = float(action.get("angle", 0))
                
                stone = self.board.board_state.get_stone_at((x, y))
                if stone and stone.player == self.board.current_player:
                    self.board.rotate_stone_to((x, y), angle)
                    self.on_stone_rotated((x, y), angle) 
                    self.board.end_turn()
                    return True
                print(f"Rotación inválida: No hay piedra propia en {x}, {y}")
                return False

            elif action_type == "move":
                from_x = int(action.get("from_x", 0))
                from_y = int(action.get("from_y", 0))
                to_x = int(action.get("to_x", 0))
                to_y = int(action.get("to_y", 0))
                
                from_pos = (from_x, from_y)
                to_pos = (to_x, to_y)
                
                stone = self.board.board_state.get_stone_at(from_pos)
                if stone and stone.player == self.board.current_player:
                    wrapped = self.board.board_state.move_stone(from_pos, to_pos)
                    if wrapped is not None:
                        self.board.move_stone_visual(from_pos, wrapped)
                        if not self.realtime_mode:
                            self.board.end_turn()
                        return True
                print(f"Movimiento inválido de {from_pos} a {to_pos}")
                return False

            elif action_type == "curve_move":
                from_x = int(action.get("from_x", 0))
                from_y = int(action.get("from_y", 0))
                cx = float(action.get("control_x", 0))
                cy = float(action.get("control_y", 0))
                ex = int(action.get("end_x", 0))
                ey = int(action.get("end_y", 0))
                
                from_pos = (from_x, from_y)
                control_points = [(cx, cy), (ex, ey)]
                
                stone = self.board.board_state.get_stone_at(from_pos)
                if stone and stone.player == self.board.current_player:
                    final_pos = self.board.board_state.move_stone_along_curve(
                        from_pos, control_points, self.board.current_player
                    )
                    if final_pos is not None:
                        self.board.move_stone_visual(from_pos, final_pos)
                        if not self.realtime_mode:
                            self.board.end_turn()
                        return True
                print(f"Movimiento curvo inválido de ({from_x},{from_y})")
                return False

            elif action_type == "laser":
                x = int(action.get("x", 0))
                y = int(action.get("y", 0))
                dx = float(action.get("dx", 0))
                dy = float(action.get("dy", 0))
                
                if dx == 0 and dy == 0:
                    return False
                    
                start = (x, y)
                direction = (dx, dy)
                self.handle_laser_mouse(start, direction, self.board.current_player)
                return True

            elif action_type == "select":
                positions = action.get("positions", [])
                valid_positions = []
                for p in positions:
                    if isinstance(p, list) and len(p) == 2:
                        valid_positions.append((p[0], p[1]))
                        
                if valid_positions:
                    self.board.highlight_stones(valid_positions)
                    print(f"SELECCIÓN: Resaltando {valid_positions}")
                    # Do NOT call end_turn(), just return True so loop breaks and we wait for next tick
                    return True
                return False

            elif action_type == "pass":
                return False 
                
            return False
        except (ValueError, TypeError, Exception) as e:
            print(f"Error parseando o ejecutando acción de IA: {e}")
            return False

    def auto_save_game(self):
        """Guarda la partida automáticamente en games/"""
        if not os.path.exists("games"):
            os.makedirs("games")
            
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"games/arena_match_{timestamp}.json"
        
        try:
            self.recorder.save_game(filename)
            print(f"Partida guardada automáticamente en: {filename}")
            QMessageBox.information(self, "Arena Finalizada", f"Juego terminado.\nGuardado en: {filename}")
        except Exception as e:
            print(f"Error guardando partida: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GoLuminamics AI Arena")
    parser.add_argument("--p1", type=str, default="gemma3:4b", help="Model for Player 1")
    parser.add_argument("--p2", type=str, default="gemma3:4b", help="Model for Player 2")
    parser.add_argument("--single-strategy", action="store_true", help="If set, AI selects ONE random strategy instead of all.")
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Estilos (copiados de main_game o importados si fuera posible reutilizar stylesheet)
    app.setStyleSheet("""
        QMainWindow { background-color: #202025; }
        QWidget { color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    """)
    
    # Por defecto use_all_playbooks es True, a menos que se pase --single-strategy
    use_all = not args.single_strategy
    
    window = ArenaWindow(args.p1, args.p2, use_all_playbooks=use_all)
    window.show()
    
    sys.exit(app.exec())
