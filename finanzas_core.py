import os
import json
import sqlite3
#from datetime import datetime, date
from datetime import datetime, date, timedelta

from dotenv import load_dotenv
from google import genai
from google.genai import types
import dateparser

load_dotenv()
DIAS_SEMANA = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}

DB_PATH = "finanzas.db"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SCHEMA_GASTOS = {
    "type": "object",
    "properties": {
        "gastos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "descripcion": {"type": "string"},
                    "monto": {"type": "number"},
                    "categoria": {"type": "string"},
                    "fecha_relativa": {"type": "string"},
                },
                "required": ["descripcion", "monto", "categoria", "fecha_relativa"],
            },
        }
    },
    "required": ["gastos"],
}

PROMPT_SISTEMA = """Eres un asistente que extrae gastos de un texto en lenguaje natural.
Identifica CADA gasto mencionado por separado. Para cada uno determina:
- descripcion: qué se compró, corto y claro
- monto: el número, sin símbolo de moneda
- categoria: elige la categoría que mejor describa el gasto (puedes usar cualquier categoría razonable: comida, transporte, entretenimiento, salud, hogar, ropa, educación, otros, etc.)
- fecha_relativa: cómo lo mencionó el usuario (ej: "ayer", "hoy", "el lunes", "15 de marzo"). Si no menciona fecha, usa "hoy".

Texto del usuario: """


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL,
            fecha DATE NOT NULL,
            texto_original TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def parsear_gastos(texto_usuario):
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=PROMPT_SISTEMA + texto_usuario,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA_GASTOS,
        ),
    )
    return json.loads(response.text)["gastos"]


def resolver_dia_semana(texto):
    """Detecta si el texto menciona un día de la semana y regresa
    la fecha del más reciente que ya pasó (incluyendo hoy si coincide)."""
    texto_lower = texto.lower()
    for nombre_dia, indice_dia in DIAS_SEMANA.items():
        if nombre_dia in texto_lower:
            hoy = date.today()
            dias_atras = (hoy.weekday() - indice_dia) % 7
            return hoy - timedelta(days=dias_atras)
    return None

def resolver_fecha(fecha_relativa):
    """Convierte 'ayer', 'el lunes', etc. en una fecha real, usando hoy como referencia."""
    fecha_dia_semana = resolver_dia_semana(fecha_relativa)
    if fecha_dia_semana:
        return fecha_dia_semana.isoformat()

    resultado = dateparser.parse(
        fecha_relativa,
        languages=["es"],
        settings={"RELATIVE_BASE": datetime.now(), "PREFER_DATES_FROM": "past"},
    )
    if resultado is not None:
        return resultado.date().isoformat()

    print(f"⚠️  No se pudo interpretar la fecha '{fecha_relativa}', usando hoy como fallback.")
    return date.today().isoformat()


def registrar_gastos(texto_usuario):
    gastos_extraidos = parsear_gastos(texto_usuario)

    conn = sqlite3.connect(DB_PATH)
    guardados = []
    for g in gastos_extraidos:
        fecha_resuelta = resolver_fecha(g["fecha_relativa"])
        conn.execute(
            "INSERT INTO gastos (descripcion, monto, categoria, fecha, texto_original) VALUES (?, ?, ?, ?, ?)",
            (g["descripcion"], g["monto"], g["categoria"], fecha_resuelta, texto_usuario),
        )
        guardados.append({**g, "fecha": fecha_resuelta})
    conn.commit()
    conn.close()
    return guardados


def listar_gastos(limite=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    filas = conn.execute(
        "SELECT * FROM gastos ORDER BY fecha DESC, id DESC LIMIT ?", (limite,)
    ).fetchall()
    conn.close()
    return [dict(f) for f in filas]


def resumen_por_categoria():
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute(
        "SELECT categoria, SUM(monto) as total FROM gastos GROUP BY categoria ORDER BY total DESC"
    ).fetchall()
    conn.close()
    return [{"categoria": f[0], "total": f[1]} for f in filas]


def resumen_por_mes():
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute(
        "SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) as total FROM gastos GROUP BY mes ORDER BY mes"
    ).fetchall()
    conn.close()
    return [{"mes": f[0], "total": f[1]} for f in filas]