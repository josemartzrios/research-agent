"""
🔧 tools.py - Herramientas del Agente Experto en Estadísticas de México

Herramientas disponibles:
  1. consultar_inegi   → Indicadores del INEGI (empleo, pobreza, demografía, PIB...)
  2. consultar_banxico → Indicadores de Banxico (inflación, tipo de cambio, tasas...)
  3. buscar_en_web     → Búsqueda general para contexto adicional
"""

import os
import requests
from ddgs import DDGS
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# CATÁLOGO DE INDICADORES INEGI
# =============================================================================
# Estos son los IDs de series del Banco de Indicadores INEGI (BIE).
# El agente puede mencionar el nombre y el código busca el ID correcto.

INDICADORES_INEGI = {
    # --- Empleo y mercado laboral ---
    "tasa_desocupacion":              "444612",   # Tasa de desocupación nacional
    "tasa_desocupacion_hombres":      "444614",   # Por sexo: hombres
    "tasa_desocupacion_mujeres":      "444616",   # Por sexo: mujeres
    "poblacion_economicamente_activa":"444556",   # PEA total
    "pea_mujeres":                    "444558",   # PEA mujeres
    "pea_hombres":                    "444557",   # PEA hombres
    "tasa_participacion_laboral":     "444554",   # TASAS de participación económica
    "participacion_laboral_mujeres":  "444560",   # Participación laboral femenina
    "participacion_laboral_hombres":  "444559",   # Participación laboral masculina
    "ocupacion_informal":             "444678",   # Tasa de informalidad laboral

    # --- Precios e inflación ---
    "inflacion_general":              "216064",   # INPC variación anual
    "inflacion_subyacente":           "382552",   # Inflación subyacente

    # --- Pobreza y bienestar ---
    "porcentaje_pobreza":             "539086",   # % pob. en pobreza (CONEVAL/INEGI)
    "pobreza_extrema":                "539087",   # % pobreza extrema

    # --- Actividad económica ---
    "igae":                           "493024",   # IGAE (indicador adelantado del PIB)
    "pib_anual":                      "381016",   # PIB a precios constantes

    # --- Demografía ---
    "poblacion_total":                "1002000001", # Población total proyectada
}


# =============================================================================
# CATÁLOGO DE INDICADORES BANXICO
# =============================================================================
# Series del Sistema de Información Económica (SIE) del Banco de México

INDICADORES_BANXICO = {
    "tipo_cambio_dolar":   "SF43718",  # Tipo de cambio FIX (pesos por dólar)
    "tasa_fondeo":         "SF61745",  # Tasa de fondeo bancario (tasa objetivo Banxico)
    "inflacion_mensual":   "SP1",      # Inflación mensual INPC
    "reservas_int":        "SF290383", # Reservas internacionales (millones de USD)
    "m1":                  "SF311408", # Agregado monetario M1
    "credito_consumo":     "SF44070",  # Crédito al consumo de la banca comercial
}


# =============================================================================
# DEFINICIÓN DE HERRAMIENTAS PARA ANTHROPIC
# =============================================================================

TOOLS = [
    {
        "name": "consultar_inegi",
        "description": (
            "Consulta indicadores estadísticos oficiales de México del INEGI "
            "(Instituto Nacional de Estadística y Geografía). "
            "Usa esta herramienta para obtener datos sobre:\n"
            "- Empleo y mercado laboral (desocupación, participación laboral por género)\n"
            "- Pobreza y bienestar social\n"
            "- Actividad económica (IGAE, PIB)\n"
            "- Demografía (población)\n"
            "- Inflación (INPC)\n\n"
            "Indicadores disponibles: "
            + ", ".join(INDICADORES_INEGI.keys())
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "indicador": {
                    "type": "string",
                    "description": (
                        "Nombre del indicador a consultar. Debe ser uno de: "
                        + ", ".join(INDICADORES_INEGI.keys())
                    )
                },
                "periodos": {
                    "type": "integer",
                    "description": "Número de periodos históricos a obtener (default: 8, max: 20)"
                }
            },
            "required": ["indicador"]
        }
    },
    {
        "name": "consultar_banxico",
        "description": (
            "Consulta indicadores financieros y monetarios de México del Banco de México (Banxico). "
            "Usa esta herramienta para obtener datos sobre:\n"
            "- Tipo de cambio peso-dólar\n"
            "- Tasas de interés (tasa objetivo de Banxico)\n"
            "- Reservas internacionales\n"
            "- Agregados monetarios\n"
            "- Crédito bancario\n\n"
            "Indicadores disponibles: "
            + ", ".join(INDICADORES_BANXICO.keys())
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "indicador": {
                    "type": "string",
                    "description": (
                        "Nombre del indicador a consultar. Debe ser uno de: "
                        + ", ".join(INDICADORES_BANXICO.keys())
                    )
                },
                "periodos": {
                    "type": "integer",
                    "description": "Número de periodos históricos a obtener (default: 8, max: 20)"
                }
            },
            "required": ["indicador"]
        }
    },
    {
        "name": "buscar_en_web",
        "description": (
            "Busca información complementaria en internet. Úsala para:\n"
            "- Obtener contexto sobre un indicador\n"
            "- Buscar noticias o análisis recientes\n"
            "- Encontrar información que no esté en las APIs anteriores\n"
            "Siempre prefiere las herramientas de INEGI o Banxico para datos numéricos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "La consulta de búsqueda web."
                }
            },
            "required": ["consulta"]
        }
    }
]


