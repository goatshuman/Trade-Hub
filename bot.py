import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import aiofiles
import io
import asyncio
import aiohttp
import random
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load .env file FIRST
load_dotenv()

# Load config
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def loaddata():
    global guildsettings, invitetracker, resetinvites
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            guildsettings = data.get('settings', {})
            invitetracker = data.get('tracker', {})
            resetinvites = data.get('resets', {})
    except:
        guildsettings = {}
        invitetracker = {}
        resetinvites = {}

def savedata():
    data = {
        'settings': guildsettings,
        'tracker': invitetracker,
        'resets': resetinvites
    }
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

def gettotalinvites(guild, user):
    guildid = str(guild.id)
    userid = str(user.id)
    if guildid not in invitetracker or userid not in invitetracker[guildid]:
        return 0
    total = sum(invitetracker[guildid][userid].values())
    resetcount = resetinvites.get(guildid, {}).get(userid, 0)
    return max(0, total - resetcount)

def getinvitedetails(guild, user):
    guildid = str(guild.id)
    userid = str(user.id)
    if guildid not in invitetracker or userid not in invitetracker[guildid]:
        return []
    details = []
    for joinedidstr, count in invitetracker[guildid][userid].items():
        try:
            joineduser = guild.get_member(int(joinedidstr))
            if joineduser:
                details.append((joineduser, count))
        except:
            continue
    return details

config = load_config()
LOGO_URL = config.get("logo_url", "")
FOOTER_TEXT = config.get("footer_text", "Powered by Trade Hub")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1423235954252185622
MEMBER_ROLE_ID = 1439203750664470589
VERIFIED_ROLE_ID = 1439203352406921377
OWNER_ROLE_ID = 1438892578580730027
CO_OWNER_ROLE_ID = 1438894594254311504
MIDDLEMAN_ROLE_ID = 1438896022590984295
HEAD_MIDDLEMAN_ROLE_ID = 1438895916596592650
MANAGER_ROLE_ID = 1438895819125297274
HEAD_MANAGER_ROLE_ID = 1438895696936828928
MODERATOR_ROLE_ID = 1438895276419977329
HEAD_MODERATOR_ROLE_ID = 1441060547700457584
ADMINISTRATOR_ROLE_ID = 1438895119360065666
COORDINATOR_ROLE_ID = 1444914892309139529
HEAD_COORDINATOR_ROLE_ID = 1444915199529324624
SUPPORT_ROLE_ID = 1441060547700457584
REQUEST_MIDDLEMAN_CHANNEL_ID = 1438899065952927917
SUPPORT_TICKET_CHANNEL_ID = 1438900365859885158
BUY_RANKS_CHANNEL_ID = 1438901827025502248
BUY_ITEMS_CHANNEL_ID = 1440345093977411645
BUY_PERSONAL_MIDDLEMAN_CHANNEL_ID = 1439932899406254100
GAMES_CHANNEL_ID = 1451911322563252379
TRANSCRIPT_CHANNEL_ID = 1439211113420951643
MIDDLEMAN_CATEGORY_ID = 1455128597927821313
PERSONAL_MIDDLEMAN_CATEGORY_ID = 1438902367280955444
SUPPORT_CATEGORY_ID = 1455128452427677840
BUY_RANKS_CATEGORY_ID = 1438901628773208215
BUY_ITEMS_CATEGORY_ID = 1440344945553834117
UNIFIED_TICKET_CATEGORY_ID = 1444708699313668096
BUY_RANKS_TRANSCRIPT_ID = 1439595144423936023
BUY_ITEMS_TRANSCRIPT_ID = 1439594824373370900
MAIN_GUIDE_CHANNEL_ID = 1439218639847952448
STAFF_CHAT_CHANNEL_ID = 1439944303261647010
WELCOME_CHANNEL_ID = 1439885573799284798
MODERATION_LOG_CHANNEL_ID = 1441073064308768898
ROLE_LOG_CHANNEL_ID = 1444925042499780679

STAFF_ROLE_IDS = [
    OWNER_ROLE_ID,
    CO_OWNER_ROLE_ID,
    ADMINISTRATOR_ROLE_ID,
    MODERATOR_ROLE_ID,
    HEAD_MODERATOR_ROLE_ID,
    COORDINATOR_ROLE_ID,
    HEAD_COORDINATOR_ROLE_ID,
    HEAD_MANAGER_ROLE_ID,
    MANAGER_ROLE_ID,
    HEAD_MIDDLEMAN_ROLE_ID,
    MIDDLEMAN_ROLE_ID,
    SUPPORT_ROLE_ID
]

spam_tracker = {}
guildsettings = {}
invitetracker = {}
resetinvites = {}

TICKET_DATA_FILE = "ticket_data.json"
MESSAGE_IDS_FILE = "message_ids.json"
WARNS_DATA_FILE = "warns_data.json"

# Embed Builder Command
class EmbedTitleModal(discord.ui.Modal, title="Embed Title"):
    title_input = discord.ui.TextInput(
        label="Embed Title",
        placeholder="Enter embed title (max 256 chars)",
        max_length=256,
        required=False
    )
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        self.embed_data['title'] = self.title_input.value
        await interaction.response.defer()
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.message.edit(embed=embed, view=view)

class EmbedDescriptionModal(discord.ui.Modal, title="Embed Description"):
    descinput = discord.ui.TextInput(
        label="Embed Description",
        placeholder="Enter embed description (max 4000 chars)",
        style=discord.TextStyle.paragraph,
        max_length=4000, 
        required=False
    )
    
    def __init__(self, embeddata):
        super().__init__()
        self.embeddata = embeddata
        
    async def on_submit(self, interaction: discord.Interaction):
        self.embeddata['description'] = self.descinput.value
        embed = discord.Embed.from_dict(self.embeddata)
        view = EmbedBuilderView(self.embeddata)
        await interaction.response.defer()
        await interaction.message.edit(embed=embed, view=view)

class EmbedColorModal(discord.ui.Modal, title="Embed Color"):
    color_input = discord.ui.TextInput(
        label="Hex Color (e.g. #FF0000 or 16711680)",
        placeholder="#FF0000 or 16711680 (decimal)",
        required=False
    )
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        color = self.color_input.value
        if color:
            try:
                if color.startswith('#'):
                    self.embed_data['color'] = int(color[1:], 16)
                else:
                    self.embed_data['color'] = int(color)
            except:
                pass
        await interaction.response.defer()
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.edit_original_response(embed=embed, view=view)

class EmbedFieldModal(discord.ui.Modal, title="Add Field"):
    name_input = discord.ui.TextInput(
        label="Field Name",
        placeholder="Field name (max 256 chars)",
        max_length=256,
        required=True
    )
    value_input = discord.ui.TextInput(
        label="Field Value",
        placeholder="Field value (max 1024 chars)",
        style=discord.TextStyle.paragraph,
        max_length=1024,
        required=True
    )
    inline_input = discord.ui.TextInput(
        label="Inline? (true/false)",
        placeholder="true or false",
        required=False,
        default="false"
    )
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        field = {
            'name': self.name_input.value,
            'value': self.value_input.value,
            'inline': self.inline_input.value.lower() == 'true'
        }
        
        if 'fields' not in self.embed_data:
            self.embed_data['fields'] = []
        self.embed_data['fields'].append(field)
        
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.response.edit_message(embed=embed, view=view)

class EmbedImageModal(discord.ui.Modal, title="Image URL"):
    image_input = discord.ui.TextInput(
        label="Image URL",
        placeholder="https://example.com/image.png",
        required=False
    )
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.image_input.value:
            self.embed_data['image'] = {'url': self.image_input.value}
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.response.edit_message(embed=embed, view=view)

class EmbedThumbnailModal(discord.ui.Modal, title="Thumbnail URL"):
    thumb_input = discord.ui.TextInput(
        label="Thumbnail URL",
        placeholder="https://example.com/thumb.png",
        required=False
    )
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.thumb_input.value:
            self.embed_data['thumbnail'] = {'url': self.thumb_input.value}
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.response.edit_message(embed=embed, view=view)

class EmbedAuthorModal(discord.ui.Modal, title="Author"):
    name_input = discord.ui.TextInput(label="Author Name", required=False)
    icon_input = discord.ui.TextInput(label="Author Icon URL", placeholder="https://...", required=False)
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.name_input.value:
            self.embed_data['author'] = {
                'name': self.name_input.value,
                'icon_url': self.icon_input.value
            }
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.response.edit_message(embed=embed, view=view)

class EmbedFooterModal(discord.ui.Modal, title="Footer"):
    text_input = discord.ui.TextInput(label="Footer Text", required=False)
    icon_input = discord.ui.TextInput(label="Footer Icon URL", placeholder="https://...", required=False)
    
    def __init__(self, embed_data):
        super().__init__()
        self.embed_data = embed_data
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.text_input.value:
            self.embed_data['footer'] = {
                'text': self.text_input.value,
                'icon_url': self.icon_input.value
            }
        embed = discord.Embed.from_dict(self.embed_data)
        view = EmbedBuilderView(self.embed_data)
        await interaction.response.edit_message(embed=embed, view=view)

