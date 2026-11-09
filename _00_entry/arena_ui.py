import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import random
import time
import math
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QPushButton, QCheckBox, QWidget, 
    QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QFrame
)
from PySide6.QtGui import QFont, QColor, QTextCursor
from PySide6.QtCore import QTimer, QThread, Signal, Qt

# Reutilizamos la ventana principal existente
from _00_entry.main_game import MainWindow
# Importamos nuestros agentes IA
from _02_engines.ai_player import AIAgent


class DualLogger:
    """Registra salida en consola y archivo simultáneamente."""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_file = open(filename, "a", encoding='utf-8')
        self.enabled = True

    def write(self, message):
        try:
            if self.enabled:
                self.terminal.write(message)
                self.log_file.write(message)
                self.log_file.flush()
        except Exception:
            pass

    def flush(self):
        if self.enabled:
            self.terminal.flush()
            self.log_file.flush()


class DummyServer:
    """Snapshot seguro para que el agente IA explore movimientos válidos."""
    def __init__(self, board_state, grid_size, realtime_mode):
        self.board = board_state
        self.grid_size = grid_size
        self.realtime_mode = realtime_mode
        self.selection = []

    def get_valid_actions(self):
        valid = []
        empty_cells = []
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if (x, y) not in self.board.stones:
                    empty_cells.append((x, y))

        sample_cells = random.sample(empty_cells, min(10, len(empty_cells))) if empty_cells else []
        for (x, y) in sample_cells:
            for st in ["PRISM", "MIRROR", "SPLITTER", "BLOCKER"]:
                valid.append({"type": "place", "x": x, "y": y, "stone_type": st})

        for pos, stone in self.board.stones.items():
            if stone.player == self.board.current_player if hasattr(self.board, "current_player") else 1:
                valid.append({"type": "rotate", "x": pos[0], "y": pos[1], "angle": 90})

                if self.realtime_mode:
                    directions = [
                        (0, -1), (0, 1), (-1, 0), (1, 0),
                        (-1, -1), (1, -1), (-1, 1), (1, 1)
                    ]
                    for dx, dy in directions:
                        nx = (pos[0] + dx) % self.grid_size
                        ny = (pos[1] + dy) % self.grid_size
                        if (nx, ny) not in self.board.stones:
                            valid.append({"type": "move", "from_x": pos[0], "from_y": pos[1], "to_x": nx, "to_y": ny})

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
        return {"valid_actions": valid}


