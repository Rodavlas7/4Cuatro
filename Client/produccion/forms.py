import requests


def get_choices_lineas_paro(token):
    resp = requests.get(
        "http://127.0.0.1:8000/api/lineas/lineas/activas/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        return [
            (l.get("codigo"), l.get("nombre"))
            for l in resp.json()
            if l.get("estado_codigo") == "ACTI"
        ]
    return []