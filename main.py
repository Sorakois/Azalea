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
from util.scrape_wiki import scrape_cookies

load_dotenv()

logging.basicConfig(filename=f'logs/{datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")}')
stderrLogger=logging.StreamHandler()
stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logging.getLogger().addHandler(stderrLogger)

sys.stdout = open(f'logs/{datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")}', 'w')

mysql_login = {'host':'78.108.218.47',
               'user':'u104092_P8hJJbGHcV',
               'password':'bt1c@A^l^obLB4hAMA8YKAOW',
               'db':'s104092_levels',
               'port':3306}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

activity = discord.Activity(type=discord.ActivityType.watching, name="the chat logs 👀")
bot = commands.Bot(command_prefix="%", intents=intents, activity=activity)

cogs = {'leveling': Leveling(bot)}

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
        em = discord.Embed(title="Help")
        em.add_field(name="", value="Need assistance?", inline=False)
        em.add_field(name="Command", value="/help\n/level\n/leaderboard", inline=True)
        em.add_field(name="Function", value="Assistance on commands\nDisplay the level of a user\nDisplay the leaderboard for this server", inline=True)
        await interaction.response.send_message(embed=em, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await cogs["leveling"].levelUp(message=message)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.User):
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT user FROM levels WHERE user = %s", member.id)
                userExists = await cursor.fetchall()
                if len(userExists) != 0:
                    return
                roleToAdd = discord.utils.get(member.guild.roles, name='Chocolate II')
                await member.add_roles(roleToAdd)

    @app_commands.command(name="declare")
    async def declare(self, interaction: discord.Interaction, prompt: str):
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
                res = scrape_cookies()
                await interaction.response.send_message(f"resolved with: {res}", ephemeral=True)
        else:
            await interaction.response.send_message('You do not have permission to use this command', ephemeral=True)

# Add the general cog after declaration.
cogs['general'] = General(bot)

@bot.event
async def on_ready():
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
    

bot.run(os.environ.get('TEST_TOKEN'))