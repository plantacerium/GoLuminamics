#!/usr/bin/env python3
"""
GoLuminamics Native MCP Server
------------------------------
Permite a Agentes AI (como Antigravity, Claude Desktop o bots autónomos)
interactuar, jugar, simular ópticas láser y consultar tácticas en GoLuminamics.

Protocolo: Model Context Protocol (MCP 2.x) vía stdio transport.
"""

import os
import sys
import json
import math
import glob
from typing import Optional, List, Dict, Any

# Asegurar importación de módulos del proyecto
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from mcp.server.mcpserver import MCPServer
from _01_core_logic.board_state import BoardState2D, StoneType
from _02_engines.laser import LaserCalculator2D
from _00_entry.live_bridge import LiveBridgeClient
from _02_engines.mcts import MCTSEngine

# Instancia del servidor MCP
server = MCPServer(
    name="goluminamics",
    version="1.0.0",
    description="Servidor MCP nativo para el juego de estrategia óptica GoLuminamics."
)

# Estado global de la partida activa
class GameSession:
    def __init__(self, grid_size: int = 9, starting_energy: int = 10, infinite_energy: bool = False, infinite_score: bool = False):
        self.grid_size = grid_size
        self.starting_energy = starting_energy
        self.infinite_energy = infinite_energy
        self.infinite_score = infinite_score
        self.current_player = 1
        self.turn_count = 0
        self.laser_calc = LaserCalculator2D(grid_size=grid_size)
        self.board = BoardState2D(
            grid_size=grid_size,
            starting_energy=starting_energy,
            infinite_energy=infinite_energy,
            infinite_score=infinite_score
        )
        self.history = []

    def reset(self, grid_size: int = None):
        if grid_size is not None:
            self.grid_size = grid_size
            self.laser_calc = LaserCalculator2D(grid_size=grid_size)
        self.current_player = 1
        self.turn_count = 0
        self.board = BoardState2D(
            grid_size=self.grid_size,
            starting_energy=self.starting_energy,
            infinite_energy=self.infinite_energy,
            infinite_score=self.infinite_score
        )
        self.history.clear()

session = GameSession()


def _render_ascii_board(board: BoardState2D, grid_size: int) -> str:
    """Genera representación visual ASCII del tablero."""
    display = [['.' for _ in range(grid_size)] for _ in range(grid_size)]
    symbols = {"PRISM": "P", "MIRROR": "M", "SPLITTER": "S", "BLOCKER": "B"}

    for (x, y), stone in board.stones.items():
        char = symbols.get(stone.stone_type.name, "?")
        if stone.player == 2:
            char = char.lower()
        display[y][x] = char

    header = "    " + " ".join([f"{i:2d}" for i in range(grid_size)])
    separator = "   +" + "--" * grid_size + "-+"
    rows = [header, separator]
    for y in range(grid_size):
        row_str = f"{y:2d} | " + "  ".join(display[y]) + " |"
        rows.append(row_str)
    rows.append(separator)
    return "\n".join(rows)


# ==============================================================================
# HERRAMIENTAS MCP (@server.tool)
# ==============================================================================

@server.tool()
def luminamics_new_game(grid_size: int = 9, starting_energy: int = 10, infinite_energy: bool = False, infinite_score: bool = False) -> str:
    """Inicia una nueva partida de GoLuminamics con los parámetros indicados.
    
    Args:
        grid_size: Tamaño de la cuadrícula (ej. 9, 13, 19). Por defecto 9x9 para juego rápido.
        starting_energy: Energía inicial por jugador (por defecto 10).
        infinite_energy: Si es True, las acciones no consumen energía.
        infinite_score: Si es True, deshabilita la regla de misericordia por diferencia de puntos.
    """
    global session
    session = GameSession(grid_size, starting_energy, infinite_energy, infinite_score)
    return f"Nueva partida iniciada ({grid_size}x{grid_size}). Es el turno del Jugador 1."


