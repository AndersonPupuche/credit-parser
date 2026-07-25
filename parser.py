import re
import pdfplumber


# ============================================
# LEER TEXTO DEL PDF
# ============================================

def extract_text(pdf_path):

    texto = ""

    with pdfplumber.open(pdf_path) as pdf:

        for pagina in pdf.pages:

            contenido = pagina.extract_text()

            if contenido:
                texto += contenido + "\n"

    return texto


# ============================================
# EXTRAER NOMBRE
# ============================================

def extract_name(text):

    # Buscar el nombre principal
    patron = re.search(
        r'Name:\s*([A-Z]+),\s*([A-Z ]+)',
        text
    )

    if patron:

        apellido = patron.group(1).title().strip()

        nombre = patron.group(2).title().strip()

        return f"{nombre} {apellido}"

    return "No encontrado"


# ============================================
# EXTRAER SCORE
# ============================================

def extract_score(text):

    patron = re.search(
        r'VANTAGESCORE\s+\d+\s+\+?(\d{3})',
        text
    )

    if patron:
        return int(patron.group(1))

    return 0


# ============================================
# EXTRAER GASTOS MENSUALES
# ============================================


def extract_gastos(text):

    total = 0

    # Dividir por cada cuenta
    cuentas = re.split(r'(?=[A-Z0-9/ ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)', text)

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        # Ignorar cuentas cerradas
        if (
            "CLOSED BY CREDIT GRANTOR" in cuenta_mayus
            or "ACCOUNT CLOSED DUE TO REFINANCE" in cuenta_mayus
            or "ACCOUNT CLOSED DUE TO TRANSFER" in cuenta_mayus
            or "PAID IN FULL" in cuenta_mayus
            or "INACTIVE ACCOUNT" in cuenta_mayus
            or "PURCHASED BY ANOTHER LENDER" in cuenta_mayus
            or re.search(r"Remarks:\s*CLOSED\b", cuenta_mayus)
        ):
            continue

        # Buscar el campo Terms
        termino = re.search(r"Terms:\s*([A-Z0-9]+)", cuenta)

        if not termino:
            continue

        termino = termino.group(1)

        # Extraer el pago mensual
        valor = None

        # Formato: uno o más dígitos + cualquier letra + monto
        pago = re.search(r"\d+[A-Z](\d+)", termino)

        if pago:
            valor = int(pago.group(1))

        else:
            # Formato: MIN36
            pago = re.search(r"MIN(\d+)", termino)

            if pago:
                valor = int(pago.group(1))

            else:
                # Formato: M441, C250, A180, etc.
                pago = re.search(r"^[A-Z](\d+)$", termino)

                if pago:
                    valor = int(pago.group(1))

        if valor is not None:

             total += valor

             print(f"Pago encontrado: {valor}")

    print("TOTAL =", total)

    return total

# ============================================
# IDENTIFICADOR DE SEGUNDO CLIENTE
# ============================================

def separar_clientes(text):

    marcador = "INPUT PARAMETERS FOR SECONDARY SUBJECT"

    # Si no existe un segundo cliente
    if marcador not in text:
        return [text]

    # Dividir el reporte en dos partes
    partes = text.split(marcador, 1)

    cliente1 = partes[0]

    # Volvemos a agregar el encabezado para que las funciones sigan funcionando
    cliente2 = marcador + partes[1]

    return [cliente1, cliente2]

# ============================================
# PROCESAR PDF
# ============================================

def process_pdf(pdf_path):

    texto = extract_text(pdf_path)

    clientes = separar_clientes(texto)

    resultados = []

    for cliente in clientes:

        resultados.append({

            "nombre": extract_name(cliente),

            "score": extract_score(cliente),

            "gastos": extract_gastos(cliente)

        })

    return resultados
