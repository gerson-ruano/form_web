import os
import json
import csv

def cargar_registros(form_name):
    """Cargar registros existentes en JSON"""
    ruta = f"data/{form_name}.json"
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def usuario_existe(form_name, identificador, valor_identificador):
    """Validar si ya existe un registro con el identificador único"""
    registros = cargar_registros(form_name)
    return any(reg.get(identificador) == valor_identificador for reg in registros)

def guardar_registro(form_name, data):
    """Guardar datos en JSON y CSV"""
    os.makedirs("data", exist_ok=True)

    # -------------------
    # Guardar en JSON
    # -------------------
    registros = cargar_registros(form_name)

    # Convertir checkbox seleccionados a lista si no lo son
    for k, v in data.items():
        if isinstance(v, str) and "," in v:
            data[k] = v.split(",")  # opcional, según cómo envíes los checkbox

    registros.append(data)
    with open(f"data/{form_name}.json", "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)

    # -------------------
    # Guardar en CSV
    # -------------------
    csv_path = f"data/{form_name}.csv"
    file_exists = os.path.exists(csv_path)

    # Convertir listas a cadenas separadas por |
    csv_data = {}
    for k, v in data.items():
        if isinstance(v, list):
            csv_data[k] = "|".join(v)
        else:
            csv_data[k] = v

    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(csv_data.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(csv_data)
