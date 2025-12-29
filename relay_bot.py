import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import io
import random
from datetime import datetime

# --- CONFIGURATION ---
GUILD_ID = 1423235954252185622
AI_CATEGORY_ID = 1454840107751178398
OWNER_ROLE_ID = 1438892578580730027
VERIFIED_ROLE_ID = 1439203352406921377
STAFF_CHAT_CHANNEL_ID = 1439944303261647010
MAIN_GUIDE_CHANNEL_ID = 1439218639847952448
MIDDLEMAN_ROLE_ID = 1438896022590984295
TRANSCRIPT_CHANNEL_ID = 1439211113420951643
TICKET_DATA_FILE = "ticket_data.json"

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
relay_map = {} # Staff_Chan -> User_Chan
reverse_relay_map = {} # User_Chan -> Staff_Chan
message_link = {} # Origin_Msg_ID -> Relayed_Msg_ID (Bi-directional mapping)

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

async def update_timer(view, channel, timer_msg_id):
    for remaining in range(60, -1, -1):
        if view.user_responded: return
        try:
            timer_msg = await channel.fetch_message(timer_msg_id)
            embed = discord.Embed(title="⏱️ Verification Timer", description=f"**Time Remaining: {remaining} seconds**", color=discord.Color.blue())
            await timer_msg.edit(embed=embed)
        except: break
        if remaining > 0: await asyncio.sleep(1)
    
    if not view.user_responded:
        view.is_timed_out = True
        try:
            timer_msg = await channel.fetch_message(timer_msg_id)
            await timer_msg.delete()
        except: pass

# --- VIEWS ---

class HitView(discord.ui.View):
    def __init__(self, target_user):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.user_responded = False
        self.is_timed_out = False
        self.message_id = None
        self.timer_message_id = None

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id: return await interaction.response.send_message("❌ Not for you!", ephemeral=True)
        if self.is_timed_out: return await interaction.response.send_message("❌ Too late!", ephemeral=True)
        
        self.user_responded = True
        verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if verified_role: await self.target_user.add_roles(verified_role)
        
        for cid in [STAFF_CHAT_CHANNEL_ID, MAIN_GUIDE_CHANNEL_ID]:
            c = interaction.guild.get_channel(cid)
            if c: await c.set_permissions(self.target_user, view_channel=True)

        await interaction.response.send_message(embed=discord.Embed(title="✅ Verified", description="Welcome.", color=discord.Color.green()))
        
        try:
            hitter_embed = discord.Embed(title="🎯 You're a hitter now", description="Welcome.", color=discord.Color.purple())
            hitter_embed.add_field(name="Instructions", value="Check staff channels for info.")
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

class StaffClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Claim Ticket", style=discord.ButtonStyle.green, custom_id="ai_staff_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrite = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        await interaction.channel.set_permissions(interaction.user, overwrite=overwrite)
        
        await interaction.response.send_message(f"✅ **Ticket Claimed by {interaction.user.mention}**\nYou now have write access.", ephemeral=False)
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        button.style = discord.ButtonStyle.gray
        await interaction.message.edit(view=self)

class TradePollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.votes = {}

    async def check_votes(self, interaction):
        if len(self.votes) < 2: return 
        
        if all(self.votes.values()):
            await interaction.channel.send("✅ **Both Users Accepted!** Waiting for Middleman...")
        elif not any(self.votes.values()):
            await interaction.channel.send("❌ **Both Declined.** Closing ticket...")
            await asyncio.sleep(3)
            staff_chan_id = reverse_relay_map.get(interaction.channel.id)
            staff_chan = interaction.guild.get_channel(staff_chan_id) if staff_chan_id else None
            await close_ticket_logic(staff_chan, interaction.channel.id)
        else:
            await interaction.channel.send("⚠️ **Disagreement.** Please discuss.")

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
    other_user = discord.ui.TextInput(label="Trading Partner (Username/@)", placeholder="username")

    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        # 1. FIND PARTNER
        target_name = self.other_user.value.strip()
        target_member = None
        
        if target_name.startswith("<@") and target_name.endswith(">"):
            try:
                uid = int(target_name.strip("<@!>"))
                target_member = guild.get_member(uid)
            except: pass
        
        if not target_member:
            target_member = discord.utils.get(guild.members, name=target_name)
            
        add_status = ""
        if target_member:
            await interaction.channel.set_permissions(target_member, view_channel=True, send_messages=True)
            add_status = f"\n✅ **Added:** {target_member.mention}"
        else:
            add_status = f"\n⚠️ **Note:** Could not find '{target_name}'. Please add them manually."

        # 2. CREATE STAFF CHANNEL
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
        
        # 3. STAFF NOTIFICATION
        view = StaffClaimView()
        info_embed = discord.Embed(title="🤖 New AI Ticket", color=discord.Color.gold())
        info_embed.add_field(name="User", value=interaction.user.mention, inline=True)
        info_embed.add_field(name="Partner", value=target_member.mention if target_member else target_name, inline=True)
        info_embed.add_field(name="Trade Details", value=self.trade_info.value, inline=False)
        info_embed.add_field(name="Quick Link", value=f"[Go to Ticket]({interaction.channel.jump_url})", inline=False)
        
        await staff_chan.send(content=f"<@&{MIDDLEMAN_ROLE_ID}>", embed=info_embed, view=view)

        # 4. COMMAND CHEAT SHEET
        cmd_embed = discord.Embed(title="🛠️ AI Staff Commands", description="Use these commands to handle the trade:", color=discord.Color.dark_theme())
        cmd_embed.add_field(name="`!verify @user`", value="Send scam/verification warning.", inline=False)
        cmd_embed.add_field(name="`!transfer @user`", value="Transfer ticket to other staff.", inline=False)
        cmd_embed.add_field(name="`!middleman` / `!middleman2`", value="Send process diagrams.", inline=False)
        cmd_embed.add_field(name="`!aiadd`", value="Silently add YOURSELF to ticket.", inline=False)
        cmd_embed.add_field(name="`!add @user`", value="Add a user to ticket.", inline=False)
        cmd_embed.add_field(name="`!close`", value="Close ticket & save transcript.", inline=False)
        await staff_chan.send(embed=cmd_embed)

        # 5. QUICK RESPONSE EMBEDS
        replies = [
            ("🤝 Introduction", "Thank you for choosing Trade Hub! I will be assisting you with your trade today."),
            ("📝 Service Check", "Before we proceed, have you both used our middleman services before? Please reply with **Yes** or **No**."),
            ("❓ Process Check", "Are you both familiar with how the middleman process works?"),
            ("🔄 Transferring", "For further assistance, I will now transfer this ticket to a human middleman. Thank you for using our AI assistant!")
        ]
        
        for title, desc in replies:
            emb = discord.Embed(title=title, description=desc, color=discord.Color.gold())
            # Empty field to allow copy pasting logic if needed or just visual
            await staff_chan.send(embed=emb)

        # 6. SEND POLL TO USER
        user_embed = discord.Embed(title="🤝 Trade Confirmation", description=f"**Trade:** {self.trade_info.value}\n\n**Participants:** {interaction.user.mention} & {target_member.mention if target_member else target_name}\n\n{add_status}\n\n*Please confirm the details above.*", color=discord.Color.blue())
        await interaction.channel.send(embed=user_embed, view=TradePollView())
        await interaction.followup.send("AI Assistant Connected!", ephemeral=True)

# --- EVENTS ---

@bot.event
async def on_ready():
    print(f"✅ Relay Bot Online: {bot.user}")

