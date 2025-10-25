from flask import Flask, render_template, request, redirect, url_for, flash
import json, os
from utils.storage import guardar_registro, usuario_existe
from utils.validators import validar_input

app = Flask(__name__)
app.secret_key = "secreto_seguro"  # Para flash messages

FORMS_DIR = "forms"

# -----------------------
# Página principal: listar formularios activos
# -----------------------
@app.route("/")
def index():
    formularios = []

    if os.path.exists(FORMS_DIR):
        for archivo in os.listdir(FORMS_DIR):
            if archivo.endswith(".json"):
                ruta = os.path.join(FORMS_DIR, archivo)
                with open(ruta, "r", encoding="utf-8") as f:
                    try:
                        config = json.load(f)
                        if not config.get("activo", True):
                            continue  # No mostrar formularios desactivados
                        nombre = os.path.splitext(archivo)[0]
                        formularios.append({
                            "nombre": nombre,
                            "titulo": config.get("titulo", nombre),
                            "descripcion": config.get("descripcion", "")
                        })
                    except json.JSONDecodeError:
                        pass

    return render_template("index.html", formularios=formularios)

# -----------------------
# Formulario dinámico
# -----------------------
@app.route("/formulario/<nombre>", methods=["GET", "POST"])
def formulario(nombre):
    ruta = os.path.join(FORMS_DIR, f"{nombre}.json")
    if not os.path.exists(ruta):
        return f"No se encontró el formulario '{nombre}'.", 404

    with open(ruta, "r", encoding="utf-8") as f:
        config = json.load(f)

    if not config.get("activo", True):
        return "Este formulario no está disponible en este momento.", 403

    datos = {}  # Para mantener los valores ingresados
    errores_por_campo = {}  # Nuevo: diccionario para errores por campo

    if request.method == "POST":
        errores_generales = []  # Para errores que no son de un campo específico
        
        for campo in config["campos"]:
            nombre_campo = campo["nombre"]

            # Checkbox puede ser multiple, otros campos simples
            if campo["tipo"] == "checkbox":
                valor = request.form.getlist(nombre_campo)
            else:
                valor = request.form.get(nombre_campo, "").strip()

            datos[nombre_campo] = valor

            # Validaciones por campo
            mensaje_error = None
            
            if campo.get("obligatorio") and (not valor or valor == [""]):
                mensaje_error = f"Este campo es obligatorio"
            elif not validar_input(valor, campo):
                mensaje_error = f"El valor no cumple con el formato requerido"
            
            if mensaje_error:
                errores_por_campo[nombre_campo] = mensaje_error

        # Validación de duplicados (error general)
        identificador = config.get("identificador_unico")
        if identificador and usuario_existe(nombre, identificador, datos.get(identificador)):
            errores_generales.append(f"Ya existe un registro con {identificador}: {datos.get(identificador)}")

        if errores_por_campo or errores_generales:
            # Pasar errores específicos a la template
            for error in errores_generales:
                flash(error, "error")
            return render_template("form.html", config=config, datos=datos, errores=errores_por_campo)

        # Guardar registro
        guardar_registro(nombre, datos)
        return render_template("success.html", titulo=config["titulo"], form_name=nombre)

    # GET request
    return render_template("form.html", config=config, datos={}, errores={})
    

# -----------------------
# Ejecutar servidor
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)