# =============================================================================
# IMPLEMENTACIÓN: INEGI
# =============================================================================

def consultar_inegi(indicador: str, periodos: int = 8) -> str:
    """
    Consulta el API BIE del INEGI.
    Requiere token en .env como INEGI_TOKEN.
    """
    token = os.getenv("INEGI_TOKEN")
    if not token:
        return (
            "⚠️ No hay token de INEGI configurado. "
            "Obtén uno gratis en: https://www.inegi.org.mx/servicios/api_biinegi.html\n"
            "Agrega INEGI_TOKEN=tu-token en el archivo .env"
        )

    indicador = indicador.lower().strip()
    if indicador not in INDICADORES_INEGI:
        return (
            f"Indicador '{indicador}' no encontrado. "
            f"Disponibles: {', '.join(INDICADORES_INEGI.keys())}"
        )

    serie_id = INDICADORES_INEGI[indicador]
    periodos = min(periodos, 20)

    url = (
        f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
        f"INDICATOR/{serie_id}/es/0910/false/BIE/2.0/{token}?type=json"
    )

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        serie = data.get("Series", [{}])[0]
        nombre = serie.get("INDICADOR", indicador)
        unidad = serie.get("UNIDAD", "")
        obs = serie.get("OBSERVATIONS", [])

        if not obs:
            return f"No se encontraron observaciones para '{indicador}'."

        # Tomar los últimos N periodos
        obs_recientes = obs[-periodos:]

        lineas = [f"📊 **{nombre}** ({unidad})"]
        lineas.append(f"Fuente: INEGI | Últimos {len(obs_recientes)} periodos\n")
        for o in obs_recientes:
            periodo = o.get("TIME_PERIOD", "?")
            valor   = o.get("OBS_VALUE", "?")
            lineas.append(f"  {periodo}: {valor}")

        return "\n".join(lineas)

    except requests.HTTPError as e:
        return f"Error HTTP al consultar INEGI: {e}"
    except Exception as e:
        return f"Error al consultar INEGI: {str(e)}"


# =============================================================================
# IMPLEMENTACIÓN: BANXICO
# =============================================================================

def consultar_banxico(indicador: str, periodos: int = 8) -> str:
    """
    Consulta el SIE API del Banco de México.
    Requiere token en .env como BANXICO_TOKEN.
    """
    token = os.getenv("BANXICO_TOKEN")
    if not token:
        return (
            "⚠️ No hay token de Banxico configurado. "
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
    periodos = min(periodos, 20)

    url = (
        f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/"
        f"{serie_id}/datos/oportuno"
    )
    headers = {"Bmx-Token": token}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        bmx  = data.get("bmx", {})
        series = bmx.get("series", [{}])[0]
        titulo = series.get("titulo", indicador)
        datos  = series.get("datos", [])

        if not datos:
            return f"No se encontraron datos para '{indicador}'."

        datos_recientes = datos[-periodos:]

        lineas = [f"🏦 **{titulo}**"]
        lineas.append(f"Fuente: Banxico | Últimos {len(datos_recientes)} registros\n")
        for d in datos_recientes:
            fecha = d.get("fecha", "?")
            dato  = d.get("dato", "?")
            lineas.append(f"  {fecha}: {dato}")

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
    "consultar_inegi":   consultar_inegi,
    "consultar_banxico": consultar_banxico,
    "buscar_en_web":     buscar_en_web,
}

def ejecutar_herramienta(nombre: str, argumentos: dict) -> str:
    if nombre not in TOOL_DISPATCHER:
        return f"Error: Herramienta '{nombre}' no encontrada."
    return TOOL_DISPATCHER[nombre](**argumentos)