class EmbedBuilderView(discord.ui.View):
    def __init__(self, embed_data):
        super().__init__(timeout=600)
        self.embed_data = embed_data
    
    @discord.ui.button(label="📝 Title", style=discord.ButtonStyle.primary, row=0)
    async def title_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedTitleModal(self.embed_data))
    
    @discord.ui.button(label="📄 Desc", style=discord.ButtonStyle.primary, row=0)
    async def desc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedDescriptionModal(self.embed_data))
    
    @discord.ui.button(label="🎨 Color", style=discord.ButtonStyle.secondary, row=0)
    async def color_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedColorModal(self.embed_data))
    
    @discord.ui.button(label="➕ Field", style=discord.ButtonStyle.green, row=1)
    async def field_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedFieldModal(self.embed_data))
    
    @discord.ui.button(label="🖼️ Image", style=discord.ButtonStyle.secondary, row=1)
    async def image_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedImageModal(self.embed_data))
    
    @discord.ui.button(label="🔍 Thumb", style=discord.ButtonStyle.secondary, row=1)
    async def thumb_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedThumbnailModal(self.embed_data))
    
    @discord.ui.button(label="👤 Author", style=discord.ButtonStyle.secondary, row=2)
    async def author_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedAuthorModal(self.embed_data))
    
    @discord.ui.button(label="📄 Footer", style=discord.ButtonStyle.secondary, row=2)
    async def footer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedFooterModal(self.embed_data))
    
    @discord.ui.button(label="✅ SEND", style=discord.ButtonStyle.success, row=2)
    async def send_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed.from_dict(self.embed_data)
            await interaction.response.send_message("✅ **Embed sent below!**", ephemeral=True)
            await interaction.channel.send(embed=embed)
            await interaction.edit_original_response(content="✅ **Embed created & sent successfully!**", embed=None, view=None)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Error:** {str(e)}", ephemeral=True)

@bot.tree.command(name="embed", description="🛠️ Interactive embed builder", guild=discord.Object(id=GUILD_ID))
async def embed_builder(interaction: discord.Interaction):
    embed_data = {}
    embed = discord.Embed(
        title="🛠️ Embed Builder",
        description="**Click buttons to customize your embed!**\n\n• 📝 Title & Description\n• 🎨 Custom Colors\n• ➕ Unlimited Fields\n• 🖼️ Images/Thumbnails\n• 👤 Author & Footer\n• **Live preview updates instantly!**",
        color=0x00ff88
    )
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    
    view = EmbedBuilderView(embed_data)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

def load_ticket_data():
    default_data = {"user_middleman_tickets": {}, "user_support_tickets": {}, "user_buyranks_tickets": {}, "user_buyitems_tickets": {}, "user_personal_middleman_tickets": {}, "ticket_counter": 0, "buyranks_counter": 0, "buyitems_counter": 0, "personal_mm_counter": 0}
    if os.path.exists(TICKET_DATA_FILE):
        with open(TICKET_DATA_FILE, 'r') as f:
            loaded_data = json.load(f)
            default_data.update(loaded_data)
            return default_data
    return default_data
 
def save_ticket_data(data):
    with open(TICKET_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
 
def load_message_ids():
    default_data = {"middleman": None, "support": None, "buyranks": None, "buyitems": None, "personal_mm": None, "games": None}
    if os.path.exists(MESSAGE_IDS_FILE):
        with open(MESSAGE_IDS_FILE, 'r') as f:
            loaded_data = json.load(f)
            default_data.update(loaded_data)
            return default_data
    return default_data
 
def save_message_ids(data):
    with open(MESSAGE_IDS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
 
def load_super_admins():
    default_data = {"super_admins": []}
    admin_file = os.path.join("admins", "super_admins.json")
    if os.path.exists(admin_file):
        try:
            with open(admin_file, 'r') as f:
                loaded_data = json.load(f)
                default_data.update(loaded_data)
                return default_data
        except:
            return default_data
    return default_data
 
def load_warns_data():
    default_data = {}
    if os.path.exists(WARNS_DATA_FILE):
        try:
            with open(WARNS_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return default_data
    return default_data
 
def save_warns_data(data):
    with open(WARNS_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
 
def load_afk_data():
    default_data = {}
    afk_file = "afk_data.json"
    if os.path.exists(afk_file):
        try:
            with open(afk_file, 'r') as f:
                return json.load(f)
        except:
            return default_data
    return default_data
 
def save_afk_data(data):
    with open("afk_data.json", 'w') as f:
        json.dump(data, f, indent=4)
 
def load_giveaway_data():
    default_data = {}
    giveaway_file = "giveaway_data.json"
    if os.path.exists(giveaway_file):
        try:
            with open(giveaway_file, 'r') as f:
                return json.load(f)
        except:
            return default_data
    return default_data
 
def save_giveaway_data(data):
    with open("giveaway_data.json", 'w') as f:
        json.dump(data, f, indent=4)
 
async def check_and_update_category_visibility(guild, ticket_type):
    """Check if any tickets remain for that type. Hide category if empty, show if has tickets"""
    try:
        ticket_data = load_ticket_data()
 
        if ticket_type == "middleman":
            ticket_count = len(ticket_data.get("user_middleman_tickets", {}))
            category_id = MIDDLEMAN_CATEGORY_ID
        elif ticket_type == "support":
            ticket_count = len(ticket_data.get("user_support_tickets", {}))
            category_id = SUPPORT_CATEGORY_ID
        else:
            return
 
        category = guild.get_channel(category_id)
        if not category:
            return
 
        if ticket_count == 0:
            await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False)})
        else:
            await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True)})
    except Exception as e:
        print(f"Error updating category visibility: {e}")
 
SUPER_ADMINS = load_super_admins()["super_admins"]
 
def is_owner_or_super_admin(user_id, user_roles):
    """Check if user is owner role or super admin - works even with member role"""
    is_owner_role = OWNER_ROLE_ID in user_roles
    is_super_admin = user_id in SUPER_ADMINS
    return is_owner_role or is_super_admin
 
async def is_middleman_or_above(interaction: discord.Interaction) -> bool:
    """Only allow middleman and above staff - block all others"""
    user_roles = [role.id for role in interaction.user.roles]
    is_staff = any(role_id in STAFF_ROLE_IDS for role_id in user_roles)
 
    if not is_staff:
        raise app_commands.MissingPermissions(["staff"])
 
    return True
 
async def is_owner_only(interaction: discord.Interaction) -> bool:
    """Only allow owner or super admins - block all others"""
    user_roles = [role.id for role in interaction.user.roles]
    is_owner_role = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
 
    if not (is_owner_role or is_super_admin):
        raise app_commands.MissingPermissions(["owner"])
 
    return True
 
async def can_add_mm(interaction: discord.Interaction) -> bool:
    """Allow: moderator, head moderator, administrator, co-owner, owner"""
    user_roles = [role.id for role in interaction.user.roles]
    allowed = [MODERATOR_ROLE_ID, HEAD_MANAGER_ROLE_ID, ADMINISTRATOR_ROLE_ID, CO_OWNER_ROLE_ID, OWNER_ROLE_ID]
 
    if not any(role_id in allowed for role_id in user_roles):
        raise app_commands.MissingPermissions(["moderator"])
 
    return True


 
async def can_remove_mm(interaction: discord.Interaction) -> bool:
    """Allow: moderator and above"""
    user_roles = [role.id for role in interaction.user.roles]
    allowed = [MODERATOR_ROLE_ID, HEAD_MANAGER_ROLE_ID, MANAGER_ROLE_ID, ADMINISTRATOR_ROLE_ID, CO_OWNER_ROLE_ID, OWNER_ROLE_ID]
 
    if not any(role_id in allowed for role_id in user_roles):
        raise app_commands.MissingPermissions(["moderator"])
 
    return True
 
async def can_add_roles(interaction: discord.Interaction) -> bool:
    """Allow: co-owner and owner only"""
    user_roles = [role.id for role in interaction.user.roles]
    allowed = [CO_OWNER_ROLE_ID, OWNER_ROLE_ID]
 
    if not any(role_id in allowed for role_id in user_roles):
        raise app_commands.MissingPermissions(["co-owner"])
 
    return True

async def status_loop():
    """SIMPLE working status cycle"""
    await bot.wait_until_ready()
    while True:
        try:
            ticket_data = load_ticket_data()
            total_tickets = sum(len(ticket_data.get(t, {})) for t in [
                'user_middleman_tickets', 'user_support_tickets', 
                'user_buy_ranks_tickets', 'user_buy_items_tickets', 
                'user_personal_middleman_tickets'
            ])
            
            await bot.change_presence(activity=discord.Game(name="Trade Hub"))
            print(f"🟢 Status: Playing Trade Hub | 🎫 {total_tickets} tickets")
            await asyncio.sleep(5)
            
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=f"🎫 {total_tickets} tickets"
            ))
            print(f"🔵 Status: Watching 🎫 {total_tickets} tickets")
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Status error: {e}")
            await asyncio.sleep(10)
 
 
class SupportTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Make Support", style=discord.ButtonStyle.success, custom_id="support_ticket_button")
    async def make_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Creation guard: only owner role or super admins can open tickets
        try:
            user_roles = [r.id for r in interaction.user.roles]
        except:
            user_roles = []
        if not (OWNER_ROLE_ID in user_roles or interaction.user.id in SUPER_ADMINS):
            await interaction.response.send_message("❌ Only Owner or Super Admins can open tickets.", ephemeral=True)
            return

        ticket_data = load_ticket_data()
        user_id = str(interaction.user.id)
 
        if user_id in ticket_data["user_support_tickets"]:
            await interaction.response.send_message("❌ You already have an open support ticket!", ephemeral=True)
            return
 
        ticket_number = str(random.randint(1000, 9999))
        username = interaction.user.name.lower().replace(" ", "-")
        channel_name = f"support-{username}-{ticket_number}"
 
        ticket_data["user_support_tickets"][user_id] = {
            "channel_id": 0,
            "ticket_number": ticket_number,
            "type": "support",
            "opener": interaction.user.id,
            "claimer": None,
            "closer": None,
            "opened_at": datetime.utcnow().isoformat(),
            "claimed_at": None,
            "closed_at": None,
            "added_users": []
        }
        save_ticket_data(ticket_data)
 
        await interaction.response.send_message("🔄 Creating ticket...", ephemeral=True)
 
        async def create_ticket():
            try:
                guild = interaction.guild
                category = guild.get_channel(SUPPORT_CATEGORY_ID)
                if not category:
                    return
 
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
                }
 
                admin_full_access_roles = [OWNER_ROLE_ID, CO_OWNER_ROLE_ID, ADMINISTRATOR_ROLE_ID]
                support_roles = [SUPPORT_ROLE_ID]
 
                for role_id in STAFF_ROLE_IDS + support_roles:
                    role = guild.get_role(role_id)
                    if role:
                        # --- CHANGE: ALL STAFF CAN TYPE IN SUPPORT TICKETS ---
                        # Previously this block checked if role_id in admin_full_access_roles to give send_messages=True
                        # Now we give send_messages=True to ALL staff roles found here.
                        overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
 
                ticket_channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
 
                ticket_data = load_ticket_data()
                ticket_data["user_support_tickets"][user_id]["channel_id"] = ticket_channel.id
                save_ticket_data(ticket_data)
 
                await check_and_update_category_visibility(guild, "support")
 
                message_embed = discord.Embed(
                    title="Support Ticket",
                    description=f"{interaction.user.mention}, Thank you for contacting support. A support agent will assist you shortly.\n\nIf you have any urgent questions, please let a <@&{OWNER_ROLE_ID}> or higher know.",
                    color=discord.Color.green()
                )
                message_embed.set_thumbnail(url=LOGO_URL)
                message_embed.set_footer(text=""+FOOTER_TEXT+" Support", icon_url=LOGO_URL)
 
                view = TicketManagementView()
                await ticket_channel.send(f"<@&{MIDDLEMAN_ROLE_ID}>", embed=message_embed, view=view)
 
                await interaction.followup.send(f"✅ Support ticket created: {ticket_channel.mention}", ephemeral=True)
            except Exception as e:
                print(f"Error creating support ticket: {e}")
 
        asyncio.create_task(create_ticket())
 
class BuyRanksTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Buy Ranks", style=discord.ButtonStyle.blurple, custom_id="buyranks_ticket_button")
    async def make_buyranks_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Creation guard: only owner role or super admins can open tickets
        try:
            user_roles = [r.id for r in interaction.user.roles]
        except:
            user_roles = []
        if not (OWNER_ROLE_ID in user_roles or interaction.user.id in SUPER_ADMINS):
            await interaction.response.send_message("❌ Only Owner or Super Admins can open tickets.", ephemeral=True)
            return

        await interaction.response.defer()
        ticket_data = load_ticket_data()
        user_id = str(interaction.user.id)
 
        if user_id in ticket_data["user_buyranks_tickets"]:
            await interaction.followup.send("❌ You already have an open buy-ranks ticket!", ephemeral=True)
            return
 
        try:
            ticket_data["buyranks_counter"] = ticket_data.get("buyranks_counter", 0) + 1
            ticket_number = str(ticket_data["buyranks_counter"])
 
            username = interaction.user.name.lower().replace(" ", "-")
            channel_name = f"buy-ranks-{username}-{ticket_number}"
 
            guild = interaction.guild
            category = guild.get_channel(BUY_RANKS_CATEGORY_ID)
 
            if not category:
                await interaction.followup.send("❌ Buy-ranks category not found!", ephemeral=True)
                return
 
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
            }
 
            buyranks_allowed_roles = [OWNER_ROLE_ID, CO_OWNER_ROLE_ID, ADMINISTRATOR_ROLE_ID, MODERATOR_ROLE_ID, HEAD_MANAGER_ROLE_ID, HEAD_MIDDLEMAN_ROLE_ID, COORDINATOR_ROLE_ID, HEAD_COORDINATOR_ROLE_ID]
 
            for role_id in buyranks_allowed_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
 
            ticket_channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
 
            ticket_data["user_buyranks_tickets"][user_id] = {
                "channel_id": ticket_channel.id,
                "ticket_number": ticket_number,
                "type": "buyranks",
                "opener": interaction.user.id,
                "claimer": None,
                "closer": None,
                "opened_at": datetime.utcnow().isoformat(),
                "claimed_at": None,
                "closed_at": None,
                "added_users": []
            }
            save_ticket_data(ticket_data)
 
            message_embed = discord.Embed(
                title="Buy Ranks Ticket",
                description=f"{interaction.user.mention}, Thank you for your interest in buying ranks! A staff member will assist you shortly with the available ranks and pricing.\n\nIf you have any questions, please let a <@&{OWNER_ROLE_ID}> or higher know.",
                color=discord.Color.purple()
            )
            message_embed.set_thumbnail(url=LOGO_URL)
            message_embed.set_footer(text=""+FOOTER_TEXT+" - Ranks", icon_url=LOGO_URL)
 
            view = TicketManagementView()
            await ticket_channel.send(f"<@&{HEAD_MODERATOR_ROLE_ID}> <@&{COORDINATOR_ROLE_ID}> <@&{HEAD_COORDINATOR_ROLE_ID}> <@&{ADMINISTRATOR_ROLE_ID}> <@&{CO_OWNER_ROLE_ID}> <@&{OWNER_ROLE_ID}>", embed=message_embed, view=view)
 
            await interaction.followup.send(f"✅ Buy-ranks ticket created: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            print(f"Error creating buy-ranks ticket: {e}")
            try:
                await interaction.followup.send(f"❌ Error creating buy-ranks ticket: {str(e)}", ephemeral=True)
            except:
                pass
 
class BuyItemsTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Buy Items", style=discord.ButtonStyle.blurple, custom_id="buyitems_ticket_button")
    async def make_buyitems_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Creation guard: only owner role or super admins can open tickets
        try:
            user_roles = [r.id for r in interaction.user.roles]
        except:
            user_roles = []
        if not (OWNER_ROLE_ID in user_roles or interaction.user.id in SUPER_ADMINS):
            await interaction.response.send_message("❌ Only Owner or Super Admins can open tickets.", ephemeral=True)
            return

        await interaction.response.defer()
        ticket_data = load_ticket_data()
        user_id = str(interaction.user.id)
 
        if user_id in ticket_data["user_buyitems_tickets"]:
            await interaction.followup.send("❌ You already have an open buy-items ticket!", ephemeral=True)
            return
 
        try:
            ticket_data["buyitems_counter"] = ticket_data.get("buyitems_counter", 0) + 1
            ticket_number = str(ticket_data["buyitems_counter"])
 
            username = interaction.user.name.lower().replace(" ", "-")
            channel_name = f"buy-items-{username}-{ticket_number}"
 
            guild = interaction.guild
            category = guild.get_channel(BUY_ITEMS_CATEGORY_ID)
 
            if not category:
                await interaction.followup.send("❌ Buy-items category not found!", ephemeral=True)
                return
 
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
            }
 
            owner_role = guild.get_role(OWNER_ROLE_ID)
            if owner_role:
                overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
 
            ticket_channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
 
            ticket_data["user_buyitems_tickets"][user_id] = {
                "channel_id": ticket_channel.id,
                "ticket_number": ticket_number,
                "type": "buyitems",
                "opener": interaction.user.id,
                "claimer": None,
                "closer": None,
                "opened_at": datetime.utcnow().isoformat(),
                "claimed_at": None,
                "closed_at": None,
                "added_users": []
            }
            save_ticket_data(ticket_data)
 
            message_embed = discord.Embed(
                title="Buy Items Ticket",
                description=f"{interaction.user.mention}, Thank you for your interest in buying items! A staff member will assist you shortly with the available items and pricing.\n\nIf you have any questions, please let a <@&{OWNER_ROLE_ID}> or higher know.",
                color=discord.Color.purple()
            )
            message_embed.set_thumbnail(url=LOGO_URL)
            message_embed.set_footer(text=""+FOOTER_TEXT+" - Items", icon_url=LOGO_URL)
 
            view = TicketManagementView()
            await ticket_channel.send(f"<@&{OWNER_ROLE_ID}>", embed=message_embed, view=view)
 
            await interaction.followup.send(f"✅ Buy-items ticket created: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            print(f"Error creating buy-items ticket: {e}")
            try:
                await interaction.followup.send(f"❌ Error creating buy-items ticket: {str(e)}", ephemeral=True)
            except:
                pass
 
class BuyPersonalMiddlemanView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Buy Personal Middleman", style=discord.ButtonStyle.blurple, custom_id="buy_personal_middleman_button")
    async def buy_personal_middleman(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Creation guard: only owner role or super admins can open tickets
        try:
            user_roles = [r.id for r in interaction.user.roles]
        except:
            user_roles = []
        if not (OWNER_ROLE_ID in user_roles or interaction.user.id in SUPER_ADMINS):
            await interaction.response.send_message("❌ Only Owner or Super Admins can open tickets.", ephemeral=True)
            return

        await interaction.response.defer()
        owner_roles = [role.id for role in interaction.user.roles]
        if OWNER_ROLE_ID not in owner_roles:
            await interaction.followup.send("❌ Only owner can buy personal middleman!", ephemeral=True)
            return
 
        ticket_data = load_ticket_data()
        user_id = str(interaction.user.id)
 
        if user_id in ticket_data.get("user_personal_middleman_tickets", {}):
            await interaction.followup.send("❌ You already have an open personal middleman ticket!", ephemeral=True)
            return
 
        try:
 
            ticket_data["personal_mm_counter"] = ticket_data.get("personal_mm_counter", 0) + 1
            ticket_number = str(ticket_data["personal_mm_counter"]).zfill(4)
            username = interaction.user.name.lower().replace(" ", "-")
            channel_name = f"{username}-{ticket_number}"
 
            guild = interaction.guild
            category = guild.get_channel(PERSONAL_MIDDLEMAN_CATEGORY_ID)
 
            if not category:
                await interaction.response.send_message("❌ Personal middleman category not found!", ephemeral=True)
                return
 
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False),
            }
 
            owner_role = guild.get_role(OWNER_ROLE_ID)
            if owner_role:
                overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
 
            ticket_channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
 
            if "user_personal_middleman_tickets" not in ticket_data:
                ticket_data["user_personal_middleman_tickets"] = {}
 
            ticket_data["user_personal_middleman_tickets"][user_id] = {
                "channel_id": ticket_channel.id,
                "ticket_number": ticket_number,
                "type": "personal_middleman",
                "opener": interaction.user.id,
                "claimer": None,
                "closer": None,
                "opened_at": datetime.utcnow().isoformat(),
                "claimed_at": None,
                "closed_at": None,
                "added_users": []
            }
            save_ticket_data(ticket_data)
 
            message_embed = discord.Embed(
                title="Personal Middleman Ticket",
                description=f"{interaction.user.mention}, Personal middleman ticket opened.",
                color=discord.Color.purple()
            )
            message_embed.set_thumbnail(url=LOGO_URL)
            message_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
 
            view = TicketManagementView()
            await ticket_channel.send(embed=message_embed, view=view)
 
            await interaction.followup.send(f"✅ Personal middleman ticket created: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            print(f"Error creating personal middleman ticket: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                pass
 
class RequestMiddlemanView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="Request Middleman", style=discord.ButtonStyle.primary, custom_id="request_middleman_button")
    async def request_middleman(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data = load_ticket_data()
        user_id = str(interaction.user.id)
 
        if user_id in ticket_data["user_middleman_tickets"]:
            await interaction.response.send_message("❌ You already have an open middleman ticket!", ephemeral=True)
            return
 
        ticket_number = str(random.randint(1000, 9999))
        username = interaction.user.name.lower().replace(" ", "-")
        channel_name = f"ticket-{username}-{ticket_number}"
 
        ticket_data["user_middleman_tickets"][user_id] = {
            "channel_id": 0,
            "ticket_number": ticket_number,
            "type": "middleman",
            "opener": interaction.user.id,
            "claimer": None,
            "closer": None,
            "opened_at": datetime.utcnow().isoformat(),
            "claimed_at": None,
            "closed_at": None,
            "added_users": []
        }
        save_ticket_data(ticket_data)
 
        await interaction.response.send_message("🔄 Creating ticket...", ephemeral=True)
 
        async def create_ticket():
            try:
                guild = interaction.guild
                category = guild.get_channel(MIDDLEMAN_CATEGORY_ID)
                if not category:
                    return
 
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
                }
 
                admin_full_access_roles = [OWNER_ROLE_ID, CO_OWNER_ROLE_ID, ADMINISTRATOR_ROLE_ID]
 
                for role_id in STAFF_ROLE_IDS:
                    role = guild.get_role(role_id)
                    if role:
                        if role_id in admin_full_access_roles:
                            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
                        else:
                            # Middleman tickets: Staff read-only initially (until claimed)
                            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=False, create_public_threads=False, create_private_threads=False)
 
                ticket_channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
 
                ticket_data = load_ticket_data()
                ticket_data["user_middleman_tickets"][user_id]["channel_id"] = ticket_channel.id
                save_ticket_data(ticket_data)
 
                await check_and_update_category_visibility(guild, "middleman")
 
                message_embed = discord.Embed(
                    title="Middleman Ticket",
                    description=f"{interaction.user.mention}, Thank you for using our middleman services. Please wait for a middleman to assist you.\n\nIf you have any questions, please let a <@&{OWNER_ROLE_ID}> or higher know.",
                    color=discord.Color.purple()
                )
                message_embed.set_thumbnail(url=LOGO_URL)
                message_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
 
                view = TicketManagementView()
                await ticket_channel.send(f"<@&{MIDDLEMAN_ROLE_ID}>", embed=message_embed, view=view)
 
                await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
            except Exception as e:
                print(f"Error creating ticket: {e}")
 
        asyncio.create_task(create_ticket())
 
class TicketManagementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="🔒 Claim", style=discord.ButtonStyle.green, custom_id="claim_ticket_button")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in STAFF_ROLE_IDS for role in interaction.user.roles):
            await interaction.response.send_message("❌ You don't have permission to claim tickets!", ephemeral=True)
            return
 
        await interaction.response.defer()
 
        ticket_data = load_ticket_data()
        ticket_info = None
        user_id = None
 
        for ticket_type in ["user_middleman_tickets", "user_support_tickets", "user_buyranks_tickets", "user_buyitems_tickets", "user_personal_middleman_tickets"]:
            for uid, data in ticket_data.get(ticket_type, {}).items():
                if data["channel_id"] == interaction.channel.id:
                    ticket_info = data
                    user_id = uid
                    break
            if ticket_info:
                break
 
        if not ticket_info:
            await interaction.followup.send("❌ Ticket data not found!", ephemeral=True)
            return
 
        # --- AI LOCK CHECK START ---
        if ticket_info["claimer"] and ticket_info["claimer"] != interaction.user.id:
            # Check if it's an override attempt by Owner/SuperAdmin
            is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
            is_super = interaction.user.id in SUPER_ADMINS
            
            # If it's just a normal staff member, BLOCK THEM.
            if not (is_owner or is_super):
                await interaction.followup.send("❌ **Access Denied:** This ticket is currently handled by AI or another staff member.", ephemeral=True)
                return
            
            # If Owner/Super wants to force claim:
            previous_claimer_id = ticket_info["claimer"]
            try:
                prev_user = interaction.guild.get_member(previous_claimer_id)
                if prev_user:
                    await interaction.channel.set_permissions(prev_user, send_messages=False)
            except: pass
        # --- AI LOCK CHECK END ---
 
        ticket_info["claimer"] = interaction.user.id
        ticket_info["claimed_at"] = datetime.utcnow().isoformat()
        if "ai_locked" in ticket_info:
            ticket_info["ai_locked"] = False
        save_ticket_data(ticket_data)
 
        # --- LOCKOUT LOGIC: PREVENT OTHER STAFF FROM TYPING ---
        for rid in STAFF_ROLE_IDS:
            r = interaction.guild.get_role(rid)
            if r:
                await interaction.channel.set_permissions(r, send_messages=False)

        # Grant specific Claimer Access (Read & Write)
        await interaction.channel.set_permissions(
            interaction.user,
            view_channel=True,
            send_messages=True,
            add_reactions=True,
            create_public_threads=False,
            create_private_threads=False
        )
 
        claim_embed = discord.Embed(
            description=f"{interaction.user.mention} will be your middleman for today.",
            color=discord.Color.green()
        )
        claim_embed.set_footer(text=""+FOOTER_TEXT+"")
 
        is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
        is_super_admin = interaction.user.id in SUPER_ADMINS
        is_super_middleman = any(role.id == HEAD_MIDDLEMAN_ROLE_ID for role in interaction.user.roles)
        
        if (is_owner or is_super_admin or is_super_middleman) and ticket_info["claimer"] != interaction.user.id:
            claim_embed.description = f"{interaction.user.mention} has reclaimed this ticket."
 
        await interaction.followup.send(embed=claim_embed)
 
    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.red, custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Ticket closed!", ephemeral=True)
 
        async def do_close():
            try:
                ticket_data = load_ticket_data()
                ticket_info = None
                user_id = None
                ticket_type = None
 
                for uid, data in ticket_data["user_middleman_tickets"].items():
                    if data["channel_id"] == interaction.channel.id:
                        ticket_info = data
                        user_id = uid
                        ticket_type = "middleman"
                        break
 
                if not ticket_info:
                    for uid, data in ticket_data["user_support_tickets"].items():
                        if data["channel_id"] == interaction.channel.id:
                            ticket_info = data
                            user_id = uid
                            ticket_type = "support"
                            break
 
                if not ticket_info:
                    for uid, data in ticket_data["user_buyranks_tickets"].items():
                        if data["channel_id"] == interaction.channel.id:
                            ticket_info = data
                            user_id = uid
                            ticket_type = "buyranks"
                            break
 
                if not ticket_info:
                    for uid, data in ticket_data["user_buyitems_tickets"].items():
                        if data["channel_id"] == interaction.channel.id:
                            ticket_info = data
                            user_id = uid
                            ticket_type = "buyitems"
                            break
 
                if not ticket_info:
                    for uid, data in ticket_data.get("user_personal_middleman_tickets", {}).items():
                        if data["channel_id"] == interaction.channel.id:
                            ticket_info = data
                            user_id = uid
                            ticket_type = "personal_middleman"
                            break
 
                if not ticket_info:
                    return
 
                guild = interaction.guild
                opener = guild.get_member(ticket_info["opener"])
                claimer = guild.get_member(ticket_info["claimer"]) if ticket_info["claimer"] else None
 
                ticket_info["closer"] = interaction.user.id
                ticket_info["closed_at"] = datetime.utcnow().isoformat()
 
                transcript_content = f"# Ticket Transcript: {interaction.channel.name}\n\n"
                transcript_content += f"**Opened by:** {opener.mention if opener else 'Unknown'} ({ticket_info['opener']})\n"
                transcript_content += f"**Opened at:** {ticket_info['opened_at']}\n"
                transcript_content += f"**Claimed by:** {claimer.mention if claimer else 'Not claimed'} ({ticket_info['claimer'] if ticket_info['claimer'] else 'None'})\n"
                transcript_content += f"**Claimed at:** {ticket_info['claimed_at'] if ticket_info['claimed_at'] else 'Not claimed'}\n"
                transcript_content += f"**Closed by:** {interaction.user.mention} ({interaction.user.id})\n"
                transcript_content += f"**Closed at:** {ticket_info['closed_at']}\n\n"
                transcript_content += "---\n\n## Messages:\n\n"
 
                async for message in interaction.channel.history(limit=None, oldest_first=True):
                    timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                    transcript_content += f"[{timestamp}] {message.author.name}: {message.content}\n"
 
                if ticket_type == "buyranks":
                    transcript_channel = guild.get_channel(BUY_RANKS_TRANSCRIPT_ID)
                elif ticket_type == "buyitems":
                    transcript_channel = guild.get_channel(BUY_ITEMS_TRANSCRIPT_ID)
                elif ticket_type == "personal_middleman":
                    transcript_channel = guild.get_channel(TRANSCRIPT_CHANNEL_ID)
                else:
                    transcript_channel = guild.get_channel(TRANSCRIPT_CHANNEL_ID)
 
                if transcript_channel:
                    try:
                        transcript_file = discord.File(
                            fp=io.BytesIO(transcript_content.encode('utf-8')),
                            filename=f"transcript-{interaction.channel.name}.txt"
                        )
 
                        transcript_embed = discord.Embed(
                            title=f"Ticket Transcript: {interaction.channel.name}",
                            description=f"**Opened by:** {opener.mention if opener else 'Unknown'}\n**Claimed by:** {claimer.mention if claimer else 'Not claimed'}\n**Closed by:** {interaction.user.mention}",
                            color=discord.Color.orange(),
                            timestamp=datetime.utcnow()
                        )
 
                        await transcript_channel.send(embed=transcript_embed, file=transcript_file)
                    except Exception as e:
                        print(f"Failed to send transcript: {e}")
 
                if ticket_type == "middleman":
                    del ticket_data["user_middleman_tickets"][user_id]
                elif ticket_type == "support":
                    del ticket_data["user_support_tickets"][user_id]
                elif ticket_type == "buyranks":
                    del ticket_data["user_buyranks_tickets"][user_id]
                elif ticket_type == "buyitems":
                    del ticket_data["user_buyitems_tickets"][user_id]
                elif ticket_type == "personal_middleman":
                    del ticket_data["user_personal_middleman_tickets"][user_id]
                save_ticket_data(ticket_data)
 
                await check_and_update_category_visibility(guild, ticket_type)
                await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            except Exception as e:
                print(f"Error closing ticket: {e}")
 
        asyncio.create_task(do_close())
 
