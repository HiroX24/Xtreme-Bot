import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="purge",
        description="Bulk delete recent messages (up to 1000 in last 14 days)."
    )
    @app_commands.describe(
        count="Number of messages to delete (max 1000, only from last 14 days)",
        from_user="Only delete messages from this user (optional)",
        server="Purge from all channels (only works with user filter)"
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        count: int,
        from_user: discord.User = None,
        server: bool = False
    ):
        # 🔒 Admin check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🚫 You need Administrator permission to use this command.",
                ephemeral=True
            )
            return

        if count > 1000:
            await interaction.response.send_message(
                "⚠ You can delete a maximum of *1000 messages* at once.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        def check(msg):
            within_14_days = (discord.utils.utcnow() - msg.created_at) < timedelta(days=14)
            return within_14_days and (from_user is None or msg.author == from_user)

        total_deleted = 0
        user_msgs = 0
        bot_msgs = 0
        media_msgs = 0
        to_delete = count

        # Function to delete in batches
        async def delete_in_channel(channel: discord.TextChannel):
            nonlocal total_deleted, user_msgs, bot_msgs, media_msgs, to_delete
            while to_delete > 0:
                batch_limit = min(100, to_delete)
                try:
                    deleted = await channel.purge(limit=batch_limit, check=check, bulk=True)
                except discord.Forbidden:
                    break  # skip if bot has no perms in that channel
                except discord.HTTPException:
                    break  # something went wrong

                if not deleted:
                    break

                for msg in deleted:
                    if msg.author.bot:
                        bot_msgs += 1
                    else:
                        user_msgs += 1
                    if msg.attachments:
                        media_msgs += 1

                total_deleted += len(deleted)
                to_delete -= len(deleted)

                if len(deleted) < batch_limit:
                    break

        if server and from_user is not None:
            for channel in interaction.guild.text_channels:
                await delete_in_channel(channel)
                if to_delete <= 0:
                    break
        else:
            await delete_in_channel(interaction.channel)

        summary = (
            f"✅ Deleted *{total_deleted}* message(s)\n"
            f"> 🧍 User: {user_msgs}\n"
            f"> 🤖 Bot: {bot_msgs}\n"
            f"> 🖼 Media: {media_msgs}"
        )

        await interaction.followup.send(summary, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Purge(bot))