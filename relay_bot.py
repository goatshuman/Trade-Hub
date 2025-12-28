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
TICKET_DATA_FILE = "ticket_data.json"

# Staff Roles Allowed to Claim and Close
STAFF_ROLES = [
    1438892578580730027, 1438894594254311504, 1438895119360065666,
    1444915199529324624, 1444914892309139529, 1441060547700457584,
    1438895276419977329, 1438895696936828928, 1438895819125297274,
    1438895916596592650, 1438896022590984295
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Map: Staff_Channel_ID -> User_Ticket_ID
relay_map = {}
# Map: User_Ticket_ID -> Staff_Channel_ID
reverse_relay_map = {}
# Track processed tickets to avoid double-posting
processed_tickets = set()

# --- HELPER FUNCTIONS ---
def load_ticket_data():
    if os.path.exists(TICKET_DATA_FILE):
        try:
            with open(TICKET_DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ JSON Decode Error (File might be busy)")
            return {}
    return {}

def save_ticket_data(data):
    try:
        with open(TICKET_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")

async def check_category_visibility(guild):
    category = guild.get_channel(AI_CATEGORY_ID)
    if not category: return
    # Hide category if 0 channels left, Show if > 0
    await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=len(category.channels) > 0)})

async def close_ticket_logic(staff_channel, user_channel_id):
    """Deletes both channels and removes data from JSON"""
    # 1. Delete User Channel
    if user_channel_id:
        user_chan = bot.get_channel(user_channel_id)
        if user_chan:
            try: await user_chan.delete()
            except: pass
    
    # 2. Update JSON
    data = load_ticket_data()
    found_uid = None
    if "user_middleman_tickets" in data:
        for uid, tinfo in data["user_middleman_tickets"].items():
            if tinfo["channel_id"] == user_channel_id:
                found_uid = uid
                break
        if found_uid:
            del data["user_middleman_tickets"][found_uid]
            save_ticket_data(data)

    # 3. Delete Staff Channel
    try: await staff_channel.delete()
    except: pass
    
    # 4. Check Visibility
    if staff_channel.guild:
        await check_category_visibility(staff_channel.guild)

# --- VIEWS & LOGIC ---

class ChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="AI", style=discord.ButtonStyle.blurple, custom_id="ai_choice")
    async def ai_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AIModal())

    @discord.ui.button(label="Middleman", style=discord.ButtonStyle.gray, custom_id="mm_choice")
    async def mm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_ticket_data()
        found = False
        for uid, tinfo in data.get("user_middleman_tickets", {}).items():
            if tinfo["channel_id"] == interaction.channel.id:
                tinfo["claimer"] = None # Free up ticket
                save_ticket_data(data)
                found = True
                break
        
        if found:
            await interaction.response.send_message("✅ AI disabled. Waiting for human middleman to claim.", ephemeral=False)
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ Ticket not found in database.", ephemeral=True)

class AIModal(discord.ui.Modal, title="AI Trade Application"):
    trade_info = discord.ui.TextInput(label="Trade Details", placeholder="I am giving...", style=discord.TextStyle.paragraph)
    users = discord.ui.TextInput(label="Users Involved", placeholder="Usernames...")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(AI_CATEGORY_ID)
        
        if category:
            await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)})

        rand_id = str(random.randint(1, 9999)).zfill(4)
        chan_name = f"ai-{interaction.user.name}-{rand_id}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for rid in STAFF_ROLES:
            role = guild.get_role(rid)
            if role: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False)

        if category:
            staff_chan = await category.create_text_channel(name=chan_name, overwrites=overwrites)
            relay_map[staff_chan.id] = interaction.channel.id
            reverse_relay_map[interaction.channel.id] = staff_chan.id

            view = discord.ui.View(timeout=None)
            claim_btn = discord.ui.Button(label="Claim Ticket", style=discord.ButtonStyle.green)
            
            async def claim_callback(itn):
                if not any(r.id in STAFF_ROLES for r in itn.user.roles): return
                await staff_chan.set_permissions(itn.user, send_messages=True)
                for rid in STAFF_ROLES:
                    role = guild.get_role(rid)
                    if role and rid != OWNER_ROLE_ID:
                        await staff_chan.set_permissions(role, send_messages=False)
                await itn.response.send_message(f"✅ Claimed by {itn.user.mention}")
                claim_btn.disabled = True
                await itn.message.edit(view=view)

            claim_btn.callback = claim_callback
            view.add_item(claim_btn)
            
            await staff_chan.send(f"**New AI Ticket**\n**Trade:** {self.trade_info.value}\n**Users:** {self.users.value}\n**User Channel:** {interaction.channel.mention}", view=view)
            
            embed = discord.Embed(title="Confirm Trade", description=f"**Trade:** {self.trade_info.value}\n**Users:** {self.users.value}\n\nDo you guys want to trade?", color=discord.Color.blue())
            await interaction.channel.send(embed=embed, view=TradePollView())
            await interaction.followup.send("Application sent!", ephemeral=True)
        else:
             await interaction.followup.send("❌ AI Category not found. Contact Admin.", ephemeral=True)

class TradePollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.votes = {}

    async def check_votes(self, interaction):
        if len(self.votes) < 2: return
        
        if all(self.votes.values()):
            await interaction.channel.send("✅ **Trade Accepted!** Proceeding...")
        elif not any(self.votes.values()):
            await interaction.channel.send("❌ As you both declined I am closing this ticket you can open middleman ticket any time you want.")
            await asyncio.sleep(5)
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            if staff_chan: await close_ticket_logic(staff_chan, interaction.channel.id)
            else: await interaction.channel.delete()
        else:
            await interaction.channel.send("⚠️ One accepted, one declined. Please decide whether you guys trading or not you can open a middleman ticket any time you want.")
            await asyncio.sleep(5)
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            if staff_chan: await close_ticket_logic(staff_chan, interaction.channel.id)
            else: await interaction.channel.delete()

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

# --- MAIN LOOPS & EVENTS ---

@tasks.loop(seconds=5)
async def backup_claim_loop():
    """Backup loop: Checks for tickets that the on_message event might have missed."""
    data = load_ticket_data()
    for uid, tinfo in data.get("user_middleman_tickets", {}).items():
        chan_id = tinfo.get("channel_id")
        
        # If ticket exists, has NO claimer, and we haven't processed it yet
        if chan_id and tinfo.get("claimer") is None and chan_id not in processed_tickets:
            channel = bot.get_channel(chan_id)
            if channel:
                print(f"🔄 Backup Loop: Found unclaimed ticket {chan_id}. Hijacking...")
                
                # Hijack JSON
                tinfo["claimer"] = bot.user.id
                save_ticket_data(data)
                
                # Send Embed
                processed_tickets.add(chan_id)
                embed = discord.Embed(title="Trade Assistant", description="Do you want AI to handle your trade or our middleman?", color=discord.Color.gold())
                await channel.send(embed=embed, view=ChoiceView())

@bot.event
async def on_ready():
    print(f"✅ Relay Bot Online: {bot.user}")
    print(f"✅ Monitoring Category: {AI_CATEGORY_ID}")
    if not backup_claim_loop.is_running():
        backup_claim_loop.start()

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id: return

    # 1. INSTANT CLAIM LOGIC (Watch for Main Bot's Embed)
    if message.author.bot and message.embeds:
        if "Middleman Ticket" in (message.embeds[0].title or ""):
            print(f"👀 Saw New Ticket: {message.channel.name} ({message.channel.id})")
            
            # Retry logic for JSON race condition
            for attempt in range(3):
                data = load_ticket_data()
                found = False
                for uid, tinfo in data.get("user_middleman_tickets", {}).items():
                    if tinfo["channel_id"] == message.channel.id:
                        tinfo["claimer"] = bot.user.id # Bot claims it instantly
                        save_ticket_data(data)
                        processed_tickets.add(message.channel.id)
                        
                        embed = discord.Embed(title="Trade Assistant", description="Do you want AI to handle your trade or our middleman?", color=discord.Color.gold())
                        await message.channel.send(embed=embed, view=ChoiceView())
                        print("✅ Instantly claimed ticket!")
                        found = True
                        break
                
                if found: break
                print(f"⚠️ JSON not ready yet, retrying {attempt+1}/3...")
                await asyncio.sleep(1)

    # 2. RELAY & COMMANDS LOGIC
    if message.channel.id in relay_map:
        user_chan_id = relay_map[message.channel.id]
        user_chan = bot.get_channel(user_chan_id)
        
        if message.content.lower() == "!close":
            if any(r.id in STAFF_ROLES for r in message.author.roles):
                await message.channel.send("⚠️ Closing ticket...")
                await asyncio.sleep(2)
                await close_ticket_logic(message.channel, user_chan_id)
            return

        if user_chan:
            content = message.content.lower()
            if content == "!middleman1":
                if os.path.exists("assets/middleman_process.webp"): await user_chan.send(file=discord.File("assets/middleman_process.webp"))
            elif content == "!middleman2":
                if os.path.exists("assets/middleman_info.jpg"): await user_chan.send(file=discord.File("assets/middleman_info.jpg"))
            elif content.startswith("!verify"):
                # Simplified Verify trigger (assumes mention)
                target = message.mentions[0] if message.mentions else None
                if target: await message.channel.send(f"✅ Verification logic triggered for {target.name}") # Placeholder for full logic
            else:
                embed = discord.Embed(description=message.content, color=discord.Color.blue())
                embed.set_author(name="Middleman", icon_url=message.author.display_avatar.url)
                await user_chan.send(embed=embed)

    await bot.process_commands(message)

# RUN WITH ENV VARIABLE
if os.getenv("AI_BOT_TOKEN"):
    bot.run(os.getenv("AI_BOT_TOKEN"))
else:
    print("❌ Error: AI_BOT_TOKEN not found")
