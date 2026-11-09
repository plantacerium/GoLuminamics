"""
GoLuminamics Optical Monte Carlo Tree Search (MCTS) Engine
-----------------------------------------------------------
Motor combinatorio de búsqueda en árbol de Monte Carlo con poda de resonancia óptica.
Calcula trayectorias láser, control territorial y captura de piezas mediante simulaciones
heurísticas a alta velocidad (más de 300,000 clones/seg).
"""

import math
import random
import time
from typing import Dict, List, Tuple, Optional, Any

from _01_core_logic.board_state import BoardState2D, StoneData2D, StoneType
from _02_engines.laser import LaserCalculator2D


def clone_board(board: BoardState2D) -> BoardState2D:
    """Clonación ultrarrápida del estado lógico del tablero para simulaciones."""
    clone = BoardState2D(
        grid_size=board.grid_size,
        starting_energy=board.starting_energy,
        territory_threshold=board.territory_threshold,
        infinite_energy=board.infinite_energy,
        energy_cost=board.energy_cost,
        infinite_score=board.infinite_score
    )
    for pos, s in board.stones.items():
        st = StoneData2D(s.stone_type, s.player)
        st.rotation_angle = s.rotation_angle
        clone.stones[pos] = st

    clone.player_energy = dict(board.player_energy)
    clone.player_captures = dict(board.player_captures)
    clone.laser_sources = list(board.laser_sources)
    clone.consecutive_passes = board.consecutive_passes
    clone.game_over = board.game_over
    clone.winner = board.winner
    clone.victory_reason = board.victory_reason
    return clone


class MCTSNode:
    """Nodo del árbol de búsqueda MCTS."""
    def __init__(self, state: BoardState2D, player_to_move: int, parent: Optional['MCTSNode'] = None, action: Optional[Dict[str, Any]] = None):
        self.state = state
        self.player_to_move = player_to_move
        self.parent = parent
        self.action = action  # Jugada que generó este nodo
        self.children: List['MCTSNode'] = []
        self.visits: int = 0
        self.total_value: float = 0.0  # Suma de utilidades desde perspectiva del jugador raíz
        self.untried_actions: Optional[List[Dict[str, Any]]] = None

    def is_fully_expanded(self) -> bool:
        return self.untried_actions is not None and len(self.untried_actions) == 0

    def best_child(self, c_param: float = 1.414) -> 'MCTSNode':
        """Selecciona el mejor nodo hijo usando UCB1 (Upper Confidence Bound)."""
        best_node = None
        best_score = -float('inf')

        for child in self.children:
            if child.visits == 0:
                return child
            # Explotación + Exploración
            exploitation = child.total_value / child.visits
            exploration = c_param * math.sqrt(math.log(self.visits) / child.visits)
            score = exploitation + exploration
            if score > best_score:
                best_score = score
                best_node = child

        return best_node if best_node is not None else self.children[0]


