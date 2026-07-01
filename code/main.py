''' External Imports '''
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiomysql
import sys
import os
import logging
import json
import datetime
from dotenv import load_dotenv
import asyncio
from asyncio import Lock
import math

''' Internal imports '''
from leveling import Leveling
#from util.scrape_wiki import scrape_cookies as scrape_cookie1
#from util.scrape_wiki_ob import scrape_cookies as scrape_cookie2
from market import Business
from debug import Prompt, Login
from knowledge import Smart
from collect import Collection_BASE
from quests import  QuestSystem
from reaction_roles import ReactionRoles
from prestige_calculator import handle_monthly_prestige_command
from dailies import AutomationCog

''' OLD imports '''
# from gacha import GachaInteraction, HelpView
# from code.deprecated.psyche import Persona
# from code.deprecated.cookie_info import CookieInfo
# import misc


class HelpView(discord.ui.View):
    '''
    HelpView Class:
        - To make the /help commannd look neat
            -> limits and UI 
    '''
    page = 1
    COMMANDS_PER_PAGE = 8

    def __init__(self, com_and_info, last_interaction: discord.Interaction, name: discord.User, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.com_and_info = com_and_info
        self.page = 1
        self.pages = math.ceil(len(self.com_and_info) / self.COMMANDS_PER_PAGE)
        self.last_interaction = last_interaction
        self.user = name
        self.bot = discord.Client

    async def view_page(self, page_num) -> discord.Embed:
        first_of_page = (page_num - 1) * self.COMMANDS_PER_PAGE
        last_of_page = self.COMMANDS_PER_PAGE * page_num
        if last_of_page > len(self.com_and_info):
            last_of_page = len(self.com_and_info)

        sorted_commands = sorted(self.com_and_info, key=lambda x: x[0].lower())

        em = discord.Embed(title=f"Azalea's Commands")
        bot_pfp = self.last_interaction.client.user.avatar.url
        em.set_thumbnail(url=bot_pfp)

        
        commands = ''
        descriptions = ''
        
        for item in range(first_of_page, last_of_page):
            commands += sorted_commands[item][0] + '\n'
            descriptions += sorted_commands[item][1] + '\n'

        em.add_field(name="Command", value=commands)
        em.add_field(name="Description", value=descriptions)
        em.set_footer(text=f"Page {self.page}/{self.pages}")
        
        return em
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple)
    async def left_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.pages if self.page == 1 else self.page - 1
        await interaction.response.send_message(embed=await self.view_page(self.page), view=self)
        await self.last_interaction.delete_original_response()
        self.last_interaction = interaction

    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def right_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 1 if self.page == self.pages else self.page + 1
        await interaction.response.send_message(embed=await self.view_page(self.page), view=self)
        await self.last_interaction.delete_original_response()
        self.last_interaction = interaction


# load the enviroment variables
load_dotenv()

# start up logging
logging.basicConfig(filename=f'logs/{datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")}')
stderrLogger=logging.StreamHandler()
stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logging.getLogger().addHandler(stderrLogger)

sys.stdout = open(f'logs/{datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")}', 'w')

# discord bot settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.watching, name="the chat logs 👀")
bot = commands.Bot(command_prefix="%", intents=intents, activity=activity)

cogs = {
    'leveling': Leveling(bot),
    'collection' : Collection_BASE(bot),
    'market': Business(bot),
    'smart': Smart(bot),
    'collect': Collection_BASE(bot),
    'quests': QuestSystem(bot),
    'roles': ReactionRoles(bot),
    'dailies': AutomationCog(bot)

    # Deprecated:
    # 'gacha' : GachaInteraction(bot),
    # 'misc' : misc.MiscCMD(bot),
    # 'psyche' : Persona(bot),
    # 'cookie_info' : CookieInfo(bot),
    }

# bot settings
f = open('bot_settings.json')
data = json.load(f)
if data['xp_modifier']['enabled']:
    Leveling.MINEXP *= data['xp_modifier']['multiplier']
    Leveling.MAXEXP *= data['xp_modifier']['multiplier']

