"""
Live UI Bridge for GoLuminamics
-------------------------------
Permite la sincronización bidireccional en tiempo real entre la interfaz gráfica
(PySide6) visible en pantalla y el servidor MCP (Antigravity / Agentes AI).
"""

import os
import sys
import json
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from PySide6.QtCore import QObject, Signal

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 18989


class BridgeRequestHandler(BaseHTTPRequestHandler):
    """Maneja las peticiones HTTP locales entrantes desde el servidor MCP hacia la UI."""
    bridge_server = None  # Asignado dinámicamente

    def do_GET(self):
        if self.path == "/status":
            data = self.bridge_server.get_status()
            self._send_json(200, data)
        elif self.path == "/state":
            data = self.bridge_server.get_live_state()
            self._send_json(200, data)
        else:
            self._send_json(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path == "/action":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                action_data = json.loads(body)
                result = self.bridge_server.dispatch_action_sync(action_data)
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})
        else:
            self._send_json(404, {"error": "Ruta no encontrada"})

    def _send_json(self, code: int, payload: dict):
        try:
            body = json.dumps(payload).encode('utf-8')
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def log_message(self, format, *args):
        # Silenciar ruido en consola
        pass


class LiveUIBridge(QObject):
    """Servidor local embebido en la ventana Qt para recibir jugadas de Antigravity MCP."""
    action_received = Signal(dict, object)  # (action_dict, response_holder)

    def __init__(self, main_window, host=BRIDGE_HOST, port=BRIDGE_PORT):
        super().__init__()
        self.main_window = main_window
        self.host = host
        self.port = port
        self.http_server = None
        self.server_thread = None
        self.is_running = False

        # Conectar señal a la ejecución en el hilo principal de Qt
        self.action_received.connect(self._handle_action_on_main_thread)

    def start(self):
        """Inicia el servidor HTTP local en un hilo secundario."""
        try:
            handler_class = BridgeRequestHandler
            handler_class.bridge_server = self
            self.http_server = HTTPServer((self.host, self.port), handler_class)
            self.server_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
            self.server_thread.start()
            self.is_running = True
            print(f"[LiveUIBridge] Puente activo en http://{self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[LiveUIBridge] No se pudo iniciar el puente en puerto {self.port}: {e}")
            return False

    def stop(self):
        """Detiene el servidor HTTP."""
        if self.http_server:
            try:
                self.http_server.shutdown()
                self.http_server.server_close()
            except Exception:
                pass
            self.is_running = False

    def get_status(self) -> dict:
        """Devuelve estado de conexión de la UI."""
        return {
            "status": "online",
            "ui_window": self.main_window.__class__.__name__,
            "grid_size": self.main_window.board.grid_size,
            "current_player": self.main_window.board.current_player,
            "game_over": self.main_window.board.board_state.game_over
        }

    def get_live_state(self) -> dict:
        """Serializa el estado visual exacto del tablero actual."""
        board = self.main_window.board.board_state
        scores = board.calculate_score()
        return {
            "grid_size": self.main_window.board.grid_size,
            "current_player": self.main_window.board.current_player,
            "game_over": board.game_over,
            "winner": board.winner,
            "victory_reason": board.victory_reason,
            "stones": {
                f"{pos[0]},{pos[1]}": {
                    "type": s.stone_type.name,
                    "player": s.player,
                    "rotation": s.rotation_angle
                }
                for pos, s in board.stones.items()
            },
            "scores": {
                "player1": scores.get("player1", 0),
                "player2": scores.get("player2", 0),
                "contested": scores.get("contested", 0),
                "player1_captures": board.get_captures(1),
                "player2_captures": board.get_captures(2)
            },
            "energy": {
                "player1": board.get_energy(1),
                "player2": board.get_energy(2)
            },
            "laser_sources": [
                [list(s[0]), list(s[1]), s[2]] for s in board.laser_sources
            ]
        }

    def dispatch_action_sync(self, action_data: dict) -> dict:
        """Encola la acción en Qt y espera a que el hilo de interfaz la dibuje."""
        response_holder = {"done_event": threading.Event(), "success": False, "message": ""}
        self.action_received.emit(action_data, response_holder)
        # Esperar hasta 3 segundos a que Qt dibuje
        completed = response_holder["done_event"].wait(timeout=3.0)
        if completed:
            return {
                "success": response_holder["success"],
                "message": response_holder["message"],
                "live_state": self.get_live_state()
            }
        return {"success": False, "error": "Timeout esperando procesamiento de la UI"}

    def _handle_action_on_main_thread(self, action_data: dict, response_holder: dict):
        """Se ejecuta en el hilo principal de Qt para interactuar de forma segura con la GUI."""
        try:
            action_type = action_data.get("type", "").lower()
            thought = action_data.get("thought", "")
            mw = self.main_window

            success = False
            msg = ""

            if action_type == "place":
                x = int(action_data.get("x", 0))
                y = int(action_data.get("y", 0))
                st = action_data.get("stone_type", "PRISM").upper()
                rot = float(action_data.get("rotation", 0.0))
                p = int(action_data.get("player", mw.board.current_player))

                mw.controls.set_stone_type(st)
                if mw.board.place_stone((x, y), st, p, rotation=rot):
                    success = True
                    msg = f"Ficha {st} colocada en ({x}, {y}) rot={rot}° por P{p}"
                    if hasattr(mw, 'thought_streamer') and thought:
                        mw.thought_streamer.append_thought(p, "Antigravity MCP", thought, msg)

            elif action_type == "rotate":
                x = int(action_data.get("x", 0))
                y = int(action_data.get("y", 0))
                ang = float(action_data.get("angle", 0.0))
                p = int(action_data.get("player", mw.board.current_player))

                stone = mw.board.board_state.get_stone_at((x, y))
                if stone:
                    mw.board.rotate_stone_to((x, y), ang)
                    mw.on_stone_rotated((x, y), ang)
                    mw.board.end_turn()
                    success = True
                    msg = f"Ficha en ({x}, {y}) rotada a {ang}°"
                    if hasattr(mw, 'thought_streamer') and thought:
                        mw.thought_streamer.append_thought(p, "Antigravity MCP", thought, msg)

            elif action_type == "laser":
                x = float(action_data.get("x", 0.0))
                y = float(action_data.get("y", 0.0))
                dx = float(action_data.get("dx", 1.0))
                dy = float(action_data.get("dy", 0.0))
                p = int(action_data.get("player", mw.board.current_player))

                mw.handle_laser_mouse((x, y), (dx, dy), p)
                if hasattr(mw, 'realtime_mode') and not mw.realtime_mode:
                    mw.board.end_turn()
                success = True
                msg = f"Láser disparado desde ({x}, {y}) dir ({dx}, {dy}) por P{p}"
                if hasattr(mw, 'thought_streamer') and thought:
                    mw.thought_streamer.append_thought(p, "Antigravity MCP", thought, msg)

            elif action_type == "move":
                fx = int(action_data.get("from_x", 0))
                fy = int(action_data.get("from_y", 0))
                tx = int(action_data.get("to_x", 0))
                ty = int(action_data.get("to_y", 0))
                p = int(action_data.get("player", mw.board.current_player))

                from_pos = (fx, fy)
                to_pos = (tx, ty)
                stone = mw.board.board_state.get_stone_at(from_pos)
                if stone and stone.player == p:
                    wrapped = mw.board.board_state.move_stone(from_pos, to_pos)
                    if wrapped is not None:
                        mw.board.move_stone_visual(from_pos, wrapped)
                        mw.board.end_turn()
                        success = True
                        msg = f"Ficha movida de {from_pos} a {wrapped}"
                        if hasattr(mw, 'thought_streamer') and thought:
                            mw.thought_streamer.append_thought(p, "Antigravity MCP", thought, msg)

            elif action_type == "pass":
                mw.handle_pass()
                success = True
                msg = "Pase de turno ejecutado"
                if hasattr(mw, 'thought_streamer') and thought:
                    mw.thought_streamer.append_thought(mw.board.current_player, "Antigravity MCP", thought, msg)

            response_holder["success"] = success
            response_holder["message"] = msg
        except Exception as e:
            response_holder["success"] = False
            response_holder["message"] = str(e)
        finally:
            response_holder["done_event"].set()


# ==============================================================================
# CLIENTE MCP HELPER (Usado por mcp_server.py)
# ==============================================================================

class LiveBridgeClient:
    """Cliente para consultar o enviar jugadas a la ventana activa si está abierta."""
    @staticmethod
    def is_ui_alive(host=BRIDGE_HOST, port=BRIDGE_PORT) -> bool:
        try:
            req = urllib.request.Request(f"http://{host}:{port}/status", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("status") == "online"
        except Exception:
            return False

    @staticmethod
    def get_ui_state(host=BRIDGE_HOST, port=BRIDGE_PORT) -> dict:
        req = urllib.request.Request(f"http://{host}:{port}/state", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return json.loads(resp.read().decode('utf-8'))

    @staticmethod
    def send_action_to_ui(action: dict, host=BRIDGE_HOST, port=BRIDGE_PORT) -> dict:
        body = json.dumps(action).encode('utf-8')
        req = urllib.request.Request(
            f"http://{host}:{port}/action",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode('utf-8'))