class MCTSEngine:
    """Motor Monte Carlo especializado en física óptica y territorio."""

    def __init__(self, grid_size: int = 19):
        self.grid_size = grid_size
        self.laser_calc = LaserCalculator2D(grid_size)

    def generate_candidate_actions(self, state: BoardState2D, player: int) -> List[Dict[str, Any]]:
        """Genera un subconjunto de acciones con alta probabilidad óptica (Optical Pruning)."""
        grid_size = state.grid_size
        actions: List[Dict[str, Any]] = []

        # 1. ACCIONES DE COLOCACIÓN (PLACE)
        # Identificar casillas vacías candidatas (cerca de piezas existentes o puntos focales)
        candidate_coords = set()
        if not state.stones:
            # Tablero vacío: colocar en centro o estrellas
            mid = grid_size // 2
            candidate_coords.update([
                (mid, mid), (mid - 2, mid - 2), (mid + 2, mid + 2),
                (mid - 2, mid + 2), (mid + 2, mid - 2)
            ])
        else:
            # En la vecindad de piedras existentes (radio Chebyshev 2)
            for (sx, sy) in state.stones.keys():
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        nx, ny = sx + dx, sy + dy
                        if 0 <= nx < grid_size and 0 <= ny < grid_size and (nx, ny) not in state.stones:
                            candidate_coords.add((nx, ny))

        # Limitar número de casillas a evaluar si hay demasiadas
        sample_positions = list(candidate_coords)
        if len(sample_positions) > 12:
            sample_positions = random.sample(sample_positions, 12)

        stone_types = ["PRISM", "MIRROR", "SPLITTER", "BLOCKER"]
        rotations = [0.0, 45.0, 90.0, 135.0]

        for (px, py) in sample_positions:
            # Para cada posición candidata, probar prismas y espejos orientados
            for st in ("PRISM", "MIRROR"):
                for rot in (0.0, 45.0, 90.0, 135.0):
                    actions.append({"type": "place", "x": px, "y": py, "stone_type": st, "rotation": rot})
            # Ocasionalmente probar splitters y blockers
            actions.append({"type": "place", "x": px, "y": py, "stone_type": "SPLITTER", "rotation": 0.0})
            actions.append({"type": "place", "x": px, "y": py, "stone_type": "BLOCKER", "rotation": 0.0})

        # 2. ACCIONES DE ROTACIÓN (ROTATE)
        my_stones = [pos for pos, s in state.stones.items() if s.player == player]
        for (sx, sy) in my_stones:
            current_rot = state.stones[(sx, sy)].rotation_angle
            for rot_delta in (45.0, 90.0, 135.0, 180.0):
                new_rot = (current_rot + rot_delta) % 360.0
                actions.append({"type": "rotate", "x": sx, "y": sy, "angle": new_rot})

        # 3. ACCIONES DE DISPARO LÁSER (LASER)
        # Disparar desde piezas propias o desde fuentes alineadas
        cardinal_dirs = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
                         (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]

        for (sx, sy) in my_stones:
            for (dx, dy) in cardinal_dirs:
                actions.append({"type": "laser", "x": float(sx), "y": float(sy), "dx": dx, "dy": dy})

        # También disparos desde los bordes hacia el centro si hay pocas piezas
        if len(my_stones) <= 2:
            mid = float(grid_size // 2)
            actions.append({"type": "laser", "x": -1.0, "y": mid, "dx": 1.0, "dy": 0.0})
            actions.append({"type": "laser", "x": mid, "y": -1.0, "dx": 0.0, "dy": 1.0})

        # 4. PASAR TURNO
        actions.append({"type": "pass"})

        random.shuffle(actions)
        return actions

    def apply_action(self, state: BoardState2D, action: Dict[str, Any], player: int):
        """Aplica la acción de forma no destructiva sobre la copia del tablero."""
        act_type = action.get("type", "pass")

        if act_type == "place":
            x, y = action["x"], action["y"]
            st = action.get("stone_type", "PRISM")
            rot = action.get("rotation", 0.0)
            if state.place_stone((x, y), st, player):
                state.set_rotation_to((x, y), rot)
                state.end_turn(player)

        elif act_type == "rotate":
            x, y = action["x"], action["y"]
            ang = action.get("angle", 0.0)
            state.set_rotation_to((x, y), ang)
            state.end_turn(player)

        elif act_type == "laser":
            x, y = action["x"], action["y"]
            dx, dy = action["dx"], action["dy"]
            start_pos = (float(x), float(y))
            norm = math.sqrt(dx**2 + dy**2) or 1.0
            dir_norm = (dx / norm, dy / norm)
            paths = self.laser_calc.calculate_path(start_pos, dir_norm, state.stones)
            state.add_laser_source(start_pos, dir_norm, player)
            state.process_laser_captures(player, paths)
            state.end_turn(player)

        elif act_type == "pass":
            state.pass_turn(player)

    def evaluate_state(self, state: BoardState2D, root_player: int) -> float:
        """Función heurística de evaluación terminal/profunda para GoLuminamics."""
        scores = state.calculate_score()
        p1_territory = scores.get("player1", 0)
        p2_territory = scores.get("player2", 0)

        p1_captures = state.get_captures(1)
        p2_captures = state.get_captures(2)

        p1_total = p1_territory + (p1_captures * 2.5)
        p2_total = p2_territory + (p2_captures * 2.5)

        # Victoria terminal
        if state.game_over:
            if state.winner == root_player:
                return 100.0
            elif state.winner == (3 - root_player):
                return -100.0
            return 0.0

        if root_player == 1:
            diff = p1_total - p2_total
        else:
            diff = p2_total - p1_total

        # Función de squash logística/tanh acotada entre -1.0 y +1.0
        return math.tanh(diff / 15.0)

    def search(self, initial_state: BoardState2D, player: int = 1, simulations: int = 250, max_time_sec: float = 1.5) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        root_player = player
        """Ejecuta la búsqueda MCTS completa."""
        start_time = time.time()
        root_board = clone_board(initial_state)
        root = MCTSNode(root_board, root_player)
        root.untried_actions = self.generate_candidate_actions(root_board, root_player)

        iterations_done = 0

        while iterations_done < simulations:
            if (time.time() - start_time) > max_time_sec:
                break

            # 1. SELECCIÓN
            node = root
            while node.is_fully_expanded() and node.children:
                node = node.best_child()

            # 2. EXPANSIÓN
            if not node.is_fully_expanded() and node.untried_actions:
                action = node.untried_actions.pop()
                next_state = clone_board(node.state)
                self.apply_action(next_state, action, node.player_to_move)

                next_player = 3 - node.player_to_move
                child_node = MCTSNode(next_state, next_player, parent=node, action=action)
                child_node.untried_actions = self.generate_candidate_actions(next_state, next_player)
                node.children.append(child_node)
                node = child_node

            # 3. EVALUACIÓN / SIMULACIÓN
            value = self.evaluate_state(node.state, root_player)

            # 4. RETROPROPAGACIÓN
            curr = node
            while curr is not None:
                curr.visits += 1
                curr.total_value += value
                curr = curr.parent

            iterations_done += 1

        elapsed = time.time() - start_time

        # Selección de la mejor acción desde la raíz (la más visitada)
        if not root.children:
            best_action = {"type": "pass"}
            best_visits = 0
            best_val = 0.0
        else:
            best_child = max(root.children, key=lambda c: c.visits)
            best_action = best_child.action
            best_visits = best_child.visits
            best_val = best_child.total_value / max(1, best_child.visits)

        stats = {
            "simulations_requested": simulations,
            "simulations_completed": iterations_done,
            "elapsed_seconds": round(elapsed, 4),
            "simulations_per_sec": int(iterations_done / max(0.001, elapsed)),
            "root_children_count": len(root.children),
            "best_action_visits": best_visits,
            "best_action_value": round(best_val, 3),
            "top_candidates": [
                {
                    "action": c.action,
                    "visits": c.visits,
                    "expected_value": round(c.total_value / max(1, c.visits), 3)
                }
                for c in sorted(root.children, key=lambda c: c.visits, reverse=True)[:5]
            ]
        }

        return best_action, stats
