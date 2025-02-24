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
            # User 1 will send a reques to User 2 on what they would like to trade!
            user1_request = await interaction.channel.send("Please type what you would like to trade!\n\nType either the name of a character or amount of essence/gems to trade.\nTo trade multiple items, seperate with commas (,)\nAdd 'G' or 'E' after a number for gem/essence")
            def check(message: discord.Message):
                return message.author.id == member.id and message.channel.id == interaction.channel.id

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
                        if any(isinstance(item, (int)) for item in list_to_trade):
                            # Essence is being traded!
                            await cursor.execute(f"SELECT USER_ESSENCE FROM USER WHERE USER_ID = %s", member.id)
                            essence_check = await cursor.fetchall()
                        else:
                            # An item/character is being traded!
                            a=1