@server.tool()
def luminamics_get_board_state() -> str:
    """Obtiene el estado completo y visual del tablero de GoLuminamics actual.
    
    Si la UI gráfica está abierta en pantalla, devuelve directamente el estado en vivo.
    """
    if LiveBridgeClient.is_ui_alive():
        try:
            live = LiveBridgeClient.get_ui_state()
            grid_size = live["grid_size"]
            current_player = live["current_player"]
            scores = live["scores"]
            energy = live["energy"]
            stones = live["stones"]
            game_over = live["game_over"]
            winner = live["winner"]
            reason = live["victory_reason"]

            display = [['.' for _ in range(grid_size)] for _ in range(grid_size)]
            symbols = {"PRISM": "P", "MIRROR": "M", "SPLITTER": "S", "BLOCKER": "B"}
            p1_stones = []
            p2_stones = []

            for key, s in stones.items():
                x, y = map(int, key.split(','))
                st_name = s["type"]
                char = symbols.get(st_name, "?")
                if s["player"] == 2:
                    char = char.lower()
                display[y][x] = char
                info = f"{st_name} en ({x}, {y}) rot={s['rotation']:.1f}°"
                if s["player"] == 1:
                    p1_stones.append(info)
                else:
                    p2_stones.append(info)

            header = "    " + " ".join([f"{i:2d}" for i in range(grid_size)])
            separator = "   +" + "--" * grid_size + "-+"
            rows = [header, separator]
            for y in range(grid_size):
                row_str = f"{y:2d} | " + "  ".join(display[y]) + " |"
                rows.append(row_str)
            rows.append(separator)
            ascii_grid = "\n".join(rows)

            return f"""=== GOLUMINAMICS ESTADO [EN VIVO EN PANTALLA] (Turno de Jugador {current_player}) ===
{ascii_grid}

Piezas Jugador 1 (MAYÚSCULAS P, M, S, B):
{chr(10).join(['  - ' + s for s in p1_stones]) if p1_stones else '  (Ninguna)'}

Piezas Jugador 2 (minúsculas p, m, s, b):
{chr(10).join(['  - ' + s for s in p2_stones]) if p2_stones else '  (Ninguna)'}

Resumen en Vivo:
  - Jugador 1: {scores.get('player1', 0) + scores.get('player1_captures', 0) * 2} pts (Territorio: {scores.get('player1', 0)}, Capturas: {scores.get('player1_captures', 0)}, Energía: {energy.get('player1', 0)})
  - Jugador 2: {scores.get('player2', 0) + scores.get('player2_captures', 0) * 2} pts (Territorio: {scores.get('player2', 0)}, Capturas: {scores.get('player2_captures', 0)}, Energía: {energy.get('player2', 0)})
  - Territorio en disputa: {scores.get('contested', 0)} pts
  - Estado: {"PARTIDA TERMINADA - Ganador: Jugador " + str(winner) + " (" + str(reason) + ")" if game_over else "En curso (Sincronizado con UI)"}
"""
        except Exception as e:
            pass  # Fallback a headless
    board = session.board
    score = board.calculate_score()
    p1_stones = []
    p2_stones = []

    for pos, stone in board.stones.items():
        info = f"{stone.stone_type.name} en {pos} rot={stone.rotation_angle:.1f}°"
        if stone.player == 1:
            p1_stones.append(info)
        else:
            p2_stones.append(info)

    ascii_grid = _render_ascii_board(board, session.grid_size)

    state_dict = {
        "turn": session.turn_count,
        "current_player": session.current_player,
        "game_over": board.game_over,
        "winner": board.winner,
        "victory_reason": board.victory_reason,
        "scores": {
            "player1_territory": score["player1"],
            "player1_captures": board.get_captures(1),
            "player1_total": score["player1"] + board.get_captures(1) * 2,
            "player2_territory": score["player2"],
            "player2_captures": board.get_captures(2),
            "player2_total": score["player2"] + board.get_captures(2) * 2,
            "contested_territory": score["contested"]
        },
        "energy": {
            "player1": board.get_energy(1),
            "player2": board.get_energy(2)
        },
        "stones_count": {
            "player1": len(p1_stones),
            "player2": len(p2_stones)
        }
    }

    report = f"""=== GOLUMINAMICS ESTADO (Turno {session.turn_count} | Turno de Jugador {session.current_player}) ===
{ascii_grid}

Piezas Jugador 1 (MAYÚSCULAS P, M, S, B):
{chr(10).join(['  - ' + s for s in p1_stones]) if p1_stones else '  (Ninguna)'}

Piezas Jugador 2 (minúsculas p, m, s, b):
{chr(10).join(['  - ' + s for s in p2_stones]) if p2_stones else '  (Ninguna)'}

Resumen de Puntuación:
  - Jugador 1: {state_dict['scores']['player1_total']} pts (Territorio: {score['player1']}, Capturas: {board.get_captures(1)}, Energía: {board.get_energy(1)})
  - Jugador 2: {state_dict['scores']['player2_total']} pts (Territorio: {score['player2']}, Capturas: {board.get_captures(2)}, Energía: {board.get_energy(2)})
  - Territorio en disputa: {score['contested']} pts
  - Estado: {"PARTIDA TERMINADA - Ganador: Jugador " + str(board.winner) + " (" + board.victory_reason + ")" if board.game_over else "En curso"}
"""
    return report


