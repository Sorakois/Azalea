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
    "Chocolate I": 1075548364814434464, 
    "Bronze II": 1075548426021912586, 
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
                    pfpURL = member.guild_avatar.url if member.guild_avatar else member.avatar.url
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

                res = await createImage(pfp, level, xp, online, highest_level[0], rankings, member.id, interaction)

                await interaction.edit_original_response(content=None, attachments=[discord.File(fp=res, filename='rank.gif')])

            
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

                    xp += random.randrange(int(self.MINEXP), int(self.MAXEXP)) #ensure both numbers are ints
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
            getRole = lambda i : discord.utils.get(guild.roles, id=list(roles.values())[i])
            if getRole(index) not in user.roles:
                roleToAdd = getRole(index)
                await user.add_roles(roleToAdd)
            if index > 0 and getRole(index-1) in user.roles:
                roleToRemove = getRole(index-1)
                await user.remove_roles(roleToRemove)      
        
        # Chocolate II (Levels 1-3)
        if level <= 3:
            await checkAssign(0)
        # Chocolate I (Levels 4-6)
        elif level <= 6:
            await checkAssign(1)
        # Bronze II (Level 7)
        elif level == 7:
            await checkAssign(2)
        # Bronze I (Level 8)
        elif level == 8:
            await checkAssign(3)
        # Silver III (Level 9)
        elif level == 9:
            await checkAssign(4)
        # Silver II (Level 10)
        elif level == 10:
            await checkAssign(5)
        # Silver I (Level 11)
        elif level == 11:
            await checkAssign(6)
        # Gold III (Level 12)
        elif level == 12:
            await checkAssign(7)
        # Gold II (Level 13)
        elif level == 13:
            await checkAssign(8)
        # Gold I (Level 14)
        elif level == 14:
            await checkAssign(9)
        # Crystal III (Level 15)
        elif level == 15:
            await checkAssign(10)
        # Crystal II (Level 16)
        elif level == 16:
            await checkAssign(11)
        # Crystal I (Level 17)
        elif level == 17:
            await checkAssign(12)
        # Diamond III (Level 18)
        elif level == 18:
            await checkAssign(13)
        # Diamond II (Level 19)
        elif level == 19:
            await checkAssign(14)
        # Diamond I (Level 20)
        elif level == 20:
            await checkAssign(15)
        
        # Grandmaster I (Level 50+, 1st Place)
        elif level == highest_level and level >= 50:
            await checkAssign(28)
        # Grandmaster II (Level 50+, Top 30% of Grandmaster)
        elif level >= highest_level * 0.7 and level >= 50:
            await checkAssign(27)
        # Grandmaster III (Level 50+)
        elif level >= 50:
            await checkAssign(26)
        
        # Elite I (Level 40-49, Top 30% of Elite)
        elif level >= highest_level * 0.7 and 40 <= level <= 49:
            await checkAssign(25)
        # Elite II (Level 40-49, Top 40% of Elite)
        elif level >= highest_level * 0.6 and 40 <= level <= 49:
            await checkAssign(24)
        # Elite III (Level 40-49, Top 50% of Elite)
        elif level >= highest_level * 0.5 and 40 <= level <= 49:
            await checkAssign(23)
        # Elite IV (Level 40-49, Top 60% of Elite)
        elif level >= highest_level * 0.4 and 40 <= level <= 49:
            await checkAssign(22)
        # Elite V (Level 40-49)
        elif 40 <= level <= 49:
            await checkAssign(21)
        
        # Master I (Level 21-39, Top 30% of Master)
        elif level >= highest_level * 0.7 and 21 <= level <= 39:
            await checkAssign(20)
        # Master II (Level 21-39, Top 40% of Master)
        elif level >= highest_level * 0.6 and 21 <= level <= 39:
            await checkAssign(19)
        # Master III (Level 21-39, Top 50% of Master)
        elif level >= highest_level * 0.5 and 21 <= level <= 39:
            await checkAssign(18)
        # Master IV (Level 21-39, Top 60% of Master)
        elif level >= highest_level * 0.4 and 21 <= level <= 39:
            await checkAssign(17)
        # Master V (Level 21-39)
        elif 21 <= level <= 39:
            await checkAssign(16)

    async def check_user_roles(self, guild):
        '''
        Audits all users' roles and fixes any mismatched roles based on their current levels.
        
        params:
            bot (commands.Bot): Bot instance to access database
            bot (commands.Bot): Bot instance to access database
            guild (discord.Guild): Guild object to check roles in
            str: Summary of role changes made
        '''
        changes_made = 0
        users_checked = 0
        errors = []
        
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                # Get all users with levels from database
                await cursor.execute("SELECT USER_ID, USER_LEVEL FROM USER WHERE USER_LEVEL > 0")
                user_data = await cursor.fetchall()
                
                # Get highest level for percentage calculations
                await cursor.execute("SELECT USER_LEVEL FROM USER ORDER BY USER_LEVEL DESC LIMIT 1")
                highest_level_result = await cursor.fetchone()
                highest_level = highest_level_result[0] if highest_level_result else 1
                
                for user_id, user_level in user_data:
                    try:
                        # Get guild member
                        member = guild.get_member(user_id)
                        if not member:
                            continue
                            
                        users_checked += 1
                        
                        # Calculate what role they should have
                        expected_role_index = self.get_expected_role_index(user_level, highest_level)
                        
                        if expected_role_index is not None:
                            expected_role_id = list(roles.values())[expected_role_index]
                            expected_role = discord.utils.get(guild.roles, id=expected_role_id)
                            
                            # Check if user has the correct role
                            current_level_roles = [role for role in member.roles if role.id in list(roles.values())]
                            
                            # If they don't have the expected role or have wrong roles
                            if expected_role not in member.roles or len(current_level_roles) != 1:
                                # Remove all level roles
                                for role in current_level_roles:
                                    if role != expected_role:
                                        await member.remove_roles(role)
                                        changes_made += 1
                                
                                # Add correct role if not already present
                                if expected_role not in member.roles and expected_role:
                                    await member.add_roles(expected_role)
                                    changes_made += 1
                        
                    except Exception as e:
                        errors.append(f"Error processing user {user_id}: {str(e)}")
                        continue
        
        # Prepare summary message
        summary = f"Checked {users_checked} users, made {changes_made} role changes"
        if errors:
            summary += f"\nErrors encountered: {len(errors)}"
            # Log first few errors for debugging
            for error in errors[:3]:
                summary += f"\n- {error}"
            if len(errors) > 3:
                summary += f"\n- ... and {len(errors) - 3} more errors"
        
        return summary


    def get_expected_role_index(self, level, highest_level):
        '''
        Helper function to determine what role index a user should have based on their level.
        
        params:
            level (int): User's current level
            highest_level (int): Highest level in the server
            
        returns:
            int or None: Index of the role they should have, or None if no role
        '''
        # Chocolate II (Levels 1-3)
        if level <= 3:
            return 0
        # Chocolate I (Levels 4-6)
        elif level <= 6:
            return 1
        # Bronze II (Level 7)
        elif level == 7:
            return 2
        # Bronze I (Level 8)
        elif level == 8:
            return 3
        # Silver III (Level 9)
        elif level == 9:
            return 4
        # Silver II (Level 10)
        elif level == 10:
            return 5
        # Silver I (Level 11)
        elif level == 11:
            return 6
        # Gold III (Level 12)
        elif level == 12:
            return 7
        # Gold II (Level 13)
        elif level == 13:
            return 8
        # Gold I (Level 14)
        elif level == 14:
            return 9
        # Crystal III (Level 15)
        elif level == 15:
            return 10
        # Crystal II (Level 16)
        elif level == 16:
            return 11
        # Crystal I (Level 17)
        elif level == 17:
            return 12
        # Diamond III (Level 18)
        elif level == 18:
            return 13
        # Diamond II (Level 19)
        elif level == 19:
            return 14
        # Diamond I (Level 20)
        elif level == 20:
            return 15
        
        # Grandmaster I (Level 50+, 1st Place)
        elif level == highest_level and level >= 50:
            return 28
        # Grandmaster II (Level 50+, Top 30% of Grandmaster)
        elif level >= highest_level * 0.7 and level >= 50:
            return 27
        # Grandmaster III (Level 50+)
        elif level >= 50:
            return 26
        
        # Elite I (Level 40-49, Top 30% of Elite)
        elif level >= highest_level * 0.7 and 40 <= level <= 49:
            return 25
        # Elite II (Level 40-49, Top 40% of Elite)
        elif level >= highest_level * 0.6 and 40 <= level <= 49:
            return 24
        # Elite III (Level 40-49, Top 50% of Elite)
        elif level >= highest_level * 0.5 and 40 <= level <= 49:
            return 23
        # Elite IV (Level 40-49, Top 60% of Elite)
        elif level >= highest_level * 0.4 and 40 <= level <= 49:
            return 22
        # Elite V (Level 40-49)
        elif 40 <= level <= 49:
            return 21
        
        # Master I (Level 21-39, Top 30% of Master)
        elif level >= highest_level * 0.7 and 21 <= level <= 39:
            return 20
        # Master II (Level 21-39, Top 40% of Master)
        elif level >= highest_level * 0.6 and 21 <= level <= 39:
            return 19
        # Master III (Level 21-39, Top 50% of Master)
        elif level >= highest_level * 0.5 and 21 <= level <= 39:
            return 18
        # Master IV (Level 21-39, Top 60% of Master)
        elif level >= highest_level * 0.4 and 21 <= level <= 39:
            return 17
        # Master V (Level 21-39)
        elif 21 <= level <= 39:
            return 16
        
        # If level doesn't match any criteria, return None
        return None