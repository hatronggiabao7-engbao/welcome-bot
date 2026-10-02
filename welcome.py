#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HGB WELCOME & GOODBYE — Classic Embed Style
Không generate card. Chỉ dùng embed + banner + thumbnail.
"""
import os
import traceback
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import database


# ── Default template ───────────────────────────────────────────────────────────
DEFAULT_WELCOME_TITLE = "📢 Chào mừng bạn đến {server} ☃️"
DEFAULT_WELCOME_DESC = (
    "♥️ Bạn có thể đọc luật để tránh những rủi ro và điều tiếc có thể xảy ra tại {rules_channel}\n\n"
    "♥️ Nếu bạn cần hỗ trợ có thể ping {admin_role} hoặc các bạn ping {owner_role}\n\n"
    "♥️ Kênh chat chung với server {general_channel}\n\n"
    "♥️ Nếu muốn build pc theo giá thì tới kênh {build_channel}\n\n"
    "♥️ Nếu bạn muốn thử việc tại server thì chat riêng với {owner_role} hay {admin_role}"
)

DEFAULT_GOODBYE_TITLE = "👋 Tạm biệt {user}"
DEFAULT_GOODBYE_DESC = "**{user}** đã rời khỏi **{server}**. Hẹn gặp lại! 💔"


# ── Helpers ────────────────────────────────────────────────────────────────────
def _safe_format(template: str, **kwargs) -> str:
    """Format template, bỏ qua lỗi KeyError."""
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        # Nếu thiếu key → trả về template gốc (không crash)
        return template


# ── Send welcome ───────────────────────────────────────────────────────────────
async def send_welcome(member: discord.Member):
    cfg = await database.get_config(str(member.guild.id))
    ch_id = cfg.get("welcome_channel")
    if not ch_id:
        return
    channel = member.guild.get_channel(int(ch_id))
    if not channel:
        return

    try:
        g = member.guild

        # Chuẩn bị context để format template
        ctx = {
            "user": member.mention,
            "user_name": member.name,
            "server": g.name,
            "member_count": g.member_count,
            "rules_channel": "<#rules>" if not g.rules_channel else g.rules_channel.mention,
            "general_channel": "<#general>" if not g.system_channel else g.system_channel.mention,
            "build_channel": "<#build-pc>",
            "admin_role": "<@&admin>",
            "owner_role": "<@&owner>",
        }

        # Title + Description
        title_tpl = cfg.get("welcome_title") or DEFAULT_WELCOME_TITLE
        desc_tpl = cfg.get("welcome_message") or DEFAULT_WELCOME_DESC
        title = _safe_format(title_tpl, **ctx)
        desc = _safe_format(desc_tpl, **ctx)

        color_hex = cfg.get("welcome_color") or 0x5865F2
        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color(color_hex),
            timestamp=discord.utils.utcnow(),
        )

        # Author = icon + tên server
        if g.icon:
            embed.set_author(name=g.name, icon_url=g.icon.url)
        else:
            embed.set_author(name=g.name)

        # Thumbnail (ảnh nhỏ góc phải)
        thumb = cfg.get("welcome_thumbnail")
        if thumb:
            embed.set_thumbnail(url=thumb)

        # Banner image lớn
        banner = cfg.get("welcome_banner")
        if banner:
            embed.set_image(url=banner)

        # Footer
        footer_text = cfg.get("welcome_footer") or g.name
        embed.set_footer(
            text=footer_text,
            icon_url=g.icon.url if g.icon else None,
        )

        await channel.send(content=member.mention, embed=embed)

        # Auto-role
        role_id = cfg.get("welcome_role")
        if role_id:
            role = g.get_role(int(role_id))
            if role:
                try:
                    await member.add_roles(role, reason="Welcome auto-role")
                except Exception as e:
                    print(f"[welcome] Auto-role fail: {e}")
    except Exception as e:
        print(f"[welcome] Lỗi gửi welcome: {e}")
        traceback.print_exc()


# ── Send goodbye ───────────────────────────────────────────────────────────────
async def send_goodbye(member: discord.Member):
    cfg = await database.get_config(str(member.guild.id))
    ch_id = cfg.get("goodbye_channel")
    if not ch_id:
        return
    channel = member.guild.get_channel(int(ch_id))
    if not channel:
        return

    try:
        g = member.guild
        ctx = {
            "user": member.name,
            "user_mention": member.mention,
            "server": g.name,
            "member_count": g.member_count,
        }

        title_tpl = cfg.get("goodbye_title") or DEFAULT_GOODBYE_TITLE
        desc_tpl = cfg.get("goodbye_message") or DEFAULT_GOODBYE_DESC
        title = _safe_format(title_tpl, **ctx)
        desc = _safe_format(desc_tpl, **ctx)

        color_hex = cfg.get("goodbye_color") or 0xED4245
        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color(color_hex),
            timestamp=discord.utils.utcnow(),
        )

        if g.icon:
            embed.set_author(name=g.name, icon_url=g.icon.url)
        else:
            embed.set_author(name=g.name)

        thumb = cfg.get("goodbye_thumbnail") or cfg.get("welcome_thumbnail")
        if thumb:
            embed.set_thumbnail(url=thumb)

        banner = cfg.get("goodbye_banner") or cfg.get("welcome_banner")
        if banner:
            embed.set_image(url=banner)

        footer_text = cfg.get("goodbye_footer") or g.name
        embed.set_footer(
            text=footer_text,
            icon_url=g.icon.url if g.icon else None,
        )

        await channel.send(embed=embed)
    except Exception as e:
        print(f"[welcome] Lỗi gửi goodbye: {e}")
        traceback.print_exc()


# ── Setup ──────────────────────────────────────────────────────────────────────
def setup_welcome(bot: commands.Bot):

    @bot.event
    async def on_member_join(member: discord.Member):
        if member.bot:
            return
        await send_welcome(member)

    @bot.event
    async def on_member_remove(member: discord.Member):
        if member.bot:
            return
        await send_goodbye(member)

    # ── WELCOME ──────────────────────────────────────────────────────────────
    @bot.tree.command(name="welcome-set",
                      description="Set kênh gửi welcome.")
    @app_commands.describe(channel="Kênh gửi welcome")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_set(interaction: discord.Interaction, channel: discord.TextChannel):
        await database.set_config(str(interaction.guild_id), welcome_channel=str(channel.id))
        embed = discord.Embed(
            title="✅ Đã set kênh Welcome",
            description=f"Welcome sẽ gửi tại {channel.mention}",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Developer by @hgb_7")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @welcome_set.error
    async def welcome_set_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    @bot.tree.command(name="welcome-off", description="Tắt welcome.")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_off(interaction: discord.Interaction):
        await database.unset_config(str(interaction.guild_id), "welcome_channel")
        await interaction.response.send_message("🔕 Đã tắt Welcome.", ephemeral=True)

    @welcome_off.error
    async def welcome_off_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    @bot.tree.command(name="welcome-test", description="Test thử welcome.")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_test(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if isinstance(interaction.user, discord.Member):
            await send_welcome(interaction.user)
            await interaction.followup.send("✅ Đã gửi test.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Không lấy được member.", ephemeral=True)

    @welcome_test.error
    async def welcome_test_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    # ── /welcome-content — Modal để nhập nội dung ────────────────────────────
    class WelcomeContentModal(discord.ui.Modal, title="✏️ Nội dung Welcome"):
        def __init__(self, guild_id: str):
            super().__init__()
            self.guild_id = guild_id

            self.title_input = discord.ui.TextInput(
                label="Tiêu đề embed",
                placeholder="📢 Chào mừng bạn đến {server} ☃️",
                default="",
                max_length=256,
                required=False,
                style=discord.TextStyle.short,
            )
            self.desc_input = discord.ui.TextInput(
                label="Nội dung (dùng {user} {server} ...)",
                placeholder="♥️ Bạn có thể đọc luật...",
                default="",
                max_length=4000,
                required=False,
                style=discord.TextStyle.paragraph,
            )
            self.banner_input = discord.ui.TextInput(
                label="URL ảnh banner (lớn, dưới cùng)",
                placeholder="https://i.imgur.com/xxx.gif",
                default="",
                max_length=500,
                required=False,
                style=discord.TextStyle.short,
            )
            self.thumb_input = discord.ui.TextInput(
                label="URL thumbnail (nhỏ, góc phải)",
                placeholder="https://i.imgur.com/xxx.png",
                default="",
                max_length=500,
                required=False,
                style=discord.TextStyle.short,
            )
            self.footer_input = discord.ui.TextInput(
                label="Footer (vd: Hồ Chí Minh)",
                placeholder="Hồ Chí Minh",
                default="",
                max_length=200,
                required=False,
                style=discord.TextStyle.short,
            )
            self.add_item(self.title_input)
            self.add_item(self.desc_input)
            self.add_item(self.banner_input)
            self.add_item(self.thumb_input)
            self.add_item(self.footer_input)

        async def on_submit(self, interaction: discord.Interaction):
            updates = {}
            if self.title_input.value.strip():
                updates["welcome_title"] = self.title_input.value.strip()
            if self.desc_input.value.strip():
                updates["welcome_message"] = self.desc_input.value.strip()
            if self.banner_input.value.strip():
                updates["welcome_banner"] = self.banner_input.value.strip()
            if self.thumb_input.value.strip():
                updates["welcome_thumbnail"] = self.thumb_input.value.strip()
            if self.footer_input.value.strip():
                updates["welcome_footer"] = self.footer_input.value.strip()

            if updates:
                await database.set_config(self.guild_id, **updates)

            embed = discord.Embed(
                title="✅ Đã cập nhật nội dung Welcome",
                description=f"Cập nhật **{len(updates)}** trường.",
                color=discord.Color.green(),
            )
            for k, v in updates.items():
                short = v if len(v) <= 100 else v[:97] + "..."
                embed.add_field(name=k, value=f"`{short}`", inline=False)
            embed.set_footer(text="Developer by @hgb_7")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="welcome-content",
                      description="Mở form nhập nội dung welcome (title, desc, banner, thumbnail).")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_content(interaction: discord.Interaction):
        cfg = await database.get_config(str(interaction.guild_id))

        modal = WelcomeContentModal(str(interaction.guild_id))
        # Pre-fill giá trị hiện tại
        if cfg.get("welcome_title"):
            modal.title_input.default = cfg["welcome_title"]
        if cfg.get("welcome_message"):
            modal.desc_input.default = cfg["welcome_message"]
        if cfg.get("welcome_banner"):
            modal.banner_input.default = cfg["welcome_banner"]
        if cfg.get("welcome_thumbnail"):
            modal.thumb_input.default = cfg["welcome_thumbnail"]
        if cfg.get("welcome_footer"):
            modal.footer_input.default = cfg["welcome_footer"]

        await interaction.response.send_modal(modal)

    @welcome_content.error
    async def welcome_content_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    @bot.tree.command(name="welcome-role",
                      description="Set auto-role cho member mới.")
    @app_commands.describe(role="Role auto-give. Bỏ trống để tắt.")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_role(interaction: discord.Interaction, role: Optional[discord.Role] = None):
        gid = str(interaction.guild_id)
        if role:
            await database.set_config(gid, welcome_role=str(role.id))
            desc = f"Sẽ gán {role.mention} cho member mới."
        else:
            await database.unset_config(gid, "welcome_role")
            desc = "Đã tắt auto-role."
        await interaction.response.send_message(f"✅ {desc}", ephemeral=True)

    @welcome_role.error
    async def welcome_role_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    # ── GOODBYE ──────────────────────────────────────────────────────────────
    @bot.tree.command(name="goodbye-set",
                      description="Set kênh gửi goodbye.")
    @app_commands.describe(channel="Kênh gửi goodbye")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_set(interaction: discord.Interaction, channel: discord.TextChannel):
        await database.set_config(str(interaction.guild_id), goodbye_channel=str(channel.id))
        embed = discord.Embed(
            title="✅ Đã set kênh Goodbye",
            description=f"Goodbye sẽ gửi tại {channel.mention}",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Developer by @hgb_7")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @goodbye_set.error
    async def goodbye_set_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    @bot.tree.command(name="goodbye-off", description="Tắt goodbye.")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_off(interaction: discord.Interaction):
        await database.unset_config(str(interaction.guild_id), "goodbye_channel")
        await interaction.response.send_message("🔕 Đã tắt Goodbye.", ephemeral=True)

    @goodbye_off.error
    async def goodbye_off_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    @bot.tree.command(name="goodbye-test", description="Test thử goodbye.")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_test(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if isinstance(interaction.user, discord.Member):
            await send_goodbye(interaction.user)
            await interaction.followup.send("✅ Đã gửi test.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Không lấy được member.", ephemeral=True)

    @goodbye_test.error
    async def goodbye_test_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    class GoodbyeContentModal(discord.ui.Modal, title="✏️ Nội dung Goodbye"):
        def __init__(self, guild_id: str):
            super().__init__()
            self.guild_id = guild_id

            self.title_input = discord.ui.TextInput(
                label="Tiêu đề embed",
                placeholder="👋 Tạm biệt {user}",
                default="",
                max_length=256,
                required=False,
            )
            self.desc_input = discord.ui.TextInput(
                label="Nội dung",
                placeholder="**{user}** đã rời khỏi **{server}**...",
                default="",
                max_length=4000,
                required=False,
                style=discord.TextStyle.paragraph,
            )
            self.banner_input = discord.ui.TextInput(
                label="URL ảnh banner",
                placeholder="https://i.imgur.com/xxx.gif",
                default="",
                max_length=500,
                required=False,
            )
            self.thumb_input = discord.ui.TextInput(
                label="URL thumbnail",
                placeholder="https://i.imgur.com/xxx.png",
                default="",
                max_length=500,
                required=False,
            )
            self.footer_input = discord.ui.TextInput(
                label="Footer",
                placeholder="Hồ Chí Minh",
                default="",
                max_length=200,
                required=False,
            )
            self.add_item(self.title_input)
            self.add_item(self.desc_input)
            self.add_item(self.banner_input)
            self.add_item(self.thumb_input)
            self.add_item(self.footer_input)

        async def on_submit(self, interaction: discord.Interaction):
            updates = {}
            if self.title_input.value.strip():
                updates["goodbye_title"] = self.title_input.value.strip()
            if self.desc_input.value.strip():
                updates["goodbye_message"] = self.desc_input.value.strip()
            if self.banner_input.value.strip():
                updates["goodbye_banner"] = self.banner_input.value.strip()
            if self.thumb_input.value.strip():
                updates["goodbye_thumbnail"] = self.thumb_input.value.strip()
            if self.footer_input.value.strip():
                updates["goodbye_footer"] = self.footer_input.value.strip()

            if updates:
                await database.set_config(self.guild_id, **updates)

            embed = discord.Embed(
                title="✅ Đã cập nhật nội dung Goodbye",
                description=f"Cập nhật **{len(updates)}** trường.",
                color=discord.Color.green(),
            )
            embed.set_footer(text="Developer by @hgb_7")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="goodbye-content",
                      description="Mở form nhập nội dung goodbye.")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_content(interaction: discord.Interaction):
        cfg = await database.get_config(str(interaction.guild_id))
        modal = GoodbyeContentModal(str(interaction.guild_id))
        if cfg.get("goodbye_title"):
            modal.title_input.default = cfg["goodbye_title"]
        if cfg.get("goodbye_message"):
            modal.desc_input.default = cfg["goodbye_message"]
        if cfg.get("goodbye_banner"):
            modal.banner_input.default = cfg["goodbye_banner"]
        if cfg.get("goodbye_thumbnail"):
            modal.thumb_input.default = cfg["goodbye_thumbnail"]
        if cfg.get("goodbye_footer"):
            modal.footer_input.default = cfg["goodbye_footer"]
        await interaction.response.send_modal(modal)

    @goodbye_content.error
    async def goodbye_content_error(interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Cần **Administrator**.", ephemeral=True)

    # ── HELP ─────────────────────────────────────────────────────────────────
    @bot.tree.command(name="help", description="Hướng dẫn sử dụng.")
    async def help_cmd(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 HGB Welcome Bot",
            description="Bot chào mừng & tạm biệt phong cách Discord classic.",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="👋 Welcome",
            value=(
                "`/welcome-set #channel` — Set kênh\n"
                "`/welcome-content` — Mở form nhập nội dung\n"
                "`/welcome-test` — Test\n"
                "`/welcome-role @role` — Auto-role\n"
                "`/welcome-off` — Tắt"
            ),
            inline=False,
        )
        embed.add_field(
            name="🚪 Goodbye",
            value=(
                "`/goodbye-set #channel`\n"
                "`/goodbye-content` — Form nội dung\n"
                "`/goodbye-test`\n"
                "`/goodbye-off`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔤 Biến dùng trong nội dung",
            value=(
                "`{user}` — mention member\n"
                "`{user_name}` — tên member\n"
                "`{server}` — tên server\n"
                "`{member_count}` — số member"
            ),
            inline=False,
        )
        embed.set_footer(text="Developer by @hgb_7")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    print("[welcome] Module (classic embed) đã setup ✅")