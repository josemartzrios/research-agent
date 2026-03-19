"""
agent.py - Mi Primer Agente de IA (con Anthropic Claude)

CÓMO FUNCIONA UN AGENTE (El Loop ReAct):
=========================================

Un agente NO es solo un chatbot. La diferencia clave es:
- Chatbot: Recibe pregunta → Responde directamente
- Agente:  Recibe pregunta → PIENSA → USA HERRAMIENTAS → OBSERVA → RESPONDE

El flujo es un LOOP (bucle):

    ┌─────────────────────────────────────────┐
    │  1. Usuario hace una pregunta           │
    │  2. LLM analiza y decide:               │
    │     ├─ "Ya sé la respuesta" → Responde  │
    │     └─ "Necesito buscar" → Usa tool     │
    │  3. Si usó tool:                        │
    │     ├─ Ejecutamos la herramienta        │
    │     ├─ Le damos los resultados al LLM   │
    │     └─ Vuelve al paso 2                 │
    │  4. El loop termina cuando el LLM       │
    │     responde sin pedir más tools        │
    └─────────────────────────────────────────┘

Este patrón se llama "ReAct" (Reason + Act) y es la base
de TODOS los agentes modernos (ChatGPT, Gemini, Claude, etc.)
"""

import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from tools import TOOLS, ejecutar_herramienta

# Cargar variables de entorno desde .env
load_dotenv()

console = Console()


# =============================================================================
# 1. CONFIGURACIÓN DEL AGENTE
# =============================================================================

SYSTEM_PROMPT = """Eres un analista experto en estadísticas económicas y sociales de México.

Tienes acceso a datos oficiales del Banco Mundial (World Bank) y del Banco de México (Banxico).

## Tu misión:
Responder preguntas sobre la realidad económica y social de México con datos reales, 
análisis riguroso y conclusiones accionables.

## Cómo debes trabajar:
1. **Siempre usa datos reales**: Antes de responder cualquier pregunta sobre indicadores,
   consulta las APIs del World Bank o Banxico para obtener cifras actuales.
2. **Compara y contextualiza**: No des solo el número. Explica la tendencia histórica,
   qué significa y qué lo causa.
3. **Cruza indicadores**: Si preguntan sobre participación laboral femenina,
   consulta también participacion_laboral_hombre, desempleo_mujer, gini, etc.
4. **Llega a conclusiones**: No te limites a reportar datos. Sintetiza, 
   identifica patrones y ofrece perspectiva analítica.
5. **Cita tus fuentes**: Menciona siempre si los datos vienen de World Bank o Banxico.
6. **Complementa con web**: Usa búsqueda web para contexto reciente o explicaciones
   que no estén en los datos.

## Indicadores disponibles (consultar_world_bank):
- **Empleo**: desempleo, participacion_laboral_total, participacion_laboral_mujer,
  participacion_laboral_hombre, desempleo_mujer, desempleo_hombre, desempleo_jovenes
- **Economía**: pib_crecimiento, pib_per_capita, pib_total, exportaciones, 
  importaciones, inversion_extranjera, inflacion
- **Bienestar**: pobreza, gini
- **Demografía**: poblacion_total, crecimiento_poblacional, poblacion_urbana
- **Social**: gasto_educacion, esperanza_vida

## Indicadores disponibles (consultar_banxico):
- tipo_cambio_dolar, tasa_fondeo, reservas_int, credito_consumo

## Personalidad:
- Objetivo y basado en evidencia
- Claro y accesible (explica sin jerga innecesaria)
- Proactivo: si una pregunta tiene varios ángulos, explóralos todos
- Responde siempre en español
"""

# Configuración del modelo
# Claude Haiku 4.5: El más barato de Anthropic ($1/$5 por 1M tokens input/output)
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10

# ─── Técnica anti-alucinación 1: Temperature = 0 ─────────────────────────────
# Temperature controla cuánta "creatividad" tiene el LLM.
# - Temperature 1.0 = muy creativo (inventa más, alucina más)
# - Temperature 0.0 = determinista (sigue los datos, inventa menos)
# Para un agente de análisis estadístico, SIEMPRE usamos 0.
TEMPERATURE = 0


# =============================================================================
# 2. CLASE DEL AGENTE
# =============================================================================

