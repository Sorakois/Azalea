import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import sys
import os
import logging
import json
import datetime
from leveling import Leveling
from dotenv import load_dotenv
from util.scrape_wiki import scrape_cookies as scrape_cookie1
from util.scrape_wiki_ob import scrape_cookies as scrape_cookie2
from cookie_info import CookieInfo
from gacha import GachaInteraction, HelpView
import misc

# load the enviroment variables
load_dotenv()

# start up logging
logging.basicConfig(filename=f'logs/{datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")}')
stderrLogger=logging.StreamHandler()
stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logging.getLogger().addHandler(stderrLogger)

sys.stdout = open(f'logs/{datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")}', 'w')

# start up database connection

mysql_login = {'host':"db-buf-05.sparkedhost.us",
               'user':"u104092_jfUaeyVlqc",
               'password':"^lR0+=!4nvkHd9zQvs0BggFS",
               'db':"s104092_db_update",
               'port':3306}

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
        '''
        Admin commands for xp boosting and extra (more will be added later)

        params:
            interaction (discord.Interaction) : Interaction object to respond to.
            prompt (str) : the given prompt to run within the function
        '''
        # Experienced role
        if discord.utils.get(interaction.guild.roles, id=1083847502580695091) in interaction.user.roles:
            split = prompt.split(' ')

            if split[0] == 'xp-boost':
                boost = int(split[1])
                days = int(split[2])
                Leveling.MINEXP *= boost
                Leveling.MAXEXP *= boost
                await interaction.response.send_message(f"Double XP Started for {days} days")
                print(f'Double XP Started at {datetime.datetime.now()} for {days} days by {interaction.user.name}||{interaction.user.id}')

            if split[0] == 'scrape_cookie':
                await interaction.response.defer()
                res = await scrape_cookie1(self.bot)
                await interaction.followup.send_message(f"resolved with: {res}", ephemeral=True)

            if split[0] == 'scrape_cookie_ob':
                await interaction.response.defer()
                res = await scrape_cookie2(self.bot)
                await interaction.followup.send('updated cookies!', ephemeral=True)
        else:
            await interaction.response.send_message('You do not have permission to use this command', ephemeral=True)

# Add the general cog after declaration.
cogs['general'] = General(bot)

@bot.event
async def on_ready():
    '''
    Runs on bot startup
    '''
    print("Ready!")
    pool = await aiomysql.create_pool(host=mysql_login['host'],
                                       user=mysql_login['user'],
                                       password=mysql_login['password'],
                                       db=mysql_login['db'],
                                       port=mysql_login['port'])
    setattr(bot, 'db', pool)
    for key in cogs.keys():
        try:
            await bot.add_cog(cogs[key])
        except discord.errors.ClientException:
            pass
    synced = await bot.tree.sync()
    


bot.run(os.environ.get('SORA_TOKEN'))