@server.tool()
def luminamics_simulate_laser(x: float, y: float, dx: float, dy: float, player: int = 0) -> str:
    """Simula el disparo de un haz láser SIN modificar el tablero de juego.
    
    Permite al agente probar trayectorias, observar rebotes, predecir qué piezas
    serían capturadas y cuántas intersecciones iluminaría antes de jugar.
    
    Args:
        x: Coordenada X de origen (puede ser borde -1, grid_size, o posición de pieza).
        y: Coordenada Y de origen.
        dx: Vector de dirección en X (ej. 1.0, 0.0, -0.707).
        dy: Vector de dirección en Y (ej. 0.0, 1.0, 0.707).
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
    """
    target_player = player if player in (1, 2) else session.current_player
    norm = math.sqrt(dx**2 + dy**2)
    if norm == 0:
        return "Error: Vector de dirección nulo."
    dir_norm = (dx / norm, dy / norm)

    paths = session.laser_calc.calculate_path((float(x), float(y)), dir_norm, session.board.stones)
    unique_points = session.laser_calc.get_unique_points(paths)

    # Identificar posibles capturas hipotéticas
    potential_captures = []
    for path in paths:
        for pt in path:
            grid_pos = (int(round(pt[0])), int(round(pt[1])))
            stone = session.board.get_stone_at(grid_pos)
            if stone and stone.player != target_player and grid_pos not in potential_captures:
                potential_captures.append((grid_pos, stone.stone_type.name, stone.player))

    res = {
        "player": target_player,
        "origin": [x, y],
        "direction": [dir_norm[0], dir_norm[1]],
        "paths_count": len(paths),
        "intersections_illuminated": len(unique_points),
        "illuminated_points_sample": list(unique_points)[:15],
        "potential_captures": [{"pos": c[0], "type": c[1], "owner": c[2]} for c in potential_captures],
        "projected_points_gain": len(unique_points) + len(potential_captures) * 2
    }
    return json.dumps(res, indent=2)


@server.tool()
def luminamics_place_stone(x: int, y: int, stone_type: str = "PRISM", rotation: float = 0.0, player: int = 0, thought: str = "") -> str:
    """Coloca una ficha en la intersección indicada y rota hacia el ángulo dado.
    
    Si la UI en pantalla está abierta, la pieza se colocará y animará en vivo.
    
    Args:
        x: Coordenada horizontal (0 a grid_size-1).
        y: Coordenada vertical (0 a grid_size-1).
        stone_type: Tipo de ficha: 'PRISM', 'MIRROR', 'SPLITTER' o 'BLOCKER'.
        rotation: Ángulo de rotación de la pieza (0 a 360 grados).
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
        thought: Pensamiento opcional de Antigravity para mostrar en el HUD de la UI.
    """
    if LiveBridgeClient.is_ui_alive():
        res = LiveBridgeClient.send_action_to_ui({
            "type": "place", "x": x, "y": y, "stone_type": stone_type,
            "rotation": rotation, "player": player, "thought": thought
        })
        if res.get("success"):
            return f"✅ [EN VIVO EN PANTALLA] {res.get('message', 'Ficha colocada con éxito')}"
        return f"❌ Error en UI: {res.get('error', res.get('message'))}"
    target_player = player if player in (1, 2) else session.current_player
    st_upper = stone_type.upper()
    if st_upper not in ("PRISM", "MIRROR", "SPLITTER", "BLOCKER"):
        return f"Error: Tipo de ficha desconocido '{stone_type}'. Tipos válidos: PRISM, MIRROR, SPLITTER, BLOCKER."

    if not session.board.has_energy(target_player, 1):
        return f"Error: El Jugador {target_player} no tiene suficiente energía para colocar una ficha."

    pos = (x, y)
    success = session.board.place_stone(pos, st_upper, target_player)
    if not success:
        return f"Error: No se pudo colocar en {pos}. La casilla puede estar ocupada o fuera de límites."

    if rotation != 0.0:
        session.board.set_rotation_to(pos, rotation)

    session.board.end_turn(target_player)
    session.turn_count += 1
    session.current_player = 3 - target_player
    session.board.check_victory_condition()

    return f"Éxito: Jugador {target_player} colocó {st_upper} en {pos} con rotación {rotation}°. Ahora es el turno del Jugador {session.current_player}."


