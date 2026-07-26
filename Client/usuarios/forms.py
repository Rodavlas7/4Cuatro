import requests
from django import forms


import requests


def get_choices_lineas(token):
    resp = requests.get(
        "http://127.0.0.1:8000/api/lineas/lineas/activas/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        return [(l["codigo"], l["nombre"]) for l in resp.json()]
    return []


def get_choices_estaciones(token, linea_id=None):
    url = "http://127.0.0.1:8000/api/lineas/lineas/estaciones/"
    if linea_id:
        url += f"?linea={linea_id}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200:
        return [(e["codigo"], e["nombre"]) for e in resp.json()]
    return []


def get_choices_roles(token):
    resp = requests.get(
        "http://127.0.0.1:8000/api/usuarios/Rol/Listar/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        return [(r["codigo"], r["nombre"]) for r in resp.json()]
    return []


def get_choices_turnos(token):
    resp = requests.get(
        "http://127.0.0.1:8000/api/usuarios/Turno/Listar/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        return [(t["codigo"], t["nombre"]) for t in resp.json()]
    return []
