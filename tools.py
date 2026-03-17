"""
🔧 tools.py - Herramientas que el agente puede usar

Este archivo define las "herramientas" (tools) disponibles para el agente.
Piensa en ellas como superpoderes que le das al LLM:
- El LLM NO puede buscar en internet por sí solo
- Pero SI puede DECIDIR cuándo necesita buscar algo
- Cuando decide buscar, ejecutamos la búsqueda aquí y le devolvemos los resultados

Esto es el corazón del patrón "Tool Calling" / "Function Calling"
"""

from google.genai import types
from duckduckgo_search import DDGS


# =============================================================================
# 1. DEFINICIÓN DE HERRAMIENTAS PARA GOOGLE GEMINI
# =============================================================================
# Gemini necesita que le describas las herramientas usando FunctionDeclaration.
# Es como darle un "manual de instrucciones" al LLM sobre qué puede hacer.
# Nota: Gemini usa un formato diferente a Anthropic, pero el concepto es el mismo.

TOOL_DECLARATIONS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="buscar_en_web",
            description=(
                "Busca información actualizada en internet usando DuckDuckGo. "
                "Úsala cuando necesites datos recientes, hechos específicos, "
                "o información que no tengas en tu conocimiento base. "
                "Puedes buscar en español o inglés."
            ),
            parameters={
                "type": "OBJECT",
                "properties": {
                    "consulta": {
                        "type": "STRING",
                        "description": "La consulta de búsqueda. Sé específico para mejores resultados."
                    },
                    "max_resultados": {
                        "type": "INTEGER",
                        "description": "Número máximo de resultados a devolver (1-10). Por defecto 5."
                    }
                },
                "required": ["consulta"]
            }
        ),
        types.FunctionDeclaration(
            name="buscar_noticias",
            description=(
                "Busca noticias recientes sobre un tema específico. "
                "Úsala cuando el usuario pregunte sobre eventos actuales, "
                "noticias de última hora, o tendencias."
            ),
            parameters={
                "type": "OBJECT",
                "properties": {
                    "consulta": {
                        "type": "STRING",
                        "description": "El tema sobre el que buscar noticias."
                    },
                    "max_resultados": {
                        "type": "INTEGER",
                        "description": "Número máximo de noticias a devolver (1-10). Por defecto 5."
                    }
                },
                "required": ["consulta"]
            }
        )
    ]
)


# =============================================================================
# 2. IMPLEMENTACIÓN DE LAS HERRAMIENTAS
# =============================================================================
# Aquí es donde realmente se ejecuta la búsqueda.
# El LLM decide QUÉ buscar, nosotros ejecutamos el CÓMO.

def buscar_en_web(consulta: str, max_resultados: int = 5) -> str:
    """
    Realiza una búsqueda web usando DuckDuckGo (gratis, sin API key).
    
    Args:
        consulta: Qué buscar
        max_resultados: Cuántos resultados devolver
    
    Returns:
        String formateado con los resultados de búsqueda
    """
    try:
        resultados = DDGS().text(
            keywords=consulta,
            max_results=min(max_resultados, 10)  # Limitar a 10 máximo
        )
        
        if not resultados:
            return "No se encontraron resultados para esta búsqueda."
        
        # Formateamos los resultados de forma clara para el LLM
        texto = []
        for i, r in enumerate(resultados, 1):
            texto.append(
                f"[Resultado {i}]\n"
                f"  Título: {r.get('title', 'Sin título')}\n"
                f"  URL: {r.get('href', 'Sin URL')}\n"
                f"  Resumen: {r.get('body', 'Sin descripción')}\n"
            )
        
        return "\n".join(texto)
    
    except Exception as e:
        return f"Error al buscar: {str(e)}"


def buscar_noticias(consulta: str, max_resultados: int = 5) -> str:
    """
    Busca noticias recientes usando DuckDuckGo News.
    
    Args:
        consulta: Tema de las noticias
        max_resultados: Cuántos resultados devolver
    
    Returns:
        String formateado con las noticias encontradas
    """
    try:
        resultados = DDGS().news(
            keywords=consulta,
            max_results=min(max_resultados, 10)
        )
        
        if not resultados:
            return "No se encontraron noticias sobre este tema."
        
        texto = []
        for i, r in enumerate(resultados, 1):
            texto.append(
                f"[Noticia {i}]\n"
                f"  Título: {r.get('title', 'Sin título')}\n"
                f"  Fuente: {r.get('source', 'Desconocida')}\n"
                f"  Fecha: {r.get('date', 'Sin fecha')}\n"
                f"  URL: {r.get('url', 'Sin URL')}\n"
                f"  Resumen: {r.get('body', 'Sin descripción')}\n"
            )
        
        return "\n".join(texto)
    
    except Exception as e:
        return f"Error al buscar noticias: {str(e)}"


# =============================================================================
# 3. DESPACHADOR DE HERRAMIENTAS
# =============================================================================
# Este diccionario conecta el NOMBRE de la herramienta (que usa el LLM)
# con la FUNCIÓN real que la ejecuta.

TOOL_DISPATCHER = {
    "buscar_en_web": buscar_en_web,
    "buscar_noticias": buscar_noticias,
}


def ejecutar_herramienta(nombre: str, argumentos: dict) -> str:
    """
    Ejecuta una herramienta por su nombre con los argumentos dados.
    
    Esta función es el puente entre lo que el LLM "pide"
    y lo que realmente se ejecuta en tu máquina.
    
    Args:
        nombre: Nombre de la herramienta a ejecutar
        argumentos: Diccionario con los parámetros
    
    Returns:
        Resultado de la herramienta como string
    """
    if nombre not in TOOL_DISPATCHER:
        return f"Error: Herramienta '{nombre}' no encontrada."
    
    funcion = TOOL_DISPATCHER[nombre]
    return funcion(**argumentos)
