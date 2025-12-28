import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import random
from datetime import datetime

# --- CONFIGURATION ---
GUILD_ID = 1423235954252185622
AI_CATEGORY_ID = 1454840107751178398
OWNER_ROLE_ID = 1438892578580730027
VERIFIED_ROLE_ID = 1439203352406921377
STAFF_CHAT_CHANNEL_ID = 1439944303261647010
MAIN_GUIDE_CHANNEL_ID = 1439218639847952448
# The role to ping when user clicks "Middleman"
MIDDLEMAN_ROLE_ID = 1438896022590984295 
TICKET_DATA_FILE = "ticket_data.json"

STAFF_ROLES = [
    1438892578580730027, 1438894594254311504, 1438895119360065666,
    1444915199529324624, 1444914892309139529, 1441060547700457584,
    1438895276419977329, 1438895696936828928, 1438895819125297274,
    1438895916596592650, 1438896022590984295
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Maps to link Staff Channels <-> User Channels
relay_map = {}
reverse_relay_map = {}

# --- DATA HANDLING ---
def load_ticket_data():
    if os.path.exists(TICKET_DATA_FILE):
        try:
            with open(TICKET_DATA_FILE, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_ticket_data(data):
    try:
        with open(TICKET_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e: print(f"Save Error: {e}")

async def close_ticket_logic(staff_channel, user_channel_id):
    """Deletes both channels and updates JSON"""
    if user_channel_id:
        chan = bot.get_channel(user_channel_id)
        if chan: 
            try: await chan.delete()
            except: pass
    
    data = load_ticket_data()
    found_uid = None
    if "user_middleman_tickets" in data:
        for uid, t in data["user_middleman_tickets"].items():
            if t["channel_id"] == user_channel_id:
                found_uid = uid
                break
        if found_uid:
            del data["user_middleman_tickets"][found_uid]
            save_ticket_data(data)

    if staff_channel:
        try: await staff_channel.delete()
        except: pass

# --- VIEWS ---

class StaffClaimView(discord.ui.View):
    """Persistent view for Staff to claim the AI ticket"""
    def __init__(self, staff_channel):
        super().__init__(timeout=None)
        self.staff_channel = staff_channel

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="staff_claim_btn")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Check Permissions
        if not any(r.id in STAFF_ROLES for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        
        # 2. Lock Channel to Claimer
        overwrites = interaction.channel.overwrites
        # Allow claimer
        overwrites[interaction.user] = discord.PermissionOverwrite(send_messages=True, view_channel=True)
        # Deny other staff (except Owner)
        for rid in STAFF_ROLES:
            role = interaction.guild.get_role(rid)
            if role and rid != OWNER_ROLE_ID:
                overwrites[role] = discord.PermissionOverwrite(send_messages=False, view_channel=True)
        
        await interaction.channel.edit(overwrites=overwrites)
        
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"✅ **Ticket Claimed!** You are now connected to the user.\nType here to message them.")

class ChoiceView(discord.ui.View):
    """The AI vs Middleman Selection"""
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ You did not create this ticket.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="AI", style=discord.ButtonStyle.blurple, custom_id="ai_choice")
    async def ai_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AIModal(self.owner_id))

    @discord.ui.button(label="Middleman", style=discord.ButtonStyle.gray, custom_id="mm_choice")
    async def mm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Release Lock in JSON
        data = load_ticket_data()
        found = False
        for uid, t in data.get("user_middleman_tickets", {}).items():
            if t["channel_id"] == interaction.channel.id:
                t["claimer"] = None # Unlock
                save_ticket_data(data)
                found = True
                break
        
        # 2. Delete the Embed
        await interaction.message.delete()
        
        # 3. Ping Middleman
        if found:
            await interaction.channel.send(f"🔔 <@&{MIDDLEMAN_ROLE_ID}> **Middleman Requested!**\nA staff member can now claim this ticket above.")
        else:
            await interaction.response.send_message("❌ Error: Ticket not found in DB.", ephemeral=True)

class AIModal(discord.ui.Modal, title="AI Trade Application"):
    trade_info = discord.ui.TextInput(label="Trade Details", placeholder="Example: My Kitsune for 2 Dragons", style=discord.TextStyle.paragraph)
    users = discord.ui.TextInput(label="Add User (Username)", placeholder="friend_name")

    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        # --- 1. Add the Second User ---
        target_name = self.users.value.strip()
        target_member = None
        # Try to find user by name
        target_member = discord.utils.get(guild.members, name=target_name)
        
        if target_member:
            await interaction.channel.set_permissions(target_member, view_channel=True, send_messages=True)
            added_text = f"{target_member.mention} has been added to the ticket."
        else:
            added_text = f"⚠️ Could not find user '{target_name}'. You can add them manually."

        # --- 2. Create Staff Relay Channel ---
        category = guild.get_channel(AI_CATEGORY_ID)
        # Unhide category
        await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)})

        rand_id = str(random.randint(1, 9999)).zfill(4)
        chan_name = f"ai-{interaction.user.name}-{rand_id}"
        
        # Permissions: Staff SEE but CANNOT TYPE
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for rid in STAFF_ROLES:
            role = guild.get_role(rid)
            if role: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False)

        staff_chan = await category.create_text_channel(name=chan_name, overwrites=overwrites)
        relay_map[staff_chan.id] = interaction.channel.id
        reverse_relay_map[interaction.channel.id] = staff_chan.id

        # --- 3. Send Controls to Staff ---
        view = StaffClaimView(staff_chan)
        await staff_chan.send(
            f"**🤖 New AI Ticket**\n"
            f"**User:** {interaction.user.mention}\n"
            f"**Trade:** {self.trade_info.value}\n"
            f"**Other User:** {self.users.value}\n"
            f"**Channel:** {interaction.channel.mention}", 
            view=view
        )

        # --- 4. Send Poll to User Channel ---
        embed = discord.Embed(title="Confirm Trade", description=f"**Trade:** {self.trade_info.value}\n**Participants:** {interaction.user.mention} & {self.users.value}\n\n{added_text}\n\nDo you both agree?", color=discord.Color.blue())
        await interaction.channel.send(embed=embed, view=TradePollView())
        await interaction.followup.send("Application Submitted!", ephemeral=True)

class TradePollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.votes = {}

    async def check_votes(self, interaction):
        if len(self.votes) < 2: return # Wait for 2 people
        
        if all(self.votes.values()):
            await interaction.channel.send("✅ **Both Accepted!** Waiting for Middleman to guide you...")
        elif not any(self.votes.values()):
            await interaction.channel.send("❌ Both declined. Closing ticket...")
            await asyncio.sleep(3)
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            await close_ticket_logic(staff_chan, interaction.channel.id)
        else:
            await interaction.channel.send("⚠️ Disagreement. Please discuss.")

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = True
        await interaction.response.send_message(f"{interaction.user.mention} Accepted.", ephemeral=False)
        await self.check_votes(interaction)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = False
        await interaction.response.send_message(f"{interaction.user.mention} Declined.", ephemeral=False)
        await self.check_votes(interaction)

# --- EVENTS ---

@tasks.loop(seconds=4)
async def monitor_tickets():
    """Backup: Finds open tickets that are unclaimed and locks them."""
    data = load_ticket_data()
    changed = False
    
    for uid, t in data.get("user_middleman_tickets", {}).items():
        # If ticket is open (has channel_id) but claimer is None
        if t.get("channel_id") and t.get("claimer") is None:
            # Check if we already processed this in memory (prevents double post)
            if t.get("ai_locked"): continue 
            
            chan = bot.get_channel(t["channel_id"])
            if chan:
                # Lock it
                t["claimer"] = bot.user.id
                t["ai_locked"] = True # New flag to track if we sent the embed
                changed = True
                
                # Identify owner
                owner_id = int(t.get("user_id", 0))
                
                # Send Embed
                embed = discord.Embed(title="Trade Assistant", description="Do you want AI to handle your trade or our middleman?", color=discord.Color.gold())
                await chan.send(embed=embed, view=ChoiceView(owner_id))
                print(f"🔒 Locked ticket {chan.name}")

    if changed:
        save_ticket_data(data)

@bot.event
async def on_ready():
    print(f"✅ Relay Bot Online: {bot.user}")
    if not monitor_tickets.is_running():
        monitor_tickets.start()

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id: return

    # 1. INSTANT CLAIM (Triggered by Bot.py's Embed)
    if message.author.bot and message.embeds:
        if "Middleman Ticket" in (message.embeds[0].title or ""):
            # Fast Hijack
            data = load_ticket_data()
            for uid, t in data.get("user_middleman_tickets", {}).items():
                if t["channel_id"] == message.channel.id:
                    # Double check we didn't already lock it
                    if t.get("claimer") == bot.user.id: return 

                    t["claimer"] = bot.user.id
                    t["ai_locked"] = True
                    save_ticket_data(data)
                    
                    owner_id = int(t.get("user_id", 0))
                    embed = discord.Embed(title="Trade Assistant", description="Do you want AI to handle your trade or our middleman?", color=discord.Color.gold())
                    await message.channel.send(embed=embed, view=ChoiceView(owner_id))
                    print(f"⚡ Instant Lock: {message.channel.name}")
                    break

    # 2. RELAY & COMMANDS
    if message.channel.id in relay_map:
        user_chan = bot.get_channel(relay_map[message.channel.id])
        if not user_chan: return

        if message.content.lower() == "!close":
            if any(r.id in STAFF_ROLES for r in message.author.roles):
                await message.channel.send("Closing...")
                await asyncio.sleep(2)
                await close_ticket_logic(message.channel, user_chan.id)
            return

        # Simple Image Commands
        if message.content == "!middleman1" and os.path.exists("assets/middleman_process.webp"):
            await user_chan.send(file=discord.File("assets/middleman_process.webp"))
        elif message.content == "!middleman2" and os.path.exists("assets/middleman_info.jpg"):
            await user_chan.send(file=discord.File("assets/middleman_info.jpg"))
        else:
            # Text Relay
            embed = discord.Embed(description=message.content, color=discord.Color.blue())
            embed.set_author(name="Middleman", icon_url=message.author.display_avatar.url)
            await user_chan.send(embed=embed)

    await bot.process_commands(message)

# RUN
if os.getenv("AI_BOT_TOKEN"):
    bot.run(os.getenv("AI_BOT_TOKEN"))
else:
    print("❌ AI_BOT_TOKEN missing!")
