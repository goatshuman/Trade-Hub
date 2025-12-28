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

# --- HELPER FUNCTIONS ---
def load_ticket_data():
    if os.path.exists(TICKET_DATA_FILE):
        with open(TICKET_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_ticket_data(data):
    with open(TICKET_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

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
            try:
                await user_chan.delete()
            except:
                pass
    
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
    try:
        await staff_channel.delete()
    except:
        pass
    
    # 4. Check Visibility
    if staff_channel.guild:
        await check_category_visibility(staff_channel.guild)

# --- VERIFY LOGIC ---
async def update_timer(view, channel, timer_msg_id, duration=60, is_final=False):
    for remaining in range(duration, -1, -1):
        if view.user_responded: return
        try:
            timer_msg = await channel.fetch_message(timer_msg_id)
            timer_title = "⏱️ Final Verification Timer" if is_final else "⏱️ Verification Timer"
            color = discord.Color.blue() if remaining > 10 else discord.Color.red()
            await timer_msg.edit(embed=discord.Embed(title=timer_title, description=f"**Time Remaining: {remaining} seconds**", color=color))
        except: break
        if remaining > 0: await asyncio.sleep(1)
    
    if not view.user_responded:
        view.is_timed_out = True
        try:
            timer_msg = await channel.fetch_message(timer_msg_id)
            await timer_msg.delete()
        except: pass

class HitView(discord.ui.View):
    def __init__(self, target_user, message_id=None, timer_message_id=None):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.message_id = message_id
        self.timer_message_id = timer_message_id
        self.user_responded = False
        self.is_timed_out = False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id: return await interaction.response.send_message("❌ Not for you!", ephemeral=True)
        if self.is_timed_out: return await interaction.response.send_message("❌ Too late!", ephemeral=True)
        
        self.user_responded = True
        verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if verified_role: await self.target_user.add_roles(verified_role)
        
        for cid in [STAFF_CHAT_CHANNEL_ID, MAIN_GUIDE_CHANNEL_ID]:
            chan = interaction.guild.get_channel(cid)
            if chan: await chan.set_permissions(self.target_user, view_channel=True)

        await interaction.response.send_message(embed=discord.Embed(title="✅ Verification Successful", description=f"{self.target_user.mention} verified!", color=discord.Color.green()))
        
        try:
            hitter_embed = discord.Embed(title="🎯 You're a hitter now", description="Welcome to the team.", color=discord.Color.purple())
            hitter_embed.add_field(name="Instructions", value="Go advertise in other servers. Bring people here for MM services.")
            await self.target_user.send(embed=hitter_embed)
        except: pass
        
        try:
            if self.message_id: (await interaction.channel.fetch_message(self.message_id)).delete()
            if self.timer_message_id: (await interaction.channel.fetch_message(self.timer_message_id)).delete()
        except: pass

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id: return
        self.user_responded = True
        await interaction.response.send_message("❌ Declined.", ephemeral=True)
        # Trigger close logic if needed, or wait for staff !close

# --- TRADE LOGIC ---
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
            # Find staff channel ID to close both
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            if staff_chan:
                await close_ticket_logic(staff_chan, interaction.channel.id)
            else:
                await interaction.channel.delete() # Fallback
        else:
            await interaction.channel.send("⚠️ One accepted, one declined. Please decide whether you guys trading or not you can open a middleman ticket any time you want.")
            await asyncio.sleep(5)
            # Find staff channel ID to close both
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            if staff_chan:
                await close_ticket_logic(staff_chan, interaction.channel.id)
            else:
                await interaction.channel.delete()

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

class AIModal(discord.ui.Modal, title="AI Trade Application"):
    trade_info = discord.ui.TextInput(label="Trade Details", placeholder="I am giving...", style=discord.TextStyle.paragraph)
    users = discord.ui.TextInput(label="Users Involved", placeholder="Usernames...")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(AI_CATEGORY_ID)
        
        # Unhide category
        await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)})

        rand_id = str(random.randint(1, 9999)).zfill(4)
        chan_name = f"ai-{interaction.user.name}-{rand_id}"
        
        # Staff see only (cannot type until claimed), Owner sees and types
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

        view = discord.ui.View(timeout=None)
        claim_btn = discord.ui.Button(label="Claim Ticket", style=discord.ButtonStyle.green)
        
        async def claim_callback(itn):
            if not any(r.id in STAFF_ROLES for r in itn.user.roles): return
            # Unlock for claimer, lock for others
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

