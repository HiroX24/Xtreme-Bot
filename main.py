import discord
from discord.ext import commands
import asyncio
import keep_alive
import os
from collections import defaultdict, deque

from ai_roast import generate_roast  # 👈 our AI roast helper

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True  # Required for on_message and slash context

# Slash-only bot, no prefix
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents, help_command=None)

# --- Roast-bot state ---

# channel_id -> deque of "Name: message"
channel_history = defaultdict(lambda: deque(maxlen=20))

# channels where the bot is "awake" and will roast on ping
active_channels = set()


@bot.event
async def setup_hook():
    # Load slash command extensions
    await bot.load_extension("slash_cmd.spam_cmds")
    await bot.load_extension("slash_cmd.purge")
    await bot.load_extension("slash_cmd.remind")
    await bot.load_extension("slash_cmd.help")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} global slash commands.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Track chat history for AI roast context
    content = message.content or ""
    line = f"{message.author.display_name}: {content}"
    channel_history[message.channel.id].append(line)

    mentioned = bot.user in message.mentions

    # First time activated in that channel
    if mentioned and message.channel.id not in active_channels:
        active_channels.add(message.channel.id)

        history_lines = list(channel_history[message.channel.id])

        roast = await generate_roast(
            author_name=message.author.display_name,
            user_message=content,
            history_lines=history_lines,
        )

        await message.channel.send(
            roast
            + "\n\nAlright, I'm awake in this channel now. Ping me again if you want more smoke."
        )

        return await bot.process_commands(message)

    # Already active here → roast only when pinged
    if mentioned and message.channel.id in active_channels:
        history_lines = list(channel_history[message.channel.id])

        roast = await generate_roast(
            author_name=message.author.display_name,
            user_message=content,
            history_lines=history_lines,
        )

        await message.channel.send(roast)
        return await bot.process_commands(message)

    # Allow slash commands to work normally
    await bot.process_commands(message)


keep_alive.keep_alive()


async def main():
    async with bot:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ No DISCORD_TOKEN found! Set it in Railway Variables.")
            return
        
        await bot.start(token)


asyncio.run(main())
