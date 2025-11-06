from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory
import json, os
import qrcode
from io import BytesIO
import base64
from utils.storage import guardar_registro, usuario_existe
from utils.validators import validar_input

app = Flask(__name__)
app.secret_key = "secreto_seguro"  # Para flash messages

os.makedirs("data", exist_ok=True)

FORMS_DIR = "forms"
DATA_DIR = "data"

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
# Formulario dinámico
# -----------------------
@app.route("/admin/formularios")
def admin_formularios():
    """Lista todos los formularios para administración"""
    formularios = []

    if os.path.exists(FORMS_DIR):
        for archivo in os.listdir(FORMS_DIR):
            if archivo.endswith(".json"):
                ruta = os.path.join(FORMS_DIR, archivo)
                with open(ruta, "r", encoding="utf-8") as f:
                    try:
                        config = json.load(f)
                        nombre = os.path.splitext(archivo)[0]
                        
                        # Obtener el número de campos
                        campos_count = len(config.get("campos", []))
                        
                        formularios.append({
                            "nombre": nombre,
                            "archivo": archivo,
                            "titulo": config.get("titulo", nombre),
                            "descripcion": config.get("descripcion", ""),
                            "activo": config.get("activo", True),
                            "campos": campos_count  # <- Agregar esta línea
                        })
                    except json.JSONDecodeError:
                        pass

    return render_template("admin_formularios.html", formularios=formularios)

