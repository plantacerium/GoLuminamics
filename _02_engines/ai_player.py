import json
import ollama
import sys
import random
import os

# Importamos el servidor del juego proporcionado
from _00_entry.game_server import GameServer

MODEL_NAME = "gemma3:4b"  # Cambia a "gemma3" si ya lo tienes en tu lista de 'ollama list'

class AIAgent:
    def __init__(self, player_id: int, model_name: str = MODEL_NAME, mechanics_path: str = "MECHANICS.md", use_all_playbooks: bool = False):
        self.player_id = player_id
        self.model_name = model_name
        self.mechanics_content = self._load_mechanics(mechanics_path)
        self.playbook_content = self._load_playbooks(use_all_playbooks)
        self.my_symbols = "MAYÚSCULAS (P, M, S)" if player_id == 1 else "minúsculas (p, m, s)"
        self.opp_symbols = "minúsculas (p, m, s)" if player_id == 1 else "MAYÚSCULAS (P, M, S)"

    def _load_mechanics(self, path: str) -> str:
        """Carga el contenido de MECHANICS.md."""
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            parent_path = os.path.join("..", path)
            if os.path.exists(parent_path):
                with open(parent_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return "No se pudo cargar MECHANICS.md. Usa tu conocimiento general del juego."
        except Exception as e:
            print(f"Error cargando mechanics: {e}")
            return "Error cargando reglas."

    def _load_playbooks(self, use_all: bool) -> str:
        """Carga una o todas las estrategias de la carpeta playbooks."""
        try:
            playbook_dir = "_02_engines/playbooks"
            if not os.path.exists(playbook_dir):
                 # Try original or local dir
                playbook_dir = "playbooks"
                if not os.path.exists(playbook_dir):
                     return ""
            
            files = [f for f in os.listdir(playbook_dir) if f.endswith(".md")]
            if not files:
                return ""
            
            if use_all:
                print(f"Agente {self.player_id} cargando TODAS las estrategias ({len(files)} playbooks)...")
                content = ""
                for filename in files:
                    with open(os.path.join(playbook_dir, filename), 'r', encoding='utf-8') as f:
                        content += f"\n--- PLAYBOOK: {filename} ---\n{f.read()}\n"
                return content
            else:
                chosen_file = random.choice(files)
                path = os.path.join(playbook_dir, chosen_file)
                print(f"Agente {self.player_id} ha seleccionado estrategia: {chosen_file}")
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()

        except Exception as e:
            print(f"Error cargando playbook: {e}")
            return ""

    def render_board_ascii(self, server: GameServer) -> str:
        """
        Convierte el estado interno del tablero en una representación ASCII.
        """
        if not server.board:
            return "Tablero vacío."

        grid_size = server.grid_size
        display = [['.' for _ in range(grid_size)] for _ in range(grid_size)]

        symbols = {"PRISM": "P", "MIRROR": "M", "SPLITTER": "S"}

        for (x, y), stone in server.board.stones.items():
            char = symbols.get(stone.stone_type.name, "?")
            if stone.player == 2:
                char = char.lower()
            display[y][x] = char

        header = "   " + "".join([f"{i%10}" for i in range(grid_size)])
        rows = []
        for y in range(grid_size):
            row_str = f"{y:2d} " + "".join(display[y])
            rows.append(row_str)
        
        return header + "\n" + "\n".join(rows)

    def get_valid_actions_summary(self, server: GameServer):
        """
        Obtiene acciones válidas y devuelve un resumen o una muestra aleatoria.
        """
        actions_response = server.get_valid_actions()
        valid_actions = actions_response.get("valid_actions", [])
        
        if not valid_actions:
            return [], "[]"

        place_actions = [a for a in valid_actions if a['type'] == 'place']
        sample = random.sample(place_actions, min(5, len(place_actions))) if place_actions else []
        
        # Add some rotate/laser examples if available
        rotate_actions = [a for a in valid_actions if a['type'] == 'rotate']
        if rotate_actions:
            sample.append(random.choice(rotate_actions))
        
        laser_actions = [a for a in valid_actions if a['type'] == 'laser']
        if laser_actions:
            # Prioritize laser actions in the sample
            sample.extend(random.sample(laser_actions, min(3, len(laser_actions))))

        # Add movement examples (Linear & Curve)
        move_actions = [a for a in valid_actions if a['type'] == 'move']
        if move_actions:
            sample.extend(random.sample(move_actions, min(3, len(move_actions))))
            
        curve_actions = [a for a in valid_actions if a['type'] == 'curve_move']
        if curve_actions:
            sample.extend(random.sample(curve_actions, min(3, len(curve_actions))))
            
        return valid_actions, json.dumps(sample)

    def get_structured_board_state(self, server: GameServer) -> str:
        """
        Devuelve una descripción textual detallada de las piezas propias y enemigas.
        """
        if not server.board:
            return "Tablero no iniciado."

        my_stones = []
        opp_stones = []
        
        # BUG FIX: Use rotation_angle instead of angle
        for pos, stone in server.board.stones.items():
            info = f"{stone.stone_type.name} en {pos} (Rotación: {stone.rotation_angle}°)"
            if stone.player == self.player_id:
                my_stones.append(info)
            else:
                opp_stones.append(info)
        
        my_stones_str = "\n".join([f"- {s}" for s in my_stones]) if my_stones else "Ninguna."
        opp_stones_str = "\n".join([f"- {s}" for s in opp_stones]) if opp_stones else "Ninguna."
        
        # Calculate scores for strategic context
        score_data = server.board.calculate_score()
        my_score = score_data[f"player{self.player_id}"]
        opp_score = score_data[f"player{3-self.player_id}"]
        
        # Strategic Directive
        if my_score > opp_score + 10:
            directive = "ESTÁS GANANDO: Mantén la ventaja, protege tus piezas clave (Prismas/Splitters)."
        elif opp_score > my_score + 10:
            directive = "VAS PERDIENDO: ¡Riesgo necesario! Busca capturas con láser o expande agresivamente."
        else:
            directive = "ESTADO EQUILIBRADO: Busca una apertura táctica o línea de tiro clara."

        # Tactical Insight: Specifically check for laser shots that score
        laser_actions = server.get_valid_actions().get("valid_actions", [])
        score_potential = [a for a in laser_actions if a['type'] == 'laser']
        if score_potential:
            directive += "\n¡OPORTUNIDAD DE DISPARO! Tienes acciones de LÁSER disponibles. Úsalas para puntuar o capturar."

        return f"""
        MIS PIEZAS (Jugador {self.player_id}):
        {my_stones_str}
        
        PIEZAS ENEMIGAS (Oponente):
        {opp_stones_str}
        
        ENERGÍA: Yo({server.board.player_energy[self.player_id]}), Oponente({server.board.player_energy[3-self.player_id]})
        PUNTUACIÓN TERRITORIO: Yo({my_score}), Oponente({opp_score})
        
        DIRECTIVA ESTRATÉGICA: {directive}
        """

    def get_move(self, server: GameServer) -> dict:
        """Consulta a Ollama para obtener el siguiente movimiento."""
        board_ascii = self.render_board_ascii(server)
        structured_state = self.get_structured_board_state(server)
        all_valid_actions, valid_sample = self.get_valid_actions_summary(server)
        
        # LOGGING REFINEMENT: Summaries for log file
        mech_summary = self.mechanics_content[:300] + "\n... [MECHANICS CONTENT TRUNCATED FOR LOG] ..."
        play_summary = (self.playbook_content[:300] + "\n... [PLAYBOOKS CONTENT TRUNCATED FOR LOG] ...") if len(self.playbook_content) > 500 else self.playbook_content

        # PROMPT CONSTRUCTION (MAPPING USER SNIPPET STYLE + ADVANCED DATA)
        prompt_template = """
        Estás jugando un juego de estrategia llamado Luminamics.
        
        CONTEXTO DE REGLAS (RESUMEN):
        {mechanics}
        
        ESTRATEGIA ACTIVA (PLAYBOOK):
        {playbooks}
        
        TU ROL:
        Eres el JUGADOR {player_id}.
        Tus piezas ({my_symbols}) vs Enemigo ({opp_symbols}).
        
        ESTADO DEL TABLERO (ASCII):
        {board_ascii}
        
        ANÁLISIS TÁCTICO:
        {structured_state}
        
        ACCIONES DISPONIBLES (MUESTRA):
        {valid_sample}
        
        TU MISIÓN:
        1. El LÁSER es tu fuente principal de puntos. Disparar el láser finaliza tu territorio e incrementa tu puntuación.
        2. Analiza el tablero. Si puedes disparar un LÁSER que cruce tus piezas y capture piezas enemigas, HAZLO.
        3. Colocar fichas es PREPARACIÓN. Solo coloca fichas si no tienes un disparo de láser efectivo este turno.
        4. MOVIMIENTO (REAL-TIME): Puedes mover tus fichas para mejorar posición o esquivar disparos.
           - Move (Lineal): Movimiento directo.
           - Curve Move (Bezier): Movimiento en arco, impredecible y útil para esquivar.
        5. Selecciona UNA acción válida.
        6. ¡NO PASAR! Debes jugar una ficha o disparar. El 'pass' está prohibido si hay opciones.
        
        FORMATO DE RESPUESTA (JSON PURO):
        Incluye un campo "thought" para explicar tu razonamiento táctico.
        
        {{
          "thought": "Basado en PUNTUACIÓN y PIEZAS ENEMIGAS, decido que...",
          "type": "place", "x": 0, "y": 0, "stone_type": "PRISM"
        }}
        
        Otras acciones:
        {{ "type": "rotate", "x": 5, "y": 5, "angle": 90 }}
        {{ "type": "laser", "x": 5, "y": 5, "dx": 1, "dy": 0 }}
        {{ "type": "move", "from_x": 2, "from_y": 2, "to_x": 2, "to_y": 3 }}
        {{ "type": "curve_move", "from_x": 0, "from_y": 0, "control_x": 2.5, "control_y": 5.0, "end_x": 5, "end_y": 5 }}
        """
        
        # 1. Real Prompt (Full Content)
        prompt = prompt_template.format(
            player_id=self.player_id,
            mechanics=self.mechanics_content,
            playbooks=self.playbook_content,
            my_symbols=self.my_symbols,
            opp_symbols=self.opp_symbols,
            board_ascii=board_ascii,
            structured_state=structured_state,
            valid_sample=valid_sample
        )
        
        # 2. Log Prompt (Truncated for readability)
        log_prompt = prompt_template.format(
            player_id=self.player_id,
            mechanics=mech_summary,
            playbooks=play_summary,
            my_symbols=self.my_symbols,
            opp_symbols=self.opp_symbols,
            board_ascii=board_ascii,
            structured_state=structured_state,
            valid_sample=valid_sample
        )

        try:
            print(f"Agente {self.player_id} ({self.model_name}) pensando...")
            
            # Print elegant log prompt
            print(f"\n--- PROMPT LOG (Player {self.player_id}) ---\n{log_prompt}\n--- PROMPT END ---")
            
            response = ollama.generate(
                model=self.model_name, 
                prompt=prompt, 
                format="json",
                options={"temperature": 0.2, "num_ctx": 4096}
            )
            
            raw_response = response['response']
            print(f"\n--- RAW RESPONSE ---\n{raw_response}\n--- END RESPONSE ---")
            
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            action = json.loads(clean_json)
            
            if "thought" in action:
                print(f"💭 PENSAMIENTO (Agente {self.player_id}): {action['thought']}")
                
            return action
        except Exception as e:
            print(f"Error en Agente {self.player_id}: {e}")
            return None

def main():
    # Test local simple
    server = GameServer(grid_size=10)
    server.reset()
    p1 = AIAgent(1)
    
    print("Iniciando prueba rápida de AIAgent...")
    move = p1.get_move(server)
    print(f"Movimiento final: {move}")

if __name__ == "__main__":
    main()
