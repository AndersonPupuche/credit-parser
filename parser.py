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
# NIVEL DE RIESGO
# ============================================

def extract_riesgo(score):

    if score >= 800:
        return "Excelente"

    elif score >= 740:
        return "Muy Bueno"

    elif score >= 670:
        return "Bueno"

    elif score >= 580:
        return "Medio"

    else:
        return "Alto"

# ============================================
# EXTRAER GASTOS MENSUALES
# ============================================


def extract_gastos(text):

    total = 0

    # Dividir por cada cuenta
    cuentas = re.split(r'(?=[A-Z0-9/&.,\'\- ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)',text)

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        # Si el campo Closed: tiene una fecha,
        # la cuenta ya no genera gasto mensual
        # ============================================
        if re.search(r"CLOSED:\s*\d{1,2}/\d{2}", cuenta_mayus):
            continue

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
# CONTAR CUENTAS ABIERTAS
# ============================================

def extract_open_accounts(text):

    total = 0

    cuentas = re.split(
        r'(?=[A-Z0-9/&.,\'\- ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)',
        text
    )

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        # Debe contener una cuenta
        if "ACCOUNT #" not in cuenta_mayus:
            continue

            # Ignorar Collections
        if (
            "TYPE: COLLECTION" in cuenta_mayus
            or "LOAN TYPE: COLLECTION" in cuenta_mayus
            or "ACCOUNT TYPE: OPEN" in cuenta_mayus
            or "ORIGINAL CREDITOR:" in cuenta_mayus
            or "AMOUNT PLACED:" in cuenta_mayus
        ):
            continue

        # Ignorar cuentas cerradas
        if (
            "CLOSED BY CREDIT GRANTOR" in cuenta_mayus
            or "ACCOUNT CLOSED DUE TO REFINANCE" in cuenta_mayus
            or "ACCOUNT CLOSED DUE TO TRANSFER" in cuenta_mayus
            or "ACCOUNT CLOSED BY CONSUMER" in cuenta_mayus
            or "TRANSFERRED TO ANOTHER LENDER" in cuenta_mayus
            or "PAID IN FULL" in cuenta_mayus
            or "INACTIVE ACCOUNT" in cuenta_mayus
            or "PURCHASED BY ANOTHER LENDER" in cuenta_mayus
            or "UNPAID BALANCE CHARGED OFF" in cuenta_mayus
            or re.search(r"REMARKS:\s*CLOSED\b", cuenta_mayus)
            or re.search(r"CLOSED:\s*\d{1,2}/\d{2}", cuenta_mayus)
        ):
            continue

        total += 1

    return total

# ============================================
# CONTAR COLLECTIONS
# ============================================

