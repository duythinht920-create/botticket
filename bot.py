import asyncio
import json
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

import config

TICKETS_FILE = "tickets.json"
PANEL_FILE = "panel.json"
PANEL_COLOR = discord.Color.from_rgb(87, 242, 135)


def load_tickets() -> dict:
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"channels": {}}


def save_tickets(data: dict) -> None:
    with open(TICKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_panel() -> dict:
    if os.path.exists(PANEL_FILE):
        with open(PANEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_panel(data: dict) -> None:
    with open(PANEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_ticket_count() -> int:
    return len(load_tickets().get("channels", {}))


def get_staff_role_ids() -> set[int]:
    ids = set()
    if config.SUPPORT_ROLE_ID:
        ids.add(config.SUPPORT_ROLE_ID)
    if config.ADMIN_ROLE_ID:
        ids.add(config.ADMIN_ROLE_ID)
    return ids


def get_staff_roles(guild: discord.Guild) -> list[discord.Role]:
    roles = []
    for role_id in get_staff_role_ids():
        role = guild.get_role(role_id)
        if role:
            roles.append(role)

    if not roles:
        for name in ("Support", "support", "Admin", "admin", "Administrator"):
            role = discord.utils.get(guild.roles, name=name)
            if role and role not in roles:
                roles.append(role)

    return roles


def is_staff(member: discord.Member) -> bool:
    staff_ids = {role.id for role in get_staff_roles(member.guild)}
    if staff_ids:
        return any(role.id in staff_ids for role in member.roles)

    return any(
        role.name.lower() in {"support", "admin", "administrator"}
        for role in member.roles
        if role != member.guild.default_role
    )


def is_admin(member: discord.Member) -> bool:
    if config.ADMIN_ROLE_ID:
        return any(role.id == config.ADMIN_ROLE_ID for role in member.roles)

    return member.guild_permissions.administrator or any(
        role.name.lower() in {"admin", "administrator"} for role in member.roles
    )


def admin_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member) or not is_admin(interaction.user):
            raise app_commands.CheckFailure("Chi Admin moi su dung duoc lenh nay.")
        return True

    return app_commands.check(predicate)


async def delete_all_tickets(guild: discord.Guild, by_user: discord.abc.User) -> int:
    tickets_data = load_tickets()
    deleted = 0

    for channel_id in list(tickets_data.get("channels", {}).keys()):
        channel = guild.get_channel(int(channel_id))
        if channel:
            try:
                await channel.delete(reason=f"Xoa tat ca ticket - {by_user}")
                deleted += 1
            except discord.HTTPException:
                pass

    tickets_data["channels"] = {}
    save_tickets(tickets_data)

    if config.LOG_CHANNEL_ID and deleted > 0:
        log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="Xoa Tat Ca Ticket",
                description=f"**Admin:** {by_user.mention}\n**Da xoa:** {deleted} ticket",
                color=discord.Color.dark_red(),
                timestamp=datetime.now(timezone.utc),
            )
            await log_channel.send(embed=log_embed)

    return deleted


def get_panel_channel_id() -> int:
    panel_data = load_panel()
    channel_id = panel_data.get("channel_id")
    if channel_id:
        return int(channel_id)
    return config.TICKET_PANEL_CHANNEL_ID


def get_ticket_category(guild: discord.Guild) -> discord.CategoryChannel | None:
    panel_data = load_panel()
    saved_category_id = panel_data.get("category_id")
    if saved_category_id:
        category = guild.get_channel(int(saved_category_id))
        if isinstance(category, discord.CategoryChannel):
            return category

    if config.TICKET_CATEGORY_ID:
        category = guild.get_channel(config.TICKET_CATEGORY_ID)
        if isinstance(category, discord.CategoryChannel):
            return category

    panel_channel = guild.get_channel(get_panel_channel_id())
    if isinstance(panel_channel, discord.TextChannel) and panel_channel.category:
        return panel_channel.category

    for name in ("Tickets", "TICKETS", "Ticket", "TDT", "ticket", "Support"):
        category = discord.utils.get(guild.categories, name=name)
        if category:
            return category

    return None


def save_panel_data(
    *,
    message_id: int,
    channel_id: int,
    category_id: int | None = None,
) -> None:
    data = load_panel()
    data["message_id"] = message_id
    data["channel_id"] = channel_id
    if category_id:
        data["category_id"] = category_id
    save_panel(data)


async def post_panel_to_channel(
    channel: discord.TextChannel,
    *,
    update_existing: bool = True,
    category_id: int | None = None,
) -> discord.Message:
    ticket_count = get_ticket_count()
    show_delete_all = ticket_count >= config.MAX_TICKETS_BEFORE_DELETE_ALL
    embed = build_panel_embed(show_delete_all=show_delete_all)
    view = build_panel_view(show_delete_all=show_delete_all)

    panel_data = load_panel()
    old_channel_id = panel_data.get("channel_id")
    old_message_id = panel_data.get("message_id")

    if (
        old_channel_id
        and old_message_id
        and int(old_channel_id) != channel.id
    ):
        old_channel = channel.guild.get_channel(int(old_channel_id))
        if old_channel:
            try:
                old_message = await old_channel.fetch_message(int(old_message_id))
                await old_message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

    resolved_category_id = (
        category_id
        or (channel.category.id if channel.category else None)
        or panel_data.get("category_id")
    )

    if (
        update_existing
        and panel_data.get("channel_id") == channel.id
        and panel_data.get("message_id")
    ):
        try:
            message = await channel.fetch_message(panel_data["message_id"])
            await message.edit(embed=embed, view=view)
            save_panel_data(
                message_id=message.id,
                channel_id=channel.id,
                category_id=resolved_category_id,
            )
            return message
        except (discord.NotFound, discord.Forbidden):
            pass

    message = await channel.send(embed=embed, view=view)
    save_panel_data(
        message_id=message.id,
        channel_id=channel.id,
        category_id=resolved_category_id,
    )
    return message


def build_panel_embed(show_delete_all: bool = False) -> discord.Embed:
    embed = discord.Embed(
        title="Create Ticket",
        description="To create a ticket use the Create ticket button",
        color=PANEL_COLOR,
    )
    embed.set_footer(text="BotTicket - Ticketing without clutter")

    if show_delete_all:
        embed.add_field(
            name="Admin",
            value=(
                f"Co {get_ticket_count()} ticket. "
                f"Admin co the dung nut Delete All Tickets."
            ),
            inline=False,
        )

    return embed


def build_panel_view(show_delete_all: bool = False) -> discord.ui.View:
    view = TicketPanelView(show_delete_all=show_delete_all)
    if not show_delete_all:
        for item in view.children:
            if getattr(item, "custom_id", None) == "panel_delete_all":
                view.remove_item(item)
                break
    return view


async def ensure_deferred(interaction: discord.Interaction) -> bool:
    if interaction.response.is_done():
        return True
    try:
        await interaction.response.defer(ephemeral=True)
        return True
    except discord.NotFound:
        return False
    except discord.HTTPException as exc:
        if exc.code in (40060, 10062):
            return False
        raise


async def safe_ephemeral(interaction: discord.Interaction, content: str = "", **kwargs):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True, **kwargs)
        else:
            await interaction.response.send_message(content, ephemeral=True, **kwargs)
    except discord.HTTPException as exc:
        if exc.code not in (40060, 10062):
            print(f"[WARN] safe_ephemeral: {exc}")


