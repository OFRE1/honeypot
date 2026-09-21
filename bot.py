import os
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


TOKEN = os.getenv("DISCORD_TOKEN")


class HoneypotBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )


bot = HoneypotBot()

# guild_id -> honeypot channel id
honeypots: dict[int, int] = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

    # Sync slash commands
    await bot.tree.sync()
    print("Slash commands synced.")


@bot.tree.command(
    name="honeypot",
    description="Cấu hình channel honeypot"
)
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    channel="Channel dùng làm honeypot"
)
async def honeypot(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    # Kiểm tra thực tế permission của người dùng
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Bạn cần quyền Manage Server để dùng command này.",
            ephemeral=True
        )
        return

    honeypots[interaction.guild_id] = channel.id

    await interaction.response.send_message(
        f"✅ Honeypot đã đặt thành {channel.mention}\n"
        f"Người gửi message vào đó sẽ bị timeout 5 phút.",
        ephemeral=True
    )


@bot.tree.command(
    name="honeypot-off",
    description="Tắt honeypot"
)
@app_commands.default_permissions(manage_guild=True)
async def honeypot_off(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Bạn cần quyền Manage Server.",
            ephemeral=True
        )
        return

    honeypots.pop(interaction.guild_id, None)

    await interaction.response.send_message(
        "✅ Đã tắt honeypot.",
        ephemeral=True
    )


@bot.event
async def on_message(message: discord.Message):

    if message.guild is None:
        return

    # Không xử lý bot
    if message.author.bot:
        return

    honeypot_channel = honeypots.get(message.guild.id)

    # Không có honeypot
    if honeypot_channel is None:
        return

    # Không phải honeypot channel
    if message.channel.id != honeypot_channel:
        return

    member = message.author

    print(
        f"[HONEYPOT] {member} ({member.id}) "
        f"triggered #{message.channel.name}: "
        f"{message.content!r}"
    )

    # Xóa message
    try:
        await message.delete()
    except discord.HTTPException as e:
        print(f"[WARN] Cannot delete message: {e}")

    # Timeout 5 phút
    try:
        await.message.author.ban(
            reason="Honeypot triggered"
        )

        print(
            f"[HONEYPOT] {member} -> timeout 5 minutes"
        )

    except discord.Forbidden:
        print(
            "[ERROR] Không đủ quyền Moderate Members "
            "hoặc role bot thấp hơn target."
        )

    except discord.HTTPException as e:
        print(f"[ERROR] Timeout failed: {e}")


bot.run(TOKEN)
