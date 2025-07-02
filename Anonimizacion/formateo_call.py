from jinja2 import Template  

def formateo_call_datos_personales(transcript): 
    """
    Envía un fragmento del contrato a AWS Bedrock y obtiene los datos personales sensibles.
    Esta es la primera fase del procesamiento que se enfoca en datos personales e identificadores.
    """
    template_string = """
    Necesito que proceses el siguiente párrafo en busca de DATOS PERSONALES E IDENTIFICADORES y devuelvas **exclusivamente** la siguiente estructura JSON (sin texto adicional). El contenido del párrafo viene dentro de la etiqueta `<data>`:
    
    <data>{{ transcript }}</data>
    
    Las categorías a extraer en esta primera fase son:

    - Nombres (nombres propios de personas)
    - Apellidos (apellidos de personas)
    - DNI (documentos nacionales de identidad españoles, formato: 8 dígitos + letra)
    - NIE (número de identidad de extranjero, formato: X/Y/Z + 7 dígitos + letra)
    - Pasaporte (números de pasaporte)
    - Numero_telefonico (cualquier número de teléfono)
    - IBAN (códigos bancarios internacionales)
    - Emails (direcciones de correo electrónico)
    - Identificador_fiscal (CIF, NIF u otros identificadores fiscales)
    - Otros_Identificadores_Numericos (cualquier otro identificador numérico relevante)

    La respuesta **solo** debe ser un JSON válido con esta forma de ejemplo:

    {
    "Nombres": ["<nombre1>", "<nombre2>"],
    "Apellidos": ["<apellido1>", "<apellido2>"],
    "DNI": ["<dni1>", "<dni2>"],
    "NIE": ["<nie1>", "<nie2>"],
    "Pasaporte": ["<pasaporte1>", "<pasaporte2>"],
    "Numero_telefonico": ["<numero1>", "<numero2>"],
    "IBAN": ["<iban1>", "<iban2>"],
    "Emails": ["<email1>", "<email2>"],
    "Identificador_fiscal": ["<identificador1>", "<identificador2>"],
    "Otros_Identificadores_Numericos": ["<otro_identificador1>", "<otro_identificador2>"]
    }

    Si alguna categoría no aplica, devuélvela con un array vacío. 
    No incluyas texto adicional, solo el objeto JSON.
    """
    
    template = Template(template_string)
    prompt = template.render(transcript=transcript)
    return prompt

def formateo_call_datos_contextuales(transcript): 
    """
    Envía un fragmento del contrato a AWS Bedrock y obtiene los datos contextuales y referencias.
    Esta es la segunda fase del procesamiento que se enfoca en datos contextuales y referencias.
    """
    template_string = """
    Necesito que proceses el siguiente párrafo en busca de DATOS CONTEXTUALES Y REFERENCIAS y devuelvas **exclusivamente** la siguiente estructura JSON (sin texto adicional). El contenido del párrafo viene dentro de la etiqueta `<data>`:
    
    <data>{{ transcript }}</data>
    
    Las categorías a extraer en esta segunda fase son:

    - Referencia_catastral (referencias catastrales de inmuebles)
    - Fechas (cualquier fecha mencionada)
    - Valores_monetarios (cantidades de dinero con o sin símbolo monetario)
    - Regiones (comunidades autónomas, provincias, etc.)
    - Nombres_Empresas (nombres de compañías, sociedades o entidades)
    - Paises (nombres de países)
    - Ciudades (nombres de ciudades)
    - Direcciones (direcciones postales completas o parciales)
    - Porcentajes (valores porcentuales)
    - Cuantias_en_palabras (cantidades escritas en texto, como "dos millones")
    - Codigos_postales (códigos postales)
    - Numero_participaciones (número de acciones o participaciones)
    - Hojas_registrales (referencias a hojas de registro)
    - Otros (información sensible que no encaja en las categorías anteriores)

    La respuesta **solo** debe ser un JSON válido con esta forma de ejemplo:

    {
    "Referencia_catastral": ["<referencia1>", "<referencia2>"],
    "Fechas": ["<fecha1>", "<fecha2>"],
    "Valores_monetarios": ["<valor1>", "<valor2>"],
    "Regiones": ["<region1>", "<region2>"],
    "Nombres_Empresas": ["<empresa1>", "<empresa2>"],
    "Paises": ["<pais1>", "<pais2>"],
    "Ciudades": ["<ciudad1>", "<ciudad2>"],
    "Direcciones": ["<direccion1>", "<direccion2>"],
    "Porcentajes": ["<porcentaje1>", "<porcentaje2>"],
    "Cuantias_en_palabras": ["<cuantia_en_palabra1>", "<cuantia_en_palabra2>"],
    "Codigos_postales": ["<codigo_postal1>", "<codigo_postal2>"],
    "Numero_participaciones": ["<participacion1>", "<participacion2>"],
    "Hojas_registrales": ["<hoja_registral1>", "<hoja_registral2>"],
    "Otros": ["<otros1>", "<otros2>"]
    }

    Si alguna categoría no aplica, devuélvela con un array vacío. 
    No incluyas texto adicional, solo el objeto JSON.
    """
    
    template = Template(template_string)
    prompt = template.render(transcript=transcript)
    return prompt