async def handle_create_ticket(interaction: discord.Interaction):
    try:
        if not await ensure_deferred(interaction):
            return

        guild = interaction.guild
        if not guild:
            await safe_ephemeral(interaction, "Lenh nay chi dung trong server.")
            return

        user = interaction.user
        tickets_data = load_tickets()

        for channel_id, info in tickets_data.get("channels", {}).items():
            if info.get("user_id") == user.id:
                channel = guild.get_channel(int(channel_id))
                if channel:
                    await safe_ephemeral(
                        interaction,
                        f"Ban da co ticket mo: {channel.mention}",
                    )
                    return

        category = get_ticket_category(guild)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
            ),
        }

        for role in get_staff_roles(guild):
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            )

        channel_name = f"TDTticket-{user.name}".lower().replace(" ", "-")[:32]
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket cua {user.display_name} | ID: {user.id}",
        )

        tickets_data.setdefault("channels", {})[str(ticket_channel.id)] = {
            "user_id": user.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "open",
        }
        save_tickets(tickets_data)

        embed = discord.Embed(
            title="Create Ticket",
            description=(
                f"Hello {user.mention}!\n\n"
                "Staff **Support** or **Admin** will reply soon.\n"
                "Please describe your issue below.\n\n"
                "*Only Support and Admin can see this channel.*"
            ),
            color=PANEL_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="BotTicket TDT - Ticketing without clutter")

        view = TicketControlView()
        mention = build_staff_mention(guild)
        await ticket_channel.send(
            content=mention or None,
            embed=embed,
            view=view,
        )

        success_embed = discord.Embed(
            title="Ticket Created",
            description=f"Your private channel: {ticket_channel.mention}",
            color=PANEL_COLOR,
        )
        success_embed.set_footer(text="BotTicket TDT")
        await safe_ephemeral(interaction, embed=success_embed)

        if config.LOG_CHANNEL_ID:
            log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="Ticket duoc tao",
                    description=f"**Nguoi dung:** {user.mention}\n**Kenh:** {ticket_channel.mention}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc),
                )
                await log_channel.send(embed=log_embed)

    except discord.Forbidden:
        await safe_ephemeral(
            interaction,
            "Bot khong co quyen tao kenh. Can quyen Manage Channels.",
        )
    except Exception as exc:
        print(f"[ERROR] create_ticket: {type(exc).__name__}: {exc}")
        await safe_ephemeral(interaction, "Loi tao ticket. Thu lai sau.")


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket_close_btn",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        tickets_data = load_tickets()
        ticket_info = tickets_data.get("channels", {}).get(str(channel.id))

        if not ticket_info:
            await interaction.response.send_message("❌ Không tìm thấy ticket.", ephemeral=True)
            return

        user_id = ticket_info.get("user_id")
        is_owner = interaction.user.id == user_id
        staff = is_staff(interaction.user)

        if not is_owner and not staff:
            await interaction.response.send_message(
                "❌ Bạn không có quyền đóng ticket này.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        overwrites = channel.overwrites
        if user_id:
            overwrites[discord.Object(id=user_id)] = discord.PermissionOverwrite(
                view_channel=False,
                send_messages=False,
            )

        await channel.edit(overwrites=overwrites)

        ticket_info["status"] = "closed"
        ticket_info["closed_at"] = datetime.now(timezone.utc).isoformat()
        ticket_info["closed_by"] = interaction.user.id
        save_tickets(tickets_data)

        embed = discord.Embed(
            title="🔒 Ticket Đã Đóng",
            description=f"Ticket đã được đóng bởi {interaction.user.mention}.",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )

        delete_view = TicketDeleteView()
        await channel.send(embed=embed, view=delete_view)
        await interaction.followup.send("✅ Đã đóng ticket.", ephemeral=True)


class TicketDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Xóa Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
        custom_id="ticket_delete_btn",
    )
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Chỉ Support/Admin mới có thể xóa ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        channel = interaction.channel
        tickets_data = load_tickets()
        tickets_data.get("channels", {}).pop(str(channel.id), None)
        save_tickets(tickets_data)

        await interaction.followup.send("🗑️ Đang xóa ticket...", ephemeral=True)
        await asyncio.sleep(2)
        await channel.delete(reason=f"Xóa bởi {interaction.user}")