@app.route("/admin/formulario/<nombre>", methods=["GET", "POST"])
def editar_formulario(nombre):
    """Editar un formulario específico"""
    ruta = os.path.join(FORMS_DIR, f"{nombre}.json")
    
    if not os.path.exists(ruta):
        return jsonify({"success": False, "error": f"No se encontró el formulario '{nombre}'."}), 404

    try:
        if request.method == "POST":
            # Obtener los datos del formulario de edición
            config_data = request.get_json()
            
            # Validar estructura básica
            if not config_data or "titulo" not in config_data:
                return jsonify({"success": False, "error": "Estructura inválida"}), 400
            
            # Guardar el archivo
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({"success": True, "message": "Formulario actualizado correctamente"})

        # GET request - cargar el formulario existente
        with open(ruta, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        return jsonify(config)
        
    except json.JSONDecodeError as e:
        return jsonify({"success": False, "error": f"Error en el formato JSON del archivo: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Error interno del servidor: {str(e)}"}), 500

@app.route("/admin/formulario/nuevo", methods=["POST"])
def nuevo_formulario():
    """Crear un nuevo formulario"""
    try:
        print("=== SOLICITUD NUEVO FORMULARIO RECIBIDA ===")  # Debug
        print("Headers:", request.headers)  # Debug
        print("Content-Type:", request.content_type)  # Debug
        
        data = request.get_json()
        print("Datos recibidos:", data)  # Debug
        
        if not data:
            print("❌ No se recibieron datos JSON")  # Debug
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
            
        nombre = data.get("nombre")
        titulo = data.get("titulo", nombre)
        
        print(f"Nombre: {nombre}, Título: {titulo}")  # Debug
        
        if not nombre:
            print("❌ Nombre vacío")  # Debug
            return jsonify({"success": False, "error": "El nombre es requerido"}), 400
        
        # Validar que el nombre sea válido para archivo
        nombre_archivo = "".join(c for c in nombre if c.isalnum() or c in (' ', '-', '_')).strip()
        nombre_archivo = nombre_archivo.replace(' ', '_').lower()
        
        print(f"Nombre archivo: {nombre_archivo}")  # Debug
        
        ruta = os.path.join(FORMS_DIR, f"{nombre_archivo}.json")
        print(f"Ruta destino: {ruta}")  # Debug
        
        # Verificar si el directorio existe
        if not os.path.exists(FORMS_DIR):
            print("❌ Directorio forms no existe")  # Debug
            os.makedirs(FORMS_DIR)
            print("✅ Directorio forms creado")  # Debug
        
        if os.path.exists(ruta):
            print("❌ Archivo ya existe")  # Debug
            return jsonify({"success": False, "error": "Ya existe un formulario con ese nombre"}), 400
        
        # Estructura básica del formulario
        nuevo_formulario = {
            "titulo": titulo,
            "activo": True,
            "descripcion": "",
            "campos": []
        }
        
        print("Guardando archivo...")  # Debug
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(nuevo_formulario, f, ensure_ascii=False, indent=2)
        
        print("✅ Archivo guardado exitosamente")  # Debug
        return jsonify({
            "success": True, 
            "message": "Formulario creado correctamente", 
            "nombre": nombre_archivo
        })
        
    except Exception as e:
        print(f"❌ Error exception: {str(e)}")  # Debug
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Debug
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/formulario/<nombre>/eliminar", methods=["POST"])
def eliminar_formulario(nombre):
    """Eliminar un formulario"""
    try:
        ruta = os.path.join(FORMS_DIR, f"{nombre}.json")
        
        if os.path.exists(ruta):
            os.remove(ruta)
            return jsonify({"success": True, "message": "Formulario eliminado correctamente"})
        else:
            return jsonify({"success": False, "error": "Formulario no encontrado"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
def verificar_archivo_formulario(ruta):
    """Verifica que el archivo de formulario exista y sea JSON válido"""
    if not os.path.exists(ruta):
        return False, "El archivo no existe"
    
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            json.load(f)
        return True, "OK"
    except json.JSONDecodeError as e:
        return False, f"JSON inválido: {str(e)}"
    except Exception as e:
        return False, f"Error al leer archivo: {str(e)}"
    
@app.route("/admin/qr-generator")
def qr_generator():
    """Página para generar códigos QR de formularios"""
    formularios = []
    
    if os.path.exists(FORMS_DIR):
        for archivo in os.listdir(FORMS_DIR):
            if archivo.endswith(".json"):
                ruta = os.path.join(FORMS_DIR, archivo)
                with open(ruta, "r", encoding="utf-8") as f:
                    try:
                        config = json.load(f)
                        nombre = os.path.splitext(archivo)[0]
                        formularios.append({
                            "nombre": nombre,
                            "titulo": config.get("titulo", nombre),
                            "descripcion": config.get("descripcion", ""),
                            "activo": config.get("activo", True)
                        })
                    except json.JSONDecodeError:
                        pass
    
    return render_template("qr_generator.html", formularios=formularios)

@app.route("/admin/generar-qr/<nombre_formulario>")
def generar_qr(nombre_formulario):
    """Genera y devuelve un código QR para un formulario específico"""
    try:
        # Construir la URL del formulario
        base_url = request.host_url.rstrip('/')
        formulario_url = f"{base_url}/formulario/{nombre_formulario}"
        
        # Crear el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(formulario_url)
        qr.make(fit=True)
        
        # Crear imagen del QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return send_file(img_buffer, mimetype='image/png', download_name=f'qr_{nombre_formulario}.png')
        
    except Exception as e:
        return f"Error al generar QR: {str(e)}", 500

@app.route("/admin/generar-qr-base64/<nombre_formulario>")
def generar_qr_base64(nombre_formulario):
    """Genera un código QR en base64 para mostrar directamente en HTML"""
    try:
        # Construir la URL del formulario
        base_url = request.host_url.rstrip('/')
        formulario_url = f"{base_url}/formulario/{nombre_formulario}"
        
        # Crear el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=2,
        )
        qr.add_data(formulario_url)
        qr.make(fit=True)
        
        # Crear imagen del QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            "success": True,
            "qr_image": f"data:image/png;base64,{img_data}",
            "formulario_url": formulario_url,
            "nombre_formulario": nombre_formulario
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/admin/registros")
def registros():
    archivos = []
    if os.path.exists(DATA_DIR):
        for archivo in os.listdir(DATA_DIR):
            if archivo.endswith(".csv"):
                ruta = os.path.join(DATA_DIR, archivo)
                tamaño = os.path.getsize(ruta) / 1024  # KB
                archivos.append({
                    "nombre": archivo,
                    "tamaño": f"{tamaño:.2f} KB"
                })
    return render_template("/registros.html", archivos=archivos)


@app.route("/descargar/<nombre>")
def descargar(nombre):
    return send_from_directory(DATA_DIR, nombre, as_attachment=True)
    

# -----------------------
# Ejecutar servidor
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)