class ThoughtStreamerWidget(QWidget):
    """Panel visualizador de razonamiento táctico y flujo de pensamientos del agente."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Header Box
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1E1E24;
                border: 1px solid #3A3A45;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(6, 6, 6, 6)
        h_layout.setSpacing(4)

        title_label = QLabel("🧠 AI THOUGHT STREAMER")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #00E5FF; letter-spacing: 1px;")
        title_label.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(title_label)

        # Status pills for both players
        pills_layout = QHBoxLayout()
        self.p1_status_lbl = QLabel("⚫ P1: Esperando")
        self.p1_status_lbl.setStyleSheet("""
            background-color: #2A1B1B; color: #FF6B6B; 
            border: 1px solid #FF4136; border-radius: 4px; padding: 3px 6px; font-size: 11px; font-weight: bold;
        """)
        self.p2_status_lbl = QLabel("⚪ P2: Esperando")
        self.p2_status_lbl.setStyleSheet("""
            background-color: #1B222A; color: #5BC0DE; 
            border: 1px solid #0074D9; border-radius: 4px; padding: 3px 6px; font-size: 11px; font-weight: bold;
        """)
        pills_layout.addWidget(self.p1_status_lbl)
        pills_layout.addWidget(self.p2_status_lbl)
        h_layout.addLayout(pills_layout)

        layout.addWidget(header_frame)

        # Text Log Area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #141418;
                color: #E2E8F0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                border: 1px solid #2D3748;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text, stretch=1)

        # Bottom controls bar
        bot_layout = QHBoxLayout()
        self.autoscroll_check = QCheckBox("Auto-scroll")
        self.autoscroll_check.setChecked(True)
        self.autoscroll_check.setStyleSheet("color: #A0AEC0; font-size: 11px;")

        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D3748; color: #CBD5E0;
                border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;
            }
            QPushButton:hover { background-color: #4A5568; }
        """)
        self.clear_btn.clicked.connect(self.log_text.clear)

        bot_layout.addWidget(self.autoscroll_check)
        bot_layout.addStretch(1)
        bot_layout.addWidget(self.clear_btn)
        layout.addLayout(bot_layout)

    def append_thought(self, player_id: int, model_name: str, thought: str, action_summary: str = "", inference_time: float = 0.0):
        color = "#FF8787" if player_id == 1 else "#7FD5FF"
        border_color = "#FF4136" if player_id == 1 else "#0074D9"
        bg_card = "#241818" if player_id == 1 else "#14212D"
        player_tag = f"JUGADOR {player_id} ({model_name})"
        time_str = f" • ⏱️ {inference_time:.2f}s" if inference_time > 0 else ""

        thought_html = f"""
        <div style="margin-bottom: 10px; padding: 8px; background-color: {bg_card}; border-left: 4px solid {border_color}; border-radius: 4px;">
            <div style="font-size: 11px; font-weight: bold; color: {color}; margin-bottom: 4px;">
                {player_tag}{time_str}
            </div>
            <div style="color: #F7FAFC; font-style: italic; line-height: 1.4; margin-bottom: 5px;">
                💭 {thought}
            </div>
            {f'<div style="font-size: 11px; color: #CBD5E0; font-weight: bold;">🎯 {action_summary}</div>' if action_summary else ''}
        </div>
        """
        self.log_text.append(thought_html)
        if self.autoscroll_check.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

    def update_player_status(self, player_id: int, is_thinking: bool, model_name: str = ""):
        if player_id == 1:
            if is_thinking:
                self.p1_status_lbl.setText("⚫ P1: Pensando...")
                self.p1_status_lbl.setStyleSheet("background-color: #4A1515; color: #FF8787; border: 1px solid #FF4136; border-radius: 4px; padding: 3px 6px; font-size: 11px; font-weight: bold;")
            else:
                self.p1_status_lbl.setText("⚫ P1: Esperando")
                self.p1_status_lbl.setStyleSheet("background-color: #2A1B1B; color: #FF6B6B; border: 1px solid #FF4136; border-radius: 4px; padding: 3px 6px; font-size: 11px; font-weight: bold;")
        else:
            if is_thinking:
                self.p2_status_lbl.setText("⚪ P2: Pensando...")
                self.p2_status_lbl.setStyleSheet("background-color: #15304A; color: #7FD5FF; border: 1px solid #0074D9; border-radius: 4px; padding: 3px 6px; font-size: 11px; font-weight: bold;")
            else:
                self.p2_status_lbl.setText("⚪ P2: Esperando")
                self.p2_status_lbl.setStyleSheet("background-color: #1B222A; color: #5BC0DE; border: 1px solid #0074D9; border-radius: 4px; padding: 3px 6px; font-size: 11px; font-weight: bold;")


class AIAgentWorker(QThread):
    """Hilo asíncrono para inferencia del modelo LLM sin bloquear la interfaz gráfica Qt."""
    move_ready = Signal(int, dict, str, float)  # player_id, action, thought, elapsed
    failed = Signal(int, str)                   # player_id, error_message

    def __init__(self, agent: AIAgent, dummy_server: DummyServer, player_id: int, max_retries: int = 3, realtime_mode: bool = False):
        super().__init__()
        self.agent = agent
        self.dummy_server = dummy_server
        self.player_id = player_id
        self.max_retries = max_retries
        self.realtime_mode = realtime_mode
        self._is_aborted = False

    def abort(self):
        self._is_aborted = True

    def run(self):
        start_time = time.time()
        action_found = None
        thought_text = ""

        try:
            for attempt in range(self.max_retries):
                if self._is_aborted:
                    return

                action = self.agent.get_move(self.dummy_server)
                if not action:
                    continue

                thought_text = action.get("thought", "")
                if action.get("type") == "pass" and not self.realtime_mode:
                    continue  # Reintento si intentó pasar en modo por turnos

                action_found = action
                break

            elapsed = time.time() - start_time
            if action_found:
                self.move_ready.emit(self.player_id, action_found, thought_text, elapsed)
            else:
                self.failed.emit(self.player_id, "No se obtuvo movimiento válido tras reintentos.")
        except Exception as e:
            self.failed.emit(self.player_id, str(e))