class TicketPanelView(discord.ui.View):
    def __init__(self, show_delete_all: bool = False):
        super().__init__(timeout=None)
        self.show_delete_all = show_delete_all

    @discord.ui.button(
        label="Create ticket",
        style=discord.ButtonStyle.secondary,
        emoji="📩",
        custom_id="panel_ticket_create",
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_create_ticket(interaction)

    @discord.ui.button(
        label="Delete All Tickets",
        style=discord.ButtonStyle.danger,
        emoji="⚠️",
        custom_id="panel_delete_all",
    )
    async def delete_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Chỉ Admin mới thấy và sử dụng được nút này.",
                ephemeral=True,
            )
            return

        count = get_ticket_count()
        if count < config.MAX_TICKETS_BEFORE_DELETE_ALL:
            await interaction.response.send_message(
                f"ℹ️ Hiện có {count} ticket. Nút này chỉ hiện khi có từ "
                f"**{config.MAX_TICKETS_BEFORE_DELETE_ALL}** ticket trở lên.",
                ephemeral=True,
            )
            return

        confirm_view = ConfirmDeleteAllView(count)
        await interaction.response.send_message(
            f"⚠️ Bạn sắp xóa **{count}** ticket. Xác nhận?",
            view=confirm_view,
            ephemeral=True,
        )


