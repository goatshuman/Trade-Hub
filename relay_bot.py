import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import io
import random
from datetime import datetime
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
GUILD_ID = 1423235954252185622
AI_CATEGORY_ID = 1454840107751178398
OWNER_ROLE_ID = 1438892578580730027
VERIFIED_ROLE_ID = 1439203352406921377
STAFF_CHAT_CHANNEL_ID = 1439944303261647010
MAIN_GUIDE_CHANNEL_ID = 1439218639847952448
MIDDLEMAN_ROLE_ID = 1438896022590984295
REQUEST_CHANNEL_ID = 1438899065952927917 
TRANSCRIPT_CHANNEL_ID = 1439211113420951643
TICKET_DATA_FILE = "ticket_data.json"
EMBED_COLOR = 0xFF00FF # Magenta

# Staff Roles
STAFF_ROLES = [
    1438892578580730027, 1438894594254311504, 1438895119360065666,
    1444915199529324624, 1444914892309139529, 1441060547700457584,
    1438895276419977329, 1438895696936828928, 1438895819125297274,
    1438895916596592650, 1438896022590984295
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Maps
relay_map = {} 
reverse_relay_map = {}
message_link = {}

# --- WEB SERVER FOR RENDER (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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

async def create_transcript(channel, opener_id, claimer_id, closer_id):
    if not channel: return
    transcript_content = f"# Ticket Transcript: {channel.name}\n"
    transcript_content += f"Opener: {opener_id}\nClaimer: {claimer_id}\nCloser: {closer_id}\n"
    transcript_content += f"Time: {datetime.utcnow().isoformat()}\n\n-- MESSAGES --\n"

    try:
        async for message in channel.history(limit=None, oldest_first=True):
            author = message.author.name
            if message.author.id == bot.user.id and message.embeds:
                if message.embeds[0].author and "Trade Hub AI" in str(message.embeds[0].author.name):
                    author = "Staff (via AI)"
            transcript_content += f"[{message.created_at}] {author}: {message.content}\n"
        
        log_chan = channel.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if log_chan:
            file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"transcript-{channel.name}.txt")
            embed = discord.Embed(title=f"📄 Transcript: {channel.name}", color=discord.Color.orange())
            await log_chan.send(embed=embed, file=file)
    except Exception as e: print(f"Transcript Error: {e}")

async def close_ticket_logic(staff_channel, user_channel_id, closer_id=None):
    user_chan = bot.get_channel(user_channel_id) if user_channel_id else None
    data = load_ticket_data()
    found_uid = None
    opener = "Unknown"
    claimer = "None"
    
    for uid, t in data.get("user_middleman_tickets", {}).items():
        if t["channel_id"] == user_channel_id:
            found_uid = uid
            opener = t.get("opener", uid)
            claimer = t.get("claimer", "None")
            break
            
    target_chan = user_chan if user_chan else staff_channel
    if target_chan: await create_transcript(target_chan, opener, claimer, closer_id)

    if found_uid:
        del data["user_middleman_tickets"][found_uid]
        save_ticket_data(data)

    if user_chan: 
        try: await user_chan.delete()
        except: pass
    if staff_channel: 
        try: await staff_channel.delete()
        except: pass

# --- VIEWS ---

