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
    @app_commands.command(name="pull", description="Pull a single character")
    async def pull(interaction : discord.Interaction):
        res = Gacha.pull()
        return res


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