def extract_collections(text):

    total = 0

    # ==========================================
    # 1. Contar las cuentas dentro de COLLECTIONS
    # ==========================================

    match = re.search(
        r'COLLECTIONS(.*?)(?:TRADES|INQUIRIES|PUBLIC RECORDS|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )

    if match:

        seccion = match.group(1)

        total += len(re.findall(
            r'ACCOUNT\s*#',
            seccion,
            re.IGNORECASE
        ))

    # ==========================================
    # 2. Buscar COLLECTION fuera de esa sección
    # ==========================================

    cuentas = re.split(
        r'(?=[A-Z0-9/&.,\'\- ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)',
        text
    )

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        if (
            "TYPE: COLLECTION" in cuenta_mayus
            or "LOAN TYPE: COLLECTION" in cuenta_mayus
            or "REMARKS: COLLECTION" in cuenta_mayus
        ):

            # Si esta cuenta ya pertenece a la sección COLLECTIONS,
            # no volver a contarla.
            if "PLACED FOR COLLECTION" in cuenta_mayus:
                continue

            total += 1

    return total


# ============================================
# CONTAR CHARGE OFFS
# ============================================

def extract_charge_offs(text):

    total = 0

    cuentas = re.split(
        r'(?=[A-Z0-9/&.,\'\- ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)',
        text
    )

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        if "UNPAID BALANCE CHARGED OFF" in cuenta_mayus:
            total += 1

    return total


# ============================================
# CONTAR DISPUTAS
# ============================================


def extract_disputes(text):

    total = 0

    cuentas = re.split(
        r'(?=[A-Z0-9/&.,\'\- ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)',
        text
    )

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        if (
            "DISPUTE" in cuenta_mayus
            or "ACCOUNT INFORMATION DISPUTED BY CONSUMER" in cuenta_mayus
            or "CUSTOMER DISAGREES" in cuenta_mayus
            or "DISPUTE INVESTIGATION COMPLETE" in cuenta_mayus
        ):
            total += 1

    return total


# ============================================
# CONTAR INQUIRIES DEL AÑO ACTUAL
# ============================================

def extract_current_year_inquiries(text):

    # Año del reporte
    match = re.search(
        r"RESULTS ISSUED:\s*\d{1,2}/\d{1,2}/(\d{2})",
        text,
        re.IGNORECASE
    )

    if not match:
        return 0

    anio_actual = match.group(1)

    # Extraer solo la sección INQUIRIES
    match = re.search(
        r"INQUIRIES(.*)$",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if not match:
        return 0

    seccion = match.group(1)

    # Buscar fechas que correspondan a una fila de inquiry
    fechas = re.findall(
        r'(\d{1,2}/\d{1,2}/\d{2})\s+[A-Z]',
        seccion
    )

    total = 0

    for fecha in fechas:
        if fecha.endswith("/" + anio_actual):
            total += 1

    return total

# ============================================
# Calcular riesgo
# ============================================


def calcular_riesgo(score, limite_credito, cuentas_abiertas,
                    charge_offs, collections, disputas):

    puntos = 0

    if score >= 670:
        puntos += 1

    if limite_credito >= 9500:
        puntos += 1

    if cuentas_abiertas >= 3:
        puntos += 1

    if charge_offs <= 2:
        puntos += 1

    if collections <= 2:
        puntos += 1

    if disputas <= 2:
        puntos += 1

    if puntos == 6:
        return "Bajo"

    elif puntos >= 4:
        return "Medio"

    else:
        return "Alto"


# ============================================
# EXTRAER LIMITE TOTAL DE CREDITO
# ============================================

def extract_credit_limit(text):

    total = 0

    cuentas = re.split(
        r'(?=[A-Z0-9/&.,\'\- ]+\s+\([A-Z]\s+[A-Z0-9]+\)\s+Account #)',
        text
    )

    for cuenta in cuentas:

        cuenta_mayus = cuenta.upper()

        # Ignorar Collections
        if "ORIGINAL CREDITOR:" in cuenta_mayus:
            continue

        # Ignorar cuentas cerradas
        if re.search(r'CLOSED:\s*\d{1,2}/\d{2,4}', cuenta_mayus):
            continue

        if (
            "CLOSED BY CREDIT GRANTOR" in cuenta_mayus
            or "ACCOUNT CLOSED DUE TO REFINANCE" in cuenta_mayus
            or "ACCOUNT CLOSED DUE TO TRANSFER" in cuenta_mayus
            or "ACCOUNT CLOSED BY CONSUMER" in cuenta_mayus
            or "TRANSFERRED TO ANOTHER LENDER" in cuenta_mayus
            or "PAID IN FULL" in cuenta_mayus
            or "INACTIVE ACCOUNT" in cuenta_mayus
            or "PURCHASED BY ANOTHER LENDER" in cuenta_mayus
            or "UNPAID BALANCE CHARGED OFF" in cuenta_mayus
        ):
            continue

        # Primero buscar Credit Limit
        match = re.search(
            r'CREDIT LIMIT:\s*\$?([\d,]+)',
            cuenta,
            re.IGNORECASE
        )

        # Si no existe Credit Limit, buscar High Credit
        if not match:
            match = re.search(
                r'HIGH CREDIT:\s*\$?([\d,]+)',
                cuenta,
                re.IGNORECASE
            )

        if match:
            limite = int(match.group(1).replace(",", ""))
            total += limite

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

        score = extract_score(cliente)

        limite_credito = extract_credit_limit(cliente)
        cuentas_abiertas = extract_open_accounts(cliente)
        charge_offs = extract_charge_offs(cliente)
        collections = extract_collections(cliente)
        disputas = extract_disputes(cliente)

        resultados.append({

            "nombre": extract_name(cliente),

            "score": score,

            "riesgo": calcular_riesgo(
                score,
                limite_credito,
                cuentas_abiertas,
                charge_offs,
                collections,
                disputas
            ),

            "gastos": extract_gastos(cliente),

            "limite_credito": limite_credito,

            "cuentas_abiertas": extract_open_accounts(cliente),

            "collections": extract_collections(cliente),

            "charge_offs": extract_charge_offs(cliente),

            "disputes": extract_disputes(cliente),

            "inquiries": extract_current_year_inquiries(cliente)

        })

    return resultados