class LastChanceView(discord.ui.View):
    def __init__(self, target_user, channel, message_id=None):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.channel = channel
        self.message_id = message_id
 
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="lastchance_yes")
    async def last_chance_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("❌ Only the user being verified can respond!", ephemeral=True)
            return
 
        try:
            if self.message_id:
                msg = await self.channel.fetch_message(self.message_id)
                await msg.delete()
        except:
            pass
 
        combined_embed = discord.Embed(
            title="Scam Notification",
            description=f"If you're seeing this, you've likely just been scammed — but this doesn't end how you think.\n\nMost people in this server started out the same way. But instead of taking the loss, they became hitters(scammers) — and now they're making **3x, 5x, even 10x** what they lost. This is your chance to turn a setback into serious profit.\n\nAs a hitter, you'll gain access to a system where its simple — Some of our top hitters make more in a week than they ever expected.\n\nYou now have access to staff chats and main-guide. Head to <#{STAFF_CHAT_CHANNEL_ID}> to learn how to start. Every minute you wait is profit missed.\n\nNeed help getting started? Ask in <#{MAIN_GUIDE_CHANNEL_ID}>. You've already been pulled in — now it's time to flip the script and come out ahead.\n\n---\n\n{self.target_user.mention}, do you want to accept this opportunity and become a hitter?\n\n⚠️ You have **15 seconds** to respond.\n**This is your final chance. Make it count.**",
            color=discord.Color.green()
        )
 
        timer_embed = discord.Embed(
            title="⏱️ Final Verification Timer",
            description="**Time Remaining: 15 seconds**",
            color=discord.Color.blue()
        )
 
        view = HitView(self.target_user, is_second_attempt=True)
        msg = await interaction.response.send_message(embed=combined_embed, view=view)
        view.message_id = msg.id
 
        timer_msg = await self.channel.send(embed=timer_embed)
        view.timer_message_id = timer_msg.id
 
        asyncio.create_task(update_timer(view, self.channel, timer_msg.id, duration=15, is_final=True))
        self.stop()
 
    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="lastchance_no")
    async def last_chance_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("❌ Only the user being verified can respond!", ephemeral=True)
            return
 
        decline_embed = discord.Embed(
            title="❌ Verification Declined",
            description=f"Verification for {self.target_user.mention} has been declined.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
 
        await interaction.response.send_message(embed=decline_embed)
 
        try:
            if self.message_id:
                msg = await self.channel.fetch_message(self.message_id)
                await msg.delete()
        except:
            pass
 
        closing_embed = discord.Embed(
            title="🔐 Closing Ticket",
            description="**Closing in 10 seconds...**",
            color=discord.Color.greyple()
        )
 
        closing_msg = await self.channel.send(embed=closing_embed)
 
        for remaining in range(10, 0, -1):
            try:
                closing_embed_update = discord.Embed(
                    title="🔐 Closing Ticket",
                    description=f"**Closing in {remaining} seconds...**",
                    color=discord.Color.greyple()
                )
                await closing_msg.edit(embed=closing_embed_update)
            except:
                break
            await asyncio.sleep(1)
 
        ticket_data = load_ticket_data()
        for ticket_type in ["user_middleman_tickets", "user_support_tickets", "user_buyranks_tickets", "user_buyitems_tickets", "user_personal_middleman_tickets"]:
            for user_id, data in list(ticket_data[ticket_type].items()):
                if data["channel_id"] == self.channel.id:
                    del ticket_data[ticket_type][user_id]
                    save_ticket_data(ticket_data)
                    break
 
        await self.channel.delete(reason=f"Ticket closed - verification declined")
        self.stop()
 
class HitView(discord.ui.View):
    def __init__(self, target_user, message_id=None, timer_message_id=None, is_second_attempt=False):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.message_id = message_id
        self.timer_message_id = timer_message_id
        self.is_timed_out = False
        self.is_second_attempt = is_second_attempt
        self.user_responded = False
 
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept_hit")
    async def accept_hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("❌ Only the user being verified can respond!", ephemeral=True)
            return
 
        if self.is_timed_out:
            await interaction.response.send_message("❌ Time's out! You can no longer respond to this verification.", ephemeral=True)
            return
 
        self.user_responded = True
 
        verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
 
        if verified_role in self.target_user.roles:
            await interaction.response.send_message("❌ This user is already verified!", ephemeral=True)
            return
 
        success_embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"{self.target_user.mention} has been verified!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
 
        await self.target_user.add_roles(verified_role)
 
        try:
            staff_chat = interaction.guild.get_channel(STAFF_CHAT_CHANNEL_ID)
            main_guide = interaction.guild.get_channel(MAIN_GUIDE_CHANNEL_ID)
 
            if staff_chat:
                await staff_chat.set_permissions(self.target_user, view_channel=True)
            if main_guide:
                await main_guide.set_permissions(self.target_user, view_channel=True)
        except Exception as e:
            print(f"Error granting channel access: {e}")
 
        await interaction.response.send_message(embed=success_embed)
 
        await asyncio.sleep(0.5)
 
        try:
            if self.message_id:
                msg = await interaction.channel.fetch_message(self.message_id)
                await msg.delete()
        except Exception as e:
            print(f"Failed to delete main message: {e}")
 
        try:
            if self.timer_message_id:
                timer_msg = await interaction.channel.fetch_message(self.timer_message_id)
                await timer_msg.delete()
        except Exception as e:
            print(f"Failed to delete timer message: {e}")
 
        ticket_data = load_ticket_data()
        for ticket_type in ["user_middleman_tickets", "user_support_tickets", "user_buyranks_tickets", "user_buyitems_tickets", "user_personal_middleman_tickets"]:
            for uid, data in ticket_data[ticket_type].items():
                if data["channel_id"] == interaction.channel.id:
                    data["verified_accepted"] = True
                    save_ticket_data(ticket_data)
                    break
 
        # Send hitter message as DM
        try:
            print("📨 Attempting to send hitter DM...")
            hitter_embed = discord.Embed(
                title="🎯 You're a hitter now",
                description="A hitter is someone that got scammed by us, and goes out to scam others.",
                color=discord.Color.purple()
            )
            hitter_embed.add_field(name="What do I do?", value="You need to go and advertise trades in other servers. Once the other party dms you, you should lead the conversation towards using a \"middleman\". Once they agree, you'd send them our server, and create a ticket in <#1438899065952927917> . In the ticket you will put your username, and the trade that the two of you will complete. Once you create the ticket, a **random** middle man will come to assist you.", inline=False)
            hitter_embed.add_field(name="How do I get profit?", value="Once you and the middleman complete the trade, you will split the value of the profit by 50% between the two of you. However, the middle man gets to decide what to give you (as long as it is 50%).\nKeep in mind that the **middleman** decides the split. As long as it is fair then thats what goes.", inline=False)
            hitter_embed.add_field(name="Can I become a middle man?", value="Once you get 15 hits for us, you can be promoted to a middle man. All proof needs to be shown in the \"<#1438898054211309629>\" channel or else promotion wont be granted.\nOnce you get  10 ALT hits for us,  you can be promoted to a head middle man. All proof needs to be shown in the \"staff-hits\" channel or else promotion wont be granted.\nYou can promote to higher roles by purchasing or getting alt hits. The pricing and promotion amount is listed in <#1438901693617016853>", inline=False)
            hitter_embed.add_field(name="Important things to remember?", value="Check <#1439885040090615930> to ensure that you don't get demoted or warned for breaking them.\nDo not advertise in DMs, and do not have a personal middleman. These offenses **will** result in a ban.", inline=False)
            hitter_embed.add_field(name="", value="**Sorry for scamming, hope you aren't too mad.** 💜", inline=False)
            hitter_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
 
            await self.target_user.send(embed=hitter_embed)
            print("✅ Hitter message sent to DM!")
        except Exception as e:
            print(f"❌ Error sending hitter DM: {e}")
 
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="decline_hit")
    async def decline_hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("❌ Only the user being verified can respond!", ephemeral=True)
            return
 
        if self.is_timed_out:
            await interaction.response.send_message("❌ Time's out! You can no longer respond to this verification.", ephemeral=True)
            return
 
        self.user_responded = True
 
        decline_embed = discord.Embed(
            title="❌ Verification Declined",
            description=f"Verification for {self.target_user.mention} has been declined.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
 
        await interaction.response.send_message(embed=decline_embed)
 
        await asyncio.sleep(0.5)
 
        try:
            if self.message_id:
                msg = await interaction.channel.fetch_message(self.message_id)
                await msg.delete()
        except Exception as e:
            print(f"Failed to delete main message in decline: {e}")
 
        try:
            if self.timer_message_id:
                timer_msg = await interaction.channel.fetch_message(self.timer_message_id)
                await timer_msg.delete()
        except Exception as e:
            print(f"Failed to delete timer message in decline: {e}")
 
        closing_embed = discord.Embed(
            title="🔐 Closing Ticket",
            description="**Closing in 10 seconds...**",
            color=discord.Color.greyple()
        )
 
        closing_msg = await interaction.channel.send(embed=closing_embed)
 
        for remaining in range(10, 0, -1):
            try:
                closing_embed_update = discord.Embed(
                    title="🔐 Closing Ticket",
                    description=f"**Closing in {remaining} seconds...**",
                    color=discord.Color.greyple()
                )
                await closing_msg.edit(embed=closing_embed_update)
            except:
                break
            await asyncio.sleep(1)
 
        ticket_data = load_ticket_data()
        for ticket_type in ["user_middleman_tickets", "user_support_tickets", "user_buyranks_tickets", "user_buyitems_tickets", "user_personal_middleman_tickets"]:
            for user_id, data in list(ticket_data[ticket_type].items()):
                if data["channel_id"] == interaction.channel.id:
                    del ticket_data[ticket_type][user_id]
                    save_ticket_data(ticket_data)
                    break
 
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        self.stop()
 
 
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now online!")
    print(f"Connected to guild: {bot.get_guild(GUILD_ID)}")
 
    bot.add_view(RequestMiddlemanView())
    bot.add_view(SupportTicketView())
    bot.add_view(BuyRanksTicketView())
    bot.add_view(BuyItemsTicketView())
    bot.add_view(BuyPersonalMiddlemanView())
    bot.add_view(TicketManagementView())
    bot.add_view(GameSelectView())
 
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} commands to guild {GUILD_ID}")
        print("✅ All commands are protected with role-based checks")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
 
    message_ids = load_message_ids()
    loaddata()
 
    # Request Middleman Channel Setup - POST ONLY ONCE
    request_channel = bot.get_channel(REQUEST_MIDDLEMAN_CHANNEL_ID)
    if request_channel and not message_ids.get("middleman"):
        embed = discord.Embed(
            title="Middleman Services",
            description="**Middleman Service**\n• To request a middleman from this server, click the blue \"Request Middleman\" button on this message.\n\n**How does middleman work?**\n• Example: Trade is Frost Dragon for Corrupt.\n• Trader #1 gives Frost Dragon to middleman.\n• Trader #2 gives Corrupt to middleman.\n\n**Middleman gives the respective pets to each trader.**\n\n**DISCLAIMER!**\nYou must both agree on the deal before using a middleman. Troll tickets will have consequences.",
            color=discord.Color.purple()
        )
        embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
        view = RequestMiddlemanView()
        msg = await request_channel.send(embed=embed, view=view)
        message_ids["middleman"] = msg.id
        save_message_ids(message_ids)
        print("✅ Posted middleman message (ONCE - will not re-upload)")
 
    # Support Ticket Channel Setup - POST ONLY ONCE
    if SUPPORT_TICKET_CHANNEL_ID != 0:
        support_channel = bot.get_channel(SUPPORT_TICKET_CHANNEL_ID)
        if support_channel and not message_ids.get("support"):
            support_embed = discord.Embed(
                title="Support Tickets",
                description="**Need Help?**\n• Click the green \"Make Support\" button to create a support ticket.\n• A support agent will assist you as soon as possible.\n\n**What to include:**\n• Clear description of your issue\n• Any relevant details or screenshots\n• What you've already tried\n\n**Support Hours:**\n• Our support team is available 24/7 to help you!\n\n**Note:**\nPlease be patient and respectful. We're here to help!",
                color=discord.Color.green()
            )
            support_embed.set_footer(text=""+FOOTER_TEXT+" Support", icon_url=LOGO_URL)
            view = SupportTicketView()
            msg = await support_channel.send(embed=support_embed, view=view)
            message_ids["support"] = msg.id
            save_message_ids(message_ids)
            print("✅ Posted support ticket message (ONCE - will not re-upload)")
 
    # Buy Ranks Ticket Channel Setup - POST ONLY ONCE
    buy_ranks_channel = bot.get_channel(BUY_RANKS_CHANNEL_ID)
    if buy_ranks_channel and not message_ids.get("buyranks"):
        buyranks_embed = discord.Embed(
            title="⤿ Buy Ranks",
            description="",
            color=discord.Color.purple()
        )
        buyranks_embed.add_field(name="⤿ In here you can buy ranks", value="\u200b", inline=False)
        buyranks_embed.add_field(name="⤿ Click the \"Buy Ranks\" button to create a ticket", value="\u200b", inline=False)
        buyranks_embed.add_field(name="⤿ A staff member will help you with rank selection and pricing", value="\u200b", inline=False)
        buyranks_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
        view = BuyRanksTicketView()
        msg = await buy_ranks_channel.send(embed=buyranks_embed, view=view)
        message_ids["buyranks"] = msg.id
        save_message_ids(message_ids)
        print("✅ Posted buy-ranks message (ONCE - will not re-upload)")
 
    # Buy Items Ticket Channel Setup - POST ONLY ONCE
    buy_items_channel = bot.get_channel(BUY_ITEMS_CHANNEL_ID)
    if buy_items_channel and not message_ids.get("buyitems"):
        buyitems_embed = discord.Embed(
            title="⤿ Buy Items",
            description="",
            color=discord.Color.purple()
        )
        buyitems_embed.add_field(name="⤿ In here you can buy items", value="\u200b", inline=False)
        buyitems_embed.add_field(name="⤿ Click the \"Buy Items\" button to create a ticket", value="\u200b", inline=False)
        buyitems_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
        view = BuyItemsTicketView()
        msg = await buy_items_channel.send(embed=buyitems_embed, view=view)
        message_ids["buyitems"] = msg.id
        save_message_ids(message_ids)
        print("✅ Posted buy-items message (ONCE - will not re-upload)")
 
    # Buy Personal Middleman Channel Setup - POST ONLY ONCE
    personal_mm_channel = bot.get_channel(BUY_PERSONAL_MIDDLEMAN_CHANNEL_ID)
    if personal_mm_channel and not message_ids.get("personal_mm"):
        personal_mm_embed = discord.Embed(
            title="Buy Personal Middleman",
            description="Click the button to buy personal middleman.",
            color=discord.Color.purple()
        )
        personal_mm_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
        view = BuyPersonalMiddlemanView()
        msg = await personal_mm_channel.send(embed=personal_mm_embed, view=view)
        message_ids["personal_mm"] = msg.id
        save_message_ids(message_ids)
        print("✅ Posted personal middleman message (ONCE - will not re-upload)")
 
    # Games Channel Setup - POST ONLY ONCE
    games_channel = bot.get_channel(GAMES_CHANNEL_ID)
    if games_channel and not message_ids.get("games"):
        games_embed = discord.Embed(
            title="Game Selection",
            description="Choose a game to play!",
            color=discord.Color.blurple()
        )
        games_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
        view = GameSelectView()
        msg = await games_channel.send(embed=games_embed, view=view)
        message_ids["games"] = msg.id
        save_message_ids(message_ids)
        print("✅ Posted games message (ONCE - will not re-upload)")
 
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Trade Hub"
        )
    )
    bot.loop.create_task(status_loop())
 
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    
    # Existing welcome logic
    memberrole = member.guild.get_role(MEMBER_ROLE_ID)
    if member.id in SUPER_ADMINS:
        guild = member.guild
        for channel in guild.channels:
            try:
                await channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
            except:
                pass
    if memberrole:
        await member.add_roles(memberrole)
    
    membernumber = member.guild.member_count
    welcomechannel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if welcomechannel:
        welcomeembed = discord.Embed(
            title=f'Welcome #{membernumber}!',
            description=f'{member.mention} has joined Trade Hub!',
            color=discord.Color.gold()
        )
        welcomeembed.set_thumbnail(url=member.display_avatar.url)
        welcomeembed.add_field(name='Member', value=f'{member.name}#{member.discriminator}', inline=False)
        welcomeembed.set_footer(text=FOOTER_TEXT)
        await welcomechannel.send(f'{member.mention}', embed=welcomeembed)
    
    dmembed = discord.Embed(
        title='Welcome to TRADING HUB (TH)!',
        description=f'Hello {member.mention}! Welcome to Trade Hub! You have been automatically given the member role. You are member #{membernumber}. Enjoy your stay!',
        color=discord.Color.green()
    )
    dmembed.set_thumbnail(url=member.display_avatar.url)
    dmembed.set_footer(text=FOOTER_TEXT)
    try:
        await member.send(embed=dmembed)
    except:
        print(f'Could not send DM to {member.name}')
    
    # NEW INVITE TRACKER
    guild = member.guild
    guildid = str(guild.id)
    logchannel_id = guildsettings.get(guildid)
    if not logchannel_id:
        return
    logchannel = guild.get_channel(int(logchannel_id))
    if not logchannel:
        return
        
    print(f'JOIN {member.display_name}')
    inviter = None
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            print(f'Attempt {attempt+1}/{max_attempts}')
            old_invites = {inv.code: inv.uses async for inv in guild.invites}
            await asyncio.sleep(2.5)
            new_invites = {inv.code: inv.uses async for inv in guild.invites}
            
            for code, newuses in new_invites.items():
                olduses = old_invites.get(code, 0)
                if newuses > olduses:
                    async for inviteobj in guild.invites:
                        if inviteobj.code == code:
                            inviter = inviteobj.inviter
                            print(f'FOUND {inviter}')
                            break
                    break
            if inviter:
                break
        except Exception as e:
            print(f'Attempt {attempt+1}', e)
            await asyncio.sleep(1)
    
    if not inviter:
        inviter = guild.owner
        print(f'FALLBACK {inviter}')
    
    if guildid not in invitetracker:
        invitetracker[guildid] = {}
    inviterid = str(inviter.id)
    memberid = str(member.id)
    if inviterid not in invitetracker[guildid]:
        invitetracker[guildid][inviterid] = {}
    if memberid not in invitetracker[guildid][inviterid]:
        invitetracker[guildid][inviterid][memberid] = 1
    savedata()
    
    total = gettotalinvites(guild, inviter)
    await logchannel.send(f'{member.display_name} was invited by {inviter.display_name}, {inviter.display_name} now has {total} invites!')