async def award_gems_to_thread_participants(bot, thread_id: int, gem_amount: int = 300):
    """
    Awards gems to all unique users who posted in a specific thread.
    
    Args:
        bot: The discord bot instance
        thread_id: The ID of the thread to scan
        gem_amount: Amount of gems to award (default: 300)
    
    Returns:
        dict: Dictionary with user_id as key and tuple of (old_gems, new_gems) as value
        None: If thread not found or error occurred
    """
    try:
        # Get the thread
        thread = await bot.fetch_channel(thread_id)
        if not isinstance(thread, discord.Thread):
            return None
        
        # Grab all unique user IDs from thread messages
        thread_user_ids = set()
        async for message in thread.history(limit=None):
            if message.author and not message.author.bot:  # Exclude bot messages
                thread_user_ids.add(message.author.id)
        
        if not thread_user_ids:
            return {}
        
        # Award gems to users
        awarded_users = {}
        async with bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                for user_id in thread_user_ids:
                    # Get current gems
                    await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (user_id,))
                    gems_old_result = await cursor.fetchone()
                    gems_old = gems_old_result[0] if gems_old_result else 0
                    
                    # Update gems
                    await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS + %s WHERE USER_ID = %s", (gem_amount, user_id))
                    
                    # Get new gems amount
                    await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (user_id,))
                    gems_new_result = await cursor.fetchone()
                    gems_new = gems_new_result[0] if gems_new_result else gem_amount
                    
                    awarded_users[user_id] = (gems_old, gems_new)
            
            await conn.commit()
        
        return awarded_users
    
    except Exception as e:
        print(f"Error awarding gems to thread {thread_id}: {e}")
        return None


