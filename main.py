from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
import httpx
import urllib.parse

app = FastAPI()

# Cambia el año si es necesario (26 o 27 según el juego actual)
YEAR = "26"

@app.get("/precio", response_class=PlainTextResponse)
async def precio(nombre: str = Query(..., min_length=2)):
    try:
        nombre_limpio = nombre.strip()
        encoded_name = urllib.parse.quote(nombre_limpio)

        url = f"https://www.futbin.org/futbin/api/{YEAR}/searchPlayersByName?playername={encoded_name}&year={YEAR}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            data = response.json()

        if not data or "data" not in data or len(data["data"]) == 0:
            return f"No encontré ninguna carta de '{nombre_limpio}'"

        # Cogemos la primera carta (normalmente la más relevante / alta)
        player = data["data"][0]

        name = player.get("name", nombre_limpio)
        rating = player.get("rating", "?")
        
        # Precios
        price_ps = player.get("ps_LCPrice") or player.get("ps_price") or 0
        price_pc = player.get("pc_LCPrice") or player.get("pc_price") or 0

        # Formato bonito
        def format_price(p):
            if not p or p == 0:
                return "N/A"
            return f"{int(p):,}".replace(",", ".")

        return f"{name} ({rating}) → PS: {format_price(price_ps)} | PC: {format_price(price_pc)}"

    except Exception as e:
        return f"Error al buscar '{nombre}'. Inténtalo de nuevo en unos segundos."
