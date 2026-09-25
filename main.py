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
        return "ERROR: Railway no encuentra la variable FUT_API_KEY."

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                PARSE_API_URL,
                params={"query": nombre.strip()},
                headers={
                    "X-API-Key": api_key
                }
            )

        if response.status_code != 200:
            return (
                f"ERROR API: HTTP {response.status_code}\n"
                f"Respuesta: {response.text[:500]}"
            )

        data = response.json()

        results = data.get("data", {}).get("results", [])

        if not results:
            return f"No encontré ninguna carta de '{nombre}'."

        respuestas = []

        for player in results:
            respuestas.append(
                f"{player.get('name', '?')} "
                f"({player.get('rating', '?')}) "
                f"{player.get('position', '?')} "
                f"[{player.get('version', '?')}] → "
                f"PS: {player.get('price_ps', '0')} | "
                f"PC: {player.get('price_pc', '0')}"
            )

        return "\n".join(respuestas)

    except httpx.RequestError as e:
        return f"ERROR DE CONEXIÓN: {type(e).__name__}: {str(e)}"

    except Exception as e:
        return f"ERROR INTERNO: {type(e).__name__}: {str(e)}"
