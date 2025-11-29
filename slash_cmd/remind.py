import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import re
from datetime import datetime

def parse_time(timestr: str):
    match = re.fullmatch(r"(\d+)([smhd])", timestr.lower())
    if not match:
        return None
    num, unit = match.groups()
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(num) * multiplier[unit]

class Remind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat_tasks = {}  # {(guild_id, channel_id): task}

    def is_allowed(self, member: discord.Member):
        user_roles = [r.id for r in member.roles]
        secure_roles = list(filter(None, [
            int(os.getenv("TOKENGM", "0")),
            int(os.getenv("TOKENVGM", "0")),
            int(os.getenv("TOKENMOD", "0"))
        ]))
        return member.guild_permissions.administrator or any(role in user_roles for role in secure_roles)

    @app_commands.command(name="remind", description="Set a reminder. If repeat is enabled, only 1 reminder is allowed per channel.")
    @app_commands.describe(
        message="Message to remind",
        time="Time delay (e.g., 10s, 5m, 2h)",
        repeat="Repeat the reminder (admin/roles only, one per channel)",
        mention="Mention a user or role (only if repeat is true)"
    )
    async def remind(self, interaction: discord.Interaction, message: str, time: str, repeat: bool = False, mention: str = None):
        delay = parse_time(time)
        if delay is None:
            await interaction.response.send_message("❌ Invalid time format. Use `10s`, `5m`, `2h`, etc.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if repeat and not self.is_allowed(interaction.user):
            await interaction.followup.send("⛔ You don't have permission to use `repeat: true`", ephemeral=True)
            return

        if repeat and (interaction.guild_id, interaction.channel_id) in self.repeat_tasks:
            await interaction.followup.send("⚠️ There's already a repeating reminder in this channel. Stop it first using `/remindstop`.", ephemeral=True)
            return

        if mention and not repeat:
            await interaction.followup.send("❌ Mentions can only be used with repeating reminders.", ephemeral=True)
            return

        now = int(datetime.utcnow().timestamp())
        await interaction.followup.send(
            f"✅ Reminder set for <t:{now + delay}:R>{' (repeats)' if repeat else ''}",
            ephemeral=True
        )

        embed = discord.Embed(
            title="🔔 Reminder",
            description=message,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        async def send_once():
            await asyncio.sleep(delay)
            try:
                await interaction.channel.send(embed=embed)
            except Exception as e:
                print(f"[ERROR] Failed to send reminder: {e}")

        async def send_repeat():
            try:
                # First immediate send
                await interaction.channel.send(f"{mention}" if mention else None, embed=embed)
                while True:
                    await asyncio.sleep(delay)
                    await interaction.channel.send(f"{mention}" if mention else None, embed=embed)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"[ERROR] Repeating reminder failed: {e}")

        if repeat:
            task = asyncio.create_task(send_repeat())
            self.repeat_tasks[(interaction.guild_id, interaction.channel_id)] = task
        else:
            asyncio.create_task(send_once())

    @app_commands.command(name="remindstop", description="Stop an active repeat reminder in a channel.")
    @app_commands.describe(
        channel="Select the channel with the active repeating reminder"
    )
    async def remindstop(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_allowed(interaction.user):
            await interaction.response.send_message("⛔ Only admins or authorized roles can stop repeat reminders.", ephemeral=True)
            return

        key = (interaction.guild_id, channel.id)
        task = self.repeat_tasks.get(key)

        if task:
            task.cancel()
            del self.repeat_tasks[key]
            await interaction.response.send_message(f"✅ Stopped repeating reminder in {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No active repeating reminder found in that channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Remind(bot))