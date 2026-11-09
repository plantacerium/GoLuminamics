"""
GoLuminamics - Stone Selector Bottom HUD
----------------------------------------
Barra horizontal de selección rápida de piezas ópticas.
Diseñada para ser fácilmente ampliable con nuevos tipos de fichas.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor


# Registro base de piezas ópticas disponibles
AVAILABLE_STONE_TYPES: List[Dict[str, Any]] = [
    {
        "id": "PRISM",
        "name": "Prisma",
        "symbol": "▲",
        "color": "#00CEC9",
        "border_color": "#81ECEC",
        "shortcut": "1",
        "desc": "Transmite y refracta a 45°/90°. Construcción de trayectorias."
    },
    {
        "id": "MIRROR",
        "name": "Espejo",
        "symbol": "⬡",
        "color": "#A29BFE",
        "border_color": "#6C5CE7",
        "shortcut": "2",
        "desc": "Refleja el haz a 90°. Rebotes y desvíos perimetrales."
    },
    {
        "id": "SPLITTER",
        "name": "Splitter",
        "symbol": "✦",
        "color": "#FFEAA7",
        "border_color": "#FDCB6E",
        "shortcut": "3",
        "desc": "Bifurca un haz incidente en 2 direcciones simultáneas."
    },
    {
        "id": "BLOCKER",
        "name": "Bloqueador",
        "symbol": "█",
        "color": "#FF7675",
        "border_color": "#D63031",
        "shortcut": "4",
        "desc": "Muro defensivo que absorbe haces y bloquea líneas de tiro."
    }
]


class StoneSelectorHUD(QFrame):
    """HUD inferior moderno para selección rápida de fichas ópticas."""
    stone_type_changed = Signal(str)  # Emite el ID de la pieza seleccionada (ej. 'PRISM')

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.selected_type: str = "PRISM"
        self.buttons: Dict[str, QPushButton] = {}
        self.stone_definitions: List[Dict[str, Any]] = list(AVAILABLE_STONE_TYPES)

        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("StoneSelectorHUD")
        self.setFixedHeight(54)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Estilo moderno del contenedor HUD
        self.setStyleSheet("""
            QFrame#StoneSelectorHUD {
                background-color: #1E1E24;
                border: 1px solid #383844;
                border-radius: 8px;
                margin: 0px 4px 6px 4px;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(12, 4, 12, 4)
        self.main_layout.setSpacing(8)

        # Etiqueta de cabecera
        title_label = QLabel("🧩 PIEZAS:")
        title_label.setStyleSheet("color: #8E8EA0; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        self.main_layout.addWidget(title_label)

        # Generar botones para cada ficha registrada
        for stone in self.stone_definitions:
            self._create_button_for_stone(stone)

        self.main_layout.addStretch(1)

        # Indicador de ayuda de teclado
        hint_label = QLabel("💡 Atajos: [1] a [4]")
        hint_label.setStyleSheet("color: #636e72; font-size: 11px; font-style: italic;")
        self.main_layout.addWidget(hint_label)

        # Marcar la primera pieza activa
        self.select_stone_type("PRISM", emit=False)

    def _create_button_for_stone(self, stone: Dict[str, Any]):
        """Crea y registra un botón seleccionable para una pieza."""
        s_id = stone["id"]
        name = stone["name"]
        symbol = stone["symbol"]
        shortcut = stone.get("shortcut", "")
        desc = stone.get("desc", "")

        label_text = f" {symbol}  {name.upper()} "
        if shortcut:
            label_text += f"[{shortcut}]"

        btn = QPushButton(label_text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setToolTip(f"<b>{name}</b> ({s_id})<br>{desc}<br><i>Atajo de teclado: [{shortcut}]</i>")
        btn.clicked.connect(lambda checked=False, sid=s_id: self.select_stone_type(sid))

        self.buttons[s_id] = btn
        self.main_layout.addWidget(btn)

    def select_stone_type(self, stone_id: str, emit: bool = True):
        """Selecciona una ficha y actualiza el estilo visual de todos los botones."""
        stone_id = stone_id.upper()
        if stone_id not in self.buttons:
            return

        self.selected_type = stone_id

        # Actualizar estilos
        for s in self.stone_definitions:
            sid = s["id"]
            btn = self.buttons.get(sid)
            if not btn:
                continue

            color = s["color"]
            border_color = s.get("border_color", color)

            if sid == self.selected_type:
                # Botón ACTIVO (con brillo y elevación)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #2D2D3A;
                        color: {color};
                        border: 2px solid {border_color};
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 12px;
                        padding: 6px 14px;
                    }}
                """)
            else:
                # Botón INACTIVO
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #25252E;
                        color: #C0C0D0;
                        border: 1px solid #3E3E4C;
                        border-radius: 6px;
                        font-size: 12px;
                        padding: 6px 12px;
                    }}
                    QPushButton:hover {{
                        background-color: #30303C;
                        color: #FFFFFF;
                        border-color: #555568;
                    }}
                """)

        if emit:
            self.stone_type_changed.emit(self.selected_type)

    def get_selected_stone_type(self) -> str:
        """Devuelve el ID de la ficha seleccionada actualmente."""
        return self.selected_type

    def add_stone_type(self, stone_def: Dict[str, Any]):
        """Permite a extensiones registrar dinámicamente un nuevo tipo de ficha."""
        s_id = stone_def["id"].upper()
        if s_id in self.buttons:
            return
        self.stone_definitions.append(stone_def)
        self._create_button_for_stone(stone_def)
        self.select_stone_type(self.selected_type, emit=False)
