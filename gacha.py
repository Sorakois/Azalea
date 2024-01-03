import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random


class Interaction(commands.Cog):
    '''
    Interaction with the users (slash commands, other than )

    functions -->
        - a single pull (interacts with the gacha pull using slash)
        - a multi pull (interacts with the gacha pull using slash)
        - check balance
        - daily login bonus
    '''
    @app_commands.command(name="pull", description="Pull once.")
    async def pull(self, interaction : discord.Interaction):
        res = Gacha.pull()
        return res
    
    @app_commands.command(name="multipull", description="Pull multiple times.")
    async def multipull(self, interaction : discord.Interaction):
        res = []
        for i in range(0, 11):    
            res.append(Gacha.pull())
        return res

    @app_commands.command(name="balance", description="Check your balance of gems.")
    async def balance(self, interaction : discord.Interaction):
        balance = 1
        await interaction.response.send_message(f"Your balance is: {balance}")

    @app_commands.command(name="daily", description="Recieve your daily bonus!")|
    async def daily(self, interaction : discord.Interaction):
        '''
        Needs time restraint for usage
        '''
        balance += random.randrange(1200, 3601) 
        await interaction.response.send_message(f"Your new balance is: {balance}")

class Gacha:
    '''
    gacha logic and computations

    functions -->
        - a pull function for gacha (cost, check if can afford, result)

    '''
    async def pull(self):
        x = random.random()
        rarity = ""

        if balance <= 300:
            if 0<=x<0.4:
                ''' Give user Common Rarity Cookie '''
            if 0.4<=x<0.65:
                ''' Give user Rare Rarity Cookie '''
            if 0.65<=x<0.83:
                ''' Give user Epic Rarity Cookie '''
            if 0.83<=x<0.93:
                ''' Give user Super Epic Rarity Cookie '''
            if 0.93<=x<0.98:
                ''' Give user Legendary, Dragon, or Special Rarity Cookie '''
            if 0.98<=x<1:
                ''' Give user Ancient Rarity Cookie '''

        pass # All the computations and stuff for pulling a cook


class Cookie:
    '''
    An individual item (cookie) stats of cookie
    C = Common, R = Rare, E = Epic, SE = Super Epic, L = Legendary, D = Dragon, S = Special, A = Ancient
    "https://ovenbreak.miraheze.org/wiki/List_of_Cookies" // "https://cookierunkingdom.fandom.com/wiki/List_of_Updates#Launch"
    
    **Cookie ID determined by general release date**
    '''
    async def __init__(self):
        self.rarity = ''
        self.name = ''

    pass
