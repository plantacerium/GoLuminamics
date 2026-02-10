import sys
import os
import random
import time
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from PySide6.QtCore import QTimer

# Reutilizamos la ventana principal existente
from _00_entry.main_game import MainWindow
# Importamos nuestros agentes IA
from _02_engines.ai_player import AIAgent

class ArenaWindow(MainWindow):
    def __init__(self, p1_model="gemma3:4b", p2_model="gemma3:4b", use_all_playbooks=True):
        super().__init__()
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

        # --- AÑADIR BOTÓN DE START ---
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
        
        # Insertar el botón en el panel de controles usando el método helper que creamos
        self.controls.add_extra_action_button(self.start_btn, index=0)
        
        print(f"Arena Inicializada. Modelos: {p1_model} vs {p2_model}. All Playbooks: {use_all_playbooks}")

    def toggle_match(self):
        if self.turn_timer.isActive():
            self.stop_match()
        else:
            self.start_match()

    def start_match(self):
        print("Iniciando partida IA...")
        self.turn_timer.start(2000) # 2 segundos por turno
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
            current_pid = self.board.current_player
            agent = self.agents[current_pid]
            
            print(f"Turno de IA Jugador {current_pid} ({agent.model_name})...")
            
            class DummyServer:
                def __init__(self, board_state, grid_size):
                    self.board = board_state
                    self.grid_size = grid_size
                    
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
                        for st in ["PRISM", "MIRROR", "SPLITTER"]:
                            valid.append({"type": "place", "x": x, "y": y, "stone_type": st})
                            
                    # Rotate actions
                    for pos, stone in self.board.stones.items():
                        if stone.player == current_pid: 
                            valid.append({"type": "rotate", "x": pos[0], "y": pos[1], "angle": 90}) 
                            
                    return {"valid_actions": valid}

            # El Grid Size se pasa actualizado aquí cada turno
            dummy_server = DummyServer(self.board.board_state, self.board.grid_size)
            
            action = agent.get_move(dummy_server)
            
            if action:
                if "thought" in action:
                    print(f"💭 PENSAMIENTO ({agent.model_name}): {action['thought']}")
                self.execute_ai_move(action)
            else:
                print("IA no devolvió acción válida. Pasando turno.")
                self.handle_pass()
                
        except Exception as e:
            print(f"Error en turno de IA: {e}")
            self.handle_pass()
        finally:
            self.is_thinking = False

    def execute_ai_move(self, action):
        """Traduce el JSON de la IA a acciones de la UI."""
        action_type = action.get("type")
        
        if action_type == "place":
            x, y = action.get("x"), action.get("y")
            stone_type = action.get("stone_type", "PRISM").upper()
            
            # Verificar validez básica
            if 0 <= x < self.board.grid_size and 0 <= y < self.board.grid_size:
                # Set stone type in UI controls (hacky but updates state correctly)
                self.controls.set_stone_type(stone_type) 
                # Place stone
                self.board.place_stone((x, y), stone_type, self.board.current_player)
            else:
                print(f"Coordenadas inválidas: {x}, {y}")
                self.handle_pass()

        elif action_type == "rotate":
            x, y = action.get("x"), action.get("y")
            angle = action.get("angle", 0)
            
            # En la UI, rotation es on_click derecho -> +45 grados o set manual
            # Vamos a intentar establecer la rotación directamente en el estado
            stone = self.board.board_state.get_stone_at((x, y))
            if stone and stone.player == self.board.current_player:
                self.board.board_state.set_rotation_to((x, y), angle)
                self.board.update() # Repaint
                self.on_stone_rotated((x, y), angle) # Trigger log/events
            else:
                self.handle_pass()

        elif action_type == "laser":
            # La UI requiere un punto de inicio y dirección
            # La IA puede dar 'x, y' y 'dx, dy'
            # Convertimos esto a una entrada de mouse simulada o llamada directa
            x, y = action.get("x"), action.get("y")
            dx, dy = action.get("dx"), action.get("dy")
            
            start = (x, y)
            direction = (dx, dy)
            self.handle_laser_mouse(start, direction, self.board.current_player)

        elif action_type == "pass":
            self.handle_pass()
            
        else:
            print(f"Acción desconocida: {action_type}")
            self.handle_pass()

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
