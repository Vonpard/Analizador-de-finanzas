from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

import finanzas_core as fc

app = FastAPI()
fc.init_db()


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/registrar")
def registrar(texto: str = Form(...)):
    gastos = fc.registrar_gastos(texto)
    return {"gastos_guardados": gastos}


@app.get("/gastos")
def gastos(limite: int = 50):
    return {"gastos": fc.listar_gastos(limite)}


@app.get("/resumen/categoria")
def resumen_categoria():
    return {"resumen": fc.resumen_por_categoria()}


@app.get("/resumen/mes")
def resumen_mes():
    return {"resumen": fc.resumen_por_mes()}