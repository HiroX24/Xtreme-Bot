import asyncio
import discord
from discord import app_commands
from discord.ext import commands

class Spam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tasks = {}  # {channel_id: asyncio.Task}

    async def spam_loop(self, channel: discord.TextChannel, message: str, interval: float):
        try:
            while True:
                await channel.send(message)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass  # Task was cancelled

    @app_commands.command(name="spam", description="Spam a message at intervals in a specific channel")
    @app_commands.describe(
        message="Message to spam",
        interval="Time between spam (in seconds) 0.1-100+ numbers available",
        channel="Channel to spam in"
    )
    async def spam(self, interaction: discord.Interaction, message: str, interval: float, channel: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        channel = channel or interaction.channel

        if channel.id in self.spam_tasks:
            await interaction.followup.send(f"⚠️ Spam already running in {channel.mention}", ephemeral=True)
            return

        task = asyncio.create_task(self.spam_loop(channel, message, interval))
        self.spam_tasks[channel.id] = task
        await interaction.followup.send(f"✅ Started spamming in {channel.mention}", ephemeral=True)

    @app_commands.command(name="stopspam", description="Stop spamming in a specific channel")
    @app_commands.describe(channel="Channel to stop spam in")
    async def stopspam(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        channel = channel or interaction.channel

        task = self.spam_tasks.pop(channel.id, None)
        if task:
            task.cancel()
            await interaction.followup.send(f"🛑 Stopped spamming in {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send(f"⚠️ No spam running in {channel.mention}", ephemeral=True)

    @app_commands.command(name="spamall", description="Spam a message in multiple channels inside a category")
    @app_commands.describe(
        message="Message to spam",
        interval="Time between spam (in seconds) 0.1-100+ numbers available",
        category="Category of channels to spam"
    )
    async def spamall(self, interaction: discord.Interaction, message: str, interval: float, category: discord.CategoryChannel = None):
        await interaction.response.defer(ephemeral=True)

        count = 0
        if category:
            channels = [ch for ch in category.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
        else:
            channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]

        for channel in channels:
            if channel.id not in self.spam_tasks:
                task = asyncio.create_task(self.spam_loop(channel, message, interval))
                self.spam_tasks[channel.id] = task
                count += 1

        await interaction.followup.send(f"✅ Started spamming in {count} channels.", ephemeral=True)

    @app_commands.command(name="stopall", description="Stop all spamming tasks")
    async def stopall(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        for task in self.spam_tasks.values():
            task.cancel()
        count = len(self.spam_tasks)
        self.spam_tasks.clear()
        await interaction.followup.send(f"🛑 Stopped all spam tasks ({count} channels).", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Spam(bot))