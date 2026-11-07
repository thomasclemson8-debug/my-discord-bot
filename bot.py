
import discord
from discord.ext import commands
import json
import os
import random
import time
import re

# ==========================================
# CONFIGURATION
# ==========================================

TOKEN = os.getenv("DISCORD_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
DATABASE_FILE = "economy.json"

PREFIX = "!"

# ==========================================
# DISCORD BOT SETUP
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

# ==========================================
# DATABASE SYSTEM
# ==========================================

DEFAULT_DATABASE = {
    "wallets": {},
    "xp": {},
    "shop_items": {
        "Vanguard Role": 500,
        "VIP Access Pass": 2500
    },
    "custom_commands": {},
    "daily_claims": {}
}


def load_database():
    if not os.path.exists(DATABASE_FILE):
        save_database(DEFAULT_DATABASE)
        return DEFAULT_DATABASE.copy()

    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        for key, value in DEFAULT_DATABASE.items():
            if key not in data:
                data[key] = value.copy()

        return data

    except (json.JSONDecodeError, OSError):
        print("Database error. Creating a new database.")
        return DEFAULT_DATABASE.copy()


def save_database(data=None):
    if data is None:
        data = database

    temporary_file = DATABASE_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    os.replace(temporary_file, DATABASE_FILE)


database = load_database()


def get_wallet(user_id):
    user_id = str(user_id)

    if user_id not in database["wallets"]:
        database["wallets"][user_id] = 0

    return database["wallets"][user_id]


def set_wallet(user_id, amount):
    database["wallets"][str(user_id)] = max(0, int(amount))
    save_database()


def get_xp(user_id):
    user_id = str(user_id)

    if user_id not in database["xp"]:
        database["xp"][user_id] = {
            "xp": 0,
            "level": 1
        }

    return database["xp"][user_id]


# ==========================================
# BOT EVENTS
# ==========================================

@bot.event
async def on_ready():
    print("========================================")
    print("🔥 ALL SYSTEMS OPERATIONAL")
    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Connected to {len(bot.guilds)} servers")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # CUSTOM TEXT COMMANDS

    if message.content.startswith(PREFIX):

        parts = message.content[1:].split(maxsplit=1)

        if parts:
            command_name = parts[0].lower()

            if command_name in database["custom_commands"]:
                await message.channel.send(
                    database["custom_commands"][command_name]
                )

        await bot.process_commands(message)
        return

    # CHAT XP SYSTEM

    if message.guild:

        sentences = [
            sentence for sentence in re.split(
                r"(?<=[.!?])\s+",
                message.content.strip()
            )
            if sentence.strip()
        ]

        if not sentences and message.content.strip():
            sentences = [message.content.strip()]

        user_data = get_xp(message.author.id)

        for sentence in sentences:

            earned_xp = random.randint(10, 25)

            user_data["xp"] += earned_xp

            while user_data["xp"] >= user_data["level"] * 100:

                required_xp = user_data["level"] * 100

                user_data["xp"] -= required_xp
                user_data["level"] += 1

                await message.channel.send(
                    f"🎉 **LEVEL UP!** {message.author.mention} "
                    f"reached **Level {user_data['level']}!**"
                )

        save_database()

    await bot.process_commands(message)


# ==========================================
# ECONOMY COMMANDS
# ==========================================

@bot.command(name="work")
@commands.cooldown(1, 30, commands.BucketType.user)
async def work(ctx):

    jobs = [
        "Pizza Delivery Driver",
        "Mechanic",
        "Security Guard",
        "Taxi Driver",
        "Construction Worker",
        "Software Developer",
        "Store Manager",
        "Police Officer",
        "Chef",
        "Professional Gamer",
        "Car Dealer",
        "Electrician"
    ]

    earnings = random.randint(50, 200)
    job = random.choice(jobs)

    balance = get_wallet(ctx.author.id)
    set_wallet(ctx.author.id, balance + earnings)

    embed = discord.Embed(
        title="💼 Work Completed!",
        description=(
            f"You worked as a **{job}**!\n\n"
            f"💵 Earnings: **${earnings:,}**"
        ),
        color=discord.Color.green()
    )

    embed.add_field(
        name="New Balance",
        value=f"${get_wallet(ctx.author.id):,}",
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command(name="daily")
async def daily(ctx):

    user_id = str(ctx.author.id)
    current_time = time.time()

    last_claim = database["daily_claims"].get(user_id, 0)

    cooldown = 24 * 60 * 60
    remaining = cooldown - (current_time - last_claim)

    if remaining > 0:

        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)

        await ctx.send(
            f"⏰ You already claimed your daily allowance!\n"
            f"Come back in **{hours}h {minutes}m**."
        )
        return

    reward = 500

    balance = get_wallet(ctx.author.id)

    set_wallet(ctx.author.id, balance + reward)

    database["daily_claims"][user_id] = current_time
    save_database()

    embed = discord.Embed(
        title="🎁 Daily Allowance",
        description=(
            f"You received your daily allowance!\n\n"
            f"💵 Bonus: **$500**\n"
            f"💰 New Balance: **${get_wallet(ctx.author.id):,}**"
        ),
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)


@bot.command(name="balance", aliases=["bal"])
async def balance(ctx, member: discord.Member = None):

    member = member or ctx.author

    cash = get_wallet(member.id)

    embed = discord.Embed(
        title="💰 Wallet Balance",
        description=f"**{member.display_name}'s Cash Stack**",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💵 Available Cash",
        value=f"**${cash:,}**",
        inline=False
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    await ctx.send(embed=embed)


@bot.command(name="gamble")
async def gamble(ctx, amount: int):

    if amount <= 0:
        await ctx.send("❌ Enter an amount greater than zero.")
        return

    balance = get_wallet(ctx.author.id)

    if amount > balance:
        await ctx.send("❌ You don't have enough money!")
        return

    if random.choice([True, False]):

        winnings = amount

        set_wallet(ctx.author.id, balance + winnings)

        await ctx.send(
            f"🎉 **YOU WON!**\n"
            f"You doubled your bet and earned **${winnings:,}**!\n"
            f"New balance: **${get_wallet(ctx.author.id):,}**"
        )

    else:

        set_wallet(ctx.author.id, balance - amount)

        await ctx.send(
            f"💀 **YOU LOST!**\n"
            f"You lost **${amount:,}**.\n"
            f"New balance: **${get_wallet(ctx.author.id):,}**"
        )


@bot.command(name="rob")
@commands.cooldown(1, 60, commands.BucketType.user)
async def rob(ctx, member: discord.Member):

    if member.bot:
        await ctx.send("❌ You cannot rob bots!")
        return

    if member.id == ctx.author.id:
        await ctx.send("❌ You cannot rob yourself!")
        return

    victim_balance = get_wallet(member.id)
    robber_balance = get_wallet(ctx.author.id)

    if victim_balance <= 100:
        await ctx.send(
            f"❌ {member.display_name} doesn't have enough money to rob!"
        )
        return

    if random.choice([True, False]):

        percentage = random.randint(20, 50)

        stolen = int(victim_balance * percentage / 100)

        set_wallet(member.id, victim_balance - stolen)
        set_wallet(ctx.author.id, robber_balance + stolen)

        await ctx.send(
            f"💰 **ROBBERY SUCCESSFUL!**\n"
            f"You stole **${stolen:,}** from {member.mention}!\n"
            f"New balance: **${get_wallet(ctx.author.id):,}**"
        )

    else:

        fine = random.randint(50, 150)
        fine = min(fine, robber_balance)

        set_wallet(ctx.author.id, robber_balance - fine)

        await ctx.send(
            f"🚨 **YOU GOT CAUGHT!**\n"
            f"You were caught trying to rob {member.mention}!\n"
            f"Fine: **${fine:,}**"
        )


# ==========================================
# ROLE SHOP SYSTEM
# ==========================================

@bot.command(name="shop")
async def shop(ctx):

    items = database["shop_items"]

    embed = discord.Embed(
        title="🛒 Server Role Shop",
        description="Purchase exclusive server roles using your wallet!",
        color=discord.Color.purple()
    )

    if not items:
        embed.description = "The shop is currently empty."

    for item_name, price in items.items():

        embed.add_field(
            name=f"🎭 {item_name}",
            value=f"Price: **${price:,}**",
            inline=False
        )

    embed.set_footer(
        text=f"Use {PREFIX}buy <item name> to purchase an item."
    )

    await ctx.send(embed=embed)


@bot.command(name="buy")
async def buy(ctx, *, item_name: str):

    guild = ctx.guild

    if guild is None:
        await ctx.send("❌ This command can only be used in a server.")
        return

    items = database["shop_items"]

    if item_name not in items:
        await ctx.send("❌ That item doesn't exist in the shop!")
        return

    price = items[item_name]

    balance = get_wallet(ctx.author.id)

    if balance < price:
        await ctx.send(
            f"❌ You need **${price - balance:,}** more to purchase this role!"
        )
        return

    role = discord.utils.get(guild.roles, name=item_name)

    try:

        if role is None:
            role = await guild.create_role(
                name=item_name,
                reason="Role purchased from the server shop."
            )

        if role >= guild.me.top_role:
            await ctx.send(
                "❌ I cannot assign this role because it is above "
                "or equal to my highest role. Move my bot role higher."
            )
            return

        if role in ctx.author.roles:
            await ctx.send("❌ You already own this role!")
            return

        await ctx.author.add_roles(
            role,
            reason="Purchased from the server shop."
        )

        set_wallet(ctx.author.id, balance - price)

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=(
                f"You purchased **{item_name}**!\n\n"
                f"💵 Cost: **${price:,}**\n"
                f"💰 Remaining Balance: **${get_wallet(ctx.author.id):,}**"
            ),
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send(
            "❌ I don't have permission to create or assign this role. "
            "Check my Manage Roles permission and role hierarchy."
        )

    except discord.HTTPException:
        await ctx.send("❌ Discord couldn't complete the role purchase.")


@bot.command(name="addshopitem")
@commands.has_permissions(administrator=True)
async def addshopitem(ctx, price: int, *, item_name: str):

    if price <= 0:
        await ctx.send("❌ The price must be greater than zero.")
        return

    if item_name in database["shop_items"]:
        await ctx.send("❌ That shop item already exists!")
        return

    database["shop_items"][item_name] = price
    save_database()

    await ctx.send(
        f"✅ Added **{item_name}** to the shop for **${price:,}**!"
    )


@bot.command(name="removeshopitem")
@commands.has_permissions(administrator=True)
async def removeshopitem(ctx, *, item_name: str):

    if item_name not in database["shop_items"]:
        await ctx.send("❌ That item doesn't exist!")
        return

    del database["shop_items"][item_name]
    save_database()

    await ctx.send(f"✅ Removed **{item_name}** from the shop!")


# ==========================================
# CUSTOM TEXT COMMAND CREATOR
# ==========================================

@bot.command(name="addcmd")
@commands.has_permissions(administrator=True)
async def addcmd(ctx, name: str, *, reply_text: str):

    name = name.lower()

    if not re.fullmatch(r"[a-z0-9_-]+", name):
        await ctx.send(
            "❌ Command names can only contain letters, numbers, "
            "underscores, and hyphens."
        )
        return

    if name in bot.all_commands:
        await ctx.send("❌ That name is already a bot command!")
        return

    database["custom_commands"][name] = reply_text
    save_database()

    await ctx.send(
        f"✅ Custom command **!{name}** has been created!"
    )


@bot.command(name="delcmd")
@commands.has_permissions(administrator=True)
async def delcmd(ctx, *, name: str):

    name = name.lower()

    if name not in database["custom_commands"]:
        await ctx.send("❌ That custom command doesn't exist!")
        return

    del database["custom_commands"][name]
    save_database()

    await ctx.send(f"✅ Deleted custom command **!{name}**!")


@bot.command(name="allcmds")
async def allcmds(ctx):

    custom_commands = database["custom_commands"]

    embed = discord.Embed(
        title="📜 Custom Server Commands",
        description="All currently active custom text triggers.",
        color=discord.Color.blurple()
    )

    if not custom_commands:
        embed.description = "There are currently no custom commands."

    for name, reply in custom_commands.items():

        embed.add_field(
            name=f"!{name}",
            value=reply[:500],
            inline=False
        )

    await ctx.send(embed=embed)


# ==========================================
# MODERATION COMMANDS
# ==========================================

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 100):

    if amount <= 0:
        await ctx.send("❌ Enter a number greater than zero.")
        return

    if amount > 1000:
        await ctx.send("❌ You cannot purge more than 1000 messages.")
        return

    deleted = await ctx.channel.purge(
        limit=amount + 1
    )

    confirmation = await ctx.send(
        f"🧹 Successfully deleted **{len(deleted) - 1}** messages!"
    )

    await confirmation.delete(delay=5)


# ==========================================
# LEVELING COMMANDS
# ==========================================

@bot.command(name="rank")
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author

    user_data = get_xp(member.id)

    current_xp = user_data["xp"]
    current_level = user_data["level"]

    required_xp = current_level * 100

    embed = discord.Embed(
        title="🏆 Level Ranking",
        description=f"**{member.display_name}**",
        color=discord.Color.gold()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name="⭐ Level",
        value=f"**{current_level}**",
        inline=True
    )

    embed.add_field(
        name="✨ XP",
        value=f"**{current_xp}/{required_xp}**",
        inline=True
    )

    embed.add_field(
        name="📊 Progress",
        value=f"**{int(current_xp / required_xp * 100)}%**",
        inline=False
    )

    await ctx.send(embed=embed)


# ==========================================
# PRIVATE TICKET SYSTEM
# ==========================================

@bot.command(name="ticket")
@commands.cooldown(1, 30, commands.BucketType.user)
async def ticket(ctx):

    guild = ctx.guild

    if guild is None:
        await ctx.send("❌ Tickets can only be created in a server.")
        return

    existing_ticket = discord.utils.get(
        guild.text_channels,
        name=f"ticket-{ctx.author.id}"
    )

    if existing_ticket:
        await ctx.send(
            f"❌ You already have an open ticket: {existing_ticket.mention}"
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        ),
        ctx.author: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )
    }

    try:

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{ctx.author.id}",
            overwrites=overwrites,
            topic=f"Ticket owner: {ctx.author.id}",
            reason="New support ticket."
        )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                f"Welcome {ctx.author.mention}!\n\n"
                "Please describe your issue and a staff member "
                "will assist you.\n\n"
                "Use **!close** to close this ticket."
            ),
            color=discord.Color.blue()
        )

        await ticket_channel.send(
            content=ctx.author.mention,
            embed=embed
        )

        await ctx.send(
            f"✅ Your private ticket has been created: "
            f"{ticket_channel.mention}"
        )

    except discord.Forbidden:
        await ctx.send(
            "❌ I don't have permission to create private channels."
        )

    except discord.HTTPException:
        await ctx.send("❌ Discord couldn't create your ticket.")


