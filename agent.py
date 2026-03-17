"""
🤖 agent.py - Tu Primer Agente de IA (con Google Gemini)

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
import time

from google import genai
from google.genai import types
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from tools import TOOL_DECLARATIONS, ejecutar_herramienta

# Cargar variables de entorno desde .env
load_dotenv()

# Rich nos da una terminal bonita con colores y formato
console = Console()


# =============================================================================
# 1. CONFIGURACIÓN DEL AGENTE
# =============================================================================

# El "system prompt" define la PERSONALIDAD y REGLAS del agente.
# Es lo primero que el LLM lee y condiciona todo su comportamiento.
SYSTEM_PROMPT = """Eres un asistente de investigación inteligente y amigable.

Tu especialidad es buscar y sintetizar información de internet para el usuario.

## Reglas:
1. Cuando el usuario te haga una pregunta factual o sobre eventos recientes, USA tus herramientas de búsqueda.
2. No inventes información. Si no encuentras algo, dilo honestamente.
3. Cita las fuentes (URLs) cuando presentes información de búsquedas.
4. Responde siempre en español, a menos que el usuario te hable en otro idioma.
5. Sé conciso pero completo. Organiza la información de forma clara.
6. Si la pregunta es ambigua, pide clarificación antes de buscar.
7. Puedes hacer MÚLTIPLES búsquedas si la pregunta lo requiere.

