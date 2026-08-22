import discord
from discord.ext import commands
import wavelink
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Configuración básica del cliente del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 🛠️ SOLUCIÓN: Usamos setup_hook en lugar de on_ready para conectar Lavalink en segundo plano
@bot.event
async def setup_hook():
    nodo = wavelink.Node(
        uri="http://127.0.0.1:2333", 
        password=os.getenv("LAVALINK_PASSWORD")
    )
    # Conectamos al pool de forma paralela sin congelar el login del bot
    bot.loop.create_task(wavelink.Pool.connect(nodes=[nodo], client=bot))

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado exitosamente a Discord como: {bot.user}")

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"✅ ¡Conectado exitosamente al servidor de Lavalink! Nodo: {payload.node.identifier}")

@bot.command(name='play')
async def play(ctx, *, busqueda: str):
    """Reproduce canciones desde texto o enlaces directos de Spotify."""
    if not ctx.author.voice:
        return await ctx.send("❌ ¡Debes unirte a un canal de voz primero!")

    # Conectarse usando el reproductor especializado de Wavelink
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    await ctx.send("🔍 Buscando en los servidores musicales...")

    # Buscamos la pista. Wavelink identificará si es texto o un link de Spotify de forma nativa
    resultado = await wavelink.Playable.search(busqueda)
    
    if not resultado:
        return await ctx.send("❌ No se encontraron resultados para tu búsqueda.")

    # Si es una playlist, tomamos la primera canción (puedes crear un ciclo para agregarlas todas)
    if isinstance(resultado, wavelink.Playlist):
        track = resultado.tracks[0]
        await ctx.send(f"🎶 Se detectó una playlist. Añadiendo la primera canción: **{track.title}**")
    else:
        track = resultado[0]

    # Reproducir la canción
    await vc.play(track)
    await ctx.send(f"🎵 Reproduciendo ahora: **{track.title}** por *{track.author}*")

@bot.command(name='stop')
async def stop(ctx):
    """Detiene la música por completo y saca al bot."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Desconectado del canal de voz.")
    else:
        await ctx.send("❌ El bot no está en ningún canal de voz.")

# RECUERDA: Cambia este Token por el nuevo que reseteaste en tu panel de Discord Developer
TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN_DISCORD)