async def scan_and_reward_unreacted_threads(bot, channel_id: int, interaction):
    """
    Scans a channel for threads with no reactions and awards gems to participants.
    
    Args:
        bot: The discord bot instance
        channel_id: The ID of the channel to scan
        interaction: The discord interaction object
    """
    try:
        # Get the channel
        channel = await bot.fetch_channel(channel_id)
        if not channel:
            await interaction.followup.send("Channel not found!")
            return
        
        # Find all threads with no reactions
        unreacted_threads = []
        total_threads_processed = 0
        
        await interaction.followup.send("🔍 Scanning archived threads...")
        
        # Get archived threads with progress updates
        try:
            async for thread in channel.archived_threads(limit=100):  # Limit to prevent timeout
                total_threads_processed += 1
                
                # Progress update every 10 threads
                if total_threads_processed % 10 == 0:
                    await interaction.followup.send(f"📊 Scanned {total_threads_processed} archived threads so far...")
                
                # Check if thread has any reactions
                has_reactions = False
                try:
                    async for message in thread.history(limit=1):  # Just check the first message (thread starter)
                        if message.reactions:
                            has_reactions = True
                            break
                except:
                    # Skip threads we can't access
                    continue
                
                if not has_reactions:
                    unreacted_threads.append(thread)
                    
                # Add small delay to prevent rate limiting
                await asyncio.sleep(0.1)
                    
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error scanning archived threads: {e}")
        
        await interaction.followup.send("🔍 Scanning active threads...")
        
        # Also check currently active threads
        if hasattr(channel, 'threads'):
            for thread in channel.threads:
                total_threads_processed += 1
                
                has_reactions = False
                try:
                    async for message in thread.history(limit=1):
                        if message.reactions:
                            has_reactions = True
                            break
                except:
                    continue
                
                if not has_reactions:
                    unreacted_threads.append(thread)
        
        await interaction.followup.send(f"📋 Found {len(unreacted_threads)} unreacted threads out of {total_threads_processed} total threads.")
        
        if not unreacted_threads:
            await interaction.followup.send(f"No unreacted threads found in the channel!")
            return
        
        # Process each unreacted thread with progress updates
        processed_threads = []
        failed_threads = []
        
        await interaction.followup.send(f"⚙️ Processing {len(unreacted_threads)} unreacted threads...")
        
        for i, thread in enumerate(unreacted_threads, 1):
            # Progress update
            await interaction.followup.send(f"🔄 Processing thread {i}/{len(unreacted_threads)}: {thread.name}")
            
            result = await award_gems_to_thread_participants(bot, thread.id)
            
            if result is not None:
                processed_threads.append({
                    'thread': thread,
                    'awarded_users': result
                })
                
                # Add ✅ reaction to the thread's first message after processing
                try:
                    async for message in thread.history(limit=1, oldest_first=True):
                        await message.add_reaction("✅")
                        break
                except Exception as e:
                    print(f"Failed to add reaction to thread {thread.name}: {e}")
                    
                # Small delay to prevent rate limiting
                await asyncio.sleep(0.5)
            else:
                failed_threads.append(thread)
        
        # Send results
        if processed_threads:
            await interaction.followup.send(f"✅ Successfully processed {len(processed_threads)} unreacted threads:")
            
            for thread_data in processed_threads:
                thread = thread_data['thread']
                awarded_users = thread_data['awarded_users']
                
                if awarded_users:
                    user_mentions = [f"<@{user_id}>" for user_id in awarded_users.keys()]
                    await interaction.followup.send(f"**Thread:** {thread.name} ({thread.mention})\n**Users awarded 300 gems:** {', '.join(user_mentions)}")
                else:
                    await interaction.followup.send(f"**Thread:** {thread.name} ({thread.mention}) - No users to award")
        
        if failed_threads:
            thread_links = [f"[{thread.name}]({thread.jump_url})" for thread in failed_threads]
            await interaction.followup.send(f"❌ **Failed to process these threads:**\n" + "\n".join(thread_links))
            
    except Exception as e:
        await interaction.followup.send(f"Error scanning channel: {e}")

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lock = Lock()

    @app_commands.command(name="help", description="Need assistance?")
    async def help(self, interaction : discord.Interaction):
        '''
        Help command displays all current commands

        params:
            interaction (discord.Interaction) : slash command object
        '''
        com_and_info = [
                        ["/level", "Check server leveling progress of any user"],
                        ["/leaderboard", "Display the leaderboard for this server"],
                        ["/build", "View what character stats to aim for [HSR/....]"],
                        ["/meta", "See what the current metas are for each gamemmode [CRK/HSR/...]"],
                        ["/shop", "Buy items with the currencies you collect [coins, tickets, ...]"],
                        ["/balance", "View how many coins/tickets you have"], 
                        
                        #["/wiki", "View wiki info for a character"], 
                        
                        #["/pull", "Spend gems, gain a character"], 
                        #["/multipull", "Spend more gems, get multiplate characters"], 
                        #["/crumble", "Destory a character you own in return for essence"], 
                        #["/featured", "View who is rate-up on /pull"], 
                        #["/fiftyfifty", "See if you lost/won your last rate-up chance"], 
                        #["/expand", "Spend essence, gain more inventory slots"], 
                        #["/promote", "Lose dupes, gain Chrono level"], 
                        
                        #["/profile", "View your overall gacha stats"], 
                        #["/setfav", "Set a character to appear on your profile"], 
                        #["/profilecolor", "Change the embed color of your profile"], 
                        #["/viewcharacter", "View any character in the gacha pool"], 
                        

                        #["/trivia", "Answer questions, get gems"], 
                        #["/hug", "Recieve a warm hug"], 
                        #["/daily", "Recieve a large sum of gems every 24hrs"],
                        ]


        
        view = HelpView(com_and_info=com_and_info, last_interaction=interaction, name=interaction.user)
        await interaction.response.send_message(embed=await view.view_page(1), view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        '''
        Runs functions whenever a message is sent

        params:
            message (discord.Message) : Message object of message sent
        '''
        valid_time = await cogs["leveling"].levelUp(message=message)
        #await cogs["collect"].crystalOnMessage(message=message, valid_time=valid_time)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        '''
        Runs whenever a user joins the server

        params:
            member (discord.User) : User object of the user that joined
        '''

        # Give "divider" roles (?)
        divider_roles = [1369751999809323109,
                         1369751936395645049,
                         1369751745927970997,
                         1369735211306188880,
                         1369750747658588201,
                         
                         1521712119513481276 #add lvl 1 role here for now as a hotfix
                         ]

        for role_id in divider_roles:
            roleToAdd = member.guild.get_role(role_id)
            if roleToAdd:
                await member.add_roles(roleToAdd)


        # Log join in #welcome
        channel = self.bot.get_channel(996903186168283220)
        if channel:
            await channel.send(f"Welcome to Nurture, <@{member.id}>! 💖\nWe hope you enjoy your stay! 🥰")

        # Send a message to #general
        channel = self.bot.get_channel(996906490663276575)
        if channel:
            message = await channel.send(f"Everyone please welcome our latest (and maybe greatest?) member... <@{member.id}>! <:poggies:1404867219002753045>")
            await message.add_reaction("<:poggies:1404867219002753045>")


        # Automatically set the user to level 1
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT LEVEL FROM USER WHERE USER_ID = %s", (member.id,))
                userExists = await cursor.fetchone()
                if userExists:
                    # User was here before... let's give them their role back
                    for index in enumerate(len(cogs['leveling'].roles)):
                        pass
                else:
                    # NEW MEMBER!
                    # Numbers = ID for level 0 role
                    roleToAdd = member.guild.get_role(1521712119513481276)
                    if roleToAdd:
                        await member.add_roles(roleToAdd)

        # Send a welcome message!
        welcome_gif = discord.File("assets/neko_wave.gif")
        await member.send(
            "# Welcome to Nurture!\n"
            "## Here's a quick few things you should know!\n"
            "### 1.) Nurture has a level system in place to hinder spammers/raiders\n"
            "> - There are cool perks for leveling up, so check here! https://ptb.discord.com/channels/996903185685946490/1084978040821514241\n"
            "### 2.) If you have any questions, please reach out to mods!\n"
            "> - Answers to our FAQ can be found here! https://ptb.discord.com/channels/996903185685946490/1365023830145499259\n"
            "### 3.) Make sure to select your roles!\n"
            "> - They can all be found here https://ptb.discord.com/channels/996903185685946490/1393934563725541457/1393973359267545148\n"
            "### 4.) Please follow rules!\n"
            "> - Read more about them here if you often break them, just to know :) https://ptb.discord.com/channels/996903185685946490/1042241938730012783\n"
            "### 5.) Feel free to ping @helper roles! We are here to help!\n\n # Above all else... enjoy your stay! :)",
            file=welcome_gif
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.bot.get_channel(1069755829126971392)
        if channel:
            await channel.send(
                f"<:sadge:1404868061571579904> **Member Left**\n"
                f"{member.display_name} (<@{member.id}> - {member.id}) has left the server."
            )

    @app_commands.command(name="declare", description="admin panel")
    async def declare(self, interaction: discord.Interaction, prompt: str):
        member = interaction.user
        
        '''
        Admin commands for xp boosting and extra (more will be added later)

        params:
            interaction (discord.Interaction) : Interaction object to respond to.
            prompt (str) : the given prompt to run within the function
        '''

        # Check if the user is allowed to make a request
        allowed_roles = {1364999650762948628, # Guide
                         1377746510816481450, # Test Server
                         1067995521270157452 # Owner
                         }
        
        if any(role.id in allowed_roles for role in interaction.user.roles):
            split = prompt.split(' ')

            # Reaction role stuff handled in reaction_roles.py
            reaction_roles_cog = self.bot.get_cog('ReactionRoles')
            if reaction_roles_cog:
                handler = reaction_roles_cog.get_reaction_role_handler()
                if await handler(interaction, prompt):
                    # Done!
                    return

            if prompt == Prompt.XP_BOOST.value: 
                boost = int(split[1])
                days = int(split[2])
                Leveling.MINEXP *= boost
                Leveling.MAXEXP *= boost
                await interaction.response.send_message(f"Double XP Started for {days} days")
                print(f'Double XP Started at {datetime.datetime.now()} for {days} days by {interaction.user.name}||{interaction.user.id}')

            elif prompt == Prompt.CRK_SCRAPE.value:
                await interaction.response.defer()
                res = await scrape_cookie1(self.bot)
                
                if not res:
                    await interaction.followup.send("No new cookies found.", ephemeral=True)
                else:
                    # Extract cookie names from the list of Cookie objects
                    cookie_names = [cookie.name for cookie in res]
                    await interaction.followup.send(f"Updated {len(res)} cookies: {', '.join(cookie_names)}", ephemeral=True)

            elif prompt == Prompt.CROB_SCRAPE.value:
                await interaction.response.defer()
                res = await scrape_cookie2(self.bot)
                await interaction.followup.send('updated cookies!', ephemeral=True)

            elif prompt == Prompt.USER_INV.value:
                await interaction.response.defer()
                await interaction.followup.send(f"Enter the USER_ID for who's inventory slot # needs fixed.")

                # Wait for the next message
                def check(message: discord.Message):
                    return message.author.id == member.id and message.channel.id == interaction.channel.id
            
                try:
                    msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                    userid_to_fix = msg.content
                    async with self.bot.db.acquire() as conn:
                        async with conn.cursor() as cursor:

                            #grab EVERY SINGLE entry to check the amount
                            await cursor.execute("SELECT ITEM_ID FROM ITEM WHERE USER_ID = %s", (userid_to_fix,))
                            all_owned_items = await cursor.fetchall()
                            number_of_items = len(all_owned_items)

                            #see the current amount for later reference
                            await cursor.execute("SELECT USER_INV_SLOTS_USED FROM USER WHERE USER_ID = %s", (userid_to_fix,))
                            original_set_slots = await cursor.fetchone()
                            original_set_slots = original_set_slots[0]

                            #if values are equal, return no issue
                            if original_set_slots == number_of_items:
                                await interaction.followup.send(f"No issue found for user with ID: {userid_to_fix}.\nOriginally, they had {original_set_slots} slots. They own {number_of_items} characters.")
                            else:
                                await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = %s WHERE USER_ID = %s", (number_of_items, userid_to_fix))
                                await conn.commit()
                                await interaction.followup.send(f"Good catch!\nUser with ID: {userid_to_fix} originally, they had {original_set_slots} slots set. However, they own {number_of_items} characters. They now have {number_of_items} slots to match the {number_of_items} characters they own.")
                        await conn.commit()
                except asyncio.TimeoutError:
                    await interaction.channel.send("You didn't send a message in time.")  
                
            elif prompt == Prompt.GIVE_GEM.value:
                await interaction.response.defer()
                await interaction.followup.send(f"Enter the USER_ID + gem amount to award.")

                def check(message: discord.Message):
                    return message.author.id == member.id and message.channel.id == interaction.channel.id
            
                try:
                    msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                    id_combo_gems = msg.content
                    gems_and_id = id_combo_gems.split()
                    gems = gems_and_id[1]
                    id_to_fix = gems_and_id[0]

                    async with self.bot.db.acquire() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (id_to_fix,))
                            gems_old = await cursor.fetchone()
                            await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS + %s WHERE USER_ID = %s", (gems,id_to_fix,))
                            await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (id_to_fix,))
                            gems_new = await cursor.fetchone()
                            await interaction.followup.send(f"Old Gems: {gems_old[0]}.\nAdded {gems} gems to user with ID: {id_to_fix}.\nNew Gems: {gems_new[0]}.")
                        await conn.commit()
                except:
                    try:
                        await interaction.followup.send(f"{gems_and_id} is invalid.")
                    except:
                        await interaction.followup.send(f"This does not work.")

            elif prompt == Prompt.EXPAND_FIX.value:
                return # not needed rn
                '''
                Since essence to expand now costs 15x less, 
                compensate users who spent essence to expand already

                Give back essence in correlation to current expand times
                '''
                await interaction.response.defer() #let it cook

                async with self.lock:
                    try:
                        async with self.bot.db.acquire() as conn:
                            async with conn.cursor() as cursor:
                                await cursor.execute("SELECT EXPAND_PURCHASES, USER_ID FROM USER;")
                                expand_data = await cursor.fetchall()
                            
                                fixedEssencePPL = []

                                for person in expand_data:
                                    person_expandAMT = person[0]
                                    personID = person[1]
                                    if person_expandAMT != 0:
                                        '''
                                        This equation currently compensates:
                                        EssenceCostEquation = (125*(TimesPurchased[0]**2)) + 150

                                        Changed to (Dec 25, 2024):
                                        EssenceCostEquation = (8*(TimesPurchased[0]**2)) + 60

                                        This is changed by a factor of 1/15.
                                        The equation compensates the difference between each sum as the return value:
                                        returnEssence = (117 * (person_expandAMT * (person_expandAMT + 1) * (2 * person_expandAMT + 1)) / 6) + (90 * (person_expandAMT + 1))
                                        '''
                                        returnEssence = (117 * (person_expandAMT * (person_expandAMT + 1) * (2 * person_expandAMT + 1)) / 6) + (90 * (person_expandAMT + 1))
                                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s WHERE USER_ID = %s", (returnEssence,personID,))
                                        fixedEssencePPL.append(f"<@{personID}> gained {returnEssence} essence back. They had expanded {person_expandAMT} times.")
                                        await conn.commit()
                                
                                #format response out
                                response_message = "\n".join(fixedEssencePPL)
                                await interaction.followup.send(f"Fixed Essences for users:\n{response_message}")
                    except Exception as e:
                        await interaction.response.send_message(f"Compensation cannot be compensated. Error with code! {e}")

            elif prompt == Prompt.QOTD_GEMS.value:
                await interaction.response.defer()

                QOTD_CHANNEL_ID = 1095876259315204226
                
                await interaction.followup.send("🚀 Starting QOTD gems distribution process...")
                
                await scan_and_reward_unreacted_threads(bot, QOTD_CHANNEL_ID, interaction)

            elif prompt == Prompt.DEBUG_ROLE_CHECK.value:
                await interaction.response.defer()
                res = await cogs['leveling'].check_user_roles(interaction.guild)
                await interaction.followup.send(f'Role check complete! {res}', ephemeral=True)

            elif prompt == Prompt.MASS_DM.value:
                # Create a modal to get the message content
                class MessageModal(discord.ui.Modal):
                    def __init__(self):
                        super().__init__(title="Mass DM Message")
                        
                    message_content = discord.ui.TextInput(
                        label="Message to send",
                        style=discord.TextStyle.paragraph,
                        placeholder="Enter the message you want to send to all members...",
                        required=True,
                        max_length=2000
                    )
                    
                    async def on_submit(self, interaction: discord.Interaction):
                        await interaction.response.defer(ephemeral=True)
                        
                        dm_message = self.message_content.value.strip()
                        
                        if not dm_message:
                            return await interaction.followup.send("❗ You must provide a message to send.", ephemeral=True)
                        
                        # Handle file attachment if present (from original interaction)
                        file = None
                        if interaction.message and interaction.message.attachments:
                            file = await interaction.message.attachments[0].to_file()
                        
                        failed = []
                        success = 0
                        
                        # Send initial status message
                        status_msg = await interaction.followup.send("📤 Sending DMs... This may take a while.", ephemeral=True)
                        
                        for member in interaction.guild.members:
                            if member.bot:
                                continue
                            try:
                                if file:
                                    await member.send(content=dm_message, file=file)
                                else:
                                    await member.send(content=dm_message)
                                success += 1
                            except Exception:
                                failed.append(member)
                        
                        # Update with final results
                        await status_msg.edit(content=f"✅ Sent DMs to {success} members.\n❌ Failed to send to {len(failed)} members.")
                
                # Send the modal to the user
                modal = MessageModal()
                await interaction.response.send_modal(modal)

            elif prompt == Prompt.META_CHANGE.value:

                await interaction.response.defer()

                async with self.bot.db.acquire() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute("SELECT DISTINCT GAME FROM META")
                            valid_games = await cursor.fetchall()
                            valid_games = tuple(game[0] for game in valid_games)

                            # Ask for what game
                            form_valid_games = "\n".join([f"> {game}" for game in valid_games])
                            await interaction.followup.send(f"What game would you like to tweak?\n{form_valid_games}")

                            # Only continue if valid input
                            async def getValidOption(valid_choices):
                                while (True):
                                    def check(message: discord.Message):
                                        return message.author.id == member.id and message.channel.id == interaction.channel.id
                                
                                    try:
                                        msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                                        chosen = msg.content.strip()
                                        if chosen.lower() in (choice.lower() for choice in valid_choices):
                                            # Done!
                                            return chosen
                                        else:
                                            # Try again
                                            raise NameError

                                    except TimeoutError:
                                        await interaction.followup.send(f"You took to long to respond! Please try again.", ephemeral=True)
                                        return None
                                    except NameError:
                                        await interaction.followup.send(f"{chosen} is invalid. Please try again.", ephemeral=True)     
                                        return None                   

                            # If we continue, valid game chosen
                            game_chose = await getValidOption(valid_games)
                            if game_chose:
                                await cursor.execute("SELECT DISTINCT MODE FROM META WHERE GAME = %s", game_chose.title())
                                valid_modes = await cursor.fetchall()
                                valid_modes = tuple(mode[0] for mode in valid_modes)

                            else:
                                # Stop if no valid input returned
                                return

                            # Ask for what gamemode after formatting
                            form_valid_modes = "\n".join([f"> {mode}" for mode in valid_modes])
                            await interaction.followup.send(f"What {game_chose} gamemode would you like to tweak?\n{form_valid_modes}")
                            mode_chose = await getValidOption(valid_modes)

                            # Loop to change links
                            while(True):
                                if mode_chose:
                                    await cursor.execute("SELECT LINK1, LINK2, LINK3 FROM META WHERE GAME = %s AND MODE = %s", (game_chose, mode_chose),)
                                    current_links = await cursor.fetchall()

                                    # Get the first row (since you're querying for a specific game/mode combination)
                                    row = current_links[0]  
                                    # Now convert each column, replacing None with "N/A"
                                    current_links = tuple(link if link is not None else "N/A" for link in row)
                                else:
                                    # Stop if no valid input returned
                                    return
                                
                                # Quick formatting, then ask for what link to change
                                formatted_links = "\n".join([f"> {i}: {link}" for i, link in enumerate(current_links, start=1)])
                                await interaction.followup.send(f"Here are the current links:\n{formatted_links}\n\nWhich would you like to change?\nGive a number like 1, 2, 3")
                                link_change = await getValidOption(("1", "2", "3"))

                                # If valid link number given, update that link! But first lets ask what to change it with
                                if link_change:
                                    await interaction.followup.send(f"What would you like to change link #{link_change} to?")
                                    def check(message: discord.Message):
                                        return message.author.id == member.id and message.channel.id == interaction.channel.id
                                
                                    try:
                                        msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                                        new_link = msg.content.strip()
                                    except TimeoutError:
                                        await interaction.followup.send(f"You didnt send a message in time! Please try again.")
                                        return
                                    
                                    # Let's update!
                                    if link_change == "1":
                                        await cursor.execute(f"UPDATE META SET LINK1 = %s WHERE GAME = %s AND MODE = %s", (new_link, game_chose, mode_chose),)
                                    elif link_change == "2":
                                        await cursor.execute(f"UPDATE META SET LINK2 = %s WHERE GAME = %s AND MODE = %s", (new_link, game_chose, mode_chose),)
                                    elif link_change == "3":
                                        await cursor.execute(f"UPDATE META SET LINK3 = %s WHERE GAME = %s AND MODE = %s", (new_link, game_chose, mode_chose),)
                                    else:
                                        pass

                                    # Done!
                                    
                                    await interaction.followup.send(f"Successfuly changed the link for {game_chose} | {mode_chose} to now be {new_link}!\nDo /meta to view your change.", ephemeral=False)
                                    
                                    # Log it all to a channnel!
                                    log_channel = 1378566736319741952
                                    channel = self.bot.get_channel(log_channel)
                                    if channel:
                                        await channel.send(f"<@{interaction.user.id}> has successfully changed the link for {game_chose}->{mode_chose} to now be {new_link}!\nDo /meta to view your change.")
                                    else:
                                        await interaction.followup.send(f"No channel message b/c this is on test server. It would be https://ptb.discord.com/channels/996903185685946490/{log_channel}", ephemeral=True)

                                    # Add logging of who and when into the database
                                    await cursor.execute("UPDATE META SET last_edit = %s, EDIT_AUTH = %s WHERE GAME = %s AND MODE = %s", (datetime.datetime.utcnow(), interaction.user.id, game_chose, mode_chose),)
                                    await conn.commit()

                                    # Ask if theres another link to add?
                                    await interaction.followup.send(f"Would you like to add another link? (Y/N)")
                                    def check(message: discord.Message):
                                        return message.author.id == member.id and message.channel.id == interaction.channel.id
                                
                                    try:
                                        msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                                        again_link = msg.content.strip()
                                    except TimeoutError:
                                        await interaction.followup.send(f"You didnt send a message in time! Please try again.")
                                        return
                                    
                                    if again_link:
                                        if again_link.upper() == "Y":
                                            continue
                                        elif again_link.upper() == "N":
                                            break
                                        
                                    # Done!
                                    return

            elif prompt == Prompt.BUILD_CHANGE.value:
                await interaction.response.defer()
    
                # Ask for character name
                await interaction.followup.send("What character would you like to edit?")
                
                def check(message: discord.Message):
                    return message.author.id == member.id and message.channel.id == interaction.channel.id
                
                try:
                    msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                    char_name = msg.content.strip().lower()
                except asyncio.TimeoutError:
                    await interaction.followup.send("You didn't send a message in time.")
                    return
                
                async with self.bot.db.acquire() as conn:
                    async with conn.cursor() as cursor:
                        # Get character info
                        await cursor.execute("SELECT * FROM HSR_BUILD WHERE name = %s", (char_name,))
                        char_data = await cursor.fetchone()
                        
                        if not char_data:
                            await interaction.followup.send(f"Character '{char_name}' not found in database.")
                            return
                        
                        # Display current build info
                        current_info = f"""**Current build for {char_name.title()}:**
                        '''
                        FIX ME
                        '''
                        ```
                        Char data: {char_data}
                        Path: {char_data[2]}
                        Stats: {char_data[3][:200]}{'...' if len(char_data[3]) > 200 else ''}
                        Trace Priority: {char_data[4][:200]}{'...' if len(char_data[4]) > 200 else ''}
                        Substats: {char_data[5][:200]}{'...' if len(char_data[5]) > 200 else ''}
                        Gear Mainstats: {char_data[6][:200]}{'...' if len(char_data[6]) > 200 else ''}
                        Best LC: {char_data[7][:200]}{'...' if len(char_data[7]) > 200 else ''}
                        Best Relics: {char_data[8][:200]}{'...' if len(char_data[8]) > 200 else ''}
                        Best Planar: {char_data[9][:200]}{'...' if len(char_data[9]) > 200 else ''}
                        Best Team: {char_data[10][:200]}{'...' if len(char_data[10]) > 200 else ''}
                        Notes: {char_data[11][:200]}{'...' if len(char_data[11]) > 200 else ''}
                        ```"""
                        
                        await interaction.followup.send(current_info)
                        
                        # Ask what field to change
                        fields = ["path", "stats", "trace_priority", "substats", "gear_mainstats", "best_lc", "best_relics", "best_planar", "best_team", "notes"]
                        field_options = "\n".join([f"{i+1}. {field}" for i, field in enumerate(fields)])
                        
                        await interaction.followup.send(f"What would you like to change?\n```{field_options}```\nEnter the number (1-10):")
                        
                        try:
                            msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                            field_choice = int(msg.content.strip())
                            
                            if field_choice < 1 or field_choice > 10:
                                await interaction.followup.send("Invalid choice. Please enter a number between 1-10.")
                                return
                                
                            selected_field = fields[field_choice - 1]
                            
                        except (asyncio.TimeoutError, ValueError):
                            await interaction.followup.send("Invalid input or timeout.")
                            return
                        
                        # Ask for new value
                        await interaction.followup.send(f"Enter the new value for **{selected_field}**:")
                        
                        try:
                            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
                            new_value = msg.content.strip()
                        except asyncio.TimeoutError:
                            await interaction.followup.send("You didn't send a message in time.")
                            return
                        
                        # Map field names to database columns
                        field_mapping = {
                            "path": "path",
                            "stats": "stats", 
                            "trace_priority": "trapri",
                            "substats": "substats",
                            "gear_mainstats": "gear_mainstats",
                            "best_lc": "bestlc",
                            "best_relics": "bestrelics", 
                            "best_planar": "bestplanar",
                            "best_team": "bestteam",
                            "notes": "notes"}
            
                        db_column = field_mapping[selected_field]
                        
                        # Construct and execute the UPDATE query.
                        # Using an f-string for the column name is safe here because its value is
                        # strictly controlled by the 'fields' list and 'field_mapping' dictionary,
                        # preventing SQL injection. User input is properly parameterized.
                        sql_query = f"UPDATE HSR_BUILD SET {db_column} = %s WHERE name = %s"
                        
                        await cursor.execute(sql_query, (new_value, char_name))
                        await conn.commit()
                        
                        await interaction.followup.send(f"Successfully updated **{selected_field}** for **{char_name.title()}**!")

            elif prompt == Prompt.MONTHLY_PRESTIGE.value:
                await handle_monthly_prestige_command(bot, interaction)

        else:
            await interaction.response.send_message('Not gonna happen 🤓', ephemeral=True)
        
        

    ''' This section is for the "daily reminder" for CRK for guild contri'''
    '''bring this back later ==============='''
    # Send the message!
    # @tasks.loop(hours=24)
    # async def daily_ping(self):
    #     channel = self.bot.get_channel(1042253069196480542)
    #     if channel:
    #         today = datetime.datetime.utcnow().weekday()  # 0=Monday, 1=Tuesday, etc.
            
    #         if today == 1:  # Tuesday - send tally day message without ping
    #             tally_message = "Today is a tally day! Enjoy the day off :)"
    #             await channel.send(tally_message)
    #             return
            
    #         # Calculate ticket count: Wed=3, Thu=6, Fri=9, Sat=12, Sun=15, Mon=18
    #         # Days after Tuesday: Wed=1, Thu=2, Fri=3, Sat=4, Sun=5, Mon=6
    #         if today >= 2:  # Wed-Sun (2-6)
    #             days_after_tuesday = today - 1
    #         else:  # Monday (0)
    #             days_after_tuesday = 6
            
    #         ticket_count = days_after_tuesday * 3  # Start at 3, +3 each day
    #         ticket_count = min(ticket_count, 18)  # Cap at 18
            
    #         ping_message = f"<@&{1042250208534343763}> be sure to contribute... there's only 2 more hours until tickets refresh!\nCurrent tickets: {ticket_count}/18"
            
    #         await channel.send(ping_message)
    #         print(f"Sent daily ping at {datetime.datetime.utcnow()}")
    #     else:
    #         print("Error: Could not find channel.")
    
    
    # # Do all of this before starting the "oh is it time yet?" loop
    # @daily_ping.before_loop
    # async def before_daily_ping(self):
    #     await self.bot.wait_until_ready()
    #     seconds = await self.seconds_until_9am()
    #     await asyncio.sleep(seconds)
    
    # # check how much longer we need to wait before sending the alert
    # async def seconds_until_9am(self):
    #     now = datetime.datetime.now(datetime.timezone.utc)
    #     target_hour = 13  # 13:00 UTC = 9:00 AM ET
    #     target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    #     if now.hour >= target_hour:
    #         target += datetime.timedelta(days=1)
    #     return (target - now).total_seconds()
    
    '''=============== bring this back later ==============='''


# Add the general cog after declaration.
cogs['general'] = General(bot)


@bot.event
async def on_ready():
    '''
    Runs on bot startup
    '''
    print("Ready!")
    pool = await aiomysql.create_pool(host=Login.mysql_login['host'],
                                       user=Login.mysql_login['user'],
                                       password=Login.mysql_login['password'],
                                       db=Login.mysql_login['db'],
                                       port=Login.mysql_login['port'])
    setattr(bot, 'db', pool)
    for key in cogs.keys():
        try:
            await bot.add_cog(cogs[key])
        except discord.errors.ClientException:
            pass
    synced = await bot.tree.sync()

    # Start the "timer" for pinging to Contribute in CRK Guild
    cogs['general'].daily_ping.start()
    


bot.run(os.environ.get('BOT_TOKEN'))
