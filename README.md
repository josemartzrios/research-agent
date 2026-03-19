# 🇲🇽 Agente de Inteligencia Económica de México

Un agente de inteligencia artificial especializado en el análisis estadístico, económico y social de México. Utiliza un modelo LLM de Anthropic (Claude) orquestado con el patrón **ReAct** (Reason + Act) para consultar datos oficiales en tiempo real y emitir conclusiones fundamentadas sin alucinaciones.

---

## 🚀 Características Principales

* **Cero Alucinaciones Numéricas**: Desarrollado con técnicas de control estricto de temperatura y forzado de selección de herramientas.
* **Datos Oficiales y Abiertos**:
  * 🌍 **Banco Mundial (World Bank API)**: Proveedor primario de datos anuales e históricos sobre desempleo, PIB, pobreza, desigualdad, etc. Completamente gratuito y sin necesidad de tokens.
  * 🏦 **Banco de México (Banxico SIE API)**: Proveedor de datos de coyuntura y financieros regulares (tipo de cambio FIX, inflación, tasa objetivo, reservas internacionales).
* **Búsqueda Web Complementaria**: Capacidad de buscar en internet (vía DuckDuckGo) cuando requiere explicaciones de contexto, noticias de última hora o razones sociológicas detrás de los números.
* **Orquestación ReAct Pura**: El agente decide orgánicamente qué herramienta usar, qué parámetros pasar y qué hacer a continuación sin rutas pre-programadas.

---

## 🛠️ Arquitectura y Estructura del Proyecto

El proyecto está modularizado para separar la inteligencia (LLM) de la obtención de datos (Herramientas).

* `agent.py`: El núcleo del proyecto. Contiene la clase principal `AgenteInvestigador` (ahora actuando como Agente Estadístico), inicializa el cliente Anthropic, gestiona el prompt del sistema y mantiene el historial del chat.
* `tools.py`: La capa de acceso a datos. Contiene los catálogos de indicadores (`INDICADORES_WB`, `INDICADORES_BANXICO`), la definición JSON-Schema requerida por la API de Anthropic, y las funciones individuales de consumo REST.
* `test_apis.py`: Script de diagnóstico y validación para asegurar que el sistema se pueda conectar a la API del Banco Mundial y a Banxico antes de arrancar.
* `.env` / `.env.example`: Gestión de secretos y tokens de acceso.
* `debug_inegi.py` (Opcional/Histórico): Archivo usado para debuggear endpoints de datos del gobierno.

---

## ⚙️ Instalación y Configuración

1. **Clona el repositorio** o descarga los archivos.
2. **Crea un entorno virtual** (recomendado):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Instala las dependencias**:
   ```powershell
   pip install -r requirements.txt
   ```
   *Dependencias base: `anthropic`, `python-dotenv`, `requests`, `ddgs`, `rich`.*
4. **Configura tus variables de entorno**:
   * Copia `.env.example` a `.env`.
   * **ANTHROPIC_API_KEY**: Tu llave de acceso de la consola de Anthropic.
   * **BANXICO_TOKEN**: (Opcional pero recomendado). Solicita tu token gratuito en el portal SIE de Banxico para acceder a tipos de cambio y tasas.

---

## 🏃‍♂️ Cómo Ejecutar

Antes de interactuar con el agente, puedes validar que tu conectividad a las APIs funcione correctamente:

```powershell
.\venv\Scripts\python.exe test_apis.py
```

Para arrancar el chat interactivo del agente:

```powershell
.\venv\Scripts\python.exe agent.py
```

### Casos de Uso de Ejemplo para Preguntar al Agente:

* *"Genérame un reporte del crecimiento del PIB de México en los últimos 10 años. ¿Cómo se compara esa tendencia con la inflación?"*
* *"Hazme un análisis de la participación laboral femenina vs masculina en México y acompáñalo con las tasas de desempleo de cada género."*
* *"Soy un inversionista extranjero. Dame un resumen rápido de cómo está México hoy: ¿a cuánto está el dólar, en cuánto está la tasa de interés y cuánto está creciendo su PIB?"*

---

## 🧠 Estructura del "System Prompt"

El `SYSTEM_PROMPT` residente en `agent.py` instruye rigurosamente al modelo a adoptar una postura objetiva, basarse siempre en datos de las APIs antes de inventar, cruzar métricas (por ejemplo, relacionar la inflación con la pobreza), e identificar patrones.

## 🛣️ Siguientes pasos posibles para monetización (Roadmap)

* [ ] Empaquetar el `agent.py` detrás de un endpoint web (`FastAPI`).
* [ ] Conectar una interfaz gráfica frontend (Next.js / React) con gráficos reales.
* [ ] Integración de un cache en base de datos (`PostgreSQL` / `Redis`) para reducir el tiempo de latencia en las llamadas al Banco Mundial y Banxico.
* [ ] Incorporación de métricas específicas de INEGI (vía Web Scraping o resolución de sus keys del Constructor de Métricas).
