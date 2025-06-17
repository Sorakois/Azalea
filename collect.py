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
from asyncio import Lock
from market import Business
from misc import cleanse_name, fix_rarity, chrono_image

# ======================================= # ======================================= 

class Collection_BASE(commands.Cog):
    '''
    This is for the 'gacha' stuff

    Users get 10 free pulls every hour.
    You can get a pass/ticket, and this resets current cooldown for the hour.
    '''
    # Constructor, lock() for asyncio
    def __init__(self, bot) -> None:
        self.bot = bot
        self.lock = Lock()

    @discord.app_commands.checks.cooldown(1, 30) # make cooldown database based
    @app_commands.command(name="pull", description="Pull to collect characters!")
    async def trade(self, interaction: discord.Interaction, other_user: discord.User):
        member = interaction.user
        '''
        All games will be in one pool,
        
        Figure out how to do rarities
        '''

        # Check for cooldown
        # NOTE: Add pull_cd to the database
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT PULL_CD FROM USER WHERE USER_ID = %s", (member.id,))
                
                # pull_cd is a date-time object
                pull_cd = await cursor.fetchone()

                # Get time now and compare to pull_cd
                currentTime = datetime.datetime.utcnow()
                cd_check = (pull_cd - currentTime).total_seconds()
                
                # 24 hours into seconds
                cd_waitforme = (60 * 60) * 24
                if cd_check > cd_waitforme:
                    # Put time back into minutes
                    cd_waitforme = cd_waitforme / 60
                    await interaction.response.send_message(f"You have {cd_waitforme} more minutes until you can do this command again.\nPlease try again later.", ephemeral=True)
                    return
                
                # If you get here, it means you can pull!

                '''pull logic'''


    '''
     
     To add:
     - Inventory (a nice looking one)
     - Profile (overal stats kinda thing)
     
     '''   