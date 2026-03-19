"""
🔧 tools.py - Herramientas del Agente Experto en Estadísticas de México

Fuentes de datos:
  1. World Bank API  → Indicadores económicos y sociales de México (sin API key)
  2. Banxico API     → Tipo de cambio, tasas, reservas (requiere token gratuito)
  3. DuckDuckGo      → Búsqueda web para contexto y noticias recientes
"""

import os
import requests
from ddgs import DDGS
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# CATÁLOGO DE INDICADORES — WORLD BANK
# =============================================================================
# Fuente oficial del Banco Mundial. Sin API key, datos anuales para México.

INDICADORES_WB = {
    # Empleo y mercado laboral
    "desempleo":                   "SL.UEM.TOTL.ZS",    # Tasa de desempleo (% fuerza laboral)
    "participacion_laboral_total": "SL.TLF.CACT.ZS",    # Participación laboral total (%)
    "participacion_laboral_mujer": "SL.TLF.CACT.FE.ZS", # Participación laboral femenina (%)
    "participacion_laboral_hombre":"SL.TLF.CACT.MA.ZS", # Participación laboral masculina (%)
    "desempleo_mujer":             "SL.UEM.TOTL.FE.ZS", # Desempleo femenino (%)
    "desempleo_hombre":            "SL.UEM.TOTL.MA.ZS", # Desempleo masculino (%)
    "desempleo_jovenes":           "SL.UEM.1524.ZS",    # Desempleo jóvenes 15-24 (%)

    # Economía y crecimiento
    "pib_crecimiento":             "NY.GDP.MKTP.KD.ZG", # Crecimiento PIB anual (%)
    "pib_per_capita":              "NY.GDP.PCAP.CD",    # PIB per cápita (USD corrientes)
    "pib_total":                   "NY.GDP.MKTP.CD",    # PIB total (USD corrientes)
    "exportaciones":               "NE.EXP.GNFS.ZS",    # Exportaciones (% del PIB)
    "importaciones":               "NE.IMP.GNFS.ZS",    # Importaciones (% del PIB)
    "inversion_extranjera":        "BX.KLT.DINV.WD.GD.ZS", # IED (% del PIB)

    # Precios
    "inflacion":                   "FP.CPI.TOTL.ZG",    # Inflación anual (%)

    # Pobreza y desigualdad
    "pobreza":                     "SI.POV.NAHC",       # Pobreza (% bajo línea nacional)
    "gini":                        "SI.POV.GINI",       # Coeficiente GINI (0-100)

    # Demografía
    "poblacion_total":             "SP.POP.TOTL",       # Población total
    "crecimiento_poblacional":     "SP.POP.GROW",       # Crecimiento poblacional (%)
    "poblacion_urbana":            "SP.URB.TOTL.IN.ZS", # Población urbana (%)

    # Educación y salud
    "gasto_educacion":             "SE.XPD.TOTL.GD.ZS", # Gasto en educación (% del PIB)
    "esperanza_vida":              "SP.DYN.LE00.IN",    # Esperanza de vida al nacer
}


# =============================================================================
# CATÁLOGO DE INDICADORES — BANXICO
# =============================================================================

INDICADORES_BANXICO = {
    "tipo_cambio_dolar":   "SF43718",   # Tipo de cambio FIX (pesos por dólar)
    "tasa_fondeo":         "SF61745",   # Tasa objetivo Banxico
    "reservas_int":        "SF290383",  # Reservas internacionales (millones USD)
    "m1":                  "SF311408",  # Agregado monetario M1
    "credito_consumo":     "SF44070",   # Crédito al consumo banca comercial
}


# =============================================================================
# DEFINICIÓN DE HERRAMIENTAS PARA ANTHROPIC
# =============================================================================

TOOLS = [
    {
        "name": "consultar_world_bank",
        "description": (
            "Consulta indicadores económicos y sociales de México del Banco Mundial. "
            "Datos anuales oficiales, sin API key, muy confiables.\n\n"
            "Úsala para datos sobre:\n"
            "- Empleo: desempleo, participacion_laboral_mujer, participacion_laboral_hombre, "
            "desempleo_jovenes\n"
            "- Economía: pib_crecimiento, pib_per_capita, inflacion, exportaciones\n"
            "- Pobreza y desigualdad: pobreza, gini\n"
            "- Demografía: poblacion_total, poblacion_urbana\n"
            "- Educación/Salud: gasto_educacion, esperanza_vida\n\n"
            "Indicadores disponibles: " + ", ".join(INDICADORES_WB.keys())
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "indicador": {
                    "type": "string",
                    "description": (
                        "Nombre del indicador. Uno de: "
                        + ", ".join(INDICADORES_WB.keys())
                    )
                },
                "anios": {
                    "type": "integer",
                    "description": "Años de historia a obtener (default: 10, max: 30)"
                }
            },
            "required": ["indicador"]
        }
    },
    {
        "name": "consultar_banxico",
        "description": (
            "Consulta indicadores financieros de México del Banco de México (Banxico). "
            "Datos en tiempo real (diarios/mensuales).\n\n"
            "Úsala para datos sobre:\n"
            "- tipo_cambio_dolar (FIX, dato diario)\n"
            "- tasa_fondeo (tasa objetivo de Banxico)\n"
            "- reservas_int (reservas internacionales en millones USD)\n"
            "- credito_consumo (crédito al consumo)\n\n"
            "Indicadores disponibles: " + ", ".join(INDICADORES_BANXICO.keys())
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "indicador": {
                    "type": "string",
                    "description": (
                        "Nombre del indicador. Uno de: "
                        + ", ".join(INDICADORES_BANXICO.keys())
                    )
                },
                "periodos": {
                    "type": "integer",
                    "description": "Número de periodos a obtener (default: 12, max: 36)"
                }
            },
            "required": ["indicador"]
        }
    },
    {
        "name": "buscar_en_web",
        "description": (
            "Busca información complementaria en internet. Úsala para:\n"
            "- Contexto, causas o explicaciones de un indicador\n"
            "- Noticias recientes sobre la economía mexicana\n"
            "- Información que no esté en World Bank o Banxico\n"
            "Siempre prefiere las herramientas de datos para cifras numéricas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "La consulta de búsqueda."
                }
            },
            "required": ["consulta"]
        }
    }
]