@server.tool()
def luminamics_rotate_stone(x: int, y: int, angle: float, player: int = 0, thought: str = "") -> str:
    """Rota una ficha existente que pertenezca al jugador activo.
    
    Si la UI en pantalla está abierta, rotará en vivo.
    
    Args:
        x: Coordenada horizontal.
        y: Coordenada vertical.
        angle: Nuevo ángulo absoluto en grados (0 a 360 grados).
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
        thought: Pensamiento opcional de Antigravity para mostrar en el HUD de la UI.
    """
    if LiveBridgeClient.is_ui_alive():
        res = LiveBridgeClient.send_action_to_ui({
            "type": "rotate", "x": x, "y": y, "angle": angle,
            "player": player, "thought": thought
        })
        if res.get("success"):
            return f"✅ [EN VIVO EN PANTALLA] {res.get('message', 'Ficha rotada con éxito')}"
        return f"❌ Error en UI: {res.get('error', res.get('message'))}"
    target_player = player if player in (1, 2) else session.current_player
    pos = (x, y)
    stone = session.board.get_stone_at(pos)
    if not stone:
        return f"Error: No hay ninguna ficha en {pos}."
    if stone.player != target_player:
        return f"Error: La ficha en {pos} pertenece al Jugador {stone.player}, no al Jugador {target_player}."

    session.board.set_rotation_to(pos, angle)
    session.board.end_turn(target_player)
    session.turn_count += 1
    session.current_player = 3 - target_player
    session.board.check_victory_condition()

    return f"Éxito: Ficha {stone.stone_type.name} en {pos} rotada a {angle:.1f}°. Turno del Jugador {session.current_player}."


@server.tool()
def luminamics_shoot_laser(x: float, y: float, dx: float, dy: float, player: int = 0, thought: str = "") -> str:
    """Dispara un haz láser real, ilumina territorio y captura piezas enemigas en su trayectoria.
    
    Si la UI en pantalla está abierta, el haz láser se disparará en vivo con efectos visuales.
    
    Args:
        x: Coordenada X de origen.
        y: Coordenada Y de origen.
        dx: Dirección en X.
        dy: Dirección en Y.
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
        thought: Pensamiento opcional de Antigravity para mostrar en el HUD de la UI.
    """
    if LiveBridgeClient.is_ui_alive():
        res = LiveBridgeClient.send_action_to_ui({
            "type": "laser", "x": x, "y": y, "dx": dx, "dy": dy,
            "player": player, "thought": thought
        })
        if res.get("success"):
            return f"✅ [EN VIVO EN PANTALLA] {res.get('message', 'Láser disparado con éxito')}"
        return f"❌ Error en UI: {res.get('error', res.get('message'))}"
    target_player = player if player in (1, 2) else session.current_player
    norm = math.sqrt(dx**2 + dy**2)
    if norm == 0:
        return "Error: Vector de dirección nulo."
    dir_norm = (dx / norm, dy / norm)

    start_pos = (float(x), float(y))
    paths = session.laser_calc.calculate_path(start_pos, dir_norm, session.board.stones)
    session.board.add_laser_source(start_pos, dir_norm, target_player)
    captures = session.board.process_laser_captures(target_player, paths)

    score_data = session.board.calculate_score()
    session.board.end_turn(target_player)
    session.turn_count += 1
    session.current_player = 3 - target_player
    session.board.check_victory_condition()

    return f"Láser disparado por Jugador {target_player} desde {start_pos}. Piezas capturadas: {len(captures)} {captures}. Territorio Jugador {target_player}: {score_data[target_player]}. Ahora es turno del Jugador {session.current_player}."


