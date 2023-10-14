import discord
from discord import app_commands
from discord.ext import commands
import datetime
import random
from io import BytesIO
from levelImage import createImage
import re
import aiomysql

roles = {
    "Chocolate II": 1083845379893772350,
    "Chocolate I": 1083845379893772350, 
    "Bronze II": 1083845379893772350, 
    "Bronze I": 1083846147359117332,
    "Silver III": 1083846231886934106, 
    "Silver II": 1083846281031594134,
    "Silver I": 1083846355946045440,
    "Gold III": 1083846397176062002,
    "Gold II": 1083846446631108658,
    "Gold I": 1083846490679689367,
    "Crystal III": 1083846553627787395,
    "Crystal II": 1083846603628089354,
    "Crystal I": 1083846651258613840,
    "Diamond III": 1083846764072812645, 
    "Diamond II": 1083846821799010439, 
    "Diamond I": 1083846870520045599, 
    "Master V": 1083846913301938228,
    "Master IV": 1083847070458331236,
    "Master III": 1083847110740414565,
    "Master II": 1083847154134696065, 
    "Master I": 1083847222610899065,
    "Grandmaster III": 1083847310976499752, 
    "Grandmaster II": 1083847373647785985, 
    "Grandmaster I": 1083847441855561799
}

# roles = {'tier 1': 1135634051479388180, 'tier 2': 1135634087051268216, 'tier 3': 1135634103211925566}

ignoreList = {836367313502208040, 329669053838917632, 400443611105460234}

