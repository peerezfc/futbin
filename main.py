import os
import asyncio
import httpx

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse

from twitchio.ext import commands


# =========================
# CONFIGURACIÓN
# =========================

TWITCH_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
FUT_API_KEY = os.getenv("FUT_API_KEY")

PARSE_API_URL = (
    "https://api.parse.bot/scraper/"
    "5feab28c-82a9-4579-ae36-9307b1b0711a/"
    "search_players_fc27"
)


# =========================
# FASTAPI
# =========================

app = FastAPI()


@app.get("/precio", response_class=PlainTextResponse)
async def precio(nombre: str = Query(..., min_length=2)):
    return await buscar_precio(nombre)


async def buscar_precio(nombre: str):
    if not FUT_API_KEY:
        return "Error: falta configurar FUT_API_KEY."

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                PARSE_API_URL,
                params={"query": nombre.strip()},
                headers={
                    "X-API-Key": FUT_API_KEY,
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

        # Primer resultado: normalmente es la coincidencia principal
        player = results[0]

        name = player.get("name", nombre)
        rating = player.get("rating", "?")
        position = player.get("position", "?")
        version = player.get("version", "?")
        price_ps = player.get("price_ps", "0")
        price_pc = player.get("price_pc", "0")

        return (
            f"{name} ({rating}) {position} [{version}] "
            f"→ PS: {price_ps} | PC: {price_pc}"
        )

    except httpx.RequestError:
        return "Error de conexión con la API de FUT."

    except Exception:
        return f"Error al buscar '{nombre}'."


# =========================
# TWITCH BOT
# =========================

class PrecioBot(commands.Bot):

    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL]
        )

    async def event_ready(self):
        print(f"Bot conectado como: {self.nick}")
        print(f"Canal: {TWITCH_CHANNEL}")

    @commands.command()
    async def precio(self, ctx: commands.Context):
        # !precio Haaland
        partes = ctx.message.content.split(maxsplit=1)

        if len(partes) < 2:
            await ctx.send(
                "Uso: !precio nombre del jugador"
            )
            return

        nombre = partes[1].strip()

        resultado = await buscar_precio(nombre)

        await ctx.send(resultado)


async def iniciar_twitch():
    if not TWITCH_TOKEN:
        print("ERROR: falta TWITCH_ACCESS_TOKEN")
        return

    if not TWITCH_CHANNEL:
        print("ERROR: falta TWITCH_CHANNEL")
        return

    bot = PrecioBot()
    await bot.start()


# =========================
# ARRANQUE
# =========================

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(iniciar_twitch())
