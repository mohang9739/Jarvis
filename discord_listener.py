"""
JARVIS Discord Listener
- Listens for messages in Discord channel
- Writes user replies to /tmp/jarvis_reply.txt
- quiz_engine.py reads from that file
"""

import os
import discord
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"[discord_listener] Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author.bot:
        return

    # Only listen to the configured channel
    if message.channel.id != DISCORD_CHANNEL_ID:
        return

    print(f"[discord_listener] Got reply: {message.content}")

    # Write reply to file for quiz_engine to read
    with open("/tmp/jarvis_reply.txt", "w") as f:
        f.write(message.content.strip())

client.run(DISCORD_BOT_TOKEN)
