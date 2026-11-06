import finanzas_core as fc

fc.init_db()

resultado = fc.registrar_gastos(
    "ayer me compré un café por 2.50 y hoy pagué 45 del súper, también gasté 15 en gasolina el lunes"
)
print("Guardados:", resultado)

print("\nResumen por categoría:", fc.resumen_por_categoria())
print("Resumen por mes:", fc.resumen_por_mes())
print("\nÚltimos gastos:", fc.listar_gastos())