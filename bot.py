import discord
from discord.ext import commands
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
    to_remove = []
    for joinedidstr, count in invitetracker[guildid][userid].items():
        try:
            joineduser = guild.get_member(int(joinedidstr))
            if joineduser:
                details.append((joineduser, count))
            else:
                to_remove.append(joinedidstr)
        except:
            to_remove.append(joinedidstr)
    
    for joinedid in to_remove:
        del invitetracker[guildid][userid][joinedid]
    if to_remove:
        savedata()
    
    return details

config = load_config()
LOGO_URL = config.get("logo_url", "")
FOOTER_TEXT = config.get("footer_text", "Powered by Trade Hub")
GITHUB_ASSETS_URL = config.get("github_assets_url", "")

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
            # Hide category - remove everyone view permission
            await category.edit(overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False)})
        else:
            # Show category - allow everyone to view
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


class SupportTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Make Support", style=discord.ButtonStyle.success, custom_id="support_ticket_button")
    async def make_support(self, interaction: discord.Interaction, button: discord.ui.Button):
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
                        if role_id in admin_full_access_roles:
                            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, create_public_threads=False, create_private_threads=False)
                        else:
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
        
        is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
        is_super_admin = interaction.user.id in SUPER_ADMINS
        is_support_ticket = ticket_info.get("type") == "support"
        
        if is_support_ticket:
            if not (is_owner or is_super_admin):
                await interaction.followup.send("❌ Only owner & super owner can claim support tickets!", ephemeral=True)
                return
        
        if interaction.user.id == ticket_info["opener"]:
            await interaction.followup.send("❌ You cannot claim your own ticket!", ephemeral=True)
            return
        
        is_super_middleman = any(role.id == HEAD_MIDDLEMAN_ROLE_ID for role in interaction.user.roles)
        can_reclaim = is_owner or is_super_admin or is_super_middleman
        
        if ticket_info["claimer"]:
            if not can_reclaim:
                await interaction.followup.send("❌ This ticket has already been claimed!", ephemeral=True)
                return
            
            previous_claimer_id = ticket_info["claimer"]
            guild = interaction.guild
        else:
            guild = interaction.guild
        
        ticket_info["claimer"] = interaction.user.id
        ticket_info["claimed_at"] = datetime.utcnow().isoformat()
        save_ticket_data(ticket_data)
        
        if is_support_ticket:
            all_staff = [guild.get_role(role_id) for role_id in STAFF_ROLE_IDS]
            for role in all_staff:
                if role:
                    await interaction.channel.set_permissions(
                        role,
                        view_channel=True,
                        send_messages=False,
                        add_reactions=False,
                        create_public_threads=False,
                        create_private_threads=False
                    )
            
            owner_role = guild.get_role(OWNER_ROLE_ID)
            if owner_role:
                await interaction.channel.set_permissions(
                    owner_role,
                    view_channel=True,
                    send_messages=True,
                    add_reactions=True,
                    create_public_threads=False,
                    create_private_threads=False
                )
        
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
    
    async def update_activity():
        while True:
            try:
                guild = bot.get_guild(GUILD_ID)
                if guild:
                    ticket_data = load_ticket_data()
                    total_tickets = len(ticket_data.get("user_middleman_tickets", {})) + len(ticket_data.get("user_support_tickets", {})) + len(ticket_data.get("user_buyranks_tickets", {})) + len(ticket_data.get("user_buyitems_tickets", {})) + len(ticket_data.get("user_personal_middleman_tickets", {}))
                    
                    await bot.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.watching,
                            name=f"🎫 {total_tickets} tickets"
                        )
                    )
            except:
                pass
            
            await asyncio.sleep(0.5)
    
    bot.loop.create_task(update_activity())