class AgenteInvestigador:
    """
    Mi primer agente de IA
    
    Esta clase encapsula toda la lógica del agente:
    - Mantiene el historial de conversación (memoria)
    - Envía mensajes al LLM vía Anthropic
    - Ejecuta herramientas cuando el LLM lo pide
    - Implementa el loop ReAct
    """
    
    def __init__(self):
        """Inicializa el agente con el cliente de Anthropic."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key or api_key == "sk-ant-tu-api-key-aqui":
            console.print(Panel(
                "[bold red]⚠️  API Key no configurada![/]\n\n"
                "1. Ve a [link=https://console.anthropic.com]console.anthropic.com[/link]\n"
                "2. Crea una cuenta\n"
                "3. Ve a [bold]Settings → API Keys → Create Key[/]\n"
                "4. Pega tu API key en el archivo [bold].env[/]",
                title="Configuración Necesaria",
                border_style="red"
            ))
            sys.exit(1)
        
        self.client = Anthropic(api_key=api_key)
        self.historial: list[dict] = []
        
        console.print(Panel(
            "[bold green]✅ Agente inicializado correctamente![/]\n\n"
            f"🧠 Modelo: [cyan]{MODEL}[/]\n"
            f"🔧 Herramientas: 2 disponibles (búsqueda web + noticias)\n"
            f"📝 Escribe tu pregunta y presiona Enter\n"
            f"💡 Escribe [bold]'salir'[/] para terminar\n"
            f"🗑️  Escribe [bold]'limpiar'[/] para resetear la conversación",
            title="🤖 Agente Investigador",
            border_style="green"
        ))
    
    def procesar_mensaje(self, mensaje_usuario: str) -> str:
        """
        Procesa un mensaje del usuario y devuelve la respuesta del agente.
        AQUÍ ESTÁ EL CORAZÓN DEL AGENTE: El Loop ReAct
        """
        self.historial.append({
            "role": "user",
            "content": mensaje_usuario
        })
        
        # =====================================================================
        # LOOP REACT
        # =====================================================================
        for ronda in range(MAX_TOOL_ROUNDS):
            
            # --- Paso 1: Enviar todo el historial al LLM ---
            #
            # ─── Técnica anti-alucinación 2: Forzar uso de herramientas ──────
            # En la PRIMERA ronda, usamos tool_choice="any" para OBLIGAR
            # al LLM a consultar una herramienta antes de responder.
            # Esto impide que responda preguntas de datos desde su memoria.
            # En rondas siguientes usamos "auto" para que pueda responder
            # cuando ya tiene los datos que necesita.
            tool_choice = {"type": "any"} if ronda == 0 else {"type": "auto"}

            respuesta = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                tool_choice=tool_choice,
                temperature=TEMPERATURE,
                messages=self.historial
            )
            
            # --- Paso 2: Analizar qué respondió ---
            # Claude usa stop_reason:
            #   "end_turn"  → Ya tiene la respuesta final
            #   "tool_use"  → Quiere usar una herramienta
            
            if respuesta.stop_reason == "end_turn":
                texto = self._extraer_texto(respuesta)
                self.historial.append({
                    "role": "assistant",
                    "content": respuesta.content
                })
                return texto
            
            elif respuesta.stop_reason == "tool_use":
                # Guardar la respuesta del LLM (con tool_calls)
                self.historial.append({
                    "role": "assistant",
                    "content": respuesta.content
                })
                
                # --- Paso 3: Ejecutar las herramientas ---
                resultados_tools = []
                
                for bloque in respuesta.content:
                    if bloque.type == "tool_use":
                        console.print(
                            f"  🔍 [dim]Buscando:[/] "
                            f"[bold cyan]{bloque.name}[/]"
                            f"([italic]{bloque.input.get('consulta', '')}[/])"
                        )
                        
                        resultado = ejecutar_herramienta(bloque.name, bloque.input)
                        
                        resultados_tools.append({
                            "type": "tool_result",
                            "tool_use_id": bloque.id,
                            "content": resultado
                        })
                
                # --- Paso 4: Devolver resultados al LLM ---
                self.historial.append({
                    "role": "user",
                    "content": resultados_tools
                })
        
        return "⚠️ Se alcanzó el límite de búsquedas."
    
    def _extraer_texto(self, respuesta) -> str:
        """Extrae el texto de la respuesta del LLM."""
        partes = []
        for bloque in respuesta.content:
            if hasattr(bloque, "text"):
                partes.append(bloque.text)
        return "\n".join(partes) or "No pude generar una respuesta."
    
    def limpiar_historial(self):
        """Limpia el historial de conversación."""
        self.historial = []
        console.print("[dim]🗑️  Historial limpiado. Nueva conversación iniciada.[/]")


# =============================================================================
# 3. INTERFAZ DE TERMINAL
# =============================================================================

def main():
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold] MI PRIMER AGENTE DE IA[/]\n"
                "[dim]Un agente que busca información en internet[/]\n"
                "[dim]Powered by Anthropic Claude[/]"
            ),
            border_style="bright_blue",
            padding=(1, 2)
        )
    )
    console.print()
    
    agente = AgenteInvestigador()
    
    while True:
        console.print()
        
        try:
            user_input = console.input("[bold green]Tú → [/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]👋 ¡Hasta luego![/]")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("salir", "exit", "quit"):
            console.print("[dim]👋 ¡Hasta luego![/]")
            break
        
        if user_input.lower() in ("limpiar", "clear", "reset"):
            agente.limpiar_historial()
            continue
        
        try:
            with console.status("[bold cyan]Pensando...[/]", spinner="dots"):
                respuesta = agente.procesar_mensaje(user_input)
            
            console.print()
            console.print(Panel(
                Markdown(respuesta),
                title="🤖 Agente",
                border_style="bright_blue",
                padding=(1, 2)
            ))
            
        except Exception as e:
            console.print(f"\n[bold red]❌ Error: {str(e)}[/]")
            console.print("[dim]Intenta de nuevo o escribe 'salir' para terminar.[/]")


if __name__ == "__main__":
    main()