@bot.command(name="close")
async def close(ctx):

    if ctx.guild is None:
        await ctx.send("❌ This command can only be used in a server.")
        return

    channel = ctx.channel

    if not channel.name.startswith("ticket-"):
        await ctx.send("❌ This command can only be used inside a ticket.")
        return

    ticket_owner = None

    if channel.topic:
        match = re.search(r"Ticket owner: (\d+)", channel.topic)

        if match:
            ticket_owner = int(match.group(1))

    is_owner = ticket_owner == ctx.author.id

    is_staff = ctx.author.guild_permissions.manage_channels

    if not is_owner and not is_staff:
        await ctx.send(
            "❌ Only the ticket owner or a staff member "
            "with Manage Channels can close this ticket."
        )
        return

    try:

        await ctx.send(
            "🔒 This ticket will be closed in 5 seconds."
        )

        await channel.delete(
            delay=5,
            reason=f"Ticket closed by {ctx.author}."
        )

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete this channel.")

    except discord.HTTPException:
        await ctx.send("❌ Discord couldn't close this ticket.")


# ==========================================
# ERROR HANDLING
# ==========================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandOnCooldown):

        await ctx.send(
            f"⏰ Slow down! Try again in **{error.retry_after:.1f} seconds**."
        )

    elif isinstance(error, commands.MissingPermissions):

        await ctx.send(
            "❌ You don't have permission to use this command."
        )

    elif isinstance(error, commands.BotMissingPermissions):

        await ctx.send(
            "❌ I'm missing the permissions needed to do that."
        )

    elif isinstance(error, commands.MissingRequiredArgument):

        await ctx.send(
            f"❌ Missing an argument: **{error.param.name}**.\n"
            f"Check the command syntax."
        )

    elif isinstance(error, commands.BadArgument):

        await ctx.send(
            "❌ Invalid argument. Please check what you entered."
        )

    elif isinstance(error, commands.CommandNotFound):

        pass

    else:

        print(f"Command error: {error}")

        await ctx.send(
            "❌ An unexpected error occurred while running that command."
        )


# ==========================================
# START BOT
# ==========================================

bot.run('MTU1NjM2MTQzMDg1OTY1MzIzMA.GSl_4F._3yMjx6ZvcG70Xkx-kA1Tu_zpiRxBWTMM9m-S0')
