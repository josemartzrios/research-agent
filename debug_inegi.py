"""
Encuentra las áreas geográficas correctas para cada serie del INEGI.
Las series de ENOE (empleo) usan área diferente a INPC o PIB.
"""
import os, requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("INEGI_TOKEN")
base = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# El problema: cada serie tiene su propio código de área válido.
# Probamos áreas comunes para la serie 444612 (desocupación)
serie = "444612"
fuentes = ["BISE", "BIE"]
areas = ["00", "700", "0910", "010", "01", "1", "0", "001"]

print(f"Probando serie {serie} con distintas áreas y fuentes:\n")
for fuente in fuentes:
    for area in areas:
        url = f"{base}/{serie}/es/{area}/false/{fuente}/2.0/{token}?type=json"
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if "Series" in data and data["Series"]:
                    obs = data["Series"][0].get("OBSERVATIONS", [])
                    print(f"✅ fuente={fuente} area={area} → {len(obs)} observaciones")
                    if obs:
                        print(f"   Último: {obs[-1]}")
                else:
                    print(f"⚠  fuente={fuente} area={area} → HTTP 200 sin Series: {str(data)[:80]}")
            else:
                pass  # Silencioso para los 400
        except Exception as e:
            print(f"💥 {e}")