## Personalidad:
- Amigable y profesional
- Curioso y proactivo
- Honesto cuando no sabes algo
"""

# Configuración del modelo
# Lista de modelos a intentar (si uno falla por cuota, prueba el siguiente)
# Todos son GRATIS en el free tier de Google AI Studio
MODELS = [
    "gemini-2.0-flash",       # El más capaz y rápido
    "gemini-2.0-flash-lite",  # Más ligero, cuotas separadas
    "gemini-1.5-flash",       # Versión anterior, muy estable
]
MAX_TOOL_ROUNDS = 10   # Máximo de veces que puede usar herramientas por turno
MAX_RETRIES = 3        # Reintentos automáticos si hay error de cuota
RETRY_BASE_DELAY = 4   # Segundos base de espera entre reintentos


# =============================================================================
# 2. CLASE DEL AGENTE
# =============================================================================

class AgenteInvestigador:
    """
    Tu primer agente de IA 🎉
    
    Esta clase encapsula toda la lógica del agente:
    - Mantiene el historial de conversación (memoria) vía el objeto chat
    - Envía mensajes al LLM
    - Ejecuta herramientas cuando el LLM lo pide
    - Implementa el loop ReAct
    """
    
    def __init__(self):
        """Inicializa el agente con el cliente de Google Gemini."""
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key or api_key == "tu-api-key-aqui":
            console.print(Panel(
                "[bold red]⚠️  API Key no configurada![/]\n\n"
                "1. Ve a [link=https://aistudio.google.com/apikey]aistudio.google.com/apikey[/link]\n"
                "2. Haz clic en [bold]'Create API Key'[/]\n"
                "3. Copia la key generada\n"
                "4. Copia el archivo [bold].env.example[/] a [bold].env[/]\n"
                "5. Pega tu API key en el archivo [bold].env[/]\n\n"
                "[green]💰 ¡Es 100% GRATIS! No necesitas tarjeta de crédito.[/]",
                title="Configuración Necesaria",
                border_style="red"
            ))
            sys.exit(1)
        
        # Crear el cliente de Google Gemini
        self.client = genai.Client(api_key=api_key)
        
        # Configuración para todas las interacciones
        # Aquí le decimos al modelo qué herramientas tiene disponibles
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[TOOL_DECLARATIONS],
            temperature=0.7,  # Un poco de creatividad, pero no demasiada
        )
        
        # Probar modelos hasta encontrar uno que funcione
        # (las API keys nuevas a veces tienen cuota temporal en algunos modelos)
        self.modelo_activo = self._encontrar_modelo_disponible()
        
        # Crear un chat (maneja el historial automáticamente)
        self._crear_chat()
        
        console.print(Panel(
            "[bold green]✅ Agente inicializado correctamente![/]\n\n"
            f"🧠 Modelo: [cyan]{self.modelo_activo}[/] (GRATIS)\n"
            f"🔧 Herramientas: 2 disponibles (búsqueda web + noticias)\n"
            f"📝 Escribe tu pregunta y presiona Enter\n"
            f"💡 Escribe [bold]'salir'[/] para terminar\n"
            f"🗑️  Escribe [bold]'limpiar'[/] para resetear la conversación",
            title="🤖 Agente Investigador",
            border_style="green"
        ))
    
    def _encontrar_modelo_disponible(self) -> str:
        """
        Prueba cada modelo de la lista hasta encontrar uno que responda.
        Las API keys nuevas de Google a veces tienen cuota 0 temporal
        en ciertos modelos, así que probamos varios.
        """
        for modelo in MODELS:
            try:
                console.print(f"  [dim]Probando modelo: {modelo}...[/]")
                # Hacer una solicitud mínima para verificar que funciona
                respuesta = self.client.models.generate_content(
                    model=modelo,
                    contents="Responde solo con: OK",
                    config=types.GenerateContentConfig(max_output_tokens=10),
                )
                console.print(f"  [green]✓ {modelo} disponible![/]")
                return modelo
            except Exception as e:
                error_msg = str(e)
                if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    console.print(f"  [yellow]⚠ {modelo}: cuota limitada, probando siguiente...[/]")
                else:
                    console.print(f"  [yellow]⚠ {modelo}: {error_msg[:80]}...[/]")
        
        # Si ninguno funcionó, usar el primero y dejar que el retry lo maneje
        console.print("  [yellow]Usando modelo por defecto con reintentos automáticos.[/]")
        return MODELS[0]
    
    def _crear_chat(self):
        """Crea (o resetea) la sesión de chat con Gemini."""
        self.chat = self.client.chats.create(
            model=self.modelo_activo,
            config=self.config,
        )
    
    def procesar_mensaje(self, mensaje_usuario: str) -> str:
        """
        Procesa un mensaje del usuario y devuelve la respuesta del agente.
        
        AQUÍ ESTÁ EL CORAZÓN DEL AGENTE: El Loop ReAct
        
        Args:
            mensaje_usuario: Lo que escribió el usuario
            
        Returns:
            La respuesta final del agente
        """
        # =====================================================================
        # Paso 1: Enviar el mensaje del usuario al LLM (con reintentos)
        # =====================================================================
        # El objeto chat se encarga de mantener el historial automáticamente
        respuesta = self._enviar_con_reintento(mensaje_usuario)
        
        # =====================================================================
        # LOOP REACT: El agente sigue pensando hasta que da una respuesta final
        # =====================================================================
        for ronda in range(MAX_TOOL_ROUNDS):
            
            # --- Paso 2: ¿El LLM quiere usar herramientas? ---
            # Revisamos si la respuesta contiene llamadas a funciones
            function_calls = [
                part for part in respuesta.candidates[0].content.parts
                if part.function_call
            ]
            
            # Si NO hay llamadas a funciones, el LLM ya tiene la respuesta final
            if not function_calls:
                return respuesta.text
            
            # --- Paso 3: Ejecutar CADA herramienta que pidió ---
            # El LLM puede pedir varias herramientas a la vez
            function_responses = []
            
            for part in function_calls:
                fc = part.function_call
                nombre_tool = fc.name
                args_tool = dict(fc.args) if fc.args else {}
                
                # Mostrar qué está haciendo el agente
                console.print(
                    f"  🔍 [dim]Usando herramienta:[/] "
                    f"[bold cyan]{nombre_tool}[/]"
                    f"([italic]{args_tool.get('consulta', '')}[/])"
                )
                
                # Ejecutar la herramienta
                resultado = ejecutar_herramienta(nombre_tool, args_tool)
                
                # Preparar el resultado para devolvérselo al LLM
                # Gemini espera un Part con from_function_response
                function_responses.append(
                    types.Part.from_function_response(
                        name=nombre_tool,
                        response={"result": resultado}
                    )
                )
            
            # --- Paso 4: Devolver TODOS los resultados al LLM ---
            # Le damos los resultados y el LLM decide:
            #   - "Necesito buscar más" → sigue el loop
            #   - "Ya tengo suficiente" → responde al usuario
            respuesta = self._enviar_con_reintento(function_responses)
        
        # Si llegamos aquí, se alcanzó el límite de rondas
        return "⚠️ Se alcanzó el límite de búsquedas. Intenta con una pregunta más específica."
    
    def _enviar_con_reintento(self, mensaje):
        """
        Envía un mensaje al chat con reintentos automáticos.
        
        Si Google devuelve RESOURCE_EXHAUSTED (error de cuota),
        esperamos unos segundos y reintentamos. Esto es una BUENA PRÁCTICA
        en cualquier integración con APIs externas.
        
        Se llama "exponential backoff": cada reintento espera más tiempo.
        Intento 1: espera 4s, Intento 2: espera 8s, Intento 3: espera 16s
        """
        for intento in range(MAX_RETRIES):
            try:
                return self.chat.send_message(mensaje)
            except Exception as e:
                error_msg = str(e)
                es_error_cuota = (
                    "RESOURCE_EXHAUSTED" in error_msg 
                    or "quota" in error_msg.lower()
                    or "429" in error_msg
                )
                
                if es_error_cuota and intento < MAX_RETRIES - 1:
                    espera = RETRY_BASE_DELAY * (2 ** intento)  # 4s, 8s, 16s
                    console.print(
                        f"  [yellow]⏳ Cuota excedida. Reintentando en {espera}s "
                        f"(intento {intento + 2}/{MAX_RETRIES})...[/]"
                    )
                    time.sleep(espera)
                else:
                    raise  # Si no es error de cuota, o ya no hay reintentos
        
        # Esto no debería alcanzarse, pero por seguridad:
        raise Exception("Se agotaron los reintentos.")
    
    def limpiar_historial(self):
        """Limpia el historial de conversación (resetea la memoria)."""
        self._crear_chat()
        console.print("[dim]🗑️  Historial limpiado. Nueva conversación iniciada.[/]")


# =============================================================================
# 3. INTERFAZ DE TERMINAL (REPL)
# =============================================================================

def main():
    """
    Punto de entrada principal.
    Ejecuta un REPL (Read-Eval-Print Loop) interactivo.
    """
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold]🤖 MI PRIMER AGENTE DE IA[/]\n"
                "[dim]Un agente que busca información en internet[/]\n"
                "[dim]Powered by Google Gemini 2.0 Flash (GRATIS)[/]"
            ),
            border_style="bright_blue",
            padding=(1, 2)
        )
    )
    console.print()
    
    # Crear el agente
    agente = AgenteInvestigador()
    
    # Loop principal de interacción
    while True:
        console.print()
        
        try:
            # Leer input del usuario
            user_input = console.input("[bold green]Tú → [/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]👋 ¡Hasta luego![/]")
            break
        
        # Comandos especiales
        if not user_input:
            continue
        
        if user_input.lower() in ("salir", "exit", "quit"):
            console.print("[dim]👋 ¡Hasta luego![/]")
            break
        
        if user_input.lower() in ("limpiar", "clear", "reset"):
            agente.limpiar_historial()
            continue
        
        # Procesar el mensaje
        try:
            with console.status("[bold cyan]Pensando...[/]", spinner="dots"):
                respuesta = agente.procesar_mensaje(user_input)
            
            # Mostrar la respuesta con formato Markdown
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
