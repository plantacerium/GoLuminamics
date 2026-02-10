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
            return [], "No valid actions."

        place_actions = [a for a in valid_actions if a['type'] == 'place']
        sample = random.sample(place_actions, min(5, len(place_actions))) if place_actions else []
        
        # Add some rotate/laser examples if available
        rotate_actions = [a for a in valid_actions if a['type'] == 'rotate']
        if rotate_actions:
            sample.append(random.choice(rotate_actions))
            
        return valid_actions, json.dumps(sample)

    def get_move(self, server: GameServer) -> dict:
        """Consulta a Ollama para obtener el siguiente movimiento."""
        board_str = self.render_board_ascii(server)
        all_valid_actions, valid_sample = self.get_valid_actions_summary(server)
        
        # Check for immediate winning moves or simple logic before LLM (optional, but good for speed)
        # For now, we rely on LLM + random fallback

        prompt = f"""
        Estás jugando un juego de estrategia por turnos llamado Luminamics.
        
        CONTEXTO DE REGLAS (RESUMEN):
        {self.mechanics_content[:1500]}... (resumido)
        
        ESTRATEGIA ACTIVA (PLAYBOOK):
        {self.playbook_content}
        
        TU ROL:
        Eres el JUGADOR {self.player_id}.
        Tus piezas se representan con {self.my_symbols}.
        El oponente son {self.opp_symbols}.
        
        ESTADO ACTUAL DEL TABLERO:
        {board_str}
        
        ACCIONES DISPONIBLES (MUESTRA):
        {valid_sample}
        
        INSTRUCCIONES:
        1. Analiza el tablero. Busca capturar piezas enemigas disparando láseres o protegiendo tu territorio.
        2. Selecciona UNA acción válida.
        3. RESPONDE SOLO CON UN JSON VÁLIDO.
        
        Formato JSON esperado:
        {{"type": "place", "x": 5, "y": 5, "stone_type": "MIRROR"}}
        o
        {{"type": "rotate", "x": 5, "y": 5, "angle": 90}}
        o
        {{"type": "laser", "x": 5, "y": 5, "dx": 1, "dy": 0}}
        
        TU RESPUESTA JSON:
        """

        try:
            print(f"Agente {self.player_id} ({self.model_name}) pensando...")
            response = ollama.generate(
                model=self.model_name, 
                prompt=prompt, 
                format="json",
                options={"temperature": 0.3} # Low temperature for more consistent JSON
            )
            
            clean_json = response['response'].replace("```json", "").replace("```", "").strip()
            action = json.loads(clean_json)
            print(f"Agente sugirió: {action}")
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
