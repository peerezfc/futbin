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
        return "ERROR: FUT_API_KEY NO EXISTE EN RAILWAY"

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

        return (
            f"HTTP: {response.status_code}\n\n"
            f"RESPUESTA DE PARSE.BOT:\n\n"
            f"{response.text[:5000]}"
        )

    except httpx.RequestError as e:
        return f"ERROR DE CONEXIÓN: {type(e).__name__}: {str(e)}"

    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"
