import logging

import discord
from discord import app_commands
from discord.ext import commands
import datetime
import random
from io import BytesIO
from levelImage import createImage
import re
import aiomysql
import asyncio

roles = {
    "(Level 1 - 5) Germinating": 1521712119513481276,
    "(Level 5 - 10) Seedling": 1521712856981311689,
    "(Level 10 - 20) Vegitative": 1521712959275929610,
    "(Level 20 - 35) Flowering": 1521713146945999165,
    "(Level 35 - 50) Senescence": 1521713250125746246,
}

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
        Check the leaderboard of the server (only showing users still in the server)
        params:
            interaction (discord.Interaction) : Interaction object to respond to
        returns:
            A message sent to user.
        '''
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                leaders = []
                offset = 0
                
                while len(leaders) < 10:
                    # Fetch users in batches, starting with 10 more than we need
                    batch_size = 10 + offset
                    await cursor.execute("SELECT USER_ID, USER_LEVEL FROM USER ORDER BY USER_LEVEL DESC LIMIT %s OFFSET %s", 
                                    (batch_size, len(leaders) + offset))
                    batch = await cursor.fetchall()
                    
                    if not batch:  # No more users in database
                        break
                    
                    # Check which users are still in the server
                    valid_users = []
                    filtered_count = 0
                    
                    for user_data in batch:
                        member = interaction.guild.get_member(user_data[0])
                        if member is not None:  # User is still in the server
                            valid_users.append(user_data)
                            if len(leaders) + len(valid_users) >= 10:  # Stop once we have enough
                                break
                        else:
                            filtered_count += 1
                    
                    leaders.extend(valid_users)
                    
                    # If we still need more users, adjust offset for next iteration
                    if len(leaders) < 10:
                        offset += filtered_count
                
                userString = ''
                levelString = ''
                for leader in leaders:
                    member = interaction.guild.get_member(leader[0])
                    userString += f'{member.mention}\n'
                    level = leader[1]
                    levelString += f'{level}\n'
                    
                em = discord.Embed(title="Leaderboard")
                em.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                em.add_field(name='Level', value=levelString, inline=True)
                em.add_field(name='User', value=userString, inline=True)
                await interaction.response.send_message(embed=em, ephemeral=False)

    '''=============== bring this back later ==============='''
    # @app_commands.command(name="level", description="Display the level of a user")
    # async def level(self, interaction: discord.Interaction, name: discord.User = None) -> None:
    #     '''
    #     Checks the current level of a server member
    #     params:
    #         interaction (discord.Interaction) : Interaction object to respond to
    #         name (discord.User) [Optional] : An optional username to check other users' level
    #     '''
    #     if name is None:
    #         member = interaction.user
    #     else:
    #         member = name
    
    #     # Check if the target user is in the server
    #     guild_member = interaction.guild.get_member(member.id)
    
    #     async with self.bot.db.acquire() as conn:
    #         async with conn.cursor() as cursor:
    #             await cursor.execute("SELECT USER_XP FROM USER WHERE USER_ID = %s", (member.id,))
    #             xp = await cursor.fetchone()
    #             await cursor.execute("SELECT USER_LEVEL FROM USER WHERE USER_ID = %s", (member.id,))
    #             level = await cursor.fetchone()
    #             if not xp or not level:
    #                 await cursor.execute("INSERT INTO USER (USER_ID, USER_LEVEL, USER_XP, USER_LAST_MSG) VALUES (%s, %s, %s, %s)", (member.id, 1, 0, datetime.datetime.utcnow(),))
    #             try:
    #                 xp = xp[0]
    #                 level = level[0]
    #             except TypeError:
    #                 em = discord.Embed()
    #                 em.add_field(name="Error", value="Sorry your current level cannot be viewed as you have not sent any messages.")
    #                 await interaction.response.send_message(embed=em, ephemeral=True)
    #                 return
    #             try:
    #                 pfpURL = member.guild_avatar.url if member.guild_avatar else member.avatar.url
    #                 pfp = re.search('^.+?(?=\..{3}\?)', pfpURL).group()
    #                 pfp += '.jpg?size=1024'
    #                 online = True
    #             except AttributeError:
    #                 pfp = 'assets/level/default.jpg'
    #                 online = False
    #             await interaction.response.send_message(content="Loading...", ephemeral=False)
    #             await cursor.execute("SELECT USER_LEVEL FROM USER ORDER BY USER_LEVEL DESC LIMIT 1")
    #             highest_level = await cursor.fetchone()
            
    #             # Get all rankings sorted by level DESC, then XP DESC
    #             await cursor.execute("SELECT ROW_NUMBER() OVER(ORDER BY USER_LEVEL DESC, USER_XP DESC), USER_ID FROM USER")
    #             all_rankings = await cursor.fetchall()
            
    #             # Filter rankings to only include users who are in the server
    #             rankings = []
    #             current_rank = 1
    #             calculated_rank = None
            
    #             for rank, user_id in all_rankings:
    #                 guild_member_check = interaction.guild.get_member(user_id)
    #                 if guild_member_check is not None:
    #                     # User is in the server, add to filtered rankings
    #                     rankings.append((current_rank, user_id))
    #                     if user_id == member.id:
    #                         calculated_rank = current_rank
    #                     current_rank += 1
            
    #             # If target user is not in server rankings, they get no rank
    #             if guild_member is None:
    #                 calculated_rank = None
            
    #             # Create and return the image
    #             res = await createImage(pfp, level, xp, online, highest_level[0], member.id, interaction, rankings, calculated_rank)
    #             await interaction.edit_original_response(content=None, attachments=[discord.File(fp=res, filename='rank.gif')])
    '''=============== bring this back later ==============='''

    async def levelUp(self, message: discord.Message):
        '''
        Called whenever a message is sent and does experience and level up logic

        params:
            message (discord.Message) : Message object that was sent
        '''
        if message.author.bot or message.author.id in ignoreList:
            return

        valid_time = False
        currentTime = datetime.datetime.utcnow()
        author = message.author
        guild = message.guild

        try:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    try:
                        # Fetch level, XP, and last message in one go
                        await asyncio.wait_for(cursor.execute("""
                            SELECT USER_LEVEL, USER_XP, USER_LAST_MSG 
                            FROM USER WHERE USER_ID = %s
                        """, (author.id,)), timeout=5)
                        result = await asyncio.wait_for(cursor.fetchone(), timeout=5)

                        if not result:
                            # New user entry
                            await asyncio.wait_for(cursor.execute("""
                                INSERT INTO USER (USER_ID, USER_LEVEL, USER_XP) 
                                VALUES (%s, %s, %s)
                            """, (author.id, 1, 0)), timeout=5)
                            xp = 0
                            level = 1
                            last_msg = None

                            # Force role assignment for brand new DB entries
                            await asyncio.wait_for(cursor.execute("SELECT MAX(USER_LEVEL) FROM USER"), timeout=5)
                            highest_level_result = await asyncio.wait_for(cursor.fetchone(), timeout=5)
                            highest_level = highest_level_result[0] if highest_level_result[0] else 1
                            await self.assign_role(author, level, highest_level, guild)
                        else:
                            level, xp, last_msg = result

                        if last_msg is None or (currentTime - last_msg).total_seconds() > self.COOLDOWN:
                            valid_time = True
                            xp += random.randrange(int(self.MINEXP), int(self.MAXEXP))

                            await asyncio.wait_for(cursor.execute("""
                                UPDATE USER SET USER_XP = %s, USER_LAST_MSG = %s WHERE USER_ID = %s
                            """, (xp, currentTime.strftime('%Y-%m-%d %H:%M:%S'), author.id)), timeout=5)

                            nextLevel = 12 * level ** 2 + 60
                            if xp >= nextLevel:
                                level += 1
                                new_xp = xp - nextLevel
                                await asyncio.wait_for(cursor.execute("""
                                    UPDATE USER SET USER_LEVEL = %s, USER_XP = %s WHERE USER_ID = %s
                                """, (level, new_xp, author.id)), timeout=5)

                                await self.bot.get_channel(self.levelUpChannel).send(
                                    f"{author.mention} has leveled up to level **{level}**!")

                                await asyncio.wait_for(cursor.execute("""
                                    SELECT MAX(USER_LEVEL) FROM USER
                                """), timeout=5)
                                highest_level = await asyncio.wait_for(cursor.fetchone(), timeout=5)
                                await self.assign_role(author, level, highest_level[0], guild)

                    except asyncio.TimeoutError:
                        logging.warning(f"Database timeout for user {author.id}")
                    except Exception as e:
                        pass
                        logging.exception(f"Unexpected error in levelUp for user {author.id}: {e}")

                await conn.commit()

            await self.bot.process_commands(message)
            return valid_time

        except Exception as e:
            pass
            logging.exception(f"Database acquisition error for user {author.id}: {e}")

    async def assign_role(self, user, level, highest_level, guild):
        '''
        Called when a user levels up, will remove and add roles of each level accordingly.
        params:
            user (discord.User) : User object to change role of
            level (int) : the new level of the user
            highest_level (int) : the highest level in the server
            guild (discord.Guild) : Guild object that the user is in.
        '''
        try:
            # Get the member object (user might be a User object, we need Member)
            member = guild.get_member(user.id)
            if not member:
                return
            
            # Get all possible level role objects
            all_level_roles = []
            for role_id in roles.values():
                role = guild.get_role(role_id)
                if role:
                    all_level_roles.append(role)
            
            # Remove ALL existing level roles first
            roles_to_remove = [role for role in member.roles if role in all_level_roles]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Level role update - removing old roles")
            
            # Determine which role they should have
            expected_role_index = self.get_expected_role_index(level, highest_level)
            
            if expected_role_index is not None:
                role_id = list(roles.values())[expected_role_index]
                new_role = guild.get_role(role_id)
                
                if new_role:
                    await member.add_roles(new_role, reason=f"Level {level} achieved")
                    print(f"Assigned {new_role.name} to {member.display_name} (Level {level})")
                    
        except discord.Forbidden:
            print(f"Missing permissions to manage roles for {user.display_name if hasattr(user, 'display_name') else user.name}")
        except discord.HTTPException as e:
            print(f"HTTP error while managing roles for {user.display_name if hasattr(user, 'display_name') else user.name}: {e}")
        except Exception as e:
            print(f"Unexpected error in assign_role for {user.display_name if hasattr(user, 'display_name') else user.name}: {e}")

    def get_expected_role_index(self, level, highest_level):
        '''
        Helper function to determine what role index a user should have based on their level.
        
        params:
            level (int): User's current level
            highest_level (int): Highest level in the server
            
        returns:
            int or None: Index of the role they should have, or None if no role
        '''
        # Index 0 maps to: (Level 1 - 5) Germinating
        if level < 5:
            return 0
            
        # Index 1 maps to: (Level 5 - 10) Seedling
        elif level < 10:
            return 1
            
        # Index 2 maps to: (Level 10 - 20) Vegitative
        elif level < 20:
            return 2
            
        # Index 3 maps to: (Level 20 - 35) Flowering
        elif level < 35:
            return 3
            
        # Index 4 maps to: (Level 35 - 50+) Senescence
        elif level >= 35:
            return 4
        
        # If level doesn't match any criteria, return None
        return None

    async def check_user_roles(self, guild):
        '''
        Audits all users' roles and fixes any mismatched roles based on their current levels.
        
        params: 
            guild (discord.Guild): Guild object to check roles in
            
        returns:
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