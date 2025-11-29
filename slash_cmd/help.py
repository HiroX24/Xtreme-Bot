import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="View all available commands and categories.")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Bot Command Help",
            description="Here are all the available commands sorted by category:",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🛠️ Utility",
            value="`/remind` — Set a reminder\n`/remindstop` — Stop your reminders",
            inline=False
        )

        embed.add_field(
            name="💬 Spam",
            value="`/spam` — Spam a message\n`/spamall` — Spam everyone\n`/stopspam` — Stop current spam\n`/stopall` — Stop all spam",
            inline=False
        )

        embed.add_field(
            name="🤖 Moderation",
            value="`/purge` — Bulk delete messages",
            inline=False
        )

        embed.set_footer(text="More commands coming soon. Use wisely.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))