"""
🧪 test_apis.py - Verifica que las APIs de INEGI y Banxico funcionen correctamente

Ejecutar con:
    .\\venv\\Scripts\\python.exe test_apis.py
"""

import os
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()
console = Console()


def test_inegi():
    """Prueba la conexión con la API del INEGI."""
    console.print("\n[bold cyan]── Prueba INEGI ──────────────────────────────[/]")
    token = os.getenv("INEGI_TOKEN")

    if not token or token == "tu-token-inegi-aqui":
        console.print("  [yellow]⚠ INEGI_TOKEN no configurado en .env[/]")
        console.print("  [dim]→ Regístrate en: https://www.inegi.org.mx/servicios/api_biinegi.html[/]")
        return False

    # Probar con tasa de desocupación (serie 444612)
    serie_id = "444612"
    url = (
        f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
        f"INDICATOR/{serie_id}/es/0910/false/BIE/2.0/{token}?type=json"
    )

    try:
        console.print(f"  [dim]Conectando a INEGI... (serie {serie_id})[/]")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        serie = data.get("Series", [{}])[0]
        nombre = serie.get("INDICADOR", "?")
        unidad = serie.get("UNIDAD", "?")
        obs = serie.get("OBSERVATIONS", [])
        ultimo = obs[-1] if obs else {}

        console.print(f"  [green]✅ INEGI conectado correctamente[/]")

        tabla = Table(show_header=True, header_style="bold green")
        tabla.add_column("Indicador")
        tabla.add_column("Unidad")
        tabla.add_column("Último periodo")
        tabla.add_column("Valor")
        tabla.add_row(
            nombre[:50],
            unidad,
            ultimo.get("TIME_PERIOD", "?"),
            ultimo.get("OBS_VALUE", "?")
        )
        console.print(tabla)
        return True

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            console.print(f"  [red]❌ Token inválido (401). Verifica tu INEGI_TOKEN[/]")
        else:
            console.print(f"  [red]❌ Error HTTP: {e}[/]")
        return False
    except Exception as e:
        console.print(f"  [red]❌ Error: {str(e)}[/]")
        return False


def test_banxico():
    """Prueba la conexión con la API del Banco de México."""
    console.print("\n[bold cyan]── Prueba Banxico ────────────────────────────[/]")
    token = os.getenv("BANXICO_TOKEN")

    if not token or token == "tu-token-banxico-aqui":
        console.print("  [yellow]⚠ BANXICO_TOKEN no configurado en .env[/]")
        console.print("  [dim]→ Regístrate en: https://www.banxico.org.mx/SieAPIRest/service/v1/[/]")
        return False

    # Probar con tipo de cambio FIX (SF43718)
    serie_id = "SF43718"
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie_id}/datos/oportuno"
    headers = {"Bmx-Token": token}

    try:
        console.print(f"  [dim]Conectando a Banxico... (serie {serie_id})[/]")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        series = data.get("bmx", {}).get("series", [{}])[0]
        titulo = series.get("titulo", "?")
        datos  = series.get("datos", [])
        ultimo = datos[-1] if datos else {}

        console.print(f"  [green]✅ Banxico conectado correctamente[/]")

        tabla = Table(show_header=True, header_style="bold green")
        tabla.add_column("Indicador")
        tabla.add_column("Fecha")
        tabla.add_column("Valor")
        tabla.add_row(
            titulo[:50],
            ultimo.get("fecha", "?"),
            ultimo.get("dato", "?")
        )
        console.print(tabla)
        return True

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            console.print(f"  [red]❌ Token inválido (401). Verifica tu BANXICO_TOKEN[/]")
        else:
            console.print(f"  [red]❌ Error HTTP: {e}[/]")
        return False
    except Exception as e:
        console.print(f"  [red]❌ Error: {str(e)}[/]")
        return False


def main():
    console.print(Panel(
        "[bold]🧪 Test de Conexión — APIs de México[/]\n"
        "[dim]Verifica que INEGI y Banxico respondan correctamente[/]",
        border_style="bright_blue"
    ))

    ok_inegi   = test_inegi()
    ok_banxico = test_banxico()

    console.print("\n[bold]── Resumen ───────────────────────────────────[/]")
    console.print(f"  INEGI:   {'[green]✅ OK[/]' if ok_inegi   else '[yellow]⚠ Sin token / revisar[/]'}")
    console.print(f"  Banxico: {'[green]✅ OK[/]' if ok_banxico else '[yellow]⚠ Sin token / revisar[/]'}")

    if not ok_inegi or not ok_banxico:
        console.print(
            "\n[dim]💡 Sin tokens: el agente igual funciona con búsqueda web,\n"
            "   pero sin datos oficiales en tiempo real.[/]"
        )
    else:
        console.print("\n[green bold]🎉 Todo listo. Corre el agente con:[/]")
        console.print("   [bold].\\venv\\Scripts\\python.exe agent.py[/]")


if __name__ == "__main__":
    main()
