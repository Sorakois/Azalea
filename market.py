# Imports
import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random
import math
from typing import Literal
import requests
import json
import asyncio
from misc import cleanse_name, fix_rarity, chrono_image
import time

class Business(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    '''
    Trade with other users!
    Input another user, what items to trade
    Other user will input trade items
    Both will confirm, exchange done!
    
    NOTE: User1 and User2 requests are stored LOCALLY!
    '''
    @discord.app_commands.checks.cooldown(1, 30)
    @app_commands.command(name="trade", description="Trade your items with others!")
    async def trade(self, interaction: discord.Interaction, other_user: discord.User):
        await interaction.response.defer()
        
        # Simplify variables
        member = interaction.user
        
        # Can't trade with the bot!
        if other_user.id == 1160998311264796714 or other_user.id == 1082486461103878245:
                # Command does not execute further.
                await interaction.followup.send(f"Azalea is busy :(", ephemeral=True)
                return
        if other_user.id == member.id:
            # Command does not execute further.
                await interaction.followup.send(f"You can't trade yourself, but... you've just played yourself.", ephemeral=True)
                return
        else:
            # variable init for the sake of scope
            existsCheck = []
            user1_chars = []
            user2_chars = []
            essence_or_gems = []
            chars_to_trade = []
            user1_gems = 0
            user2_gems = 0
            user1_ess = 0
            user2_ess = 0
            
            # go twice, one time for each user
            for index_user in range(2):
            
                # Ask what to trade! User 1 makes the request first.
                correctUserID = member.id if index_user == 0 else other_user.id
                
                # Keep looping until valid input
                while(True):
                    # Clear to avoid bugs
                    existsCheck.clear()
                    user1_chars.clear() if index_user == 0 else user2_chars.clear()
                    essence_or_gems.clear()
                    chars_to_trade.clear()
                    try:
                        await interaction.followup.send(f"<@{correctUserID}>, please type what you would like to trade!\n\nType either the name of a character or amount of essence/gems to trade.\nTo trade multiple items, seperate with commas (,)\nAdd 'G' or 'E' after a number for gem/essence\n\nExample: 'Firefly, 300G, 200E, Angel Cookie, ...")
                        def check(message: discord.Message):
                            if index_user == 0:
                                return message.author.id == member.id and message.channel.id == interaction.channel.id # Fisrt User
                            else:
                                return message.author.id == other_user.id and message.channel.id == interaction.channel.id # Second User

                        # Grab user's raw input
                        msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                        item_to_trade = msg.content
                    
                    # User did not respond in time
                    except asyncio.TimeoutError:
                        await interaction.followup.send("You took too long to respond!", ephemeral=True)
                        return
                    
                    # The input might contain multiple items... break them apart.
                    item_to_trade = item_to_trade.strip()  # Remove overall leading and/or trailing whitespace
                    list_to_trade = [item.strip() for item in item_to_trade.split(",") if item.strip()]  # Clean up each item and remove ","

                    # Split items into two lists
                    for item in list_to_trade:
                        if len(item) > 1 and item[:-1].isdigit() and item[-1] in ['E', 'G', 'e', 'g']:
                            essence_or_gems.append(item)
                        else:
                            chars_to_trade.append(item)

                    
                    try:
                        async with self.bot.db.acquire() as conn:
                            async with conn.cursor() as cursor:
                                # Check if the user actually owns what they want to trade
                                validInp = True
                                
                                # Execute only if a number is followed by a letter
                                if essence_or_gems:
                                    
                                    # Figure out if gem or essence is being traded.
                                    trading_essence = [int(item[:-1]) for item in essence_or_gems if item.endswith('E') or item.endswith('e')]
                                    trading_gems = [int(item[:-1]) for item in essence_or_gems if item.endswith('G') or item.endswith('g')]
                                    
                                    if trading_essence or trading_gems:
                                        if trading_essence:
                                            await cursor.execute("SELECT USER_ESSENCE FROM USER WHERE USER_ID = %s", (correctUserID,))
                                            essence_check = await cursor.fetchone()
                                            if essence_check and len(essence_check) > 0:
                                                essence_check = essence_check[0]
                                            
                                            # Check if trading_essence is a list or a single value
                                            essence_amount = sum(trading_essence)
                                            
                                            if index_user == 0:
                                                user1_ess = essence_amount
                                            else:
                                                user2_ess = essence_amount
                                            
                                            if essence_amount > essence_check:
                                                # STOP! User input error.
                                                await interaction.followup.send(f"You are requesting to trade more essence than you own!\nYou own {essence_check} essence, yet requested to trade {essence_amount} essence.\nPlease try again.", ephemeral=True)
                                                continue # Go to the top and try again.
                                        
                                        if trading_gems:
                                            await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (correctUserID,))
                                            gems_check = await cursor.fetchone()
                                            if gems_check and len(gems_check) > 0:
                                                gems_check = gems_check[0]
                                                
                                            # Check if trading_gems is a list or a single value
                                            gems_amount = sum(trading_gems)
                                            
                                            if index_user == 0:
                                                user1_gems = gems_amount
                                            else:
                                                user2_gems = gems_amount
                                            
                                            if gems_amount > gems_check:
                                                # STOP! User input error.
                                                await interaction.followup.send(f"You are requesting to trade more gems than you own!\nYou own {gems_check} gems, yet requested to trade {gems_amount} gems.\nPlease try again.", ephemeral=True)
                                                continue # Go to the top and try again.
                                        
                                        #await interaction.followup.send(f"TESTING:\n    USERGEMS = {gems_check} | USERESS = {essence_check} | USERno = {index_user}", ephemeral=True)
                                            
                                    else:
                                        await interaction.followup.send(f"Invalid request: Ensure only G or E is added to the end of numbers.\nPlease try again.", ephemeral=True)
                                        continue # Go to the top and try again.
                                    
                                if chars_to_trade:
                                    # An item/character is being traded!

                                    # Cleanse each name then check compare to database
                                    for character in chars_to_trade:
                                        character = cleanse_name(character)
                                        await cursor.execute("SELECT ITEM_NAME, ITEM_ID, ITEM_INFO_ID, USER_ID, PROMO FROM ITEM NATURAL JOIN ITEM_INFO WHERE ITEM_NAME LIKE %s AND PROMO = 0 AND USER_ID = %s LIMIT 1;", ((f"%{character}%",), correctUserID))
                                        # [charname, instanceID, infoID, UID, promo]                                        
                                        validCheck = await cursor.fetchone()
                                        if not validCheck:
                                            # At the current index position, this character does NOT exist
                                            existsCheck.append((character, False))
                                        else:
                                            # At the current index position, this character DOES exist
                                            existsCheck.append((character, True))
                                            
                                            # Add the character to their list to trade
                                            if index_user == 0:
                                                # Will look like -> [(firefly, 3000, 300), (Pure Vanilla Cookie, 2999, 299)]
                                                user1_chars.append((validCheck[0], validCheck[1], validCheck[2]))
                                            else:
                                                # Will look like -> [(firefly, 3000, 300), (Pure Vanilla Cookie, 2999, 299)]
                                                user2_chars.append((validCheck[0], validCheck[1], validCheck[2]))
                                    
                                    # Show user what inputs are invalid and will be removed from their query
                                    for character, is_valid in existsCheck:
                                        if not is_valid:
                                            await interaction.followup.send(f"{character} is not valid/unowned and will be removed from your trade query.", ephemeral=True)
                                            validInp = False
                                            
                                    '''NOTE: IMPORTANT
                                            Do a inventory check on the other person. Trade can't continue if someone has a full inventory.
                                    '''
                                    await cursor.execute("SELECT USER_INV_SLOTS, USER_INV_SLOTS_USED FROM USER WHERE USER_ID = %s", member.id)
                                    user1_invspace = await cursor.fetchone()
                                    await cursor.execute("SELECT USER_INV_SLOTS, USER_INV_SLOTS_USED FROM USER WHERE USER_ID = %s", other_user.id)
                                    user2_invspace = await cursor.fetchone()
                                    
                                    if user1_invspace[0] <= (user1_invspace[1] + len(user2_chars)): # User 1 has a full inventory
                                        await interaction.followup.send(f"<@{member.id} has a full inventory! Please /crumble or /promote and try again.", ephemeral=True)
                                        return
                                    if user2_invspace[0] <= (user2_invspace[1] + len(user1_chars)): # User 2 has a full inventory
                                        await interaction.followup.send(f"<@{other_user.id} has a full inventory! Please /crumble or /promote and try again.", ephemeral=True)
                                        return
                                 
                                    #await interaction.followup.send(f"TESTING2:\n    {testing2}", ephemeral=True)                                    
                    except Exception as e:
                    # General error catch
                        await interaction.followup.send(f"ERROR: Invalid input.\n{e}\nPlease try again.", ephemeral=True)
                        continue # Go to the top and try again.
                    
                    # User 1 has successfully requested! Enter loop again for User 2. Break after both succeed.
                    # This will only be executed if the continues do not.
                    if validInp:
                        break
            
            '''
            NOTE: LOOP ESCAPED!
                  Now, we should:
                    - Delete/remove the items from each user's inventory
                    - "Swap" their items!
                    - say success
                    
                    To swap a character, the UserID corresponding the instance IDs will simply swap
                    To swap gems/essence, subtract and add
            '''
            #await interaction.followup.send(f"CHECKING VALID:\n[USER1 -> ESS = {user1_ess if user1_ess is not None else 0} | GEM = {user1_gems if user1_gems is not None else 0} | CHAR = {user1_chars if user1_chars is not None else 0}]", ephemeral=True)
            #await interaction.followup.send(f"CHECKING VALID:\n[USER2 -> ESS = {user2_ess if user2_ess is not None else 0} | GEM = {user2_gems if user2_gems is not None else 0} | CHAR = {user2_chars if user2_chars is not None else 0}]", ephemeral=True)
            
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Add Gems if applicable:
                    if user1_gems is not None: # User 1 -> User 2, GEMS
                        # Remove from User 1
                        await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS - %s WHERE USER_ID = %s", (user1_gems, member.id))
                        # Add to User 2
                        await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS + %s WHERE USER_ID = %s", (user1_gems, other_user.id))
                    if user2_gems is not None: # User 2 -> User 1, GEMS
                        # Remove from User 2
                        await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS - %s WHERE USER_ID = %s", (user2_gems, other_user.id))
                        # Add to User 1
                        await cursor.execute("UPDATE USER SET USER_GEMS = USER_GEMS + %s WHERE USER_ID = %s", (user2_gems, member.id))
                    
                    # Add Essence if applicable:
                    if user1_ess is not None: # User 1 -> User 2, ESSENCE
                        # Remove from User 1
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE - %s WHERE USER_ID = %s", (user1_ess, member.id))
                        # Add to User 2
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s WHERE USER_ID = %s", (user1_ess, other_user.id))
                    if user2_ess is not None:# User 2 -> User 1, ESSENCE
                        # Remove from User 2
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE - %s WHERE USER_ID = %s", (user2_ess, other_user.id))
                        # Add to User 1
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s WHERE USER_ID = %s", (user2_ess, member.id))
                    
                    # "Add" characters if possible
                    if user1_chars is not None: # User1 -> User2, CHAR
                        '''
                        NOTE: User1char and User2char will look like -> [(firefly, 3000, 300), (Pure Vanilla Cookie, 2999, 299)]
                        '''
                        for eachChar in user1_chars:
                            instanceID = eachChar[1]
                            infoID = eachChar[2]
                            # Swap the ID from it being User1 to it now being User2
                            await cursor.execute("UPDATE ITEM SET USER_ID = %s WHERE ITEM_ID = %s AND ITEM_INFO_ID = %s AND PROMO = 0 AND USER_ID = %s", (other_user.id, instanceID, infoID, member.id))
                            # Subtract inv slot from User 1, add to User 2
                            await cursor.execute("UPDATE USER SET USER_INV_SLOT = USER_INV_SLOT + 1 WHERE USER_ID = %s", other_user.id)
                            await cursor.execute("UPDATE USER SET USER_INV_SLOT = USER_INV_SLOT - 1 WHERE USER_ID = %s", member.id)
                    if user2_chars is not None: # User2 -> User1, CHAR
                        for eachChar in user2_chars:
                            instanceID = eachChar[1]
                            infoID = eachChar[2]
                            # Swap the ID from it being User1 to it now being User2
                            await cursor.execute("UPDATE ITEM SET USER_ID = %s WHERE ITEM_ID = %s AND ITEM_INFO_ID = %s AND PROMO = 0 AND USER_ID = %s", (member.id, instanceID, infoID, other_user.id))
                            # Subtract inv slot from User 1, add to User 2
                            await cursor.execute("UPDATE USER SET USER_INV_SLOT = USER_INV_SLOT + 1 WHERE USER_ID = %s", member.id)
                            await cursor.execute("UPDATE USER SET USER_INV_SLOT = USER_INV_SLOT - 1 WHERE USER_ID = %s", other_user.id)
            '''
            DONE!!!! Output to user now to show the results.
            '''
            
            # Quickly make things look neat
            user1_charGained = []
            for char in user1_chars:
                if char[0].upper() == "TOPAZ NUMBY":
                    name = "Topaz"
                else:
                    name = char[0]
                user1_charGained.append(name.title())

            user2_charGained = []
            for char in user2_chars:
                if char[0].upper() == "TOPAZ NUMBY":
                    name = "Topaz"
                else:
                    name = char[0]
                user2_charGained.append(name.title())

            # Embed setup
            em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title="Trade SUCCESS!\nSummary:\n")
            em.set_image(url="https://media1.tenor.com/m/6O2uFeYTDOMAAAAC/cookierun-milky-way-cookie.gif")
            em.set_thumbnail(url=interaction.user.guild.icon.url)

            # User 1 results
            if user2_gems and user2_gems > 0:
                em.add_field(name=f"{member.display_name} Gained: ", value=f"{user2_gems} :gem:", inline=True)
            if user2_ess and user2_ess > 0:
                em.add_field(name=f"{member.display_name} Gained: ", value=f"{user2_ess} <:essence:1295791325094088855>", inline=True)
            if user1_charGained:
                em.add_field(name=f"{member.display_name} Gained: ", value=", ".join(user1_charGained), inline=True)
            
            # User 2 results
            if user1_gems and user1_gems > 0:
                em.add_field(name=f"{other_user.display_name} Gained: ", value=f"{user1_gems} :gem:", inline=True)
            if user1_ess and user1_ess > 0:
                em.add_field(name=f"{other_user.display_name} Gained: ", value=f"{user1_ess} <:essence:1295791325094088855>", inline=True)
            if user2_charGained:
                em.add_field(name=f"{other_user.display_name} Gained: ", value=", ".join(user2_charGained), inline=True)

            em.set_footer(text=f"Trade between {member.display_name} and {other_user.display_name}")
            await interaction.followup.send(embed=em, ephemeral=False)
            return
        
    @trade.error
    async def on_trade_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))