class Leveling(commands.Cog):

    MINEXP = 10 # 10
    MAXEXP = 25 # 25
    COOLDOWN = 30 # 30
    levelUpChannel = 1135736911948951593

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Display the leaderboard for this server")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT user, level FROM levels ORDER BY level DESC LIMIT 10")
                leaders = await cursor.fetchall()

                userString = ''
                levelString = ''
                for leader in leaders:
                    user = await self.bot.fetch_user(leader[0])
                    userString += f'{user.mention}\n'

                    level = leader[1]
                    levelString += f'{level}\n'


                em = discord.Embed(title="Leaderboard")
                em.add_field(name='Level', value=levelString, inline=True)
                em.add_field(name='User', value=userString, inline=True)

                await interaction.response.send_message(embed=em, ephemeral=True)

    @app_commands.command(name="level", description="Display the level of a user")
    async def level(self, interaction: discord.Interaction, name: discord.User = None) -> None:
        if name is None:
            member = interaction.user
        else:
            member = name
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT xp FROM levels WHERE user = %s AND guild = %s", (member.id, interaction.guild.id,))
                xp = await cursor.fetchone()
                await cursor.execute("SELECT level FROM levels WHERE user = %s AND guild = %s", (member.id, interaction.guild.id,))
                level = await cursor.fetchone()

                if not xp or not level:
                    await cursor.execute("INSERT INTO levels (level, xp, user, guild, last_msg) VALUES (%s, %s, %s, %s, %s)", (1, 0, member.id, interaction.guild.id, datetime.datetime.utcnow(),))

                try:
                    xp = xp[0]
                    level = level[0]
                except TypeError:
                    em = discord.Embed()
                    em.add_field(name="Error", value="Sorry your current level cannot be viewed as you have not sent any messages.")
                    await interaction.response.send_message(embed=em, ephemeral=True)
                    return

                try:
                    pfpURL = member.avatar.url
                    pfp = re.search('^.+?(?=\..{3}\?)', pfpURL).group()
                    pfp += '.jpg?size=1024'
                    online = True
                except AttributeError:
                    pfp = 'assets/level/default.jpg'
                    online = False

                await interaction.response.send_message(content="Loading...", ephemeral=True)

                await cursor.execute("SELECT level FROM levels ORDER BY level DESC LIMIT 1")
                highest_level = await cursor.fetchone()
                await cursor.execute("SELECT ROW_NUMBER() OVER(ORDER BY level DESC), user FROM levels ")
                rankings = await cursor.fetchall()

                res = await createImage(pfp, level, xp, online, highest_level[0], rankings, member.id)

                await interaction.edit_original_response(content=None, attachments=[discord.File(fp=res, filename='rank.png')])

            
    async def levelUp(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.author.id in ignoreList:
            return

        currentTime = datetime.datetime.utcnow()
        author = message.author
        guild = message.guild
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT xp FROM levels WHERE user = %s AND guild = %s", (author.id, guild.id,))
                xp = await cursor.fetchone()
                await cursor.execute("SELECT level FROM levels WHERE user = %s AND guild = %s", (author.id, guild.id,))
                level = await cursor.fetchone()

                if not xp or not level:
                    await cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (%s, %s, %s, %s)", (1, 0, author.id, guild.id,))

                await cursor.execute("SELECT last_msg FROM levels WHERE user = %s AND guild = %s", (author.id, guild.id,))
                last_message_sent = await cursor.fetchone()

                if last_message_sent[0] == None or (currentTime - last_message_sent[0]).total_seconds() > self.COOLDOWN:
                    try:
                        xp = xp[0]
                        level = level[0]
                    except TypeError:
                        xp = 0
                        level = 0

                    xp += random.randint(self.MINEXP, self.MAXEXP)
                    await cursor.execute("UPDATE levels SET xp = %s WHERE user = %s AND guild = %s", (xp, author.id, guild.id,))
                    await cursor.execute("UPDATE levels SET last_msg = %s WHERE user = %s AND guild = %s", (datetime.datetime.strftime(currentTime, '%Y-%m-%d %H:%M:%S'), author.id, guild.id,)) # time

                    nextLevel = 12*level**2+60
                    if xp >= nextLevel:
                        level += 1
                        await cursor.execute("UPDATE levels SET level = %s WHERE user = %s AND guild = %s", (level, author.id, guild.id,))
                        await cursor.execute("UPDATE levels SET xp = %s WHERE user = %s AND guild = %s", (xp-nextLevel, author.id, guild.id,))
                        await self.bot.get_channel(self.levelUpChannel).send(f"{author.mention} has leveled up to level **{level}**!") # sends message to level-up channel

                        await cursor.execute("SELECT level FROM levels ORDER BY level DESC LIMIT 1")
                        highest_level = await cursor.fetchone()

                        await self.assign_role(author, level, highest_level[0], message.guild)

            await conn.commit()
            await self.bot.process_commands(message)

    async def assign_role(self, user, level, highest_level, guild):
        async def checkAssign(index):
            getRole = lambda i : discord.utils.get(guild.roles, name=list(roles.keys())[i])
            if getRole(index) not in user.roles:
                roleToAdd = getRole(index)
                await user.add_roles(roleToAdd)
            if index > 0 and getRole(index-1) in user.roles:
                roleToRemove = getRole(index-1)
                await user.remove_roles(roleToRemove)      

        if level <= 3:
            await checkAssign(0)
        elif level <= 6:
            await checkAssign(1)
        elif level == 7:
            await checkAssign(2)
        elif level == 8:
            await checkAssign(3)
        elif level == 9:
            await checkAssign(4)
        elif level == 10:
            await checkAssign(5)
        elif level == 11:
            await checkAssign(6)
        elif level == 12:
            await checkAssign(7)
        elif level == 13:
            await checkAssign(8)
        elif level == 14:
            await checkAssign(9)
        elif level == 15:
            await checkAssign(10)
        elif level == 16:
            await checkAssign(11)
        elif level == 17:
            await checkAssign(12)
        elif level == 18:
            await checkAssign(13)
        elif level == 19:
            await checkAssign(14)
        elif level == 20:
            await checkAssign(15)
        elif level == highest_level and level >= 50:
            await checkAssign(23)
        elif level >= highest_level * .9 and level >= 50:
            await checkAssign(22)
        elif level >= highest_level * .8 and level >= 50:
            await checkAssign(21)
        elif level >= highest_level * .6 and level > 20:
            await checkAssign(20)
        elif level >= highest_level * .5 and level > 20:
            await checkAssign(19)
        elif level >= highest_level * .3 and level > 20:
            await checkAssign(18)
        elif level >= highest_level * .2 and level > 20:
            await checkAssign(17)
        elif level > 20:
            await checkAssign(16)
