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
    async def number_guess(self, interaction : discord.Interaction, other_user : discord.User):
        await interaction.response.defer()
        
        # Simplify variables
        member = interaction.user
        
        # Can't trade with the bot!
        if other_user.id == 1160998311264796714 or other_user.id == 1082486461103878245:
                # Command does not execute further.
                await interaction.followup.send(f"Azalea is busy :(", ephemeral=True)
                return
        else:
            # go twice, one time for each user
            for index_user in range(2):
            
                # Ask what to trade! User 1 makes the request first.
                correctUserID = member.id if index_user == 0 else other_user.id
                
                # Keep looping until valid input
                while(True):
                    try:
                        await interaction.followup.send(f"<@{correctUserID}>, please type what you would like to trade!\n\nType either the name of a character or amount of essence/gems to trade.\nTo trade multiple items, seperate with commas (,)\nAdd 'G' or 'E' after a number for gem/essence")
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

                    # Initialize lists to hold results
                    essence_or_gems = []
                    chars_to_trade = []

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
                                
                                # Execute only if a number is followed by a letter
                                if essence_or_gems:
                                    
                                    # Figure out if gem or essence is being traded.
                                    trading_essence = [int(item[:-1]) for item in essence_or_gems if item.endswith('E') or item.endswith('e')]
                                    trading_gems = [int(item[:-1]) for item in essence_or_gems if item.endswith('G') or item.endswith('g')]
                                    
                                    if trading_essence or trading_gems:
                                        if trading_essence:
                                            await cursor.execute(f"SELECT USER_ESSENCE FROM USER WHERE USER_ID = %s", (correctUserID))
                                            essence_check = await cursor.fetchone()
                                            essence_check = essence_check[0]
                                        if trading_gems:
                                            await cursor.execute(f"SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (correctUserID))
                                            gems_check = await cursor.fetchone()
                                            gems_check = gems_check[0]
                                            
                                        if sum(trading_essence) > essence_check:
                                            # STOP! User input error.
                                            await interaction.followup.send(f"You are requesting to trade more essence than you own!\nYou own {essence_check} essence, yet requested to trade {trading_essence} essence.\nPlease try again.", ephemeral=True)
                                            continue # Go to the top and try again.
                                        if sum(trading_gems) > gems_check:
                                            # STOP! User input error.
                                            await interaction.followup.send(f"You are requesting to trade more gems than you own!\nYou own {gems_check} gems, yet requested to trade {trading_gems} gems.\nPlease try again.", ephemeral=True)
                                            continue # Go to the top and try again.
                                        
                                        #await interaction.followup.send(f"TESTING:\n    USERGEMS = {gems_check} | USERESS = {essence_check} | USERno = {index_user}", ephemeral=True)
                                        
                                        #store essence/gems via what user
                                        if index_user == 0:
                                            # First user
                                            user1_gems = trading_gems
                                            user1_ess = trading_essence
                                        else:
                                            # Second user
                                            user2_gems = trading_gems
                                            user2_ess = trading_essence
                                            
                                    else:
                                        await interaction.followup.send(f"Invalid request: Ensure only G or E is added to the end of numbers.\nPlease try again.", ephemeral=True)
                                        continue # Go to the top and try again.
                                    
                                if chars_to_trade:
                                    # An item/character is being traded!
                                    
                                    existsCheck = []
                                    user1_chars = []
                                    user2_chars = []
                                    
                                    # Cleanse each name then check compare to database
                                    for character in chars_to_trade:
                                        character = cleanse_name(character)
                                                                                
                                        await cursor.execute(f"SELECT USER_ID, ITEM_ID, ITEM_NAME, ITEM_RARITY FROM ITEM NATURAL JOIN ITEM_INFO WHERE ITEM_NAME LIKE '{character}%' AND USER_ID = {correctUserID} AND PROMO = 0 LIMIT 1;")
                                        validCheck = await cursor.fetchall()
                                        if not validCheck:
                                            # At the current index position, this character does NOT exist
                                            existsCheck.append((character, False))
                                        else:
                                            # At the current index position, this character DOES exist
                                            existsCheck.append((character, True))
                                            
                                            # Add the character to their list to trade
                                            if index_user == 0:
                                                user1_chars.append(character)
                                            else:
                                                user2_chars.append(character)
                                    
                                    # Show user what inputs are invalid and will be removed from their query
                                    for character, is_valid in existsCheck:
                                        if not is_valid:
                                            await interaction.followup.send(f"{character} is not valid and will be removed from your trade query.", ephemeral=True)

                                            
                                    #await interaction.followup.send(f"TESTING2:\n    {testing2}", ephemeral=True)                                    
                    except Exception as e:
                    # General error catch
                        await interaction.followup.send(f"ERROR: Invalid input.\n{e}\nPlease try again.", ephemeral=True)
                        continue # Go to the top and try again.
                    
                    # User 1 has successfully requested! Enter loop again for User 2. Break after both succeed.
                    # This will only be executed if the continues do not.
                    break
            
            '''
            NOTE: LOOP ESCAPED!
                  Now, we should:
                    - Delete/remove the items from each user's inventory
                    - "Swap" their items!
                    - say success
            '''
