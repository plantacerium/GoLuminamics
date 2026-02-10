import json
import time
import random
import ollama
from typing import List, Dict, Any

# Importamos el servidor del juego y el agente unificado
from _00_entry.game_server import GameServer
from _02_engines.ai_player import AIAgent

# --- CONFIGURACIÓN DE LA ARENA ---
MODELO_JUGADOR_1 = "gemma3:4b"
MODELO_JUGADOR_2 = "gemma3:4b"
DELAY_ENTRE_TURNOS = 3.0

def main():
    # 1. Inicializar Servidor y Agentes
    server = GameServer(grid_size=10) # Reducido a 10x10 para que sea más rápido para la IA
    server.reset({"starting_energy": 10})
    
    # El nuevo Agente carga mechanics y playbooks automáticamente
    p1 = AIAgent(1, MODELO_JUGADOR_1, mechanics_path="MECHANICS.md", use_all_playbooks=True)
    p2 = AIAgent(2, MODELO_JUGADOR_2, mechanics_path="MECHANICS.md", use_all_playbooks=True)
    
    agents = {1: p1, 2: p2}
    
    print(f"--- INICIANDO ARENA CLI: {MODELO_JUGADOR_1} vs {MODELO_JUGADOR_2} ---")
    
    turn = 0
    while not server.game_over and turn < 50: # Límite de seguridad
        current_pid = server.current_player
        current_agent = agents[current_pid]
        
        print(f"\n\n=== TURNO {turn} | JUGADOR {current_pid} ({current_agent.model_name}) ===")
        
        # El agente ahora se encarga de ver el tablero y elegir movimiento
        print(f"Agente {current_pid} pensando...")
        action = current_agent.get_move(server)
        
        # Ejecutar y Validar
        success = False
        if action:
            print(f"Intento de acción: {action}")
            result = server.step(action)
            
            if result.get("reward", 0) != -0.1 and not result.get("error"):
                success = True
                print(f"--> ÉXITO. Recompensa: {result.get('reward')}")
            else:
                print(f"--> MOVIMIENTO ILEGAL detectado por el motor: {result.get('error')}")
        
        if not success:
            print("!! FALLBACK: Ejecutando movimiento aleatorio.")
            valid_resp = server.get_valid_actions()
            valid_actions = valid_resp.get("valid_actions", [])
            if valid_actions:
                random_action = random.choice(valid_actions)
                server.step(random_action)
                print(f"--> Fallback ejecutado: {random_action['type']}")
            else:
                server.step({"type": "pass"})

        turn += 1
        time.sleep(DELAY_ENTRE_TURNOS)


    # Fin del juego
    print("\n" + "="*30)
    print("JUEGO TERMINADO")
    print(f"Ganador: Jugador {server.winner}")
    print(f"Razón: {server.victory_reason}")
    print("="*30)

if __name__ == "__main__":
    main()