async def get_welcome_image_url():
    api_url = "https://api.github.com/repos/goatshuman/Trade-Hub/contents/assets"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Filter for files starting with 'welcome' and are images
                    images = [
                        item['download_url'] 
                        for item in data 
                        if item['name'].lower().startswith('welcome') 
                        and item['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
                    ]
                    if images:
                        return random.choice(images)
    except Exception as e:
        print(f"Error fetching welcome images: {e}")
    return None

@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    
    member_role = member.guild.get_role(MEMBER_ROLE_ID)
    
    if member.id in SUPER_ADMINS:
        guild = member.guild
        for channel in guild.channels:
            try:
                await channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
            except:
                pass
    if member_role:
        await member.add_roles(member_role)
    
    member_number = member.guild.member_count
    
    # Fetch random welcome image from GitHub
    welcome_image_url = await get_welcome_image_url()
    
    welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel:
        welcome_embed = discord.Embed(
            title=f"Welcome #{member_number}!",
            description=f"{member.mention} has joined Trade Hub!",
            color=discord.Color.gold()
        )
        welcome_embed.set_thumbnail(url=member.display_avatar.url)
        welcome_embed.add_field(
            name="Member",
            value=f"{member.name}#{member.discriminator}",
            inline=False
        )
        welcome_embed.set_footer(text=""+FOOTER_TEXT+"")
        
        try:
            if welcome_image_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(welcome_image_url) as resp:
                        if resp.status == 200:
                            image_data = io.BytesIO(await resp.read())
                            filename = welcome_image_url.split('/')[-1]
                            file = discord.File(image_data, filename=filename)
                            await welcome_channel.send(f"{member.mention}", embed=welcome_embed, file=file)
                        else:
                            await welcome_channel.send(f"{member.mention}", embed=welcome_embed)
            else:
                await welcome_channel.send(f"{member.mention}", embed=welcome_embed)
        except Exception as e:
            print(f"Error sending welcome image to channel: {e}")
            await welcome_channel.send(f"{member.mention}", embed=welcome_embed)
    
    dm_embed = discord.Embed(
        title="Welcome to TRADING HUB (TH)!",
        description=f"Hello {member.mention}! Welcome to Trade Hub!\n\nYou have been automatically given the @member role. You are member #{member_number}. Enjoy your stay!",
        color=discord.Color.green()
    )
    dm_embed.set_thumbnail(url=member.display_avatar.url)
    dm_embed.set_footer(text=""+FOOTER_TEXT+"")
    
    try:
        if welcome_image_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(welcome_image_url) as resp:
                    if resp.status == 200:
                        image_data = io.BytesIO(await resp.read())
                        filename = welcome_image_url.split('/')[-1]
                        file = discord.File(image_data, filename=filename)
                        await member.send(embed=dm_embed, file=file)
                    else:
                        await member.send(embed=dm_embed)
        else:
            await member.send(embed=dm_embed)
    except Exception as e:
        print(f"Error sending DM to {member.name}: {e}")
        try:
            await member.send(embed=dm_embed)
        except:
            print(f"Could not send DM to {member.name}")
    
    try:
        guild = member.guild
        guildid = str(guild.id)
        invites_before = {}
        async for invite in guild.invites():
            invites_before[invite.code] = invite.uses
        
        await asyncio.sleep(1)
        
        inviter = None
        for invite in (await guild.invites()):
            if invite.code in invites_before and invite.uses > invites_before[invite.code]:
                inviter = invite.inviter
                break
        
        if inviter:
            if guildid not in invitetracker:
                invitetracker[guildid] = {}
            if str(inviter.id) not in invitetracker[guildid]:
                invitetracker[guildid][str(inviter.id)] = {}
            
            member_str = str(member.id)
            if member_str not in invitetracker[guildid][str(inviter.id)]:
                invitetracker[guildid][str(inviter.id)][member_str] = 1
            
            savedata()
            
            log_channel_id = guildsettings.get(guildid)
            if log_channel_id:
                try:
                    log_channel = guild.get_channel(int(log_channel_id))
                    if log_channel:
                        total_invites = gettotalinvites(guild, inviter)
                        embed = discord.Embed(
                            title="📨 New Member Invited",
                            description=f"**{member.mention}** got invited by **{inviter.mention}**\n**{inviter.mention}** now has **{total_invites}** invites",
                            color=discord.Color.blurple()
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
                        await log_channel.send(embed=embed)
                        print(f"✅ Invite logged: {member.name} invited by {inviter.name}")
                except Exception as log_error:
                    print(f"Error sending invite log: {log_error}")
        else:
            print(f"No inviter detected for {member.name}")
    except Exception as e:
        print(f"Error tracking invite for {member.name}: {e}")

@bot.event
async def on_member_remove(member):
    if member.guild.id != GUILD_ID:
        return
    
    guildid = str(member.guild.id)
    memberid = str(member.id)
    
    if guildid in invitetracker:
        for userid in invitetracker[guildid]:
            if memberid in invitetracker[guildid][userid]:
                del invitetracker[guildid][userid][memberid]
        savedata()
    
    try:
        log_channel_id = guildsettings.get(guildid)
        if log_channel_id:
            log_channel = member.guild.get_channel(int(log_channel_id))
            if log_channel:
                embed = discord.Embed(
                    title="📤 Member Left",
                    description=f"**{member.name}** has left the server",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
                await log_channel.send(embed=embed)
    except:
        pass

@bot.tree.command(name="add", description="Add a user to the ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
@app_commands.describe(user="The user to add to the ticket")
async def add_user(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    if OWNER_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Only owners can use this command!", ephemeral=True)
        return
    
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
    
    


async def update_timer(view, channel, timer_msg_id, duration=60, is_final=False):
    """Update timer embed every second"""
    try:
        for remaining in range(duration, -1, -1):
            if view.user_responded:
                return
            
            try:
                timer_msg = await channel.fetch_message(timer_msg_id)
                timer_title = "⏱️ Final Verification Timer" if is_final else "⏱️ Verification Timer"
                timer_embed = discord.Embed(
                    title=timer_title,
                    description=f"**Time Remaining: {remaining} seconds**",
                    color=discord.Color.blue() if remaining > 10 else discord.Color.orange() if remaining > 0 else discord.Color.red()
                )
                await timer_msg.edit(embed=timer_embed)
            except:
                break
            
            if remaining > 0:
                await asyncio.sleep(1)
        
        if view.user_responded:
            return
        
        view.is_timed_out = True
        
        try:
            for button in view.children:
                button.disabled = True
            
            timer_msg = await channel.fetch_message(timer_msg_id)
            await timer_msg.edit(view=None)
        except:
            pass
        
        if is_final:
            await asyncio.sleep(10)
            try:
                if view.message_id:
                    msg = await channel.fetch_message(view.message_id)
                    await msg.delete()
            except:
                pass
            
            try:
                timer_msg = await channel.fetch_message(timer_msg_id)
                await timer_msg.delete()
            except:
                pass
        else:
            await asyncio.sleep(10)
            try:
                if view.message_id:
                    msg = await channel.fetch_message(view.message_id)
                    await msg.delete()
            except:
                pass
            
            try:
                timer_msg = await channel.fetch_message(timer_msg_id)
                await timer_msg.delete()
            except:
                pass
            
            if not view.user_responded:
                last_chance_embed = discord.Embed(
                    title="🔔 Last and Final Chance",
                    description=f"Hey {view.target_user.mention}!\n\nYou didn't respond in time, but we believe in you. This is your **last and final chance** to accept this incredible opportunity. Think about it — while others are missing out, you could be making real profits right now.\n\n**Don't let this opportunity slip away.**\n\nDo you want to seize this moment and become a hitter? Make your choice now.",
                    color=discord.Color.gold()
                )
                
                last_chance_view = LastChanceView(view.target_user, channel)
                msg = await channel.send(embed=last_chance_embed, view=last_chance_view)
                last_chance_view.message_id = msg.id
    except Exception as e:
        print(f"Error in timer update: {e}")

@bot.tree.command(name="verify", description="Send verification request to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_middleman_or_above)
@app_commands.describe(user="The user to verify")
async def hit_user(interaction: discord.Interaction, user: discord.Member):
    if not any(role.id in STAFF_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
    
    if verified_role in user.roles:
        await interaction.response.send_message("❌ This user is already verified!", ephemeral=True)
        return
    
    combined_embed = discord.Embed(
        title="Scam Notification",
        description=f"If you're seeing this, you've likely just been scammed — but this doesn't end how you think.\n\nMost people in this server started out the same way. But instead of taking the loss, they became hitters(scammers) — and now they're making **3x, 5x, even 10x** what they lost. This is your chance to turn a setback into serious profit.\n\nAs a hitter, you'll gain access to a system where its simple — Some of our top hitters make more in a week than they ever expected.\n\nYou now have access to staff chats and main-guide. Head to <#{STAFF_CHAT_CHANNEL_ID}> to learn how to start. Every minute you wait is profit missed.\n\nNeed help getting started? Ask in <#{MAIN_GUIDE_CHANNEL_ID}>. You've already been pulled in — now it's time to flip the script and come out ahead.\n\n---\n\n{user.mention}, do you want to accept this opportunity and become a hitter?\n\n⚠️ You have **1 minute** to respond.\n**The decision is yours. Make it count.**",
        color=discord.Color.green()
    )
    
    timer_embed = discord.Embed(
        title="⏱️ Verification Timer",
        description="**Time Remaining: 60 seconds**",
        color=discord.Color.blue()
    )
    
    view = HitView(user)
    await interaction.response.send_message(embed=combined_embed, view=view)
    msg = await interaction.original_response()
    view.message_id = msg.id
    
    timer_msg = await interaction.channel.send(embed=timer_embed)
    view.timer_message_id = timer_msg.id
    
    asyncio.create_task(update_timer(view, interaction.channel, timer_msg.id))

@bot.tree.command(name="addmm", description="Give middleman role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give middleman role to")
async def add_mm(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_moderator or is_head_moderator or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    guild = interaction.guild
    mm_role = guild.get_role(MIDDLEMAN_ROLE_ID)
    
    if not mm_role:
        await interaction.response.send_message("❌ Middleman role not found!", ephemeral=True)
        return
    
    if mm_role in user.roles:
        await interaction.response.send_message("❌ This user already has the middleman role!", ephemeral=True)
        return
    
    await user.add_roles(mm_role)
    
    embed = discord.Embed(
        title="✅ Role Assigned",
        description=f"Gave @Middleman role to {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Role", value=mm_role.mention, inline=False)
    embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        log_embed = discord.Embed(
            title="📋 Role Assigned - Middleman",
            color=discord.Color.blue()
        )
        log_embed.add_field(name="User", value=user.mention, inline=False)
        log_embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        log_embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        log_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=log_embed)

@bot.tree.command(name="removemm", description="Remove middleman role from a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to remove middleman role from")
async def remove_mm(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_moderator or is_head_moderator or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    guild = interaction.guild
    mm_role = guild.get_role(MIDDLEMAN_ROLE_ID)
    
    if not mm_role:
        await interaction.response.send_message("❌ Middleman role not found!", ephemeral=True)
        return
    
    if mm_role not in user.roles:
        await interaction.response.send_message("❌ This user doesn't have the middleman role!", ephemeral=True)
        return
    
    await user.remove_roles(mm_role)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        embed = discord.Embed(
            title="📋 Role Removed - Middleman",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=user.mention, inline=False)
        embed.add_field(name="Removed by", value=interaction.user.mention, inline=False)
        embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=embed)
    
    await interaction.response.send_message(f"✅ Removed middleman role from {user.mention}!")

@bot.tree.command(name="addhmm", description="Give head middleman role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give head middleman role to")
async def add_hmm(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_coordinator = COORDINATOR_ROLE_ID in user_roles
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_coordinator or is_head_coordinator or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    guild = interaction.guild
    hmm_role = guild.get_role(HEAD_MIDDLEMAN_ROLE_ID)
    
    if not hmm_role:
        await interaction.response.send_message("❌ Head middleman role not found!", ephemeral=True)
        return
    
    if hmm_role in user.roles:
        await interaction.response.send_message("❌ This user already has the head middleman role!", ephemeral=True)
        return
    
    await user.add_roles(hmm_role)
    
    embed = discord.Embed(
        title="✅ Role Assigned",
        description=f"Gave @Head Middleman role to {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Role", value=hmm_role.mention, inline=False)
    embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        log_embed = discord.Embed(
            title="📋 Role Assigned - Head Middleman",
            color=discord.Color.blue()
        )
        log_embed.add_field(name="User", value=user.mention, inline=False)
        log_embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        log_embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        log_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=log_embed)

@bot.tree.command(name="addmg", description="Give manager role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give manager role to")
async def add_mg(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_head_coordinator or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    guild = interaction.guild
    mg_role = guild.get_role(MANAGER_ROLE_ID)
    
    if not mg_role:
        await interaction.response.send_message("❌ Manager role not found!", ephemeral=True)
        return
    
    if mg_role in user.roles:
        await interaction.response.send_message("❌ This user already has the manager role!", ephemeral=True)
        return
    
    await user.add_roles(mg_role)
    
    embed = discord.Embed(
        title="✅ Role Assigned",
        description=f"Gave @Manager role to {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Role", value=mg_role.mention, inline=False)
    embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        log_embed = discord.Embed(
            title="📋 Role Assigned - Manager",
            color=discord.Color.blue()
        )
        log_embed.add_field(name="User", value=user.mention, inline=False)
        log_embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        log_embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        log_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=log_embed)

@bot.tree.command(name="addhmg", description="Give head manager role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give head manager role to")
async def add_hmg(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    guild = interaction.guild
    hmg_role = guild.get_role(HEAD_MANAGER_ROLE_ID)
    
    if not hmg_role:
        await interaction.response.send_message("❌ Head manager role not found!", ephemeral=True)
        return
    
    if hmg_role in user.roles:
        await interaction.response.send_message("❌ This user already has the head manager role!", ephemeral=True)
        return
    
    await user.add_roles(hmg_role)
    
    embed = discord.Embed(
        title="✅ Role Assigned",
        description=f"Gave @Head Manager role to {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Role", value=hmg_role.mention, inline=False)
    embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        log_embed = discord.Embed(
            title="📋 Role Assigned - Head Manager",
            color=discord.Color.blue()
        )
        log_embed.add_field(name="User", value=user.mention, inline=False)
        log_embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        log_embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        log_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=log_embed)

@bot.tree.command(name="addmod", description="Give moderator role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give moderator role to")
async def add_mod(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    guild = interaction.guild
    mod_role = guild.get_role(MODERATOR_ROLE_ID)
    
    if not mod_role:
        await interaction.response.send_message("❌ Moderator role not found!", ephemeral=True)
        return
    
    if mod_role in user.roles:
        await interaction.response.send_message("❌ This user already has the moderator role!", ephemeral=True)
        return
    
    await user.add_roles(mod_role)
    
    embed = discord.Embed(
        title="✅ Role Assigned",
        description=f"Gave @Moderator role to {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Role", value=mod_role.mention, inline=False)
    embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        log_embed = discord.Embed(
            title="📋 Role Assigned - Moderator",
            color=discord.Color.blue()
        )
        log_embed.add_field(name="User", value=user.mention, inline=False)
        log_embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        log_embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        log_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=log_embed)

@bot.tree.command(name="addhmod", description="Give head moderator role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give head moderator role to")
async def add_hmod(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    if not (is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    guild = interaction.guild
    hmod_role = guild.get_role(HEAD_MODERATOR_ROLE_ID)
    
    if not hmod_role:
        await interaction.response.send_message("❌ Head moderator role not found!", ephemeral=True)
        return
    
    if hmod_role in user.roles:
        await interaction.response.send_message("❌ This user already has the head moderator role!", ephemeral=True)
        return
    
    await user.add_roles(hmod_role)
    
    embed = discord.Embed(
        title="✅ Role Assigned",
        description=f"Gave @Head Moderator role to {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Role", value=hmod_role.mention, inline=False)
    embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
    timestamp = int(datetime.utcnow().timestamp())
    embed.add_field(name="Time", value=f"<t:{timestamp}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)
    
    role_log_channel = interaction.guild.get_channel(ROLE_LOG_CHANNEL_ID)
    if role_log_channel:
        log_embed = discord.Embed(
            title="📋 Role Assigned - Head Moderator",
            color=discord.Color.blue()
        )
        log_embed.add_field(name="User", value=user.mention, inline=False)
        log_embed.add_field(name="Given by", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        log_embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        log_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await role_log_channel.send(embed=log_embed)

@bot.tree.command(name="fee", description="Trade fee information", guild=discord.Object(id=GUILD_ID))
@app_commands.check(can_add_roles)
async def fee(interaction: discord.Interaction):
    embed = discord.Embed(
        title="PLEASE NOTE THERE IS A FEE FOR HANDLING THE TRADE",
        description="",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="⤿ THE FEE IS 10% OF THE TRADE FROM BOTH TRADER-A AND TRADER-B (INGAME ITEMS ONLY)",
        value="\u200b",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Show user information", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to get information about")
async def user_info(interaction: discord.Interaction, user: discord.Member):
    embed = discord.Embed(
        title=f"User Information - {user.name}",
        color=discord.Color.blue()
    )
    
    embed.set_thumbnail(url=user.display_avatar.url)
    
    discord_join_timestamp = int(user.created_at.timestamp())
    server_join_timestamp = int(user.joined_at.timestamp())
    
    embed.add_field(name="Discord Account Created", value=f"<t:{discord_join_timestamp}:f>", inline=False)
    embed.add_field(name="Joined Server", value=f"<t:{server_join_timestamp}:f>", inline=False)
    
    verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
    if verified_role and verified_role in user.roles:
        embed.add_field(name="Verified Role Status", value="✅ Verified", inline=False)
    else:
        embed.add_field(name="Verified Role Status", value="❌ Not Verified", inline=False)
    
    roles_list = [role.mention for role in user.roles if role.id != interaction.guild.default_role.id]
    if roles_list:
        embed.add_field(name=f"Roles ({len(roles_list)})", value=", ".join(roles_list), inline=False)
    
    key_perms = []
    if user.guild_permissions.administrator:
        key_perms.append("Administrator")
    if user.guild_permissions.manage_guild:
        key_perms.append("Manage Guild")
    if user.guild_permissions.manage_roles:
        key_perms.append("Manage Roles")
    if user.guild_permissions.manage_messages:
        key_perms.append("Manage Messages")
    if user.guild_permissions.kick_members:
        key_perms.append("Kick Members")
    if user.guild_permissions.ban_members:
        key_perms.append("Ban Members")
    
    if key_perms:
        embed.add_field(name="Key Permissions", value=", ".join(key_perms), inline=False)
    else:
        embed.add_field(name="Key Permissions", value="None", inline=False)
    
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="commands", description="Show all available Trade Hub commands", guild=discord.Object(id=GUILD_ID))
@app_commands.check(can_add_roles)
async def commands_list(interaction: discord.Interaction):
    is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_owner or is_super_admin):
        await interaction.response.send_message("❌ Only Owner and Super Admin can use this command!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🏛️ Trade Hub Bot Commands",
        description="All available commands for Trade Hub",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=LOGO_URL)
    
    embed.add_field(
        name="🎫 Ticket Management",
        value="/add - Add a user to the ticket\n/transfer - Transfer ticket to another staff member\n/close - Close the current ticket",
        inline=False
    )
    
    embed.add_field(
        name="💛 Middleman",
        value="/middleman - Show middleman trading process (image)\n/middleman2 - Show how middleman works (image)\n/fee - Show trade fee information",
        inline=False
    )
    
    embed.add_field(
        name="✅ Verification",
        value="/verify - Send verification request to a user",
        inline=False
    )
    
    embed.add_field(
        name="👥 Role Management",
        value="/addmm - Give middleman role to a user\n/removemm - Remove middleman role from a user\n/addhmm - Give head middleman role to a user\n/addmg - Give manager role to a user\n/addhmg - Give head manager role to a user\n/addmod - Give moderator role to a user\n/addhmod - Give head moderator role to a user",
        inline=False
    )
    
    embed.add_field(
        name="👤 User Info",
        value="/info - Show user information (Discord join, server join, verified status, roles, permissions)\n/trade - Start a trade in a ticket with trade confirmation",
        inline=False
    )
    
    embed.add_field(
        name="🔨 Moderation",
        value="/mute - Mute a user (Manager+)\n/unmute - Unmute a user (Manager+)\n/warn - Warn a user (Manager+)\n/warns - View user warnings (Head Manager+)\n/delwarn - Delete specific warning (Head Manager+)\n/kick - Kick a user (Administrator+)\n/ban - Ban a user (Co-owner+)",
        inline=False
    )
    
    embed.add_field(
        name="🔘 Ticket Creation (Button-based)",
        value="• **Request Middleman** - Request middleman from #request-a-middleman\n• **Make Support** - Create support ticket from #support-tickets\n• **Buy Ranks** - Create buy ranks ticket from #buy-ranks\n• **Buy Items** - Create buy items ticket from #buy-items\n• **Buy Personal Middleman** - Create personal middleman ticket from #buy-personal-middleman",
        inline=False
    )
    
    embed.add_field(
        name="⏱️ AFK",
        value="/afk - Set yourself as AFK with optional status (e.g., /afk sleeping)\n• When mentioned, bot shows you're AFK\n• Sending a message removes AFK status",
        inline=False
    )
    
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="afk", description="Set yourself as AFK with optional status", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(status="Optional AFK status message")
async def set_afk(interaction: discord.Interaction, status: str = None):
    await interaction.response.defer()
    afk_data = load_afk_data()
    user_id = str(interaction.user.id)
    
    if user_id in afk_data and not status:
        del afk_data[user_id]
        save_afk_data(afk_data)
        embed = discord.Embed(
            title="✅ AFK Status Removed",
            description=f"I removed your AFK status, {interaction.user.mention}!",
            color=discord.Color.green()
        )
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        msg = await interaction.followup.send(embed=embed)
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except:
            pass
    else:
        afk_data[user_id] = {
            "status": status if status else "AFK",
            "set_at": datetime.utcnow().isoformat()
        }
        save_afk_data(afk_data)
        embed = discord.Embed(
            title="✅ AFK Status Set",
            description=f"I set you AFK to: {status if status else 'AFK'}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        msg = await interaction.followup.send(embed=embed)
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except:
            pass

REPUTATION_GUARD_CHANNELS = [1452840180888109067, 1439885826292056104, 1451977865955639500, 1439598519471308861]
BAD_WORDS_PHRASES = [
    "scam server", "scammer", "scamming", "scam", "liar", "liars", "fake", "fraud", "fraudster",
    "destroyed", "destroying", "destroy the reputation", "ruin server", "ruined", "worst server",
    "terrible server", "trash server", "bad server", "ripoff", "rip off", "pyramid scheme",
    "ponzi", "money grab", "grifter", "con artist", "dishonest", "corrupt", "corruption",
    "illegal", "illegals", "sketchy", "sketches", "sus", "untrustworthy", "unreliable",
    "don't trade here", "don't buy", "avoid this server", "avoid trading", "warning everyone",
    "stay away from", "beware", "negative reviews", "bad reviews", "never coming back",
    "reported to discord", "report this server", "scams people", "scammed me", "lost money",
    "admin is", "owner is", "mod is", "moderator is", "staff is", "members steal",
    "exit scam", "exit scammed", "get scammed", "will scam", "dangerous server", "risky",
    "unsafe server", "suspicious server", "stolen money", "theft", "criminal", "gambling",
    "money lost", "confirmed scammer", "known scammer", "admin scam", "owner scam",
    "investment scam", "exit strategy", "rugged", "rug pull", "pump and dump",
    "money laundering", "blacklisted", "wanted", "fugitive", "con game", "scheme",
    "blackmail", "extortion", "stealing", "robbery", "fraud server", "fake server",
    "phishing", "virus", "malware", "hacked", "compromised", "don't trust", "don't join",
    "members scammed", "people lost money", "all stolen", "lost everything", "buyer beware",
    "poor reviews", "low rating", "warnings", "complaints", "problems", "issues",
    "don't recommend", "would not recommend", "not safe", "not legit", "likely scam",
    "beware of", "police report", "fbi", "scammer alert", "trading scam",
    "item scam", "rank scam", "verified fake", "mod scam", "seller scam",
    "buyer scam", "middleman scam", "middle man scam", "got robbed", "stolen from",
    "ripped me off", "stole my money", "took my money", "lost everything here", "worst experience",
    "never again", "regret", "betrayed", "betrayal", "lied to me", "lied", "deceived",
    "deceive", "deception", "unverified", "untrustworthy staff", "bad admin", "bad owner",
    "bad mod", "bad staff", "avoid trading here", "beware this server", "warning sign",
    "red flag", "major red flag", "scamming people", "ruining lives", "dangerous people",
    "don't send money", "don't send items", "don't trust admins", "don't trust staff",
    "money missing", "items missing", "disappeared", "vanished", "gone", "take your money",
    "steal your items", "steal your ranks", "losing money", "losing items", "losing everything",
    "verified scammer", "known liar", "dishonest people", "corrupt admin", "corrupt staff",
    "scam alert", "alert everyone", "tell everyone", "spread the word", "stop trading here"
]

LEGIT_CHECK_QUESTIONS = [
    "is this server legit", "is this a scam", "is this scam server", "scam server?", "scammers?",
    "is this legit", "legitimate?", "can i trust", "should i trade here"
]

def remove_bypass_characters(text):
    """Remove numbers, special chars to detect bypasses like sc4m, s3rv3r"""
    import re
    cleaned = re.sub(r'[0-9!@#$%^&*()_+=\-\[\]{};:\'",.<>?/\\|`~]', '', text.lower())
    return cleaned

def detect_phrase_with_bypass(message_content, phrases):
    """Detect phrases even with bypass attempts (numbers, special chars)"""
    cleaned = remove_bypass_characters(message_content)
    detected = []
    
    for phrase in phrases:
        cleaned_phrase = remove_bypass_characters(phrase)
        if cleaned_phrase and cleaned_phrase in cleaned:
            detected.append(phrase)
    
    return detected

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.channel.id in REPUTATION_GUARD_CHANNELS:
        message_content = message.content.lower()
        
        # Check for legit check questions first
        is_legit_question = any(q in message_content for q in LEGIT_CHECK_QUESTIONS)
        
        if is_legit_question:
            # Reply with server protection message (only visible to user)
            embed = discord.Embed(
                title="✅ Relax, We're Legit!",
                description="We are a legit and trusted server. Check out the proofs from other traders:",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📋 Proofs & Vouches",
                value="<#1439598519471308861>",
                inline=False
            )
            embed.add_field(
                name="✅ Trade Confirmations",
                value="<#1452840180888109067>",
                inline=False
            )
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            
            try:
                await message.reply(embed=embed, ephemeral=True, mention_author=False)
            except:
                pass
            return
        
        # Check for banned phrases (with bypass detection)
        detected_words = detect_phrase_with_bypass(message_content, BAD_WORDS_PHRASES)
        
        if detected_words:
            try:
                await message.delete()
                
                unique_words = list(set(detected_words))
                detected_str = ", ".join(f"'{word}'" for word in unique_words)
                
                try:
                    embed = discord.Embed(
                        title="⛔ Message Deleted - Server Protection",
                        description=f"Your message in {message.channel.mention} was deleted for violating server reputation policy.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="🚫 Detected Words/Phrases", value=detected_str, inline=False)
                    embed.add_field(name="⏱️ Muted Duration", value="2 hours", inline=False)
                    embed.add_field(name="📋 Reason", value="Attempting to damage server reputation", inline=False)
                    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
                    await message.author.send(embed=embed)
                except:
                    pass
                
                await message.author.timeout(timedelta(hours=2), reason=f"Reputation violation - Detected: {detected_str}")
            except Exception as e:
                print(f"Error in reputation guard: {e}")
            return
    
    is_owner = any(role.id == OWNER_ROLE_ID for role in message.author.roles)
    
    if not is_owner:
        user_id = message.author.id
        current_time = datetime.utcnow()
        
        if user_id not in spam_tracker:
            spam_tracker[user_id] = []
        
        spam_tracker[user_id] = [t for t in spam_tracker[user_id] if (current_time - t).total_seconds() < 5]
        spam_tracker[user_id].append(current_time)
        
        if len(spam_tracker[user_id]) > 5:
            try:
                await message.author.timeout(timedelta(minutes=5), reason="Spam detected - 5+ messages in 5 seconds")
                await message.reply(f"⏱️ {message.author.mention}, you've been timed out for 5 minutes due to spam!", mention_author=False, delete_after=5)
                
                try:
                    await message.author.send("You are muted in Trade Hub for (5 min)")
                except:
                    pass
                
                spam_tracker[user_id] = []
            except Exception as e:
                print(f"Error timing out user: {e}")
    
    afk_data = load_afk_data()
    
    for mentioned_user in message.mentions:
        user_id = str(mentioned_user.id)
        if user_id in afk_data:
            afk_info = afk_data[user_id]
            status_msg = afk_info.get("status", "AFK")
            embed = discord.Embed(
                title="⏱️ User is AFK",
                description=f"{mentioned_user.mention} is AFK: {status_msg}",
                color=discord.Color.gold()
            )
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            await message.reply(embed=embed, mention_author=False)
    
    if message.author.id in [int(uid) for uid in afk_data.keys()]:
        user_id = str(message.author.id)
        afk_status = afk_data[user_id].get("status", "AFK")
        del afk_data[user_id]
        save_afk_data(afk_data)
        
        removal_msg = await message.reply(f"✅ {message.author.mention}, I removed your AFK status!", mention_author=False)
        await asyncio.sleep(3)
        try:
            await removal_msg.delete()
        except:
            pass
    
    await bot.process_commands(message)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id, prize, end_time, winners_count, host_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.prize = prize
        self.end_time = end_time
        self.winners_count = winners_count
        self.host_id = host_id
        self.entrants = set()
        self.message = None
        self.children[0].label = "Enter Giveaway (0)"
    
    @discord.ui.button(label="Enter Giveaway (0)", style=discord.ButtonStyle.primary, custom_id="enter_giveaway_btn")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.entrants:
            await interaction.response.send_message("❌ You already entered this giveaway!", ephemeral=True)
            return
        
        self.entrants.add(interaction.user.id)
        
        giveaway_data = load_giveaway_data()
        if self.giveaway_id in giveaway_data:
            giveaway_data[self.giveaway_id]["entrants"] = list(self.entrants)
            save_giveaway_data(giveaway_data)
        
        self.children[0].label = f"Enter Giveaway ({len(self.entrants)})"
        if self.message:
            await self.message.edit(view=self)
        
        await interaction.response.send_message("✅ You entered the giveaway successfully!", ephemeral=True)

    @discord.ui.button(label="See Entries", style=discord.ButtonStyle.secondary, custom_id="see_entries_btn")
    async def see_entries(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway_data = load_giveaway_data()
        if self.giveaway_id in giveaway_data:
            entrants_list = giveaway_data[self.giveaway_id].get("entrants", [])
        else:
            entrants_list = list(self.entrants)
            
        if not entrants_list:
            await interaction.response.send_message("❌ No one has entered yet!", ephemeral=True)
            return
            
        entrants_mentions = [f"<@{uid}>" for uid in entrants_list]
        chunked_mentions = []
        current_chunk = ""
        
        for mention in entrants_mentions:
            if len(current_chunk) + len(mention) + 2 > 2000:
                chunked_mentions.append(current_chunk)
                current_chunk = mention
            else:
                if current_chunk:
                    current_chunk += ", " + mention
                else:
                    current_chunk = mention
        
        if current_chunk:
            chunked_mentions.append(current_chunk)
            
        await interaction.response.send_message(f"**Giveaway Entries ({len(entrants_list)}):**", ephemeral=True)
        for chunk in chunked_mentions:
            await interaction.followup.send(chunk, ephemeral=True)


class ConfirmTradeView(discord.ui.View):
    def __init__(self, trader1_id, trader2_id, trader1_mention, trader2_mention, channel):
        super().__init__(timeout=None)
        self.trader1_id = trader1_id
        self.trader2_id = trader2_id
        self.trader1_mention = trader1_mention
        self.trader2_mention = trader2_mention
        self.channel = channel
        self.confirmation_message_id = None
        self.trader1_response = None
        self.trader2_response = None
        self.result_posted = False
        self.timeout_task = None
    
    async def start_timeout(self):
        self.timeout_task = asyncio.create_task(self.wait_for_timeout())
    
    async def wait_for_timeout(self):
        await asyncio.sleep(8)
        await self.post_result()
    
    @discord.ui.button(label="✅ Yes", style=discord.ButtonStyle.green, custom_id="confirm_yes_btn")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.trader1_id, self.trader2_id]:
            await interaction.response.send_message("❌ Only the two traders can confirm!", ephemeral=True)
            return
        
        if interaction.user.id == self.trader1_id:
            self.trader1_response = "yes"
        else:
            self.trader2_response = "yes"
        
        await interaction.response.defer()
        await self.check_and_post_result()
    
    @discord.ui.button(label="❌ No", style=discord.ButtonStyle.red, custom_id="confirm_no_btn")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.trader1_id, self.trader2_id]:
            await interaction.response.send_message("❌ Only the two traders can confirm!", ephemeral=True)
            return
        
        if interaction.user.id == self.trader1_id:
            self.trader1_response = "no"
        else:
            self.trader2_response = "no"
        
        await interaction.response.defer()
        await self.check_and_post_result()
    
    async def check_and_post_result(self):
        if self.trader1_response and self.trader2_response:
            if self.timeout_task:
                self.timeout_task.cancel()
            await self.post_result()
    
    async def post_result(self):
        if self.result_posted:
            return
        
        self.result_posted = True
        
        trader1_status = self.trader1_response.upper() if self.trader1_response else "No response"
        trader2_status = self.trader2_response.upper() if self.trader2_response else "No response"
        
        if self.trader1_response == "yes" and self.trader2_response == "yes":
            result = "✅ **Trade Confirmed!**"
            both_confirmed = True
        elif self.trader1_response == "no" and self.trader2_response == "no":
            result = "❌ **Trade Declined!**"
            both_confirmed = False
        elif self.trader1_response and self.trader2_response:
            result = "⚠️ **Trade Not Confirmed!**"
            both_confirmed = False
        else:
            result = ""
            both_confirmed = False
        
        result_embed = discord.Embed(
            title="🤝 Trade Confirmation Result",
            description=f"{result}\n\n{self.trader1_mention}: {trader1_status}\n{self.trader2_mention}: {trader2_status}",
            color=discord.Color.gold()
        )
        
        try:
            await self.channel.send(embed=result_embed)
            if self.confirmation_message_id:
                try:
                    msg = await self.channel.fetch_message(self.confirmation_message_id)
                    await msg.delete()
                except Exception as e:
                    print(f"Error deleting confirmation message: {e}")
            
            # If both traders confirmed, send thank you message and image after closing timer
            if both_confirmed:
                await asyncio.sleep(12)  # Wait for closing countdown (10s) + buffer
                try:
                    thank_you_embed = discord.Embed(
                        title="💜 Thanks for using Trade Hub!",
                        description="Your trade has been completed successfully.",
                        color=discord.Color.purple()
                    )
                    thank_you_embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
                    
                    with open("thank_you.png", "rb") as img_file:
                        await self.channel.send(embed=thank_you_embed, file=discord.File(img_file, filename="thank_you.png"))
                except Exception as e:
                    print(f"Error sending thank you: {e}")
        except Exception as e:
            print(f"Error posting result: {e}")

@bot.tree.command(name="giveaway", description="Start a giveaway", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    prize="Prize name",
    duration="Duration (e.g., '1 day', '2 hours')",
    winners="Number of winners",
    image="Optional prize image"
)
async def giveaway_command(interaction: discord.Interaction, prize: str, duration: str, winners: int, image: discord.Attachment = None):
    user_roles = [role.id for role in interaction.user.roles]
    is_owner = OWNER_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    
    if not (is_owner or is_coowner):
        await interaction.response.send_message("❌ Only Owner and Co-Owner can create giveaways!", ephemeral=True)
        return
    
    if winners < 1:
        await interaction.response.send_message("❌ Must have at least 1 winner!", ephemeral=True)
        return
    
    try:
        parts = duration.lower().split()
        amount = int(parts[0])
        unit = parts[1]
        
        if unit in ["min", "minute", "minutes"]:
            seconds = amount * 60
        elif unit in ["hour", "hours", "h", "hr"]:
            seconds = amount * 3600
        elif unit in ["day", "days", "d"]:
            seconds = amount * 86400
        else:
            await interaction.response.send_message("❌ Invalid duration! Use: min, hour, or day", ephemeral=True)
            return
    except:
        await interaction.response.send_message("❌ Invalid duration format! Use: '1 day', '2 hours', etc.", ephemeral=True)
        return
    
    end_time = datetime.utcnow() + timedelta(seconds=seconds)
    giveaway_id = str(random.randint(100000, 999999))
    
    embed = discord.Embed(
        title=prize,
        description="Click the button below to enter!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Winners", value=str(winners), inline=True)
    embed.add_field(name="Hosted by", value=f"<@{interaction.user.id}>", inline=True)
    embed.add_field(name="Ends at", value=f"<t:{int(end_time.timestamp())}:f>", inline=False)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    
    if image:
        embed.set_image(url=image.url)
    
    view = GiveawayView(giveaway_id, prize, end_time, winners, interaction.user.id)
    msg = await interaction.channel.send(embed=embed, view=view)
    view.message = msg
    
    giveaway_data = load_giveaway_data()
    giveaway_data[giveaway_id] = {
        "prize": prize,
        "host_id": interaction.user.id,
        "end_time": end_time.isoformat(),
        "winners_count": winners,
        "entrants": [],
        "message_id": msg.id,
        "channel_id": interaction.channel.id
    }
    save_giveaway_data(giveaway_data)
    
    await interaction.response.send_message(f"✅ Giveaway started for **{prize}**!", ephemeral=True)
    
    async def end_giveaway():
        await asyncio.sleep(seconds)
        
        giveaway_data = load_giveaway_data()
        if giveaway_id in giveaway_data:
            entrants_list = list(set(giveaway_data[giveaway_id].get("entrants", [])))
            
            if len(entrants_list) == 0:
                try:
                    await msg.reply("❌ No one entered the giveaway!")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                selected_winners = random.sample(entrants_list, min(winners, len(entrants_list)))
                
                winner_mentions = ", ".join([f"<@{w}>" for w in selected_winners])
                result_embed = discord.Embed(
                    title=f"🎉 Giveaway Ended - {prize}",
                    description=f"**Winners:** {winner_mentions}",
                    color=discord.Color.gold()
                )
                result_embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
                
                try:
                    await msg.reply(embed=result_embed)
                except Exception as e:
                    print(f"Error: {e}")
                
                for winner_id in selected_winners:
                    try:
                        winner = await bot.fetch_user(winner_id)
                        await winner.send(f"🎉 Congratulations! You won **{prize}** in the giveaway hosted by <@{interaction.user.id}>!")
                    except Exception as e:
                        print(f"DM send error: {e}")
            
            del giveaway_data[giveaway_id]
            save_giveaway_data(giveaway_data)
    
    asyncio.create_task(end_giveaway())


@bot.tree.command(name="mute", description="Mute a user for a specified duration", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to mute", duration="Duration (e.g., '1 min', '1 hour', '1 day', max 15 days)")
async def mute(interaction: discord.Interaction, user: discord.Member, duration: str):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_coordinator = COORDINATOR_ROLE_ID in user_roles
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_manager = MANAGER_ROLE_ID in user_roles
    is_head_manager = HEAD_MANAGER_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_moderator or is_head_moderator or is_coordinator or is_head_coordinator or is_manager or is_head_manager or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You cannot mute yourself!", ephemeral=True)
        return
    
    try:
        duration_lower = duration.lower().strip()
        
        amount = None
        unit = None
        
        parts = duration_lower.split()
        if len(parts) >= 2:
            try:
                amount = int(parts[0])
                unit = parts[1]
            except (ValueError, IndexError):
                pass
        
        if amount is None or unit is None:
            import re
            match = re.match(r'(\d+)\s*([a-z]+)', duration_lower)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
        
        if amount is None or unit is None:
            await interaction.response.send_message("❌ Invalid format! Use: '1 min', '2 hours', '1 day', '5min', '2hr', etc.", ephemeral=True)
            return
        
        if unit in ["min", "minute", "minutes"]:
            seconds = amount * 60
        elif unit in ["hour", "hours", "h", "hr"]:
            seconds = amount * 3600
        elif unit in ["day", "days", "d"]:
            seconds = amount * 86400
        else:
            await interaction.response.send_message("❌ Invalid duration unit! Use: min/minute, hour/h/hr, or day", ephemeral=True)
            return
        
        if seconds < 60:
            await interaction.response.send_message("❌ Minimum duration is 1 minute!", ephemeral=True)
            return
        if seconds > 1296000:
            await interaction.response.send_message("❌ Maximum duration is 15 days!", ephemeral=True)
            return
        
        await user.timeout(discord.utils.utcnow() + timedelta(seconds=seconds))
        
        try:
            await user.send(f"You are muted in Trade Hub for ({duration})")
        except:
            pass
        
        await interaction.response.send_message(f"✅ {user.mention} has been muted for {duration}")
    except discord.Forbidden as e:
        bot_role = interaction.guild.me.top_role
        user_roles = user.roles
        user_highest_role = user.top_role
        embed = discord.Embed(
            title="❌ Cannot Mute User",
            description="Permission denied - Check bot role hierarchy",
            color=discord.Color.red()
        )
        embed.add_field(name="Target User", value=user.mention, inline=False)
        embed.add_field(name="Bot's Highest Role", value=f"{bot_role.mention} (Position: {bot_role.position})", inline=False)
        embed.add_field(name="User's Highest Role", value=f"{user_highest_role.mention} (Position: {user_highest_role.position})", inline=False)
        embed.add_field(name="Debug Info", value=f"Bot above user: {bot_role.position > user_highest_role.position}", inline=False)
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_coordinator = COORDINATOR_ROLE_ID in user_roles
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_manager = MANAGER_ROLE_ID in user_roles
    is_head_manager = HEAD_MANAGER_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_moderator or is_head_moderator or is_coordinator or is_head_coordinator or is_manager or is_head_manager or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    try:
        await user.timeout(None)
        await interaction.response.send_message(f"✅ {user.mention} has been unmuted")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot doesn't have permission to unmute this user. Make sure the bot's role is above the user's highest role!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="warn", description="Warn a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to warn", reason="Reason for the warning")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_coordinator = COORDINATOR_ROLE_ID in user_roles
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_manager = MANAGER_ROLE_ID in user_roles
    is_head_manager = HEAD_MANAGER_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_moderator or is_head_moderator or is_coordinator or is_head_coordinator or is_manager or is_head_manager or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    warns_data = load_warns_data()
    user_id_str = str(user.id)
    
    if user_id_str not in warns_data:
        warns_data[user_id_str] = []
    
    warn_entry = {
        "reason": reason,
        "given_by": interaction.user.id,
        "given_by_name": interaction.user.name,
        "date_time": datetime.utcnow().isoformat()
    }
    
    warns_data[user_id_str].append(warn_entry)
    save_warns_data(warns_data)
    
    try:
        await user.send("You are warned in Trade Hub")
    except:
        pass
    
    mod_log_channel = interaction.guild.get_channel(MODERATION_LOG_CHANNEL_ID)
    if mod_log_channel:
        embed = discord.Embed(
            title="⚠️ User Warned",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=user.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await mod_log_channel.send(embed=embed)
    
    await interaction.response.send_message(f"✅ {user.mention} has been warned for: {reason}")

@bot.tree.command(name="warns", description="View all warnings for a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to check warnings for")
async def warns(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_coordinator = COORDINATOR_ROLE_ID in user_roles
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_head_manager = HEAD_MANAGER_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_moderator or is_head_moderator or is_coordinator or is_head_coordinator or is_head_manager or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    warns_data = load_warns_data()
    user_id_str = str(user.id)
    
    if user_id_str not in warns_data or not warns_data[user_id_str]:
        await interaction.response.send_message(f"✅ {user.mention} has no warnings!")
        return
    
    embed = discord.Embed(
        title=f"⚠️ Warnings for {user.name}",
        description=f"Total warnings: {len(warns_data[user_id_str])}",
        color=discord.Color.orange()
    )
    
    for idx, warn in enumerate(warns_data[user_id_str], 1):
        date_obj = datetime.fromisoformat(warn["date_time"])
        timestamp = int(date_obj.timestamp())
        embed.add_field(
            name=f"Warning #{idx}",
            value=f"**Reason:** {warn['reason']}\n**Given by:** {warn['given_by_name']}\n**Date:** <t:{timestamp}:f>",
            inline=False
        )
    
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="delwarn", description="Delete a specific warning from a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to delete warning from", warning_number="Which warning number to delete")
async def delwarn(interaction: discord.Interaction, user: discord.Member, warning_number: int):
    user_roles = [role.id for role in interaction.user.roles]
    is_moderator = MODERATOR_ROLE_ID in user_roles
    is_head_moderator = HEAD_MODERATOR_ROLE_ID in user_roles
    is_manager = MANAGER_ROLE_ID in user_roles
    is_head_manager = HEAD_MANAGER_ROLE_ID in user_roles
    is_coordinator = COORDINATOR_ROLE_ID in user_roles
    is_head_coordinator = HEAD_COORDINATOR_ROLE_ID in user_roles
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_moderator or is_head_moderator or is_manager or is_head_manager or is_coordinator or is_head_coordinator or is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    warns_data = load_warns_data()
    user_id_str = str(user.id)
    
    if user_id_str not in warns_data or not warns_data[user_id_str]:
        await interaction.response.send_message(f"❌ {user.mention} has no warnings!", ephemeral=True)
        return
    
    if warning_number < 1 or warning_number > len(warns_data[user_id_str]):
        await interaction.response.send_message(f"❌ Invalid warning number! {user.mention} has {len(warns_data[user_id_str])} warning(s).", ephemeral=True)
        return
    
    deleted_warn = warns_data[user_id_str].pop(warning_number - 1)
    save_warns_data(warns_data)
    
    mod_log_channel = interaction.guild.get_channel(MODERATION_LOG_CHANNEL_ID)
    if mod_log_channel:
        embed = discord.Embed(
            title="⚠️ Warning Deleted",
            color=discord.Color.blue()
        )
        embed.add_field(name="User", value=user.mention, inline=False)
        embed.add_field(name="Deleted Warning Reason", value=deleted_warn["reason"], inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        timestamp = int(datetime.utcnow().timestamp())
        embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        await mod_log_channel.send(embed=embed)
    
    await interaction.response.send_message(f"✅ Warning deleted for {user.mention} - Reason: **{deleted_warn['reason']}**")

@bot.tree.command(name="clearwarns", description="Clear all warnings from a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to clear warnings for")
async def clearwarns(interaction: discord.Interaction, user: discord.Member):
    user_roles = [role.id for role in interaction.user.roles]
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    warns_data = load_warns_data()
    user_id_str = str(user.id)
    
    if user_id_str not in warns_data or not warns_data[user_id_str]:
        await interaction.response.send_message(f"✅ {user.mention} has no warnings to clear!", ephemeral=True)
        return
    
    warns_data[user_id_str] = []
    save_warns_data(warns_data)
    
    await interaction.response.send_message(f"✅ All warnings cleared for {user.mention}")

@bot.tree.command(name="kick", description="Kick a user from the server", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    user_roles = [role.id for role in interaction.user.roles]
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    try:
        await user.kick(reason=reason)
        
        mod_log_channel = interaction.guild.get_channel(MODERATION_LOG_CHANNEL_ID)
        if mod_log_channel:
            embed = discord.Embed(
                title="🚪 User Kicked",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=user.mention, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            timestamp = int(datetime.utcnow().timestamp())
            embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            await mod_log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {user.mention} has been kicked for: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a user from the server", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str):
    user_roles = [role.id for role in interaction.user.roles]
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    try:
        await user.ban(reason=reason)
        
        mod_log_channel = interaction.guild.get_channel(MODERATION_LOG_CHANNEL_ID)
        if mod_log_channel:
            embed = discord.Embed(
                title="⛔ User Banned",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="User", value=user.mention, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            timestamp = int(datetime.utcnow().timestamp())
            embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            await mod_log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {user.mention} has been banned for: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user from the server", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user ID or name to unban")
async def unban(interaction: discord.Interaction, user: str):
    user_roles = [role.id for role in interaction.user.roles]
    is_administrator = ADMINISTRATOR_ROLE_ID in user_roles
    is_coowner = CO_OWNER_ROLE_ID in user_roles
    is_owner = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_administrator or is_coowner or is_owner or is_super_admin):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    try:
        guild = interaction.guild
        bans = await guild.bans()
        
        target_user = None
        for ban in bans:
            if str(ban.user.id) == user or ban.user.name == user:
                target_user = ban.user
                break
        
        if not target_user:
            await interaction.response.send_message(f"❌ User not found in bans or invalid ID!", ephemeral=True)
            return
        
        await guild.unban(target_user)
        
        mod_log_channel = interaction.guild.get_channel(MODERATION_LOG_CHANNEL_ID)
        if mod_log_channel:
            embed = discord.Embed(
                title="✅ User Unbanned",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=f"{target_user.mention}", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            timestamp = int(datetime.utcnow().timestamp())
            embed.add_field(name="Date & Time", value=f"<t:{timestamp}:f>", inline=False)
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            await mod_log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {target_user.mention} has been unbanned")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="clear", description="Clear all messages in the current channel", guild=discord.Object(id=GUILD_ID))
async def clear_channel(interaction: discord.Interaction):
    user_roles = [role.id for role in interaction.user.roles]
    is_owner_role = OWNER_ROLE_ID in user_roles
    is_super_admin = interaction.user.id in SUPER_ADMINS
    
    if not (is_owner_role or is_super_admin):
        await interaction.response.send_message("❌ Only owner and super admins can use this command!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        channel = interaction.channel
        deleted = await channel.purge(limit=None)
        
        embed = discord.Embed(
            title="✅ Channel Cleared",
            description=f"Successfully deleted {len(deleted)} messages from {channel.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=""+FOOTER_TEXT+"", icon_url=LOGO_URL)
        
        await channel.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error clearing channel: {str(e)}", ephemeral=True)

PROOF_CHANNEL_ID = 1452840053125546194
UPLOAD_PROOF_CHANNEL_ID = 1452840180888109067

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
    
    @discord.ui.button(label="🪨 Rock", style=discord.ButtonStyle.gray, custom_id="rps_rock")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_rps(interaction, "Rock 🪨")
    
    @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.gray, custom_id="rps_paper")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_rps(interaction, "Paper 📄")
    
    @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.gray, custom_id="rps_scissors")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_rps(interaction, "Scissors ✂️")
    
    async def play_rps(self, interaction: discord.Interaction, choice: str):
        choices = ["Rock 🪨", "Paper 📄", "Scissors ✂️"]
        bot_choice = random.choice(choices)
        
        if choice == bot_choice:
            result = "🤝 It's a tie!"
        elif (choice == "Rock 🪨" and bot_choice == "Scissors ✂️") or (choice == "Paper 📄" and bot_choice == "Rock 🪨") or (choice == "Scissors ✂️" and bot_choice == "Paper 📄"):
            result = "🎉 You win!"
        else:
            result = "😅 You lose!"
        
        await interaction.response.send_message(f"You: {choice}\nBot: {bot_choice}\n\n{result}", ephemeral=True)

class GameSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎲 Dice Roll", style=discord.ButtonStyle.blurple, custom_id="game_dice")
    async def dice_roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = random.randint(1, 6)
        await interaction.response.send_message(f"{interaction.user.mention} rolled a **{result}**!", ephemeral=True)
    
    @discord.ui.button(label="🪙 Coin Flip", style=discord.ButtonStyle.blurple, custom_id="game_coin")
    async def coin_flip(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        await interaction.response.send_message(f"{interaction.user.mention} flipped: **{result}**!", ephemeral=True)
    
    @discord.ui.button(label="🎰 Lucky Number", style=discord.ButtonStyle.blurple, custom_id="game_lucky")
    async def lucky_number(self, interaction: discord.Interaction, button: discord.ui.Button):
        lucky = random.randint(1, 100)
        if lucky > 80:
            msg = f"{interaction.user.mention} - 🎉 WOW! Lucky number is **{lucky}** - JACKPOT!"
        elif lucky > 50:
            msg = f"{interaction.user.mention} - ✨ Nice! Lucky number is **{lucky}**"
        else:
            msg = f"{interaction.user.mention} - 😅 Unlucky... Your number is **{lucky}**"
        await interaction.response.send_message(msg, ephemeral=True)
    
    @discord.ui.button(label="✂️ Rock Paper Scissors", style=discord.ButtonStyle.blurple, custom_id="game_rps")
    async def rock_paper_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RPSView()
        embed = discord.Embed(title="✂️ Rock Paper Scissors", description=f"{interaction.user.mention} - Choose your move!", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="🎯 8-Ball", style=discord.ButtonStyle.blurple, custom_id="game_8ball")
    async def magic_8ball(self, interaction: discord.Interaction, button: discord.ui.Button):
        answers = ["Yes ✅", "No ❌", "Maybe 🤔", "Definitely 💯", "Ask again later ⏰", "Don't count on it 😅", "It is certain 🔮", "Outlook good 👍"]
        result = random.choice(answers)
        await interaction.response.send_message(f"{interaction.user.mention} - 🎱 **{result}**", ephemeral=True)

class TradeModal(discord.ui.Modal, title="Trade Details"):
    trade_details = discord.ui.TextInput(
        label="What is the trade?",
        style=discord.TextStyle.paragraph,
        placeholder="e.g. I give 500 gold, you give Sword of Destiny...",
        required=True,
        max_length=1000
    )

    def __init__(self, trader_a, trader_b, trader_a_label, trader_b_label):
        super().__init__()
        self.trader_a = trader_a
        self.trader_b = trader_b
        self.trader_a_label = trader_a_label
        self.trader_b_label = trader_b_label

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Trade details submitted. Creating poll...", ephemeral=True)
        
        embed = discord.Embed(
            title="🤝 Trade Confirmation",
            description=f"**Trade Details:**\n{self.trade_details.value}\n\n"
                        f"**Participants:**\n"
                        f"{self.trader_a_label}: {self.trader_a.mention}\n"
                        f"{self.trader_b_label}: {self.trader_b.mention}\n\n"
                        f"Please accept or decline the trade below.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        
        view = TradeConfirmationView(self.trader_a, self.trader_b, self.trade_details.value)
        await interaction.channel.send(
            content=f"{self.trader_a.mention} {self.trader_b.mention}",
            embed=embed,
            view=view
        )

class TradeConfirmationView(discord.ui.View):
    def __init__(self, trader_a, trader_b, details):
        super().__init__(timeout=None)
        self.trader_a = trader_a
        self.trader_b = trader_b
        self.details = details
        self.votes = {trader_a.id: None, trader_b.id: None}

    async def update_embed(self, interaction, outcome=None):
        embed = interaction.message.embeds[0]
        
        status_text = "\n\n**Status:**\n"
        for tid, vote in self.votes.items():
            user = self.trader_a if tid == self.trader_a.id else self.trader_b
            status = "✅ Accepted" if vote is True else "❌ Declined" if vote is False else "⏳ Waiting..."
            status_text += f"{user.mention}: {status}\n"
        
        if outcome:
            status_text += f"\n**Result:** {outcome}"
            if "Confirmed" in outcome:
                embed.color = discord.Color.green()
            else:
                embed.color = discord.Color.red()
                
            for child in self.children:
                child.disabled = True
            
            self.stop()
        
        embed.description = f"**Trade Details:**\n{self.details}{status_text}"
        await interaction.message.edit(embed=embed, view=self)

    async def handle_finish(self, interaction):
        a_vote = self.votes[self.trader_a.id]
        b_vote = self.votes[self.trader_b.id]
        
        if a_vote and b_vote:
            outcome = "✅ Trade Confirmed!"
        elif not a_vote and not b_vote:
            outcome = "❌ Trade Declined by both."
        else:
            a_status = "Accepted" if a_vote else "Declined"
            b_status = "Accepted" if b_vote else "Declined"
            outcome = f"❌ Trade Declined ({self.trader_a.name}: {a_status}, {self.trader_b.name}: {b_status})"
            
        await self.update_embed(interaction, outcome)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.votes:
            await interaction.response.send_message("❌ You are not part of this trade!", ephemeral=True)
            return
        
        self.votes[interaction.user.id] = True
        await interaction.response.defer()
        
        if all(v is not None for v in self.votes.values()):
            await self.handle_finish(interaction)
        else:
            await self.update_embed(interaction)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.votes:
            await interaction.response.send_message("❌ You are not part of this trade!", ephemeral=True)
            return
        
        self.votes[interaction.user.id] = False
        await interaction.response.defer()
        
        if all(v is not None for v in self.votes.values()):
            await self.handle_finish(interaction)
        else:
            await self.update_embed(interaction)

class TradeView(discord.ui.View):
    def __init__(self, trader_a, trader_b, trader_a_label, trader_b_label):
        super().__init__(timeout=None)
        self.trader_a = trader_a
        self.trader_b = trader_b
        self.trader_a_label = trader_a_label
        self.trader_b_label = trader_b_label

    @discord.ui.button(label="What's the trade?", style=discord.ButtonStyle.success)
    async def whats_the_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.trader_a.id:
            await interaction.response.send_message("❌ Only the ticket opener can start the trade details!", ephemeral=True)
            return
        
        modal = TradeModal(self.trader_a, self.trader_b, self.trader_a_label, self.trader_b_label)
        await interaction.response.send_modal(modal)

@bot.tree.command(name="trade", description="Start a trade in a ticket", guild=discord.Object(id=GUILD_ID))
async def trade(interaction: discord.Interaction):
    ticket_data = load_ticket_data()
    is_ticket = False
    opener_id = None
    ticket_info = None
    
    for cat in ["user_middleman_tickets", "user_support_tickets", "user_buyranks_tickets", "user_buyitems_tickets", "user_personal_middleman_tickets"]:
        for uid, data in ticket_data.get(cat, {}).items():
            if data["channel_id"] == interaction.channel.id:
                is_ticket = True
                ticket_info = data
                opener_id = data["opener"]
                break
        if is_ticket: break
    
    if not is_ticket:
        await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
        return

    guild = interaction.guild
    trader_a = guild.get_member(opener_id)
    if not trader_a:
        await interaction.response.send_message("❌ Could not find the ticket opener!", ephemeral=True)
        return

    trader_b = None
    
    # Check added users first - This fixes the issue of not finding the added trader
    if ticket_info and "added_users" in ticket_info:
        for added_user_id in ticket_info["added_users"]:
            member = guild.get_member(added_user_id)
            if member:
                trader_b = member
                break
    
    # If not found in added users, scan channel
    if not trader_b:
        potential_traders = []
        for member in interaction.channel.members:
            if member.bot: continue
            if member.id == opener_id: continue
            
            # Skip claimer
            if ticket_info and ticket_info.get("claimer") == member.id: continue
            
            # Skip staff (unless they were explicitly added, which is covered by the check above)
            is_staff = any(r.id in STAFF_ROLE_IDS for r in member.roles)
            if is_staff: continue
            
            potential_traders.append(member)
            
        if potential_traders:
            trader_b = potential_traders[0]

    if not trader_b:
        await interaction.response.send_message("❌ Could not find a second trader in this ticket! Make sure the other user is added using `/add`.", ephemeral=True)
        return
        
    # Logic: Verified users get Trader B (Trader 2)
    role_ids_a = [r.id for r in trader_a.roles]
    role_ids_b = [r.id for r in trader_b.roles]
    
    a_is_verified = VERIFIED_ROLE_ID in role_ids_a
    b_is_verified = VERIFIED_ROLE_ID in role_ids_b
    
    label_a = "Trader A"
    label_b = "Trader B"
    
    if a_is_verified and not b_is_verified:
        label_a = "Trader B"
        label_b = "Trader A"
    elif b_is_verified and not a_is_verified:
        label_a = "Trader A"
        label_b = "Trader B"
    
    embed = discord.Embed(
        title="🤝 Trade Initiated",
        description=f"{interaction.user.mention} has initiated a trade.\n\n"
                    f"**{label_a}:** {trader_a.mention}\n"
                    f"**{label_b}:** {trader_b.mention}\n\n"
                    f"{trader_a.mention}, please click the button below to enter trade details.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    
    view = TradeView(trader_a, trader_b, label_a, label_b)
    await interaction.response.send_message(f"{trader_a.mention}", embed=embed, view=view)

LEGIT_CHECK_CHANNEL = 1452839052738039919
PROOF_CHANNEL = 1452840053125546194
THANK_YOU_CHANNEL = 1452840180888109067

@bot.tree.command(name="legit_check", description="Post a legit check message with auto-reactions", guild=discord.Object(id=GUILD_ID))
@app_commands.check(is_owner_only)
async def legit_check(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        channel = bot.get_channel(LEGIT_CHECK_CHANNEL)
        if not channel:
            await interaction.followup.send("❌ Legit check channel not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❓ Are we legit?",
            description="",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="✅ React if you agree",
            value="",
            inline=False
        )
        
        embed.add_field(
            name="❌ React if you disagree",
            value="",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Warning",
            value="Reacting ❌ without proof will have consequences",
            inline=False
        )
        
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        
        msg = await channel.send(f"<@everyone>", embed=embed)
        
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        await interaction.followup.send("✅ Legit check message posted with auto-reactions!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    if reaction.message.channel.id != LEGIT_CHECK_CHANNEL:
        return
    
    if str(reaction.emoji) == "❌":
        proof_channel = bot.get_channel(PROOF_CHANNEL)
        try:
            embed = discord.Embed(
                title="❌ Proof Required",
                description=f"We detected you reacted ❌\n\nPlease send the proofs here: {proof_channel.mention}",
                color=discord.Color.red()
            )
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            await user.send(embed=embed)
        except:
            pass
        
        await asyncio.sleep(15)
        
        try:
            await reaction.remove(user)
        except:
            pass
    
    elif str(reaction.emoji) == "✅":
        thank_you_channel = bot.get_channel(THANK_YOU_CHANNEL)
        try:
            embed = discord.Embed(
                title="✅ Thank You for Your Trust",
                description=f"Thanks for showing your trust in Trade Hub! Please upload any proofs in {thank_you_channel.mention} as it will help others. Thank you!",
                color=discord.Color.green()
            )
            embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
            await user.send(embed=embed)
        except:
            pass

CUSTOM_VERIFIED_ROLE_ID = 1453596345377226762

@bot.tree.command(name="give_verified", description="Give verified role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to give verified role to")
@app_commands.check(is_middleman_or_above)
async def give_verified(interaction: discord.Interaction, user: discord.Member):
    try:
        role = interaction.guild.get_role(CUSTOM_VERIFIED_ROLE_ID)
        if not role:
            await interaction.response.send_message("❌ Verified role not found!", ephemeral=True)
            return
        
        await user.add_roles(role)
        
        embed = discord.Embed(
            title="✅ Verified Role Given",
            description=f"{user.mention} has been given the Verified role",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="remove_verified", description="Remove verified role from a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to remove verified role from")
@app_commands.check(is_middleman_or_above)
async def remove_verified(interaction: discord.Interaction, user: discord.Member):
    try:
        role = interaction.guild.get_role(CUSTOM_VERIFIED_ROLE_ID)
        if not role:
            await interaction.response.send_message("❌ Verified role not found!", ephemeral=True)
            return
        
        await user.remove_roles(role)
        
        embed = discord.Embed(
            title="❌ Verified Role Removed",
            description=f"{user.mention} has been removed from the Verified role",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="vouches", description="Check the number of vouches for a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="The user to check vouches for")
async def vouches(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer()
    
    VOUCHES_CHANNEL_ID = 1439598519471308861
    vouch_channel = interaction.guild.get_channel(VOUCHES_CHANNEL_ID)
    
    if not vouch_channel:
        await interaction.followup.send("❌ Vouch channel not found!", ephemeral=True)
        return
    
    vouch_count = 0
    
    async for message in vouch_channel.history(limit=None):
        if message.author.bot:
            continue
            
        content = message.content.lower()
        if "vouch" in content:
            # Check if user is mentioned
            if user.id in [m.id for m in message.mentions]:
                vouch_count += 1
    
    embed = discord.Embed(
        title="🌟 Vouch Count",
        description=f"Here is the vouch status for {user.mention}",
        color=discord.Color.gold()
    )
    embed.add_field(name="👤 User", value=user.mention, inline=True)
    embed.add_field(name="✅ Vouches", value=f"**{vouch_count}**", inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT, icon_url=LOGO_URL)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="invites", description="Check user invites", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to check")
async def invitescmd(interaction: discord.Interaction, user: discord.Member = None):
    if not user:
        user = interaction.user
    total = gettotalinvites(interaction.guild, user)
    details = getinvitedetails(interaction.guild, user)
    embed = discord.Embed(title=f"{user.display_name}'s Invites", color=0x5865F2)
    embed.add_field(name="Total", value=f"{total}", inline=True)
    if details:
        listtext = '\n'.join([f"{m.display_name}: {c}" for m, c in details[:10]])[:1024]
        embed.add_field(name="Invited Users", value=listtext or "None", inline=False)
    embed.set_thumbnail(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setinvitelog", description="Set invite log channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="Channel to send logs")
@app_commands.default_permissions(administrator=True)
async def setlog(interaction: discord.Interaction, channel: discord.TextChannel):
    guildsettings[str(interaction.guild.id)] = channel.id
    savedata()
    await interaction.response.send_message(f"✅ Invite logs set to {channel.mention}")

@bot.tree.command(name="resetinvites", description="Reset a user invites (Admin)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User", reason="Reason")
@app_commands.default_permissions(administrator=True)
async def resetcmd(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    guildid = str(interaction.guild.id)
    userid = str(user.id)
    oldtotal = gettotalinvites(interaction.guild, user)
    
    if guildid in invitetracker and userid in invitetracker[guildid]:
        del invitetracker[guildid][userid]
    savedata()
    
    embed = discord.Embed(title="🔄 Invites Reset", color=0xff0000)
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Old Total", value=str(oldtotal), inline=True)
    embed.add_field(name="New Total", value="0", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.command()
async def unclaim(ctx):
    try:
        if ctx.channel.category_id != SUPPORT_CATEGORY_ID:
            await ctx.send("❌ This command only works in support tickets.")
            return
    except:
        await ctx.send("❌ Unable to verify channel category.")
        return
    
    is_owner = any(role.id == OWNER_ROLE_ID for role in ctx.author.roles)
    is_super_admin = ctx.author.id in SUPER_ADMINS
    if not (is_owner or is_super_admin):
        await ctx.send("❌ Only owner & super owner can unclaim support tickets.")
        return
    
    data = load_ticket_data()
    for uid, info in list(data.get("user_support_tickets", {}).items()):
        if info.get("channel_id") == ctx.channel.id:
            if info.get("opener") == ctx.author.id:
                await ctx.send("❌ You cannot unclaim a ticket you opened.")
                return
            
            prev_claimer = info.get("claimer")
            info["claimer"] = None
            info["claimed_at"] = None
            save_ticket_data(data)
            
            try:
                if prev_claimer:
                    prev_member = ctx.guild.get_member(prev_claimer)
                    if prev_member:
                        await ctx.channel.set_permissions(prev_member, send_messages=True)
            except:
                pass
            
            all_staff = [ctx.guild.get_role(role_id) for role_id in STAFF_ROLE_IDS]
            for role in all_staff:
                if role:
                    await ctx.channel.set_permissions(role, send_messages=True)
            
            await ctx.send("🔓 Ticket unclaimed. Everyone can type again.")
            return
    
    await ctx.send("❌ No support ticket found for this channel.")

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN not found in environment variables!")
    else:
        print("🌐 Keep-alive server started on http://0.0.0.0:8080 - visit to see 'I'm alive!'")
        bot.run(TOKEN)