@server.tool()
def luminamics_move_stone(from_x: int, from_y: int, to_x: int, to_y: int, player: int = 0, thought: str = "") -> str:
    """Mueve una ficha a una posición vecina con soporte para envoltura toroidal (wrap-around).
    
    Si la UI en pantalla está abierta, la pieza se desplazará visualmente en vivo.
    
    Args:
        from_x: X origen.
        from_y: Y origen.
        to_x: X destino.
        to_y: Y destino.
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
        thought: Pensamiento opcional de Antigravity para mostrar en el HUD de la UI.
    """
    if LiveBridgeClient.is_ui_alive():
        res = LiveBridgeClient.send_action_to_ui({
            "type": "move", "from_x": from_x, "from_y": from_y,
            "to_x": to_x, "to_y": to_y, "player": player, "thought": thought
        })
        if res.get("success"):
            return f"✅ [EN VIVO EN PANTALLA] {res.get('message', 'Ficha movida con éxito')}"
        return f"❌ Error en UI: {res.get('error', res.get('message'))}"
    target_player = player if player in (1, 2) else session.current_player
    from_pos = (from_x, from_y)
    to_pos = (to_x, to_y)

    stone = session.board.get_stone_at(from_pos)
    if not stone or stone.player != target_player:
        return f"Error: No tienes una ficha propia en {from_pos}."

    wrapped = session.board.move_stone(from_pos, to_pos)
    if wrapped is None:
        return f"Error: Movimiento inválido de {from_pos} a {to_pos} (casilla ocupada)."

    session.board.end_turn(target_player)
    session.turn_count += 1
    session.current_player = 3 - target_player
    return f"Ficha movida con éxito de {from_pos} a {wrapped}. Turno del Jugador {session.current_player}."


@server.tool()
def luminamics_curve_move_stone(from_x: int, from_y: int, control_x: float, control_y: float, end_x: int, end_y: int, player: int = 0) -> str:
    """Mueve una ficha a lo largo de una curva de Bézier cuadrática hacia el destino final.
    
    Args:
        from_x: X origen.
        from_y: Y origen.
        control_x: Punto de control X de la curva Bézier.
        control_y: Punto de control Y de la curva Bézier.
        end_x: X destino final.
        end_y: Y destino final.
        player: ID del jugador (1 o 2).
    """
    target_player = player if player in (1, 2) else session.current_player
    from_pos = (from_x, from_y)
    control_points = [(control_x, control_y), (end_x, end_y)]

    stone = session.board.get_stone_at(from_pos)
    if not stone or stone.player != target_player:
        return f"Error: No tienes una ficha propia en {from_pos}."

    final_pos = session.board.move_stone_along_curve(from_pos, control_points, target_player)
    if final_pos is None:
        return f"Error: Movimiento curvo bloqueado hacia {end_x},{end_y}."

    session.board.end_turn(target_player)
    session.turn_count += 1
    session.current_player = 3 - target_player
    return f"Ficha desplazada en trayectoria curva a {final_pos}. Turno del Jugador {session.current_player}."


@server.tool()
def luminamics_pass_turn(player: int = 0, thought: str = "") -> str:
    """Pasa el turno actual. Dos pases consecutivos finalizan la partida por conteo de puntos.
    
    Si la UI en pantalla está abierta, se actualizará el turno en vivo.
    
    Args:
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
        thought: Pensamiento opcional de Antigravity para mostrar en el HUD de la UI.
    """
    if LiveBridgeClient.is_ui_alive():
        res = LiveBridgeClient.send_action_to_ui({
            "type": "pass", "player": player, "thought": thought
        })
        if res.get("success"):
            return f"✅ [EN VIVO EN PANTALLA] {res.get('message', 'Pase de turno')}"
        return f"❌ Error en UI: {res.get('error', res.get('message'))}"
    target_player = player if player in (1, 2) else session.current_player
    game_ended = session.board.pass_turn(target_player)
    session.turn_count += 1
    session.current_player = 3 - target_player

    if game_ended:
        return f"Jugador {target_player} pasó su turno. ¡Ambos jugadores han pasado! Partida terminada. Ganador: Jugador {session.board.winner} ({session.board.victory_reason})."
    return f"Jugador {target_player} pasó su turno. Ahora es el turno del Jugador {session.current_player}."


