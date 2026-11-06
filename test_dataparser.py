import dateparser
from datetime import datetime
import finanzas_core as fc

pruebas = ["ayer", "hoy", "el lunes", "el lunes pasado", "hace 3 días", "15 de marzo"]

for texto in pruebas:
    print(f"{texto!r:25} -> {fc.resolver_fecha(texto)}")