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
    "Elite V": 1176363093853483008,
    "Elite IV": 1176363039352705104,
    "Elite III": 1176362985363611709,
    "Elite II": 1176362613563732059,
    "Elite I": 1176362538766708816,
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
        '''
        Check the leaderboard of the server

        params:
            interaction (discord.Interaction) : Interaction object to respond to

        returns:
            A message sent to user.
        '''
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_ID, USER_LEVEL FROM USER ORDER BY USER_LEVEL DESC LIMIT 10")
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

                await interaction.response.send_message(embed=em, ephemeral=False)

    @app_commands.command(name="level", description="Display the level of a user")
    async def level(self, interaction: discord.Interaction, name: discord.User = None) -> None:
        '''
        Checks the current level of a server member

        params:
            interaction (discord.Interaction) : Interaction object to respond to
            name (discord.User) [Optional] : An optional username to check other users' level
        '''
        if name is None:
            member = interaction.user
        else:
            member = name
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_XP FROM USER WHERE USER_ID = %s", (member.id,))
                xp = await cursor.fetchone()
                await cursor.execute("SELECT USER_LEVEL FROM USER WHERE USER_ID = %s", (member.id,))
                level = await cursor.fetchone()

                if not xp or not level:
                    await cursor.execute("INSERT INTO USER (USER_ID, USER_LEVEL, USER_XP, USER_LAST_MSG) VALUES (%s, %s, %s, %s)", (member.id, 1, 0, datetime.datetime.utcnow(),))

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

                await interaction.response.send_message(content="Loading...", ephemeral=False)

                await cursor.execute("SELECT USER_LEVEL FROM USER ORDER BY USER_LEVEL DESC LIMIT 1")
                highest_level = await cursor.fetchone()
                await cursor.execute("SELECT ROW_NUMBER() OVER(ORDER BY USER_LEVEL DESC), USER_ID FROM USER")
                rankings = await cursor.fetchall()

                res = await createImage(pfp, level, xp, online, highest_level[0], rankings, member.id)

                await interaction.edit_original_response(content=None, attachments=[discord.File(fp=res, filename='rank.png')])

            
    async def levelUp(self, message: discord.Message):
        '''
        Called whenever a message is sent and does experience and level up logic

        params:
            message (discord.Message) : Message object that was sent
        '''
        if message.author.bot:
            return
        if message.author.id in ignoreList:
            return

        valid_time = False # returned to send if time is valid to operate other on-message functions

        currentTime = datetime.datetime.utcnow()
        author = message.author
        guild = message.guild
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_XP FROM USER WHERE USER_ID = %s", (author.id,))
                xp = await cursor.fetchone()
                await cursor.execute("SELECT USER_LEVEL FROM USER WHERE USER_ID = %s", (author.id,))
                level = await cursor.fetchone()

                if not xp or not level:
                    await cursor.execute("INSERT INTO USER (USER_ID, USER_LEVEL, USER_XP) VALUES (%s, %s, %s)", (author.id, 1, 0,))

                await cursor.execute("SELECT USER_LAST_MSG FROM USER WHERE USER_ID = %s", (author.id,))
                last_message_sent = await cursor.fetchone()

                if last_message_sent[0] == None or (currentTime - last_message_sent[0]).total_seconds() > self.COOLDOWN:
                    try:
                        xp = xp[0]
                        level = level[0]
                    except TypeError:
                        xp = 0
                        level = 0

                    valid_time = True

                    xp += random.randint(int(self.MINEXP), int(self.MAXEXP)) #ensure both numbers are ints
                    await cursor.execute("UPDATE USER SET USER_XP = %s WHERE USER_ID = %s", (xp, author.id,))
                    await cursor.execute("UPDATE USER SET USER_LAST_MSG = %s WHERE USER_ID = %s", (datetime.datetime.strftime(currentTime, '%Y-%m-%d %H:%M:%S'), author.id,)) # time

                    nextLevel = 12*level**2+60
                    if xp >= nextLevel:
                        level += 1
                        await cursor.execute("UPDATE USER SET USER_LEVEL = %s WHERE USER_ID = %s", (level, author.id,))
                        await cursor.execute("UPDATE USER SET USER_XP = %s WHERE USER_ID = %s", (xp-nextLevel, author.id,))
                        await self.bot.get_channel(self.levelUpChannel).send(f"{author.mention} has leveled up to level **{level}**!") # sends message to level-up channel

                        await cursor.execute("SELECT USER_LEVEL FROM USER ORDER BY USER_LEVEL DESC LIMIT 1")
                        highest_level = await cursor.fetchone()

                        await self.assign_role(author, level, highest_level[0], message.guild)

            await conn.commit()
            await self.bot.process_commands(message)
        return valid_time

    async def assign_role(self, user, level, highest_level, guild):
        '''
        Called when a user levels up, will remove and add roles of each level accordingly.

        params:
            user (discord.User) : User object to change role of
            level (int) : the new level of the user
            highest_level (int) : the highest level in the server
            guild (discord.Guild) : Guild object that the user is in.
        '''
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
            await checkAssign(28)
        elif level >= highest_level * .9 and level >= 50:
            await checkAssign(27)
        elif level >= highest_level * .8 and level >= 50:
            await checkAssign(26)
        elif level >= highest_level * .7 and level > 20:
            await checkAssign(25)
        elif level >= highest_level * .6 and level > 20:
            await checkAssign(24)
        elif level >= highest_level * .5 and level > 20:
            await checkAssign(23)
        elif level >= highest_level * .4 and level > 20:
            await checkAssign(22)
        elif level >= highest_level * .3 and level > 20:
            await checkAssign(21)
        elif level >= highest_level * .25 and level > 20:
            await checkAssign(20)
        elif level >= highest_level * .2 and level > 20:
            await checkAssign(19)
        elif level >= highest_level * .15 and level > 20:
            await checkAssign(18)
        elif level >= highest_level * .1 and level > 20:
            await checkAssign(17)
        elif level > 20:
            await checkAssign(16)
