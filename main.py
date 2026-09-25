from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
import httpx
import os

app = FastAPI()

PARSE_API_URL = (
    "https://api.parse.bot/scraper/"
    "5feab28c-82a9-4579-ae36-9307b1b0711a/search_players_fc27"
)


@app.get("/precio", response_class=PlainTextResponse)
async def precio(nombre: str = Query(..., min_length=2)):
    api_key = os.getenv("FUT_API_KEY")

    if not api_key:
        return "Error: falta configurar FUT_API_KEY."

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                PARSE_API_URL,
                params={"query": nombre.strip()},
                headers={
                    "X-API-Key": api_key,
                    "Accept": "application/json"
                }
            )

        if response.status_code != 200:
            return f"Error de la API: HTTP {response.status_code}"

        data = response.json()

        if data.get("status") != "success":
            return f"No se pudo buscar '{nombre}'."

        results = data.get("data", {}).get("results", [])

        if not results:
            return f"No encontré ninguna carta de '{nombre}'."

        # Mostramos las cartas encontradas
        respuestas = []

        for player in results:
            name = player.get("name", "?")
            rating = player.get("rating", "?")
            position = player.get("position", "?")
            version = player.get("version", "?")
            price_ps = player.get("price_ps", "0")
            price_pc = player.get("price_pc", "0")

            respuestas.append(
                f"{name} ({rating}) {position} [{version}] "
                f"→ PS: {price_ps} | PC: {price_pc}"
            )

        return "\n".join(respuestas)

    except httpx.RequestError:
        return "Error de conexión con la API de FUT."

    except Exception:
        return f"Error al buscar '{nombre}'."