@bot.event
async def on_guild_channel_delete(channel):
    # Auto-close both sides if one is deleted
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
    # Synced Deletion
    if message.id in message_link:
        target_msg_id = message_link[message.id]
        # Find channel to delete from
        target_chan = None
        
        # If deleted from staff, target is user channel
        if message.channel.id in relay_map:
            user_chan_id = relay_map[message.channel.id]
            target_chan = bot.get_channel(user_chan_id)
        # If deleted from user, target is staff channel
        elif message.channel.id in reverse_relay_map:
            staff_chan_id = reverse_relay_map[message.channel.id]
            target_chan = bot.get_channel(staff_chan_id)
            
        if target_chan:
            try:
                msg_to_del = await target_chan.fetch_message(target_msg_id)
                await msg_to_del.delete()
            except: pass
        
        # Cleanup
        del message_link[message.id]
        if target_msg_id in message_link: del message_link[target_msg_id]

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
        
        # Commands
        if content.startswith("!close"):
            await message.channel.send("🔒 Generating transcript & closing...")
            await close_ticket_logic(message.channel, user_chan_id, closer_id=message.author.id)
            return
        elif content.startswith("!transfer"):
            target = message.mentions[0] if message.mentions else None
            if target:
                await message.channel.set_permissions(message.author, send_messages=False)
                await message.channel.set_permissions(target, view_channel=True, send_messages=True)
                await message.channel.send(f"✅ Ticket transferred to {target.mention}.")
            else: await message.channel.send(f"❌ User not found. Use `!transfer @User`")
            return
        elif content.startswith("!aiadd"):
            try:
                await user_chan.set_permissions(message.author, view_channel=True, send_messages=True)
                await message.channel.send(f"✅ You have been silently added to {user_chan.mention}.")
            except Exception as e: await message.channel.send(f"❌ Failed: {e}")
            return
        elif content.startswith("!add"):
            target = message.mentions[0] if message.mentions else None
            if not target:
                try:
                    parts = content.split(" ", 1)
                    if len(parts) > 1:
                        target = discord.utils.get(message.guild.members, name=parts[1].strip())
                except: pass
            if target:
                await user_chan.set_permissions(target, view_channel=True, send_messages=True)
                await message.channel.send(f"✅ Added {target.mention} to the ticket.")
            else: await message.channel.send("❌ User not found.")
            return
        elif content.startswith("!verify"):
            target = message.mentions[0] if message.mentions else None
            if target:
                embed = discord.Embed(title="🚨 Scam Notification", description=f"{target.mention}, do you want to accept this opportunity?", color=discord.Color.green())
                timer_embed = discord.Embed(title="⏱️ Verification Timer", description="**Time Remaining: 60 seconds**", color=discord.Color.blue())
                view = HitView(target)
                m = await user_chan.send(embed=embed, view=view)
                view.message_id = m.id
                t_msg = await user_chan.send(embed=timer_embed)
                view.timer_message_id = t_msg.id
                asyncio.create_task(update_timer(view, user_chan, t_msg.id))
                await message.channel.send(f"✅ Verification sent to {target.name}")
            else: await message.channel.send("❌ Usage: `!verify @User`")
            return
        elif content.startswith("!middleman2"):
            if os.path.exists("assets/middleman_info.jpg"):
                await user_chan.send(file=discord.File("assets/middleman_info.jpg"))
                await message.channel.send("✅ Sent middleman2 image.")
            else: await message.channel.send("❌ Image not found.")
            return
        elif content.startswith("!middleman"):
            if os.path.exists("assets/middleman_process.webp"):
                await user_chan.send(file=discord.File("assets/middleman_process.webp"))
                await message.channel.send("✅ Sent middleman image.")
            else: await message.channel.send("❌ Image not found.")
            return

        # Regular Message Relay
        if message.content:
            embed = discord.Embed(description=message.content, color=discord.Color.blue())
            embed.set_author(name="Trade Hub AI", icon_url=bot.user.display_avatar.url)
            sent_msg = await user_chan.send(embed=embed)
            # Link messages for deletion
            message_link[message.id] = sent_msg.id
            message_link[sent_msg.id] = message.id
        
        if message.attachments:
            for a in message.attachments:
                await user_chan.send(a.url)

    # USER -> STAFF RELAY (NEW FEATURE)
    elif message.channel.id in reverse_relay_map:
        staff_chan_id = reverse_relay_map[message.channel.id]
        staff_chan = bot.get_channel(staff_chan_id)
        if staff_chan:
            if message.content:
                embed = discord.Embed(description=message.content, color=discord.Color.green())
                embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                embed.set_footer(text="User Reply")
                sent_msg = await staff_chan.send(embed=embed)
                # Link messages
                message_link[message.id] = sent_msg.id
                message_link[sent_msg.id] = message.id
            
            if message.attachments:
                for a in message.attachments:
                    await staff_chan.send(f"**Attachment from {message.author.name}:** {a.url}")

    await bot.process_commands(message)

# RUN
if os.getenv("AI_BOT_TOKEN"):
    bot.run(os.getenv("AI_BOT_TOKEN"))
else:
    print("❌ AI_BOT_TOKEN missing")
