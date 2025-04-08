import discord
from discord import app_commands
from discord.ext import commands
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
from scrapebuild import BuildScrape, fullScrape

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
    'market': Business(bot),
    'buildscrape' : fullScrape(bot)
    }

# bot settings
f = open('bot_settings.json')
data = json.load(f)
if data['xp_modifier']['enabled']:
    Leveling.MINEXP *= data['xp_modifier']['multiplier']
    Leveling.MAXEXP *= data['xp_modifier']['multiplier']

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
        #if discord.utils.get(interaction.guild.roles, id=1083847502580695091) in interaction.user.roles:
            #split = prompt.split(' ')

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

        if prompt == Prompt.HSR_BUILD.value:
            async with self.lock:
                await interaction.response.defer()
                try:
                    fullScrape.fullScrapeBuild(self, interaction)
                    await interaction.response.send_message("Done! Check /build!")
                except Exception as e:
                    await interaction.followup.send(f"Error! {e}")

        if prompt == Prompt.QOTD_GEMS.value:
            
            '''
            The idea:
                - parameters would be the thread id
                - taking the thread id, scan the messages to find unique user IDS
                - award 300 gems to each unique user
            '''
            await interaction.response.defer()
            await interaction.followup.send(f"Enter the thread ID to reward users.")

            def check(message: discord.Message):
                    return message.author.id == member.id and message.channel.id == interaction.channel.id
            
            try:
                msg = await interaction.client.wait_for('message', check=check, timeout=90.0)
                thread_id = int(msg.content)

                #get the thread
                thread = await bot.fetch_channel(thread_id)
                if isinstance(thread, discord.Thread):
                    #grab all QOTD answer-ers
                    qotd_user_ids = set()
                    async for message in thread.history(limit=None):
                        if message.author:  # Ensure the author is valid
                            qotd_user_ids.add(message.author.id)
                    qotd_awarded = {}

                    #now, reward people with gems!
                    qotd_award = 300
                    async with self.bot.db.acquire() as conn:
                        async with conn.cursor() as cursor:
                            for qotd_user in qotd_user_ids:
                                await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (qotd_user,))
                                gems_old = await cursor.fetchone()
                                await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS + %s WHERE USER_ID = %s", (qotd_award,qotd_user,))
                                await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (qotd_user,))
                                gems_new = await cursor.fetchone()
                                qotd_awarded[qotd_user] = (gems_old[0], gems_new[0])
                        await conn.commit()
                    #print to show who was given gems
                    for key, value in qotd_awarded.items():
                        await interaction.followup.send(f"Added {qotd_award} gems to <@{key}>.\nNew vs Old Gems: {value}.")
            except:
                await interaction.followup.send(f"Invalid thread ID")

                
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
    


bot.run(os.environ.get('SORA_TOKEN'))
