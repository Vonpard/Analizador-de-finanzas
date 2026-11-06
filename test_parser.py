import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

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
- categoria: elige la categoría que mejor describa el gasto (ej: comida, transporte, entretenimiento, salud, hogar, ropa, otros) - puedes usar cualquier categoría que tenga sentido, no estás limitado a esta lista
- fecha_relativa: cómo lo mencionó el usuario (ej: "ayer", "hoy", "el lunes", "15 de marzo") - no calcules la fecha exacta, solo repite cómo se refirió a ella

Texto del usuario: """


def parsear_gastos(texto_usuario):
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=PROMPT_SISTEMA + texto_usuario,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA_GASTOS,
        ),
    )
    return json.loads(response.text)


if __name__ == "__main__":
    prueba = "ayer me compré un café por 2.50 y hoy pagué 45 del súper, también gasté 15 en gasolina el lunes"
    resultado = parsear_gastos(prueba)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))