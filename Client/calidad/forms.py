import requests

API_BASE = "http://127.0.0.1:8000/api"


def get_choices_laptops(token):
    resp = requests.get(
        f"{API_BASE}/produccion/laptops/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        return [
            (l["numero"], f"{l['numero']} - {l.get('num_serie', '')} ({l.get('modelo_nombre', '')})")
            for l in resp.json()
            if l.get("estado_codigo") == "PENSAM"
        ]
    return []


def get_choices_lineas_produccion(token):
    resp = requests.get(
        f"{API_BASE}/lineas/lineas/activas/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        return [(l.get("codigo"), l.get("nombre")) for l in resp.json()]
    return []
