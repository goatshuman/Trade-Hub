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
MIDDLEMAN_ROLE_ID = 1438896022590984295  # Role to ping when user selects "Middleman"
TICKET_DATA_FILE = "ticket_data.json"

# Staff who can see the relay channel
STAFF_ROLES = [
    1438892578580730027, 1438894594254311504, 1438895119360065666,
    1444915199529324624, 1444914892309139529, 1441060547700457584,
    1438895276419977329, 1438895696936828928, 1438895819125297274,
    1438895916596592650, 1438896022590984295
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Relay Maps
relay_map = {}
reverse_relay_map = {}
processed_tickets = set()

# --- DATA HELPERS ---
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
    except: pass

async def close_ticket_logic(staff_channel, user_channel_id):
    """Deletes both channels and cleans JSON"""
    if user_channel_id:
        c = bot.get_channel(user_channel_id)
        if c: 
            try: await c.delete()
            except: pass
    
    data = load_ticket_data()
    found = None
    for uid, t in data.get("user_middleman_tickets", {}).items():
        if t["channel_id"] == user_channel_id:
            found = uid
            break
    if found:
        del data["user_middleman_tickets"][found]
        save_ticket_data(data)

    if staff_channel:
        try: await staff_channel.delete()
        except: pass

# --- VIEWS ---

class StaffClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim AI Ticket", style=discord.ButtonStyle.green, custom_id="ai_staff_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Lock relay channel to this staff member
        await interaction.channel.set_permissions(interaction.user, send_messages=True)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}. You can now type here to talk to the user.")
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.message.edit(view=self)

class TradePollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.votes = {}

    async def check_votes(self, interaction):
        if len(self.votes) < 2: return
        if all(self.votes.values()):
            await interaction.channel.send("✅ **Both Accepted!** A staff member will guide you shortly.")
        elif not any(self.votes.values()):
            await interaction.channel.send("❌ Both declined. Closing ticket...")
            await asyncio.sleep(3)
            # Close logic
            s_id = reverse_relay_map.get(interaction.channel.id)
            s_chan = interaction.guild.get_channel(s_id) if s_id else None
            await close_ticket_logic(s_chan, interaction.channel.id)
        else:
            await interaction.channel.send("⚠️ One accepted, one declined. Please discuss.")

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="poll_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = True
        await interaction.response.send_message(f"{interaction.user.mention} Accepted.", ephemeral=False)
        await self.check_votes(interaction)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="poll_decline")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = False
        await interaction.response.send_message(f"{interaction.user.mention} Declined.", ephemeral=False)
        await self.check_votes(interaction)

class AIModal(discord.ui.Modal, title="Trade Details"):
    trade_info = discord.ui.TextInput(label="What is the trade?", style=discord.TextStyle.paragraph)
    other_user = discord.ui.TextInput(label="Who are you trading with? (Username)", placeholder="username")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        # 1. Find and Add User
        target_name = self.other_user.value.strip()
        target = discord.utils.get(guild.members, name=target_name)
        
        added_msg = ""
        if target:
            await interaction.channel.set_permissions(target, view_channel=True, send_messages=True)
            added_msg = f"\n✅ Added {target.mention} to the ticket."
        else:
            added_msg = f"\n⚠️ Could not find user '{target_name}'. Please add them manually."

        # 2. Create Relay Channel
        cat = guild.get_channel(AI_CATEGORY_ID)
        await cat.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)})
        
        c_name = f"ai-{interaction.user.name}-{random.randint(1000,9999)}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for rid in STAFF_ROLES:
            r = guild.get_role(rid)
            if r: overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False)
            
        staff_chan = await cat.create_text_channel(name=c_name, overwrites=overwrites)
        relay_map[staff_chan.id] = interaction.channel.id
        reverse_relay_map[interaction.channel.id] = staff_chan.id
        
        # 3. Send Staff Controls
        view = StaffClaimView()
        await staff_chan.send(f"**New AI Ticket**\n**User:** {interaction.user.mention}\n**Trade:** {self.trade_info.value}\n**Partner:** {self.other_user.value}\n**Link:** {interaction.channel.mention}", view=view)

        # 4. Send Poll to User
        embed = discord.Embed(title="Confirm Trade", description=f"**Trade:** {self.trade_info.value}\n**Partner:** {self.other_user.value}{added_msg}", color=discord.Color.blue())
        await interaction.channel.send(embed=embed, view=TradePollView())
        await interaction.followup.send("Application sent!", ephemeral=True)

class ChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="AI", style=discord.ButtonStyle.blurple, custom_id="btn_ai")
    async def ai(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AIModal())

    @discord.ui.button(label="Middleman", style=discord.ButtonStyle.gray, custom_id="btn_mm")
    async def mm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Unlock JSON
        data = load_ticket_data()
        found = False
        for uid, t in data.get("user_middleman_tickets", {}).items():
            if t["channel_id"] == interaction.channel.id:
                t["claimer"] = None # Unlock
                t["ai_locked"] = False
                save_ticket_data(data)
                found = True
                break
        
        await interaction.message.delete()
        if found:
            await interaction.channel.send(f"🔔 <@&{MIDDLEMAN_ROLE_ID}> **Middleman Requested!** A staff member will be with you shortly.")
        else:
            await interaction.response.send_message("❌ Error: Ticket not found.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Relay Bot Online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id: return

    # INSTANT CLAIM
    if message.author.bot and message.embeds:
        if "Middleman Ticket" in (message.embeds[0].title or ""):
            data = load_ticket_data()
            for uid, t in data.get("user_middleman_tickets", {}).items():
                if t["channel_id"] == message.channel.id:
                    if t.get("ai_locked"): return
                    
                    t["claimer"] = bot.user.id
                    t["ai_locked"] = True
                    save_ticket_data(data)
                    
                    embed = discord.Embed(title="Trade Assistant", description="Do you want AI to handle your trade or our middleman?", color=discord.Color.gold())
                    await message.channel.send(embed=embed, view=ChoiceView())
                    break

    # RELAY LOGIC
    if message.channel.id in relay_map:
        user_chan = bot.get_channel(relay_map[message.channel.id])
        if not user_chan: return
        
        if message.content == "!close":
            await close_ticket_logic(message.channel, user_chan.id)
            return

        # Simple commands or relay
        if message.content == "!middleman1":
            if os.path.exists("assets/middleman_process.webp"): await user_chan.send(file=discord.File("assets/middleman_process.webp"))
        elif message.content == "!middleman2":
            if os.path.exists("assets/middleman_info.jpg"): await user_chan.send(file=discord.File("assets/middleman_info.jpg"))
        else:
            embed = discord.Embed(description=message.content, color=discord.Color.blue())
            embed.set_author(name="Middleman", icon_url=message.author.display_avatar.url)
            await user_chan.send(embed=embed)

if os.getenv("AI_BOT_TOKEN"):
    bot.run(os.getenv("AI_BOT_TOKEN"))
