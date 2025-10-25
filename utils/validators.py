import re

def validar_input(valor, campo):
    tipo = campo.get("tipo")
    opciones = campo.get("opciones", [])

    # Texto libre
    if tipo == "text":
        if not valor:
            return not campo.get("obligatorio", False)
        # Solo letras y espacios opcional
        return bool(re.match(r"^[\w\sáéíóúÁÉÍÓÚñÑ.,-]*$", valor))

    # Correo electrónico
    if tipo == "email":
        if not valor:
            return not campo.get("obligatorio", False)
        return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", valor))

    # Número
    if tipo == "number":
        if not valor:
            return not campo.get("obligatorio", False)
        if not valor.isdigit():
            return False
        # Validar longitud exacta si se especifica
        longitud = campo.get("longitud")
        if longitud and len(valor) != longitud:
            return False
        # Opcional: rango mínimo/máximo
        minimo = campo.get("min")
        maximo = campo.get("max")
        if minimo and int(valor) < minimo:
            return False
        if maximo and int(valor) > maximo:
            return False
        return True


    # Select
    if tipo == "select":
        if not valor:
            return not campo.get("obligatorio", False)
        return valor in opciones

    # Checkbox (lista de valores)
    if tipo == "checkbox":
        if not valor:
            return not campo.get("obligatorio", False)
        
        valores_lista = valor if isinstance(valor, list) else [valor]
        
        # Validar cantidad de opciones
        if not campo.get("multiple", True) and len(valores_lista) > 1:
            return False
        
        # Validar que las opciones sean válidas
        return all(v in opciones for v in valores_lista)
    
    # Radio
    if tipo == "radio":
        if not valor:
            return not campo.get("obligatorio", False)
        return valor in opciones

    # Textarea
    if tipo == "textarea":
        if not valor:
            return not campo.get("obligatorio", False)
        # Opcional: longitud máxima 500
        return len(valor) <= 500

    return True  # Por defecto, pasa la validación