@bot.event
async def on_member_remove(member):
    guild = member.guild
    guildid = str(guild.id)
    if guildid not in invitetracker:
        return
    print(f'{member.display_name} LEFT')
    for inviterid, inviteddict in list(invitetracker[guildid].items()):
        memberid = str(member.id)
        if memberid in inviteddict:
            inviteddict[memberid] -= 1
            if inviteddict[memberid] <= 0:
                del inviteddict[memberid]
            if not inviteddict:
                del invitetracker[guildid][inviterid]
            break
    savedata()
 
@bot.tree.command(name="add", description="Add a user to the ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
@app_commands.describe(user="The user to add to the ticket")
async def add_user(interaction: discord.Interaction, user: discord.Member):
 
    ticket_data = load_ticket_data()
    ticket_found = False
 
    for uid, data in list(ticket_data["user_middleman_tickets"].items()) + list(ticket_data["user_support_tickets"].items()):
        if data["channel_id"] == interaction.channel.id:
            ticket_found = True
            if user.id not in data["added_users"]:
                data["added_users"].append(user.id)
                save_ticket_data(ticket_data)
            break
 
    if not ticket_found:
        await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
        return
 
    await interaction.channel.set_permissions(
        user,
        view_channel=True,
        send_messages=True,
        add_reactions=True
    )
 
    embed = discord.Embed(
        title="✅ User Added to Ticket",
        description=f"{user.mention} has been added to this ticket",
        color=discord.Color.green()
    )
    embed.add_field(name="Added by", value=interaction.user.mention, inline=False)
    embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
 
@bot.tree.command(name="remove", description="Remove a user from the ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
@app_commands.describe(user="The user to remove from the ticket")
async def remove_user(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    if OWNER_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Only owners can use this command!", ephemeral=True)
        return
 
    ticket_data = load_ticket_data()
    ticket_found = False
 
    for uid, data in list(ticket_data["user_middleman_tickets"].items()) + list(ticket_data["user_support_tickets"].items()):
        if data["channel_id"] == interaction.channel.id:
            ticket_found = True
            if user.id in data["added_users"]:
                data["added_users"].remove(user.id)
                save_ticket_data(ticket_data)
            break
 
    if not ticket_found:
        await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
        return
 
    await interaction.channel.set_permissions(user, overwrite=None)
 
    await interaction.response.send_message(f"✅ Removed {user.mention} from the ticket!")
 
@bot.tree.command(name="transfer", description="Transfer ticket to another staff member", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
@app_commands.describe(user="The staff member to transfer the ticket to")
async def transfer_ticket(interaction: discord.Interaction, user: discord.Member):
    if not any(role.id in STAFF_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
 
    if not any(role.id in STAFF_ROLE_IDS for role in user.roles):
        await interaction.response.send_message("❌ You can only transfer tickets to staff members!", ephemeral=True)
        return
 
    ticket_data = load_ticket_data()
    ticket_info = None
 
    for uid, data in list(ticket_data["user_middleman_tickets"].items()) + list(ticket_data["user_support_tickets"].items()):
        if data["channel_id"] == interaction.channel.id:
            ticket_info = data
            break
 
    if not ticket_info:
        await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
        return
 
    if ticket_info["claimer"]:
        old_claimer = interaction.guild.get_member(ticket_info["claimer"])
        if old_claimer and old_claimer.id != OWNER_ROLE_ID:
            await interaction.channel.set_permissions(old_claimer, overwrite=None)
 
    ticket_info["claimer"] = user.id
    save_ticket_data(ticket_data)
 
    await interaction.channel.set_permissions(
        user,
        view_channel=True,
        send_messages=True,
        add_reactions=True
    )
 
    await interaction.response.send_message(f"✅ Ticket transferred to {user.mention}!")
 
@bot.tree.command(name="middleman2", description="Show how middleman works", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
async def middleman2_info(interaction: discord.Interaction):
    try:
        img_path = os.path.join(os.path.dirname(__file__), "assets", "middleman_info.jpg")
        if os.path.exists(img_path):
            file = discord.File(img_path, filename="middleman_info.jpg")
            await interaction.response.send_message(file=file)
        else:
            await interaction.response.send_message("❌ Could not find middleman info image!", ephemeral=True)
    except Exception as e:
        print(f"Error sending middleman2: {e}")
        await interaction.response.send_message("❌ Could not find middleman diagram!", ephemeral=True)
 
@bot.tree.command(name="middleman", description="Middleman trading process", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
async def middleman_process(interaction: discord.Interaction):
    try:
        img_path = os.path.join(os.path.dirname(__file__), "assets", "middleman_process.webp")
        if os.path.exists(img_path):
            file = discord.File(img_path, filename="middleman_process.webp")
            await interaction.response.send_message(file=file)
        else:
            await interaction.response.send_message("❌ Could not find middleman process image!", ephemeral=True)
    except Exception as e:
        print(f"Error sending middleman: {e}")
        await interaction.response.send_message("❌ Could not find middleman process image!", ephemeral=True)
 
@bot.tree.command(name="close", description="Close the current ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
async def close_ticket_command(interaction: discord.Interaction):
    await interaction.response.defer()
    ticket_data = load_ticket_data()
    ticket_info = None
    user_id = None
    ticket_type = None
 
    for uid, data in ticket_data["user_middleman_tickets"].items():
        if data["channel_id"] == interaction.channel.id:
            ticket_info = data
            user_id = uid
            ticket_type = "middleman"
            break
 
    if not ticket_info:
        for uid, data in ticket_data["user_support_tickets"].items():
            if data["channel_id"] == interaction.channel.id:
                ticket_info = data
                user_id = uid
                ticket_type = "support"
                break
 
    if not ticket_info:
        for uid, data in ticket_data["user_buyranks_tickets"].items():
            if data["channel_id"] == interaction.channel.id:
                ticket_info = data
                user_id = uid
                ticket_type = "buyranks"
                break
 
    if not ticket_info:
        for uid, data in ticket_data["user_buyitems_tickets"].items():
            if data["channel_id"] == interaction.channel.id:
                ticket_info = data
                user_id = uid
                ticket_type = "buyitems"
                break
 
    if not ticket_info:
        for uid, data in ticket_data.get("user_personal_middleman_tickets", {}).items():
            if data["channel_id"] == interaction.channel.id:
                ticket_info = data
                user_id = uid
                ticket_type = "personal_middleman"
                break
 
    if not ticket_info:
        await interaction.followup.send("❌ Ticket data not found!", ephemeral=True)
        return
 
    is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
    is_ticket_opener = interaction.user.id == ticket_info["opener"]
    is_claimer = interaction.user.id == ticket_info["claimer"]
    is_added_user = interaction.user.id in ticket_info["added_users"]
 
    if not (is_owner or is_ticket_opener or is_claimer or is_added_user):
        await interaction.followup.send("❌ Only the ticket opener, claimer, added users, or owner can close this ticket!", ephemeral=True)
        return
 
    guild = interaction.guild
    opener = guild.get_member(ticket_info["opener"])
    claimer = guild.get_member(ticket_info["claimer"]) if ticket_info["claimer"] else None
 
    ticket_info["closer"] = interaction.user.id
    ticket_info["closed_at"] = datetime.utcnow().isoformat()
 
    transcript_content = f"# Ticket Transcript: {interaction.channel.name}\n\n"
    transcript_content += f"**Opened by:** {opener.mention if opener else 'Unknown'} ({ticket_info['opener']})\n"
    transcript_content += f"**Opened at:** {ticket_info['opened_at']}\n"
    transcript_content += f"**Claimed by:** {claimer.mention if claimer else 'Not claimed'} ({ticket_info['claimer'] if ticket_info['claimer'] else 'None'})\n"
    transcript_content += f"**Claimed at:** {ticket_info['claimed_at'] if ticket_info['claimed_at'] else 'Not claimed'}\n"
    transcript_content += f"**Closed by:** {interaction.user.mention} ({interaction.user.id})\n"
    transcript_content += f"**Closed at:** {ticket_info['closed_at']}\n\n"
    transcript_content += "---\n\n## Messages:\n\n"
 
    async for message in interaction.channel.history(limit=None, oldest_first=True):
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        transcript_content += f"[{timestamp}] {message.author.name}: {message.content}\n"
 
    if ticket_type == "buyranks":
        transcript_channel = guild.get_channel(BUY_RANKS_TRANSCRIPT_ID)
    elif ticket_type == "buyitems":
        transcript_channel = guild.get_channel(BUY_ITEMS_TRANSCRIPT_ID)
    elif ticket_type == "personal_middleman":
        transcript_channel = guild.get_channel(TRANSCRIPT_CHANNEL_ID)
    else:
        transcript_channel = guild.get_channel(TRANSCRIPT_CHANNEL_ID)
 
    if transcript_channel:
        try:
            transcript_file = discord.File(
                fp=io.BytesIO(transcript_content.encode('utf-8')),
                filename=f"transcript-{interaction.channel.name}.txt"
            )
 
            transcript_embed = discord.Embed(
                title=f"Ticket Transcript: {interaction.channel.name}",
                description=f"**Opened by:** {opener.mention if opener else 'Unknown'}\n**Claimed by:** {claimer.mention if claimer else 'Not claimed'}\n**Closed by:** {interaction.user.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
 
            await transcript_channel.send(embed=transcript_embed, file=transcript_file)
        except Exception as e:
            print(f"Failed to send transcript: {e}")
 
    if ticket_type == "middleman":
        del ticket_data["user_middleman_tickets"][user_id]
    elif ticket_type == "support":
        del ticket_data["user_support_tickets"][user_id]
    elif ticket_type == "buyranks":
        del ticket_data["user_buyranks_tickets"][user_id]
    elif ticket_type == "buyitems":
        del ticket_data["user_buyitems_tickets"][user_id]
    elif ticket_type == "personal_middleman":
        del ticket_data["user_personal_middleman_tickets"][user_id]
 
    save_ticket_data(ticket_data)
 
    guild = interaction.guild
    await check_and_update_category_visibility(guild, ticket_type)
 
 
    await interaction.followup.send("✅ Closing ticket and sending transcript...")
 
    if ticket_info.get("verified_accepted"):
        try:
            cat_embed = discord.Embed(
                title="🐱 Thanks for using Trade Hub!",
                description="Your ticket has been closed successfully.",
                color=discord.Color.purple()
            )
            cat_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
 
            cat_img_path = os.path.join(os.path.dirname(__file__), "assets", "cat.png")
 
            if os.path.exists(cat_img_path):
                with open(cat_img_path, "rb") as cat_file:
                    await interaction.channel.send(embed=cat_embed, file=discord.File(cat_file, filename="cat.png"))
            else:
                await interaction.channel.send(embed=cat_embed)
        except Exception as e:
            print(f"Error sending cat image: {e}")
 
    closing_embed = discord.Embed(
        title="🔐 Closing Ticket",
        description="**Closing in 10 seconds...**",
        color=discord.Color.greyple()
    )
 
    closing_msg = await interaction.channel.send(embed=closing_embed)
 
    for remaining in range(10, 0, -1):
        try:
            closing_embed_update = discord.Embed(
                title="🔐 Closing Ticket",
                description=f"**Closing in {remaining} seconds...**",
                color=discord.Color.greyple()
            )
            await closing_msg.edit(embed=closing_embed_update)
        except:
            break
        await asyncio.sleep(1)
 
    await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
 
@bot.command(name="unclaim")
async def unclaim_ticket(ctx):
    # Only usable in ticket channels
    try:
        if ctx.channel.category_id not in [MIDDLEMAN_CATEGORY_ID, SUPPORT_CATEGORY_ID, BUY_RANKS_CATEGORY_ID, BUY_ITEMS_CATEGORY_ID, PERSONAL_MIDDLEMAN_CATEGORY_ID]:
            await ctx.send("❌ This command only works in ticket channels.")
            return
    except Exception:
        await ctx.send("❌ Unable to verify channel category.")
        return

    # Only middleman and above roles can unclaim
    user_roles = [r.id for r in ctx.author.roles]
    if not any(rid in STAFF_ROLE_IDS for rid in user_roles):
        await ctx.send("❌ Only middleman & above can unclaim.")
        return

    data = load_ticket_data()
    ticket_info = None
    ticket_type = None

    for ttype in ["user_middleman_tickets", "user_support_tickets", "user_buyranks_tickets", "user_buyitems_tickets", "user_personal_middleman_tickets"]:
        for uid, info in data.get(ttype, {}).items():
            if info.get("channel_id") == ctx.channel.id:
                ticket_info = info
                ticket_type = ttype
                break
        if ticket_info: break

    if not ticket_info:
        await ctx.send("❌ No ticket found associated with this channel.")
        return

    # opener cannot unclaim their own ticket
    if ticket_info.get('opener') == ctx.author.id:
        await ctx.send('❌ You cannot unclaim a ticket you opened.')
        return

    prev_claimer = ticket_info.get('claimer')
    ticket_info['claimer'] = None
    ticket_info['claimed_at'] = None
    if 'ai_locked' in ticket_info:
        ticket_info['ai_locked'] = False
    
    save_ticket_data(data)

    # Reset permissions for previous claimer
    try:
        if prev_claimer:
            prev_member = ctx.guild.get_member(prev_claimer)
            if prev_member:
                # Remove specific override
                await ctx.channel.set_permissions(prev_member, overwrite=None)
    except Exception:
        pass
    
    # Reset Staff Permissions based on ticket type
    # Support: All staff can type
    # Others: Staff read-only until claim
    admin_full_access_roles = [OWNER_ROLE_ID, CO_OWNER_ROLE_ID, ADMINISTRATOR_ROLE_ID]
    support_roles = [SUPPORT_ROLE_ID]

    if ticket_type == "user_support_tickets":
        # Support logic: All staff + support roles get write access
        for role_id in STAFF_ROLE_IDS + support_roles:
            role = ctx.guild.get_role(role_id)
            if role:
                 await ctx.channel.set_permissions(role, view_channel=True, send_messages=True)
    else:
        # Other tickets: Staff read-only, Admins write
        for role_id in STAFF_ROLE_IDS:
            role = ctx.guild.get_role(role_id)
            if role:
                if role_id in admin_full_access_roles:
                    await ctx.channel.set_permissions(role, view_channel=True, send_messages=True)
                else:
                    await ctx.channel.set_permissions(role, view_channel=True, send_messages=False)

    await ctx.send('🔓 Ticket unclaimed.')

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN not found in .env file!")
    else:
        bot.run(TOKEN)