@server.tool()
def luminamics_get_valid_actions(player: int = 0, sample_size: int = 15) -> str:
    """Devuelve un conjunto variado de jugadas legales (colocaciones, rotaciones, tiros láser y pases).
    
    Args:
        player: ID del jugador (1 o 2).
        sample_size: Número máximo de ejemplos de colocación a listar.
    """
    target_player = player if player in (1, 2) else session.current_player
    board = session.board
    grid_size = session.grid_size
    valid = []

    # Opciones de colocación
    empty = [(x, y) for y in range(grid_size) for x in range(grid_size) if (x, y) not in board.stones]
    sampled = random.sample(empty, min(sample_size, len(empty))) if empty else []
    for (x, y) in sampled:
        for st in ["PRISM", "MIRROR", "SPLITTER", "BLOCKER"]:
            valid.append({"type": "place", "x": x, "y": y, "stone_type": st})

    # Opciones de rotación y láser
    for pos, stone in board.stones.items():
        if stone.player == target_player:
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                valid.append({"type": "rotate", "x": pos[0], "y": pos[1], "angle": angle})
            for direction in range(8):
                rad = direction * math.pi / 4
                valid.append({
                    "type": "laser",
                    "x": pos[0], "y": pos[1],
                    "dx": round(math.cos(rad), 3),
                    "dy": round(math.sin(rad), 3)
                })

    valid.append({"type": "pass"})
    return json.dumps({"player": target_player, "total_sample_actions": len(valid), "actions": valid}, indent=2)


@server.tool()
def luminamics_list_playbooks(query: str = "") -> str:
    """Lista las estrategias y playbooks tácticos disponibles para GoLuminamics.
    
    Args:
        query: Término de búsqueda opcional para filtrar nombres de estrategias.
    """
    playbook_dir = os.path.join(WORKSPACE_DIR, "_02_engines", "playbooks")
    if not os.path.exists(playbook_dir):
        return "No se encontró el directorio de playbooks."

    files = [f for f in os.listdir(playbook_dir) if f.endswith(".md")]
    if query:
        files = [f for f in files if query.lower() in f.lower()]

    playbooks = [f.replace(".md", "") for f in files]
    return json.dumps({"count": len(playbooks), "playbooks": sorted(playbooks)}, indent=2)


@server.tool()
def luminamics_read_playbook(name: str) -> str:
    """Lee y devuelve el contenido completo de una estrategia o playbook específico.
    
    Args:
        name: Nombre del playbook (ej. 'The_Beam_Surgeon', 'The_Photon_Cage').
    """
    clean_name = name.replace(".md", "") + ".md"
    path = os.path.join(WORKSPACE_DIR, "_02_engines", "playbooks", clean_name)
    if not os.path.exists(path):
        return f"Error: No existe el playbook '{name}'. Usa luminamics_list_playbooks para ver los disponibles."

    with open(path, "r", encoding="utf-8") as f:
        return f.read()




