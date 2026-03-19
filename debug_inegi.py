"""
Prueba del World Bank API con indicadores de México.
Sin API key, completamente gratuita y abierta.
"""
import requests

BASE = "https://api.worldbank.org/v2/country/MX/indicator"

# Indicadores clave para México
INDICADORES = {
    "desempleo":                  "SL.UEM.TOTL.ZS",   # Tasa de desempleo total (%)
    "participacion_laboral_total":"SL.TLF.CACT.ZS",   # Participación laboral total (%)
    "participacion_laboral_mujer":"SL.TLF.CACT.FE.ZS",# Participación laboral femenina (%)
    "participacion_laboral_hombre":"SL.TLF.CACT.MA.ZS",# Participación laboral masculina (%)
    "pib_crecimiento":            "NY.GDP.MKTP.KD.ZG", # Crecimiento PIB anual (%)
    "pib_per_capita":             "NY.GDP.PCAP.CD",    # PIB per cápita (USD)
    "inflacion":                  "FP.CPI.TOTL.ZG",    # Inflación anual (%)
    "pobreza":                    "SI.POV.NAHC",       # Pobreza (% pob. bajo línea nacional)
    "poblacion":                  "SP.POP.TOTL",       # Población total
    "gini":                       "SI.POV.GINI",       # Coeficiente GINI (desigualdad)
}

print("🌍 TEST — World Bank API — México (MX)\n")
print(f"{'Indicador':<30} {'Año':>6}  {'Valor':>12}  Código WB")
print("-" * 75)

exitosos = 0
for nombre, codigo in INDICADORES.items():
    url = f"{BASE}/{codigo}?format=json&mrv=5&country=MX"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # El WB retorna [metadata, [datos]]
            registros = data[1] if len(data) > 1 else []
            # Buscar el dato más reciente que NO sea None
            ultimo = next((d for d in registros if d.get("value") is not None), None)
            if ultimo:
                anio  = ultimo.get("date", "?")
                valor = ultimo.get("value", "?")
                print(f"  ✅ {nombre:<28} {anio:>6}  {str(round(valor,2)):>12}  {codigo}")
                exitosos += 1
            else:
                print(f"  ⚠  {nombre:<28} {'Sin datos':>20}  {codigo}")
        else:
            print(f"  ❌ {nombre:<28} HTTP {r.status_code}  {codigo}")
    except Exception as e:
        print(f"  💥 {nombre:<28} {str(e)[:30]}")

print(f"\n{'='*75}")
print(f"  ✅ {exitosos}/{len(INDICADORES)} indicadores disponibles")
print(f"\n  Fuente: World Bank Open Data")
print(f"  Sin API key • Datos anuales • Gratis")