class ArenaWindow(MainWindow):
    def __init__(self, p1_model="gemma3:4b", p2_model="gemma3:4b", use_all_playbooks=True, max_turns=0):
        super().__init__()
        self.max_turns = max_turns
        self.turn_count = 0

        # --- CONFIGURAR LOGGING ---
        if not os.path.exists("logs"):
            os.makedirs("logs")
        log_filename = f"logs/match_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        self.logger = DualLogger(log_filename)
        sys.stdout = self.logger
        print(f"=== INICIO DE REGISTRO EN: {log_filename} ===")

        self.setWindowTitle("GoLuminamics - AI Arena")
        self.resize(1560, 850)

        # Configurar agentes
        self.p1_agent = AIAgent(1, p1_model, mechanics_path="MECHANICS.md", use_all_playbooks=use_all_playbooks)
        self.p2_agent = AIAgent(2, p2_model, mechanics_path="MECHANICS.md", use_all_playbooks=use_all_playbooks)
        self.agents = {1: self.p1_agent, 2: self.p2_agent}

        # Estado de ejecución y worker
        self.is_match_running = False
        self.active_worker = None

        # Timer para el bucle de juego
        self.turn_timer = QTimer(self)
        self.turn_timer.timeout.connect(self.execute_turn_cycle)

        # Iniciar modo infinito de energía por defecto
        self.board.board_state.infinite_energy = True
        self.update_energy_display()

        # --- AÑADIR BOTÓN DE START Y CHECKBOXES ---
        self.ai_match_container = QWidget()
        ai_main_layout = QVBoxLayout(self.ai_match_container)
        ai_main_layout.setContentsMargins(0, 0, 0, 0)
        ai_main_layout.setSpacing(6)

        ai_row1 = QHBoxLayout()
        ai_row1.setContentsMargins(0, 0, 0, 0)

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
        ai_row1.addWidget(self.start_btn, 4)

        self.log_check = QCheckBox("Log")
        self.log_check.setChecked(True)
        self.log_check.setToolTip("Habilitar/Deshabilitar registro en archivo")
        self.log_check.setStyleSheet("color: #CCC; font-weight: bold; margin-left: 5px;")
        self.log_check.stateChanged.connect(self.handle_logging_toggle)
        ai_row1.addWidget(self.log_check, 1)

        self.realtime_check = QCheckBox("Realtime")
        self.realtime_check.setChecked(False)
        self.realtime_check.setToolTip("Modo tiempo real con movimiento de velocidad")
        self.realtime_check.setStyleSheet("color: #7FDBFF; font-weight: bold; margin-left: 5px;")
        self.realtime_check.stateChanged.connect(self.handle_realtime_toggle)
        ai_row1.addWidget(self.realtime_check, 1)

        ai_main_layout.addLayout(ai_row1)

        self.realtime_mode = False
        self.realtime_elapsed = 0.0
        self.is_mcp_mode = False

        # Botón para activar el modo AI MCP (Antigravity)
        self.mcp_mode_btn = QPushButton("🤖 AI MCP (Jugar contra Antigravity)")
        self.mcp_mode_btn.setToolTip("Pasa el control a Antigravity para jugar en vivo desde el chat vía MCP")
        self.mcp_mode_btn.setStyleSheet("""
            QPushButton { 
                background-color: #6C5CE7; 
                color: #FFFFFF;
                font-weight: bold; 
                font-size: 13px; 
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #8172F5; }
        """)
        self.mcp_mode_btn.clicked.connect(self.enable_mcp_antigravity_mode)
        ai_main_layout.addWidget(self.mcp_mode_btn)

        # Insertar controles extra
        self.controls.add_extra_action_button(self.ai_match_container, index=0)

        # --- AÑADIR THOUGHT STREAMER AL SPLITTER HORIZONTAL ---
        self.thought_streamer = ThoughtStreamerWidget(self)
        self.splitter.addWidget(self.thought_streamer)
        self.splitter.setStretchFactor(2, 1)

        # Botón para colapsar/mostrar Thought Streamer en la barra superior
        self.btn_toggle_streamer = QPushButton("🧠 AI Thoughts")
        self.btn_toggle_streamer.setToolTip("Ocultar o desplegar el panel de pensamientos de la IA")
        self.btn_toggle_streamer.setStyleSheet("""
            QPushButton {
                background-color: #2D2D38;
                color: #DFDFE8;
                border: 1px solid #444455;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #383848; color: #FFF; }
        """)
        self.btn_toggle_streamer.clicked.connect(self.toggle_streamer_panel)
        self.top_toolbar.layout().addWidget(self.btn_toggle_streamer)

        # Proporciones iniciales: [Tablero + Bottom HUD, Controles, Pensamientos]
        self.splitter.setSizes([920, 280, 360])

        print(f"Arena Inicializada. Modelos: {p1_model} vs {p2_model}. All Playbooks: {use_all_playbooks}")

    def enable_mcp_antigravity_mode(self):
        """Pasa el control de la partida a Antigravity vía MCP."""
        self.stop_match()
        self.is_mcp_mode = True
        self.start_btn.setText("MODO MCP ACTIVO")
        self.start_btn.setEnabled(False)
        self.mcp_mode_btn.setStyleSheet("background-color: #00B894; color: white; font-weight: bold; padding: 10px;")

        current_pid = self.board.current_player
        self.thought_streamer.update_player_status(current_pid, True, "Antigravity MCP")
        self.thought_streamer.append_thought(
            current_pid,
            "Antigravity MCP",
            "🎮 MODO MCP EN VIVO CONECTADO. La ventana está sincronizada con el servidor MCP en http://127.0.0.1:18989.\n"
            "Dile a Antigravity en el chat qué jugada realizar o pídele: 'Antigravity, haz tu jugada'.\n"
            "Cada herramienta que use Antigravity se dibujará inmediatamente en esta pantalla en tiempo real.",
            "Esperando llamada de herramienta MCP...",
            0.0
        )
        print("[ArenaUI] Modo AI MCP (Antigravity) activado. Escuchando en puerto 18989.")

    def toggle_streamer_panel(self):
        """Muestra u oculta el panel lateral de pensamientos."""
        if hasattr(self, 'thought_streamer'):
            is_vis = self.thought_streamer.isVisible()
            self.thought_streamer.setVisible(not is_vis)
            if not is_vis:
                self.btn_toggle_streamer.setStyleSheet("background-color: #2D2D38; color: #DFDFE8; border: 1px solid #444455; border-radius: 5px; padding: 4px 10px; font-size: 12px;")
            else:
                self.btn_toggle_streamer.setStyleSheet("background-color: #1F1F26; color: #666675; border: 1px solid #30303A; border-radius: 5px; padding: 4px 10px; font-size: 12px;")

    def toggle_match(self):
        if self.is_match_running:
            self.stop_match()
        else:
            self.start_match()

    def handle_realtime_toggle(self, state):
        self.realtime_mode = (state == 2)
        mode_name = "REALTIME" if self.realtime_mode else "TURN-BASED"
        print(f"Modo cambiado a: {mode_name}")

    def start_match(self):
        if self.board.board_state.game_over:
            return
        print("Iniciando partida IA...")
        self.is_match_running = True
        self.board.start_timer()
        self.start_btn.setText("PAUSE AI MATCH")
        self.start_btn.setStyleSheet("background-color: #CC7A00; font-weight: bold; padding: 10px;")
        self.schedule_next_turn(100)

    def stop_match(self):
        print("Pausando partida IA...")
        self.is_match_running = False
        self.board.pause_timer()
        if self.turn_timer.isActive():
            self.turn_timer.stop()
        self.start_btn.setText("RESUME AI MATCH")
        self.start_btn.setStyleSheet("background-color: #007ACC; font-weight: bold; padding: 10px;")
        if self.active_worker and self.active_worker.isRunning():
            self.thought_streamer.update_player_status(self.active_worker.player_id, False)

    def schedule_next_turn(self, delay_ms: int = 500):
        if not self.is_match_running or self.board.board_state.game_over:
            return
        self.turn_timer.stop()
        QTimer.singleShot(delay_ms, self.execute_turn_cycle)

    def execute_turn_cycle(self):
        if not self.is_match_running or self.board.board_state.game_over:
            if self.board.board_state.game_over:
                self.on_match_finished()
            return

        if self.active_worker and self.active_worker.isRunning():
            return

        current_pid = self.board.current_player
        agent = self.agents[current_pid]

        self.thought_streamer.update_player_status(current_pid, True, agent.model_name)

        # Snapshot seguro del tablero para el hilo
        dummy_server = DummyServer(self.board.board_state.clone(), self.board.grid_size, self.realtime_mode)
        dummy_server.board.current_player = current_pid

        self.active_worker = AIAgentWorker(agent, dummy_server, current_pid, max_retries=3, realtime_mode=self.realtime_mode)
        self.active_worker.move_ready.connect(self.on_worker_move_ready)
        self.active_worker.failed.connect(self.on_worker_failed)
        self.active_worker.start()

    def on_worker_move_ready(self, player_id: int, action: dict, thought: str, elapsed: float):
        self.thought_streamer.update_player_status(player_id, False)

        atype = action.get("type", "unknown")
        if atype == "place":
            summary = f"Colocar {action.get('stone_type', 'PRISM')} en ({action.get('x')}, {action.get('y')})"
        elif atype == "rotate":
            summary = f"Girar piedra en ({action.get('x')}, {action.get('y')}) a {action.get('angle')}°"
        elif atype == "laser":
            summary = f"Disparar LÁSER desde ({action.get('x')}, {action.get('y')}) dir ({action.get('dx')}, {action.get('dy')})"
        elif atype == "move":
            summary = f"Mover desde ({action.get('from_x')}, {action.get('from_y')}) hasta ({action.get('to_x')}, {action.get('to_y')})"
        elif atype == "curve_move":
            summary = f"Curva Bézier hacia ({action.get('end_x')}, {action.get('end_y')})"
        elif atype == "select":
            summary = f"Selección en {action.get('positions', [])}"
        else:
            summary = f"Acción: {atype}"

        self.thought_streamer.append_thought(
            player_id,
            self.agents[player_id].model_name,
            thought if thought else "Estrategia ejecutada según el playbook activo.",
            summary,
            elapsed
        )

        success = self.execute_ai_move(action)
        if not success:
            print(f"Movimiento {atype} rechazado por la UI, ejecutando fallback.")
            self._execute_fallback(player_id)

        self.turn_count += 1
        if self.max_turns and self.turn_count >= self.max_turns:
            print(f"=== Límite de {self.max_turns} turnos alcanzado ===")
            self.board.board_state.end_game_by_time()
            self.check_game_over()
            self.on_match_finished()
            return

        self.check_game_over()
        if not self.board.board_state.game_over and self.is_match_running:
            delay = 300 if self.realtime_mode else 1000
            self.schedule_next_turn(delay)

    def on_worker_failed(self, player_id: int, error_message: str):
        self.thought_streamer.update_player_status(player_id, False)
        print(f"Agente {player_id} falló: {error_message}")
        self.thought_streamer.append_thought(
            player_id,
            self.agents[player_id].model_name,
            f"Fallo en inferencia: {error_message}",
            "Ejecutando fallback de recuperación",
            0.0
        )
        self._execute_fallback(player_id)
        self.turn_count += 1
        if self.max_turns and self.turn_count >= self.max_turns:
            print(f"=== Límite de {self.max_turns} turnos alcanzado ===")
            self.board.board_state.end_game_by_time()
            self.check_game_over()
            self.on_match_finished()
            return

        self.check_game_over()
        if not self.board.board_state.game_over and self.is_match_running:
            delay = 300 if self.realtime_mode else 1000
            self.schedule_next_turn(delay)

    def _execute_fallback(self, player_id: int):
        dummy_server = DummyServer(self.board.board_state, self.board.grid_size, self.realtime_mode)
        valid_actions = dummy_server.get_valid_actions().get("valid_actions", [])
        if valid_actions:
            fb = random.choice(valid_actions)
            self.execute_ai_move(fb)
        else:
            self.handle_pass()

    def on_match_finished(self):
        self.is_match_running = False
        self.start_btn.setText("MATCH FINISHED")
        self.start_btn.setEnabled(False)
        print("Juego terminado. Guardando partida...")
        self.auto_save_game()

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
                if not self.realtime_mode:
                    self.board.end_turn()
                return True

            elif action_type == "select":
                positions = action.get("positions", [])
                valid_positions = []
                for p in positions:
                    if isinstance(p, list) and len(p) == 2:
                        valid_positions.append((p[0], p[1]))

                if valid_positions:
                    self.board.highlight_stones(valid_positions)
                    return True
                return False

            elif action_type == "pass":
                return False

            return False
        except Exception as e:
            print(f"Error ejecutando acción de IA: {e}")
            return False

    def handle_restart(self):
        self.stop_match()
        self.is_mcp_mode = False
        super().handle_restart()
        self.start_btn.setText("START AI MATCH")
        self.start_btn.setEnabled(True)
        if hasattr(self, 'mcp_mode_btn'):
            self.mcp_mode_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #6C5CE7; 
                    color: #FFFFFF;
                    font-weight: bold; 
                    font-size: 13px; 
                    padding: 10px;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #8172F5; }
            """)
        if hasattr(self, 'thought_streamer'):
            self.thought_streamer.log_text.clear()

    def handle_grid_size_change(self, new_size):
        super().handle_grid_size_change(new_size)
        if self.board.board_state.grid_size == new_size:
            self.stop_match()
            self.start_btn.setText("START AI MATCH")

    def handle_infinite_score_change(self, enabled):
        super().handle_infinite_score_change(enabled)
        self.controls.pass_btn.setEnabled(not enabled)

    def handle_logging_toggle(self, state):
        is_enabled = (state == 2)
        if hasattr(self, 'logger'):
            self.logger.enabled = is_enabled

    def auto_save_game(self):
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

    def closeEvent(self, event):
        self.is_match_running = False
        if self.active_worker and self.active_worker.isRunning():
            self.active_worker.abort()
            self.active_worker.wait(1000)
        if hasattr(self, 'live_bridge') and self.live_bridge:
            self.live_bridge.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GoLuminamics AI Arena")
    parser.add_argument("--p1", type=str, default="gemma3:4b", help="Model for Player 1")
    parser.add_argument("--p2", type=str, default="gemma3:4b", help="Model for Player 2")
    parser.add_argument("--single-strategy", action="store_true", help="If set, AI selects ONE random strategy instead of all.")

    parser.add_argument("--auto-start", action="store_true", help="Start match automatically on launch")
    parser.add_argument("--max-turns", type=int, default=0, help="Max turns before ending (0 for infinite)")

    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background-color: #202025; }
        QWidget { color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    """)

    use_all = not args.single_strategy
    window = ArenaWindow(args.p1, args.p2, use_all_playbooks=use_all, max_turns=args.max_turns)
    window.show()

    if args.auto_start:
        QTimer.singleShot(600, window.start_match)

    sys.exit(app.exec())
