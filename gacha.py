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
    @app_commands.command(name="pull", description="Pull once")
    async def pull(interaction : discord.Interaction):
        res = Gacha.pull()
        return res
    
    @app_commands.command(name="multipull", description="Pull multiple times")
    async def multipull(interaction : discord.Interaction):
        res = []
        for i in range(0, 11):    
            res.append(Gacha.pull())
        return res

    @app_commands.command(name="balance", description="Check your balance of gems")
    async def balance(interaction : discord.Interaction):
        balance = 1
        interaction.response.send_message(f"Your balance is: {balance}")

class Gacha:
    '''
    gacha logic and computations

    functions -->
        - a pull function for gacha (cost, check if can afford, result)

    '''
    async def pull():
        pass # All the computations and stuff for pulling a cook


class Cookie:
    '''
    An individual item (cookie) stats of cookie


    '''
    pass
