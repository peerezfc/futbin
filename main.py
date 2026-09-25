import os
import asyncio
import httpx

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse

from twitchio.ext import commands
from twitchio import eventsub


# ============================================================
# VARIABLES
# ============================================================

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")

FUT_API_KEY = os.getenv("FUT_API_KEY")

PARSE_API_URL = (
    "https://api.parse.bot/scraper/"
    "5feab28c-82a9-4579-ae36-9307b1b0711a/"
    "search_players_fc27"
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI()


async def buscar_precio(nombre: str):

    if not FUT_API_KEY:
        return "Error: falta configurar FUT_API_KEY."

    try:

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.get(
                PARSE_API_URL,
                params={
                    "query": nombre.strip()
                },
                headers={
                    "X-API-Key": FUT_API_KEY,
                    "Accept": "application/json"
                }
            )

        print(
            f"API FUT → HTTP {response.status_code}"
        )

        if response.status_code != 200:

            print(
                f"Respuesta API: "
                f"{response.text[:500]}"
            )

            return (
                f"Error de la API: "
                f"HTTP {response.status_code}"
            )

        data = response.json()

        if data.get("status") != "success":

            print(
                f"API devolvió status: "
                f"{data.get('status')}"
            )

            return (
                f"No se pudo buscar '{nombre}'."
            )

        results = (
            data
            .get("data", {})
            .get("results", [])
        )

        if not results:

            return (
                f"No encontré ninguna carta "
                f"de '{nombre}'."
            )

        player = results[0]

        name = player.get(
            "name",
            nombre
        )

        rating = player.get(
            "rating",
            "?"
        )

        position = player.get(
            "position",
            "?"
        )

        version = player.get(
            "version",
            "?"
        )

        price_ps = player.get(
            "price_ps",
            "0"
        )

        price_pc = player.get(
            "price_pc",
            "0"
        )

        resultado = (
            f"{name} ({rating}) "
            f"{position} [{version}] "
            f"→ PS: {price_ps} | PC: {price_pc}"
        )

        return resultado

    except httpx.RequestError as e:

        print(
            f"ERROR DE CONEXIÓN API: {e}"
        )

        return (
            "Error de conexión "
            "con la API de FUT."
        )

    except Exception as e:

        print(
            f"ERROR BUSCANDO PRECIO: "
            f"{type(e).__name__}: {e}"
        )

        return (
            f"Error al buscar '{nombre}'."
        )


@app.get(
    "/precio",
    response_class=PlainTextResponse
)
async def precio(
    nombre: str = Query(
        ...,
        min_length=2
    )
):

    return await buscar_precio(nombre)


# ============================================================
# TWITCH HELIX
# ============================================================

async def obtener_usuario_twitch():

    token = TWITCH_ACCESS_TOKEN.replace(
        "oauth:",
        ""
    )

    async with httpx.AsyncClient(
        timeout=15.0
    ) as client:

        response = await client.get(
            "https://id.twitch.tv/oauth2/validate",
            headers={
                "Authorization": f"OAuth {token}"
            }
        )

    if response.status_code != 200:

        raise RuntimeError(
            "Token de Twitch inválido: "
            f"HTTP {response.status_code}"
        )

    data = response.json()

    return (
        data["user_id"],
        data.get("login")
    )


async def obtener_id_canal():

    token = TWITCH_ACCESS_TOKEN.replace(
        "oauth:",
        ""
    )

    async with httpx.AsyncClient(
        timeout=15.0
    ) as client:

        response = await client.get(
            "https://api.twitch.tv/helix/users",
            params={
                "login": TWITCH_CHANNEL
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Client-Id": TWITCH_CLIENT_ID
            }
        )

    if response.status_code != 200:

        raise RuntimeError(
            "No se pudo obtener el canal: "
            f"HTTP {response.status_code} "
            f"{response.text[:300]}"
        )

    data = response.json()

    if not data.get("data"):

        raise RuntimeError(
            f"No encontré el canal: "
            f"{TWITCH_CHANNEL}"
        )

    return data["data"][0]["id"]


# ============================================================
# BOT
# ============================================================

class PrecioBot(commands.Bot):

    def __init__(
        self,
        bot_id: str
    ):

        super().__init__(
            client_id=TWITCH_CLIENT_ID,
            client_secret=TWITCH_CLIENT_SECRET,
            bot_id=bot_id,
            prefix="!"
        )


    async def setup_hook(self):

        print(
            "Obteniendo ID del canal..."
        )

        broadcaster_id = (
            await obtener_id_canal()
        )

        print(
            f"Canal: {TWITCH_CHANNEL}"
        )

        print(
            f"Broadcaster ID: "
            f"{broadcaster_id}"
        )

        print(
            f"Bot ID: {self.bot_id}"
        )

        payload = eventsub.ChatMessageSubscription(
            broadcaster_user_id=broadcaster_id,
            user_id=self.bot_id
        )

        await self.subscribe_websocket(
            payload=payload
        )

        print(
            "Suscripción al chat creada."
        )


    async def event_ready(self):

        print(
            "=============================="
        )

        print(
            "BOT DE TWITCH CONECTADO"
        )

        print(
            f"Canal: {TWITCH_CHANNEL}"
        )

        print(
            "=============================="
        )


    # ========================================================
    # LOG DE MENSAJES
    # ========================================================
    #
    # IMPORTANTE:
    # Usamos listen() en lugar de sobrescribir event_message().
    # Así TwitchIO puede seguir procesando automáticamente
    # los comandos registrados con @commands.command().
    #

    @commands.Bot.listen()
    async def event_message(self, message):

        print(
            "MENSAJE RECIBIDO:",
            message.text
        )


    # ========================================================
    # COMANDO !PRECIO
    # ========================================================

    @commands.command()
    async def precio(
        self,
        ctx: commands.Context
    ):

        print(
            "COMANDO PRECIO RECIBIDO"
        )

        if ctx.message is None:

            print(
                "ERROR: el mensaje del contexto es None."
            )

            return

        contenido = ctx.message.content

        print(
            f"Contenido del comando: "
            f"{contenido}"
        )

        partes = contenido.split(
            maxsplit=1
        )

        if len(partes) < 2:

            await ctx.send(
                "Uso: !precio nombre del jugador"
            )

            return

        nombre = partes[1].strip()

        print(
            f"Buscando precio para: "
            f"{nombre}"
        )

        resultado = await buscar_precio(
            nombre
        )

        print(
            f"Respuesta para Twitch: "
            f"{resultado}"
        )

        await ctx.send(
            resultado
        )


    # ========================================================
    # ERRORES DE COMANDOS
    # ========================================================

    async def event_command_error(
        self,
        payload
    ):

        print(
            "ERROR EN COMANDO:"
        )

        print(
            f"{type(payload).__name__}: "
            f"{payload}"
        )


# ============================================================
# INICIAR TWITCH
# ============================================================

async def iniciar_twitch():

    variables = {

        "TWITCH_ACCESS_TOKEN":
            TWITCH_ACCESS_TOKEN,

        "TWITCH_REFRESH_TOKEN":
            TWITCH_REFRESH_TOKEN,

        "TWITCH_CLIENT_ID":
            TWITCH_CLIENT_ID,

        "TWITCH_CLIENT_SECRET":
            TWITCH_CLIENT_SECRET,

        "TWITCH_CHANNEL":
            TWITCH_CHANNEL,

        "FUT_API_KEY":
            FUT_API_KEY

    }

    for nombre, valor in variables.items():

        if not valor:

            print(
                f"ERROR: falta {nombre}"
            )

            return

    try:

        bot_id, login = (
            await obtener_usuario_twitch()
        )

        print(
            f"Usuario asociado al token: "
            f"{login}"
        )

        print(
            f"ID del usuario: "
            f"{bot_id}"
        )

        bot = PrecioBot(
            bot_id
        )

        await bot.add_token(
            TWITCH_ACCESS_TOKEN,
            TWITCH_REFRESH_TOKEN
        )

        await bot.start(
            load_tokens=False
        )

    except Exception as e:

        print(
            "ERROR AL CONECTAR TWITCH: "
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():

    asyncio.create_task(
        iniciar_twitch()
    )
