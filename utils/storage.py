import os
import json
import csv

# Ruta absoluta a la carpeta de datos (persistente en Render)
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")

# Crear carpeta de datos si no existe
os.makedirs(DATA_DIR, exist_ok=True)


def cargar_registros(form_name):
    """Cargar registros existentes en JSON"""
    ruta = os.path.join(DATA_DIR, f"{form_name}.json")

    if not os.path.exists(ruta):
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def usuario_existe(form_name, identificador, valor_identificador):
    """Validar si ya existe un registro con el identificador único"""
    registros = cargar_registros(form_name)
    return any(reg.get(identificador) == valor_identificador for reg in registros)


def guardar_registro(form_name, data):
    """Guardar datos en JSON y CSV (persistentes en Render)"""
    os.makedirs(DATA_DIR, exist_ok=True)

    # -------------------
    # Guardar en JSON
    # -------------------
    registros = cargar_registros(form_name)

    # Convertir valores con comas en listas
    for k, v in data.items():
        if isinstance(v, str) and "," in v:
            data[k] = v.split(",")

    registros.append(data)

    json_path = os.path.join(DATA_DIR, f"{form_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)

    # -------------------
    # Guardar en CSV
    # -------------------
    csv_path = os.path.join(DATA_DIR, f"{form_name}.csv")
    file_exists = os.path.exists(csv_path)

    # Convertir listas a cadenas separadas por |
    csv_data = {
        k: "|".join(v) if isinstance(v, list) else v
        for k, v in data.items()
    }

    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(csv_data.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(csv_data)
