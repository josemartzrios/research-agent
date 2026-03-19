"""
🧪 test_apis.py - Verifica que las APIs de World Bank y Banxico funcionen correctamente

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


def test_world_bank():
    """Prueba la conexión con la API del Banco Mundial."""
    console.print("\n[bold cyan]── Prueba World Bank ─────────────────────────[/]")
    
    # Probar con Tasa de Desempleo (SL.UEM.TOTL.ZS)
    codigo = "SL.UEM.TOTL.ZS"
    url = f"https://api.worldbank.org/v2/country/MX/indicator/{codigo}?format=json&mrv=1"

    try:
        console.print(f"  [dim]Conectando a World Bank API... ({codigo})[/]")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if len(data) > 1 and data[1]:
            ultimo = data[1][0]
            nombre = ultimo.get("indicator", {}).get("value", "?")
            anio = ultimo.get("date", "?")
            valor = str(round(ultimo.get("value", 0), 2)) + "%" if ultimo.get("value") else "Sin dato"

            console.print(f"  [green]✅ World Bank conectado correctamente[/]")

            tabla = Table(show_header=True, header_style="bold green")
            tabla.add_column("Indicador")
            tabla.add_column("Último año")
            tabla.add_column("Valor")
            tabla.add_row(nombre[:50], anio, valor)
            console.print(tabla)
            return True
        else:
            console.print(f"  [red]❌ Respuesta inesperada del World Bank[/]")
            return False

    except requests.HTTPError as e:
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
        "[dim]Verifica que World Bank y Banxico respondan correctamente[/]",
        border_style="bright_blue"
    ))

    ok_wb      = test_world_bank()
    ok_banxico = test_banxico()

    console.print("\n[bold]── Resumen ───────────────────────────────────[/]")
    console.print(f"  World Bank: {'[green]✅ OK (API Abierta)[/]' if ok_wb else '[red]❌ Falla de conexión[/]'}")
    console.print(f"  Banxico:    {'[green]✅ OK[/]' if ok_banxico else '[yellow]⚠ Sin token / revisar[/]'}")

    if not ok_banxico:
        console.print(
            "\n[dim]💡 Sin token de Banxico: el agente usará datos del World Bank y web,\n"
            "   pero no tendrá el tipo de cambio ni tasas al día exacto.[/]"
        )
    else:
        console.print("\n[green bold]🎉 Todo listo. Corre el agente con:[/]")
        console.print("   [bold].\\venv\\Scripts\\python.exe agent.py[/]")


if __name__ == "__main__":
    main()
