# Imports
import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
import logging

class Business(commands.Cog):
    
    '''
    Trade with other users!
    Input another user, what items to trade
    Other user will input trade items
    Both will confirm, exchange done!
    
    NOTE: Store locally user1 VS user2 requests!
    '''
    
    @discord.app_commands.checks.cooldown(1, 30)
    @app_commands.command(name="trade", description="Trade your items with others!")
    async def number_guess(self, interaction : discord.Interaction, other_user : discord.User):
        # Simplify variables
        member = interaction.user
        
        # Can't trade with the bot!
        if other_user.id == 1160998311264796714 or other_user.id == 1082486461103878245:
                await interaction.response.send_message(f"Azalea is busy :(", ephemeral=True)
        else:
            # go twice, one time for each user
            for index_user in range(2):
            
                # Ask what to trade! User 1 makes the request first.
                
                # Keep looping until valid input
                while(True):
                    
                    await interaction.channel.send("Please type what you would like to trade!\n\nType either the name of a character or amount of essence/gems to trade.\nTo trade multiple items, seperate with commas (,)\nAdd 'G' or 'E' after a number for gem/essence")
                    def check(message: discord.Message):
                        if index_user == 0:
                            return message.author.id == member.id and message.channel.id == interaction.channel.id # Fisrt User
                        else:
                            return message.author.id == other_user.id and message.channel.id == interaction.channel.id # Second User

                    # Grab user's raw input
                    msg = await interaction.client.wait_for('message', check=check, timeout=30.0)
                    item_to_trade = msg.content
                    
                    # The input might contain multiple items... break them appart.
                    item_to_trade = item_to_trade.strip()
                    list_to_trade = item_to_trade.split(",")
                    # Remove user inputted ","
                    for request in list_to_trade:
                        request.replace(",","")
                    
                    try:
                        async with self.bot.db.acquire() as conn:
                            async with conn.cursor() as cursor:
                                
                                # Check if the user actually owns what they want to trade!
                                
                                # Execute if a number is followed by a letter
                                if any(isinstance(list_to_trade[i], int) and isinstance(list_to_trade[i + 1], str) and list_to_trade[i + 1].isalpha() 
                                for i in range(len(list_to_trade) - 1)):
                                    
                                    # Figure out if gem or essence is being traded.
                                    trading_essence = [item for item in list_to_trade if item.endswith('E')]
                                    trading_gems = [item for item in list_to_trade if item.endswith('G')]
                                    
                                    if trading_essence is not None:
                                        await cursor.execute(f"SELECT USER_ESSENCE, USER_GEMS FROM USER WHERE USER_ID = %s", (member.id if index_user == 0 else other_user.id))
                                        essence_gems = await cursor.fetchone()
                                        
                                        # Seperate gems and essence
                                        essence_check = essence_gems[0]
                                        gems_check = essence_gems[1]
                                        
                                        if trading_essence > essence_check:
                                            # STOP! User input error.
                                            await interaction.channel.send(f"You are requesting to trade more essence than you own!\nYou own {essence_check} essence, yet requested to trade {trading_essence} essence.\nPlease try again.")
                                            continue # Go to the top and try again.
                                        if trading_gems > gems_check:
                                            # STOP! User input error.
                                            await interaction.channel.send(f"You are requesting to trade more gems than you own!\nYou own {gems_check} gems, yet requested to trade {trading_gems} gems.\nPlease try again.")
                                            continue # Go to the top and try again.
                                        
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
                                        await interaction.channel.send(f"Invalid request: Ensure only G or E is added to the end of numbers.\nPlease try again.")
                                        continue # Go to the top and try again.
                                else:
                                    # An item/character is being traded!
                                    
                                    '''
                                    PROCESS:
                                        Check if the item exists
                                        Check if the user owns the item
                                        Assign items as a tuple(), no need to mutate
                                    '''
                                    
                                    
                    except ValueError as valE:
                        # An error is thrown, likely because the user did not enter a valid name
                        await interaction.channel.send(f"ERROR: One of the characters you entered do not exist.\nPlease try again.")
                        continue # Go to the top and try again.
                    except:
                    # General error catch
                        await interaction.channel.send(f"ERROR: Invalid input.\nPlease try again.")
                        continue # Go to the top and try again.
                    
                    # User 1 has successfully requested! Enter loop again for User 2. Break after both succeed.
                    # This will only be executed if the continues do not.
                    break
