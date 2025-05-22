import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiomysql
import sys
import os
import logging
import json
import datetime
import gacha
from leveling import Leveling
from dotenv import load_dotenv
from util.scrape_wiki import scrape_cookies as scrape_cookie1
from util.scrape_wiki_ob import scrape_cookies as scrape_cookie2
from cookie_info import CookieInfo
from gacha import GachaInteraction, HelpView
from market import Business
import misc
from psyche import Persona
import asyncio
from asyncio import Lock
from debug import Prompt, Login

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
    'cookie_info' : CookieInfo(bot),
    'gacha' : GachaInteraction(bot),
    'misc' : misc.MiscCMD(bot),
    'psyche' : Persona(bot),
    'market': Business(bot)
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
        
        # Get active threads
        async for thread in channel.archived_threads(limit=None):
            total_threads_processed += 1
            
            # Check if thread has any reactions
            has_reactions = False
            async for message in thread.history(limit=1):  # Just check the first message (thread starter)
                if message.reactions:
                    has_reactions = True
                    break
            
            if not has_reactions:
                unreacted_threads.append(thread)
        
        # Also check currently active threads
        if hasattr(channel, 'threads'):
            for thread in channel.threads:
                total_threads_processed += 1
                
                has_reactions = False
                async for message in thread.history(limit=1):
                    if message.reactions:
                        has_reactions = True
                        break
                
                if not has_reactions:
                    unreacted_threads.append(thread)
        
        if not unreacted_threads:
            await interaction.followup.send(f"No unreacted threads found in the channel! (Scanned {total_threads_processed} threads)")
            return
        
        # Process each unreacted thread
        processed_threads = []
        failed_threads = []
        
        for thread in unreacted_threads:
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
        
        # Get active threads
        async for thread in channel.archived_threads(limit=None):
            total_threads_processed += 1
            
            # Check if thread has any reactions
            has_reactions = False
            async for message in thread.history(limit=1):  # Just check the first message (thread starter)
                if message.reactions:
                    has_reactions = True
                    break
            
            if not has_reactions:
                unreacted_threads.append(thread)
        
        # Also check currently active threads
        if hasattr(channel, 'threads'):
            for thread in channel.threads:
                total_threads_processed += 1
                
                has_reactions = False
                async for message in thread.history(limit=1):
                    if message.reactions:
                        has_reactions = True
                        break
                
                if not has_reactions:
                    unreacted_threads.append(thread)
        
        if not unreacted_threads:
            await interaction.followup.send(f"No unreacted threads found in the channel! (Scanned {total_threads_processed} threads)")
            return
        
        # Process each unreacted thread
        processed_threads = []
        failed_threads = []
        
        for thread in unreacted_threads:
            result = await award_gems_to_thread_participants(bot, thread.id)
            
            if result is not None:
                processed_threads.append({
                    'thread': thread,
                    'awarded_users': result
                })
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
        com_and_info = [["/help", "See available commands"],
                        ["/level", "Display the level of a user"],
                        ["/leaderboard", "Display the leaderboard for this server"], 
                        ["/wiki", "View wiki info for a character"], 
                        ["/build", "View the best stats for a character"],
                        ["/pull", "Spend gems, gain a character"], 
                        ["/multipull", "Spend more gems, get multiplate characters"], 
                        ["/profile", "View your overall gacha stats"], 
                        ["/trivia", "Answer questions, get gems"], 
                        ["/crumble", "Destory a character you own in return for essence"], 
                        ["/featured", "View who is rate-up on /pull"], 
                        ["/fiftyfifty", "See if you lost/won your last rate-up chance"], 
                        ["/expand", "Spend essence, gain more inventory slots"], 
                        ["/promote", "Lose dupes, gain Chrono level"], 
                        ["/hug", "Recieve a warm hug"], 
                        ["/setfav", "Set a character to appear on your profile"], 
                        ["/balance", "View how many gems/essence you have"], 
                        ["/profilecolor", "Change the embed color of your profile"], 
                        ["/viewcharacter", "View any character in the gacha pool"], 
                        ["/daily", "Recieve a large sum of gems every 24hrs"],
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
        await cogs["gacha"].crystalOnMessage(message=message, valid_time=valid_time)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.User):
        '''
        Runs whenever a user joins the server

        params:
            member (discord.User) : User object of the user that joined
        '''
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_ID FROM USER WHERE USER_ID = %s", member.id)
                userExists = await cursor.fetchall()
                if len(userExists) != 0:
                    return
                roleToAdd = discord.utils.get(member.guild.roles, name='Chocolate II')
                await member.add_roles(roleToAdd)

    @app_commands.command(name="declare", description="admin panel")
    async def declare(self, interaction: discord.Interaction, prompt: str):
        member = interaction.user
        
        '''
        Admin commands for xp boosting and extra (more will be added later)

        params:
            interaction (discord.Interaction) : Interaction object to respond to.
            prompt (str) : the given prompt to run within the function
        '''
        # Experienced role
        if discord.utils.get(interaction.guild.roles, id=1083847502580695091) in interaction.user.roles:
            split = prompt.split(' ')

        '''fix this'''
        if prompt == Prompt.XP_BOOST.value: 
            boost = int(split[1])
            days = int(split[2])
            Leveling.MINEXP *= boost
            Leveling.MAXEXP *= boost
            await interaction.response.send_message(f"Double XP Started for {days} days")
            print(f'Double XP Started at {datetime.datetime.now()} for {days} days by {interaction.user.name}||{interaction.user.id}')

        if prompt == Prompt.CRK_SCRAPE.value:
            await interaction.response.defer()
            res = await scrape_cookie1(self.bot)
            
            if not res:
                await interaction.followup.send("No new cookies found.", ephemeral=True)
            else:
                # Extract cookie names from the list of Cookie objects
                cookie_names = [cookie.name for cookie in res]
                await interaction.followup.send(f"Updated {len(res)} cookies: {', '.join(cookie_names)}", ephemeral=True)

        if prompt == Prompt.CROB_SCRAPE.value:
            await interaction.response.defer()
            res = await scrape_cookie2(self.bot)
            await interaction.followup.send('updated cookies!', ephemeral=True)

        if prompt == Prompt.USER_INV.value:
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
            
        if prompt == Prompt.GIVE_GEM.value:
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

        if prompt == Prompt.EXPAND_FIX.value:
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

        if prompt == Prompt.QOTD_GEMS.value:
            await interaction.response.defer()

            QOTD_CHANNEL_ID = 1095876259315204226
            
            await interaction.followup.send("🔍 Scanning for threads with no reactions and awarding gems...")
            
            await scan_and_reward_unreacted_threads(bot, QOTD_CHANNEL_ID, interaction)

    ''' This section is for the "daily reminder" for CRK for guild contri'''
    # Send the message!
    @tasks.loop(hours=24)
    async def daily_ping(self):
        channel = self.bot.get_channel(1042253069196480542)
        if channel:
            ping_message = f"<@&{1042250208534343763}> be sure to contribute... there's only 2 more hours until tickets refresh!"
            await channel.send(ping_message)
            print(f"Sent daily ping at {datetime.datetime.utcnow()}")
        else:
            print("Error: Could not find channel.")
    
    # Do all of this before starting the "oh is it time yet?" loop
    @daily_ping.before_loop
    async def before_daily_ping(self):
        await self.bot.wait_until_ready()
        seconds = await self.seconds_until_9am()
        await asyncio.sleep(seconds)
    
    # check how much longer we need to wait before sending the alert
    async def seconds_until_9am(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        target_hour = 13  # 13:00 UTC = 9:00 AM ET
        target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if now.hour >= target_hour:
            target += datetime.timedelta(days=1)
        return (target - now).total_seconds()
    
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