# =============================================================================
# IMPLEMENTACIÓN: WORLD BANK
# =============================================================================

def consultar_world_bank(indicador: str, anios: int = 10) -> str:
    """Consulta el World Bank Open Data API para México. Sin API key."""
    indicador = indicador.lower().strip()

    if indicador not in INDICADORES_WB:
        return (
            f"Indicador '{indicador}' no encontrado. "
            f"Disponibles: {', '.join(INDICADORES_WB.keys())}"
        )

    codigo = INDICADORES_WB[indicador]
    anios  = min(anios, 30)

    url = (
        f"https://api.worldbank.org/v2/country/MX/indicator/{codigo}"
        f"?format=json&mrv={anios}&per_page={anios}"
    )

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if len(data) < 2 or not data[1]:
            return f"No se encontraron datos para '{indicador}'."

        registros = data[1]
        # Filtrar los que tienen valor (algunos años pueden ser None)
        validos = [r for r in registros if r.get("value") is not None]
        validos_ordenados = sorted(validos, key=lambda x: x.get("date", "0"))

        if not validos_ordenados:
            return f"No hay datos disponibles para '{indicador}' en los últimos {anios} años."

        meta = data[0]
        nombre_ind = registros[0].get("indicator", {}).get("value", indicador)
        ultimo = validos_ordenados[-1]

        lineas = [
            f"📊 **{nombre_ind}** — México",
            f"Fuente: World Bank Open Data | Últimos {len(validos_ordenados)} años con datos\n"
        ]
        for r in validos_ordenados:
            anio  = r.get("date", "?")
            valor = r.get("value")
            if valor is not None:
                lineas.append(f"  {anio}: {round(valor, 2)}")

        lineas.append(f"\n  → Dato más reciente: {ultimo['date']} = {round(ultimo['value'], 2)}")
        return "\n".join(lineas)

    except requests.HTTPError as e:
        return f"Error HTTP al consultar World Bank: {e}"
    except Exception as e:
        return f"Error al consultar World Bank: {str(e)}"


# =============================================================================
# IMPLEMENTACIÓN: BANXICO
# =============================================================================

def consultar_banxico(indicador: str, periodos: int = 12) -> str:
    """Consulta el SIE API del Banco de México. Requiere BANXICO_TOKEN en .env"""
    token = os.getenv("BANXICO_TOKEN")
    if not token or token == "tu-token-banxico-aqui":
        return (
            "⚠️ No hay token de Banxico configurado.\n"
            "Obtén uno gratis en: https://www.banxico.org.mx/SieAPIRest/service/v1/\n"
            "Agrega BANXICO_TOKEN=tu-token en el archivo .env"
        )

    indicador = indicador.lower().strip()
    if indicador not in INDICADORES_BANXICO:
        return (
            f"Indicador '{indicador}' no encontrado. "
            f"Disponibles: {', '.join(INDICADORES_BANXICO.keys())}"
        )

    serie_id = INDICADORES_BANXICO[indicador]
    periodos = min(periodos, 36)

    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie_id}/datos/oportuno"
    headers = {"Bmx-Token": token}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        series = data.get("bmx", {}).get("series", [{}])[0]
        titulo = series.get("titulo", indicador)
        datos  = series.get("datos", [])

        if not datos:
            return f"No se encontraron datos para '{indicador}'."

        datos_recientes = datos[-periodos:]

        lineas = [
            f"🏦 **{titulo}** — México",
            f"Fuente: Banco de México | Últimos {len(datos_recientes)} periodos\n"
        ]
        for d in datos_recientes:
            lineas.append(f"  {d.get('fecha', '?')}: {d.get('dato', '?')}")

        return "\n".join(lineas)

    except requests.HTTPError as e:
        return f"Error HTTP al consultar Banxico: {e}"
    except Exception as e:
        return f"Error al consultar Banxico: {str(e)}"


# =============================================================================
# IMPLEMENTACIÓN: BÚSQUEDA WEB
# =============================================================================

def buscar_en_web(consulta: str) -> str:
    """Búsqueda web con DuckDuckGo para contexto adicional."""
    try:
        resultados = DDGS().text(keywords=consulta, max_results=5)
        if not resultados:
            return "No se encontraron resultados."
        texto = []
        for i, r in enumerate(resultados, 1):
            texto.append(
                f"[Resultado {i}]\n"
                f"  Título: {r.get('title', '')}\n"
                f"  URL: {r.get('href', '')}\n"
                f"  Resumen: {r.get('body', '')}\n"
            )
        return "\n".join(texto)
    except Exception as e:
        return f"Error al buscar: {str(e)}"


# =============================================================================
# DESPACHADOR
# =============================================================================

TOOL_DISPATCHER = {
    "consultar_world_bank": consultar_world_bank,
    "consultar_banxico":    consultar_banxico,
    "buscar_en_web":        buscar_en_web,
}

def ejecutar_herramienta(nombre: str, argumentos: dict) -> str:
    if nombre not in TOOL_DISPATCHER:
        return f"Error: Herramienta '{nombre}' no encontrada."
    return TOOL_DISPATCHER[nombre](**argumentos)