@server.tool()
def luminamics_mcts_recommend_move(player: int = 0, simulations: int = 350) -> str:
    """Ejecuta el motor Monte Carlo Tree Search (MCTS) con poda óptica sobre el tablero actual
    y devuelve la mejor jugada calculada matemáticamente junto con las estadísticas de exploración.
    
    Args:
        player: ID del jugador (1 o 2). Si es 0, usa el jugador activo.
        simulations: Cantidad de simulaciones a explorar (100 a 2000). Por defecto 350.
    """
    target_player = player if player in (1, 2) else session.current_player
    board_to_search = session.board
    grid_size = session.grid_size

    # Si la UI está viva, reconstruir el tablero exacto de la UI para buscar sobre él
    if LiveBridgeClient.is_ui_alive():
        try:
            live = LiveBridgeClient.get_ui_state()
            grid_size = live["grid_size"]
            target_player = player if player in (1, 2) else live["current_player"]
            
            temp_board = BoardState2D(grid_size)
            for pos_str, s_info in live["stones"].items():
                x, y = map(int, pos_str.split(","))
                temp_board.place_stone((x, y), s_info["type"], s_info["player"])
                temp_board.set_rotation_to((x, y), s_info["rotation"])
            for src in live.get("laser_sources", []):
                temp_board.add_laser_source(tuple(src[0]), tuple(src[1]), src[2])
            board_to_search = temp_board
        except Exception:
            pass

    engine = MCTSEngine(grid_size)
    best_action, stats = engine.search(board_to_search, player=target_player, simulations=simulations)

    act_type = best_action.get("type", "pass").upper()
    summary = f"🌲 RECOMENDACIÓN MCTS ÓPTICO (Jugador {target_player}):\n"
    summary += f"  - Acción recomendada: {act_type}\n"
    if act_type == "PLACE":
        summary += f"    Ficha: {best_action.get('stone_type')} en ({best_action.get('x')}, {best_action.get('y')}) rot={best_action.get('rotation')}°\n"
    elif act_type == "ROTATE":
        summary += f"    Pieza en ({best_action.get('x')}, {best_action.get('y')}) rotar a {best_action.get('angle')}°\n"
    elif act_type == "LASER":
        summary += f"    Disparar desde ({best_action.get('x')}, {best_action.get('y')}) dirección ({best_action.get('dx')}, {best_action.get('dy')})\n"
    elif act_type == "PASS":
        summary += "    Pase de turno estratégico.\n"

    summary += f"  - Simulaciones: {stats['simulations_completed']} exploradas en {stats['elapsed_seconds']}s ({stats['simulations_per_sec']} sims/s)\n"
    summary += f"  - Visitas de la mejor jugada: {stats['best_action_visits']} | Valor esperado (Q): {stats['best_action_value']:+.3f}\n"
    summary += "  - Top alternativas evaluadas:\n"
    for idx, cand in enumerate(stats['top_candidates'][:3], 1):
        summary += f"    {idx}. {cand['action']} (visitas: {cand['visits']}, valor: {cand['expected_value']:+.3f})\n"

    summary += f"\nJSON Jugada: {json.dumps(best_action)}"
    return summary


# ==============================================================================
# RECURSOS MCP (@server.resource)
# ==============================================================================

@server.resource("luminamics://rules")
def get_rules_resource() -> str:
    """Devuelve las reglas oficiales completas de GoLuminamics (MECHANICS.md)."""
    mechanics_path = os.path.join(WORKSPACE_DIR, "MECHANICS.md")
    if os.path.exists(mechanics_path):
        with open(mechanics_path, "r", encoding="utf-8") as f:
            return f.read()
    return "MECHANICS.md no disponible."


@server.resource("luminamics://state/ascii")
def get_ascii_resource() -> str:
    """Devuelve la vista ASCII actual del tablero."""
    return _render_ascii_board(session.board, session.grid_size)


# ==============================================================================
# PROMPTS MCP (@server.prompt)
# ==============================================================================

@server.prompt("luminamics_tactical_coach")
def tactical_coach_prompt() -> str:
    """Instruye al modelo para actuar como Gran Maestro y Asesor Táctico de GoLuminamics."""
    return """Eres el Gran Maestro Táctico de GoLuminamics.
Tu misión es asistir al jugador a ganar la partida mediante la física óptica y el control de territorio:
1. Analiza el tablero actual usando `luminamics_get_board_state()`.
2. Explora simulaciones de líneas láser con `luminamics_simulate_laser()` para encontrar capturas y áreas de luz máxima.
3. Sugiere colocaciones de prismas y rotaciones de espejos que creen trampas de fuego cruzado o redes reflectoras.
4. Explica con claridad la razón táctica detrás de cada movimiento sugerido."""


def main():
    """Ejecuta el servidor MCP sobre stdio."""
    server.run()


if __name__ == "__main__":
    main()