class StaffDashboard(discord.ui.View):
    def __init__(self, user_chan_id, claimer_id):
        super().__init__(timeout=None)
        self.user_chan_id = user_chan_id
        self.claimer_id = claimer_id

    # SECURITY CHECK
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
        if interaction.user.id != self.claimer_id and not is_owner:
            await interaction.response.send_message("❌ **Access Denied:** Only the claimer can control this session.", ephemeral=True)
            return False
        return True

    async def send_to_user(self, interaction, text=None, embed=None, file=None):
        user_chan = bot.get_channel(self.user_chan_id)
        if user_chan:
            if text or embed:
                if not embed:
                    embed = discord.Embed(description=text, color=EMBED_COLOR)
                    embed.set_author(name="Trade Hub AI", icon_url=bot.user.display_avatar.url)
                
                await user_chan.send(embed=embed, file=file)
            await interaction.response.send_message("✅ Sent.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ User channel not found.", ephemeral=True)

    @discord.ui.button(label="👋 Intro", style=discord.ButtonStyle.blurple, row=0)
    async def btn_intro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_to_user(interaction, "👋 Thank you for having me! I will assist you in your trade today.")

    @discord.ui.button(label="📝 Terms Check", style=discord.ButtonStyle.blurple, row=0)
    async def btn_terms(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_to_user(interaction, "Before we continue, I want to ask: **Did you both use our services before?**\nReply with **Yes** or **No**.")

    @discord.ui.button(label="❓ Process Check", style=discord.ButtonStyle.blurple, row=0)
    async def btn_process(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_to_user(interaction, "Do you both know how middlemans work? 🤔")

    @discord.ui.button(label="🔄 Transfer", style=discord.ButtonStyle.blurple, row=0)
    async def btn_transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Notify User
        await self.send_to_user(interaction, "For further assistance, I will now transfer this ticket to our middleman. Thanks for having me! 🫡")
        # 2. Notify Staff
        await interaction.response.send_message("🔒 **Transfer Initiated:** AI Ticket will auto-close in 10 seconds...", ephemeral=True)
        
        # 3. Wait 10s
        await asyncio.sleep(10)
        
        # 4. UNLINK Channels so user ticket DOES NOT close
        staff_chan_id = interaction.channel.id
        user_chan_id = relay_map.get(staff_chan_id)
        
        if staff_chan_id in relay_map: del relay_map[staff_chan_id]
        if user_chan_id in reverse_relay_map: del reverse_relay_map[user_chan_id]
        
        # 5. Delete AI Ticket
        try: await interaction.channel.delete()
        except: pass

    @discord.ui.button(label="Middleman", style=discord.ButtonStyle.gray, row=1)
    async def btn_mm1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if os.path.exists("assets/middleman_process.webp"):
            embed = discord.Embed(
                description="**The middleman is the trusted person between traders.**\n\n・**Step 1:** Both parties give items to MM.\n・**Step 2:** MM verifies items.\n・**Step 3:** MM swaps items to respective parties.",
                color=EMBED_COLOR
            )
            file = discord.File("assets/middleman_process.webp", filename="mm_process.webp")
            embed.set_image(url="attachment://mm_process.webp")
            await self.send_to_user(interaction, embed=embed, file=file)
        else:
            await interaction.response.send_message("❌ Image missing.", ephemeral=True)

    @discord.ui.button(label="Middleman 2", style=discord.ButtonStyle.gray, row=1)
    async def btn_mm2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if os.path.exists("assets/middleman_info.jpg"):
            embed = discord.Embed(description="**Middleman Information**", color=EMBED_COLOR)
            file = discord.File("assets/middleman_info.jpg", filename="mm_info.jpg")
            embed.set_image(url="attachment://mm_info.jpg")
            await self.send_to_user(interaction, embed=embed, file=file)
        else:
            await interaction.response.send_message("❌ Image missing.", ephemeral=True)

    @discord.ui.button(label="⛔ Close Ticket", style=discord.ButtonStyle.red, row=1)
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket sequence initiated...", ephemeral=True)
        await close_ticket_logic(interaction.channel, self.user_chan_id, closer_id=interaction.user.id)

class StaffClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Claim & Unlock", style=discord.ButtonStyle.green, custom_id="ai_staff_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. CHECK FOR SELF-CLAIM
        data = load_ticket_data()
        ticket_info = None
        for uid, t in data.get("user_middleman_tickets", {}).items():
            if t.get("staff_channel_id") == interaction.channel.id:
                ticket_info = t
                break
        
        if ticket_info and int(ticket_info.get("opener")) == interaction.user.id:
            await interaction.response.send_message("❌ **Access Denied:** You cannot claim your own ticket.", ephemeral=True)
            return

        # 2. PROCEED
        overwrite = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        await interaction.channel.set_permissions(interaction.user, overwrite=overwrite)
        
        await interaction.response.send_message(f"✅ **Claimed by {interaction.user.mention}**\nYou have write access.", ephemeral=False)
        
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        button.style = discord.ButtonStyle.gray
        await interaction.message.edit(view=self)

        if interaction.channel.id in relay_map:
            user_chan_id = relay_map[interaction.channel.id]
            # PASS CLAIMER ID
            dashboard = StaffDashboard(user_chan_id, claimer_id=interaction.user.id)
            
            embed = discord.Embed(title="🎛️ Staff Control Panel", description="Use the buttons below to interact with the user.", color=discord.Color.dark_theme())
            embed.add_field(name="👋 Intro", value="Send Welcome Message", inline=True)
            embed.add_field(name="📝 Terms", value="Ask Service History", inline=True)
            embed.add_field(name="❓ Process", value="Ask MM Knowledge", inline=True)
            embed.add_field(name="🔄 Transfer", value="**End Session (10s Timer)**", inline=True)
            embed.add_field(name="🖼️ MM / MM2", value="Send Diagrams", inline=True)
            embed.add_field(name="⛔ Close", value="Delete Ticket & Log", inline=True)
            embed.add_field(name="⚠️ Need to Transfer Ownership?", value="To fully transfer the ticket to another staff member (give them write access), use:\n**`!transfer @User`**", inline=False)
            
            await interaction.channel.send(embed=embed, view=dashboard)

class TradePollView(discord.ui.View):
    def __init__(self, allowed_users):
        super().__init__(timeout=None)
        self.votes = {}
        self.allowed_users = allowed_users

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message("❌ **Access Denied:** You are not a participant in this trade.", ephemeral=True)
            return False
        return True

    async def check_votes(self, interaction):
        if len(self.votes) < 2: return 
        
        if all(self.votes.values()):
            # BOTH ACCEPTED
            await interaction.channel.send("✅ **Trade Accepted!** Both parties confirmed. Waiting for staff to proceed...")
        
        elif not any(self.votes.values()):
            # BOTH DECLINED
            await interaction.channel.send(f"🚫 **Trade Declined.**\nYou both declined the trade. I am now closing the ticket.\nFeel free to request a middleman anytime you want here: <#{REQUEST_CHANNEL_ID}>")
            await asyncio.sleep(4)
            # Find staff channel to close properly
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            await close_ticket_logic(staff_chan, interaction.channel.id)
        
        else:
            # MIXED / DISAGREEMENT
            await interaction.channel.send(f"⚠️ **Trade Disagreement.**\nPlease decide the trade terms and confirm it before opening a ticket. I will close this now.\nFeel free to open a new ticket in <#{REQUEST_CHANNEL_ID}> when you are ready.")
            await asyncio.sleep(4)
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            await close_ticket_logic(staff_chan, interaction.channel.id)

    @discord.ui.button(label="Accept Trade", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = True
        await interaction.response.send_message(f"{interaction.user.mention} Accepted.", ephemeral=False)
        await self.check_votes(interaction)

    @discord.ui.button(label="Decline Trade", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = False
        await interaction.response.send_message(f"{interaction.user.mention} Declined.", ephemeral=False)
        await self.check_votes(interaction)

class ChoiceView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ You did not create this ticket.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🤖 AI Assistant", style=discord.ButtonStyle.blurple, custom_id="btn_ai")
    async def ai(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AIModal(self.owner_id))

    @discord.ui.button(label="👤 Human Middleman", style=discord.ButtonStyle.gray, custom_id="btn_mm")
    async def mm(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_ticket_data()
        found = False
        for uid, t in data.get("user_middleman_tickets", {}).items():
            if t["channel_id"] == interaction.channel.id:
                t["claimer"] = None 
                t["ai_locked"] = False
                save_ticket_data(data)
                found = True
                break
        
        await interaction.message.delete()
        if found:
            await interaction.channel.send(f"🔔 <@&{MIDDLEMAN_ROLE_ID}> **Middleman Requested!**\nA staff member can now claim this ticket above.")
        else:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)

class AIModal(discord.ui.Modal, title="AI Trade Setup"):
    trade_info = discord.ui.TextInput(label="Trade Details", style=discord.TextStyle.paragraph, placeholder="My X for their Y...")
    other_user = discord.ui.TextInput(label="Trading Partner (Username ONLY - No @)", placeholder="username")

    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        target_name = self.other_user.value.strip()
        target_member = discord.utils.get(guild.members, name=target_name)
            
        add_status = ""
        allowed_voters = [interaction.user.id]
        
        if target_member:
            await interaction.channel.set_permissions(target_member, view_channel=True, send_messages=True)
            add_status = f"\n✅ **Added:** {target_member.mention}"
            allowed_voters.append(target_member.id)
        else:
            add_status = f"\n⚠️ **Note:** Could not find '{target_name}'. Please add them manually."

        cat = guild.get_channel(AI_CATEGORY_ID)
        if cat: await cat.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)})
        
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
        
        data = load_ticket_data()
        for uid, t in data.get("user_middleman_tickets", {}).items():
            if t["channel_id"] == interaction.channel.id:
                t["staff_channel_id"] = staff_chan.id
                save_ticket_data(data)
                break

        view = StaffClaimView()
        info_embed = discord.Embed(title="🤖 New AI Ticket", color=discord.Color.gold())
        info_embed.add_field(name="User", value=interaction.user.mention, inline=True)
        info_embed.add_field(name="Partner", value=target_member.mention if target_member else target_name, inline=True)
        info_embed.add_field(name="Details", value=self.trade_info.value, inline=False)
        info_embed.add_field(name="Quick Link", value=f"[Go to Ticket]({interaction.channel.jump_url})", inline=False)
        
        await staff_chan.send(content=f"<@&{MIDDLEMAN_ROLE_ID}>", embed=info_embed, view=view)

        user_embed = discord.Embed(title="🤝 Trade Confirmation", description=f"**Trade:** {self.trade_info.value}\n\n**Participants:** {interaction.user.mention} & {target_member.mention if target_member else target_name}\n\n{add_status}\n\n*Please confirm the details above.*", color=EMBED_COLOR)
        await interaction.channel.send(embed=user_embed, view=TradePollView(allowed_voters))
        await interaction.followup.send("AI Assistant Connected!", ephemeral=True)

# --- EVENTS ---

@bot.event
async def on_ready():
    print(f"✅ Relay Bot Online: {bot.user}")
    bot.add_view(StaffClaimView())
    
    # REBUILD MAPS
    data = load_ticket_data()
    for uid, t in data.get("user_middleman_tickets", {}).items():
        if "channel_id" in t and "staff_channel_id" in t:
            user_id = t["channel_id"]
            staff_id = t["staff_channel_id"]
            relay_map[staff_id] = user_id
            reverse_relay_map[user_id] = staff_id
    print(f"✅ Restored {len(relay_map)} active sessions.")

@bot.event
async def on_guild_channel_delete(channel):
    # Auto-close
    if channel.id in reverse_relay_map:
        staff_chan_id = reverse_relay_map[channel.id]
        staff_chan = bot.get_channel(staff_chan_id)
        if staff_chan:
            try: await staff_chan.send("⚠️ User ticket deleted. Closing...")
            except: pass
            await asyncio.sleep(1)
            try: await staff_chan.delete()
            except: pass
        del reverse_relay_map[channel.id]
        if staff_chan_id in relay_map: del relay_map[staff_chan_id]

    elif channel.id in relay_map:
        user_chan_id = relay_map[channel.id]
        user_chan = bot.get_channel(user_chan_id)
        if user_chan:
            try: await user_chan.send("⚠️ Staff closed the connection. Closing...")
            except: pass
            await asyncio.sleep(1)
            try: await user_chan.delete()
            except: pass
        del relay_map[channel.id]
        if user_chan_id in reverse_relay_map: del reverse_relay_map[user_chan_id]

@bot.event
async def on_message_delete(message):
    if message.id in message_link:
        target_msg_id = message_link[message.id]
        target_chan = None
        if message.channel.id in relay_map:
            target_chan = bot.get_channel(relay_map[message.channel.id])
        elif message.channel.id in reverse_relay_map:
            target_chan = bot.get_channel(reverse_relay_map[message.channel.id])
            
        if target_chan:
            try:
                msg_to_del = await target_chan.fetch_message(target_msg_id)
                await msg_to_del.delete()
            except: pass
        del message_link[message.id]

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
                    owner_id = int(t.get("opener", 0))
                    embed = discord.Embed(title="🤖 Trade Assistant", description="**Do you want AI to handle your trade or our middleman?**\n*Select an option below.*", color=discord.Color.gold())
                    await message.channel.send(embed=embed, view=ChoiceView(owner_id))
                    break

    # STAFF -> USER RELAY
    if message.channel.id in relay_map:
        user_chan_id = relay_map[message.channel.id]
        user_chan = bot.get_channel(user_chan_id)
        if not user_chan: return

        content = message.content
        
        if content.startswith("!close"):
            await message.channel.send("🔒 Closing...")
            await close_ticket_logic(message.channel, user_chan_id, closer_id=message.author.id)
            return
        elif content.startswith("!transfer"):
            target = message.mentions[0] if message.mentions else None
            if target:
                await message.channel.set_permissions(message.author, send_messages=False)
                await message.channel.set_permissions(target, view_channel=True, send_messages=True)
                await message.channel.send(f"✅ Ticket transferred to {target.mention}.")
            else: await message.channel.send("❌ Use `!transfer @User`")
            return
        elif content.startswith("!aiadd"):
            try:
                await user_chan.set_permissions(message.author, view_channel=True, send_messages=True)
                await message.channel.send(f"✅ Added to {user_chan.mention}")
            except: pass
            return
        elif content.startswith("!add"):
            target = message.mentions[0] if message.mentions else None
            if not target:
                try: target = discord.utils.get(message.guild.members, name=content.split(" ", 1)[1].strip())
                except: pass
            if target:
                await user_chan.set_permissions(target, view_channel=True, send_messages=True)
                await message.channel.send(f"✅ Added {target.mention}")
            else: await message.channel.send("❌ User not found.")
            return

        # Text Relay
        if message.content:
            embed = discord.Embed(description=message.content, color=EMBED_COLOR)
            embed.set_author(name="Trade Hub AI", icon_url=bot.user.display_avatar.url)
            sent_msg = await user_chan.send(embed=embed)
            message_link[message.id] = sent_msg.id
            message_link[sent_msg.id] = message.id
        
        if message.attachments:
            for a in message.attachments: await user_chan.send(a.url)

    # USER -> STAFF RELAY
    elif message.channel.id in reverse_relay_map:
        staff_chan_id = reverse_relay_map[message.channel.id]
        staff_chan = bot.get_channel(staff_chan_id)
        if staff_chan:
            if message.content:
                embed = discord.Embed(description=message.content, color=EMBED_COLOR)
                embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                embed.set_footer(text="User Reply")
                sent_msg = await staff_chan.send(embed=embed)
                message_link[message.id] = sent_msg.id
                message_link[sent_msg.id] = message.id
            if message.attachments:
                for a in message.attachments: await staff_chan.send(f"**Attachment:** {a.url}")

    await bot.process_commands(message)

# RUN WEB SERVER
keep_alive()

# START BOT
if os.getenv("AI_BOT_TOKEN"):
    bot.run(os.getenv("AI_BOT_TOKEN"))
else:
    print("❌ AI_BOT_TOKEN missing")