def build_staff_mention(guild: discord.Guild) -> str:
    mentions = [role.mention for role in get_staff_roles(guild)]
    return " ".join(mentions) if mentions else ""


class ConfirmDeleteAllView(discord.ui.View):
    def __init__(self, count: int):
        super().__init__(timeout=60)
        self.count = count

    @discord.ui.button(label="Xac nhan xoa", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message("Khong co quyen.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        deleted = await delete_all_tickets(interaction.guild, interaction.user)
        await interaction.followup.send(f"Da xoa **{deleted}** ticket.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Huy", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Da huy.", ephemeral=True)
        self.stop()


class TicketBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(TicketControlView())
        self.add_view(TicketDeleteView())
        self.add_view(TicketPanelView())

        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def ensure_panel(self):
        channel_id = get_panel_channel_id()
        if not channel_id:
            return

        panel_data = load_panel()
        if not panel_data.get("message_id"):
            return

        channel = self.get_channel(channel_id)
        if not channel:
            print(f"[WARN] Khong tim thay kenh panel: {channel_id}")
            return

        try:
            await post_panel_to_channel(channel)
            print(f"[OK] Da cap nhat panel trong kenh {channel.id}")
        except discord.Forbidden:
            print(
                f"[ERROR] Bot khong co quyen gui tin vao kenh {channel.id}. "
                "Hay cap quyen View Channel + Send Messages + Embed Links cho bot."
            )

    async def on_ready(self):
        print(f"[OK] Bot da online: {self.user} (ID: {self.user.id})")
        print(f"[INFO] So server: {len(self.guilds)}")
        print(f"[INFO] So ticket: {get_ticket_count()}")
        await self.ensure_panel()


bot = TicketBot()


async def send_panel_to_channel_cmd(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    category: discord.CategoryChannel | None = None,
):
    await interaction.response.defer(ephemeral=True)
    try:
        await post_panel_to_channel(
            channel,
            category_id=category.id if category else None,
        )

        panel_data = load_panel()
        category_text = ""
        if panel_data.get("category_id"):
            category_text = f"\nCategory ticket: <#{panel_data['category_id']}>"

        await interaction.followup.send(
            f"Da gui panel ticket vao {channel.mention}!{category_text}",
            ephemeral=True,
        )
    except discord.Forbidden:
        await interaction.followup.send(
            f"Bot khong co quyen gui tin vao {channel.mention}. "
            "Hay cap quyen View Channel + Send Messages + Embed Links.",
            ephemeral=True,
        )


@bot.tree.command(name="setup-ticket", description="[Admin] Chon kenh va gui panel ticket")
@admin_only()
@app_commands.describe(
    channel="Kenh hien panel ticket",
    category="Category chua cac kenh ticket",
)
async def setup_ticket(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    category: discord.CategoryChannel | None = None,
):
    await send_panel_to_channel_cmd(interaction, channel, category)


@bot.tree.command(name="delete-all-tickets", description="[Admin] Xoa TAT CA ticket")
@admin_only()
async def delete_all_tickets_cmd(interaction: discord.Interaction):
    count = get_ticket_count()
    if count == 0:
        await interaction.response.send_message("Khong co ticket nao de xoa.", ephemeral=True)
        return

    confirm_view = ConfirmDeleteAllView(count)
    await interaction.response.send_message(
        f"Ban sap xoa **{count}** ticket. Xac nhan?",
        view=confirm_view,
        ephemeral=True,
    )


@setup_ticket.error
@delete_all_tickets_cmd.error
async def admin_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "Chi Admin moi su dung duoc lenh Bot Ticket TDT.",
            ephemeral=True,
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "Chi Admin moi su dung duoc lenh Bot Ticket TDT.",
            ephemeral=True,
        )


def main():
    if not config.DISCORD_TOKEN:
        print("[ERROR] Thieu DISCORD_TOKEN trong file .env")
        return

    try:
        bot.run(config.DISCORD_TOKEN)
    except discord.PrivilegedIntentsRequired:
        print("[ERROR] Can bat privileged intents trong Discord Developer Portal")


if __name__ == "__main__":
    main()