@bot.event
async def on_ready():
    print(f"✅ Relay Bot Online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id: return

    # 1. INSTANT CLAIM LOGIC (Watch for Main Bot's Embed)
    if message.author.bot and message.embeds:
        if "Middleman Ticket" in (message.embeds[0].title or ""):
            data = load_ticket_data()
            for uid, tinfo in data.get("user_middleman_tickets", {}).items():
                if tinfo["channel_id"] == message.channel.id:
                    tinfo["claimer"] = bot.user.id # Bot claims it instantly
                    save_ticket_data(data)
                    embed = discord.Embed(title="Trade Assistant", description="Do you want AI to handle your trade or our middleman?", color=discord.Color.gold())
                    await message.channel.send(embed=embed, view=ChoiceView())
                    break

    # 2. RELAY & COMMANDS LOGIC
    if message.channel.id in relay_map:
        user_chan_id = relay_map[message.channel.id]
        user_chan = bot.get_channel(user_chan_id)
        
        # !close Command
        if message.content.lower() == "!close":
            if not any(r.id in STAFF_ROLES for r in message.author.roles):
                return await message.channel.send("❌ Not authorized.")
            
            await message.channel.send("⚠️ Closing ticket in 3 seconds...")
            await asyncio.sleep(3)
            await close_ticket_logic(message.channel, user_chan_id)
            return

        if not user_chan: return

        content = message.content.lower()
        
        if content == "!middleman1":
            if os.path.exists("assets/middleman_process.webp"):
                await user_chan.send(file=discord.File("assets/middleman_process.webp"))
            else: await message.channel.send("❌ Asset missing: assets/middleman_process.webp")
        
        elif content == "!middleman2":
            if os.path.exists("assets/middleman_info.jpg"):
                await user_chan.send(file=discord.File("assets/middleman_info.jpg"))
            else: await message.channel.send("❌ Asset missing: assets/middleman_info.jpg")

        elif content.startswith("!verify"):
            try:
                target = message.mentions[0] if message.mentions else None
                if target:
                    embed = discord.Embed(title="Scam Notification", description=f"{target.mention}, do you want to accept this opportunity?", color=discord.Color.green())
                    timer_embed = discord.Embed(title="⏱️ Verification Timer", description="**Time Remaining: 60 seconds**", color=discord.Color.blue())
                    view = HitView(target)
                    msg = await user_chan.send(embed=embed, view=view)
                    view.message_id = msg.id
                    timer_msg = await user_chan.send(embed=timer_embed)
                    view.timer_message_id = timer_msg.id
                    asyncio.create_task(update_timer(view, user_chan, timer_msg.id))
                    await message.channel.send(f"✅ Verification sent to {target.name}")
                else: await message.channel.send("❌ Please mention the user: `!verify @user`")
            except Exception as e: await message.channel.send(f"❌ Error: {e}")

        else:
            # Relay text
            embed = discord.Embed(description=message.content, color=discord.Color.blue())
            embed.set_author(name="Middleman", icon_url=message.author.display_avatar.url)
            await user_chan.send(embed=embed)

    await bot.process_commands(message)

# RUN WITH ENV VARIABLE
if os.getenv("AI_BOT_TOKEN"):
    bot.run(os.getenv("AI_BOT_TOKEN"))
else:
    print("❌ Error: AI_BOT_TOKEN not found in Environment Variables")