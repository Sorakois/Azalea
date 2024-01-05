import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random
import math


class GachaInteraction(commands.Cog):
    '''
    Interaction with the users (slash commands, other than )

    functions -->
        - a single pull (interacts with the gacha pull using slash)
        - a multi pull (interacts with the gacha pull using slash)
        - check balance
        - daily login bonus
    '''

    MINCRYS = 20
    MAXCRYS = 55
    DAILYCOOLDOWN = 82800 # 23 hours in seconds

    def __init__(self, bot) -> None:
        self.bot = bot

    async def crystalOnMessage(self, message: discord.Message, valid_time):
        if message.author.bot:
            return
        
        author = message.author

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT crystals FROM currencies WHERE userID = %s", (author.id,))
                crystals = await cursor.fetchone()

                if not crystals:
                    await cursor.execute("INSERT INTO currencies (userID, crystals) VALUES (%s, %s)", (author.id, 0))

                if valid_time:
                    try:
                        crystals = crystals[0]
                    except ValueError:
                        crystals = 0
                    
                    crystals += random.randrange(self.MINCRYS, self.MAXCRYS)
                    await cursor.execute("UPDATE currencies SET crystals = %s WHERE userID = %s", (crystals, author.id,))
        
            await conn.commit()
            await self.bot.process_commands(message)  

    @app_commands.command(name="pull", description="Pull once.")
    async def pull(self, interaction : discord.Interaction):
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                pass
    
        res = Gacha.pull_cookie()
        return res
    
    @app_commands.command(name="multipull", description="Pull multiple times.")
    async def multipull(self, interaction : discord.Interaction):
        res = []
        for i in range(0, 11):    
            res.append(Gacha.pull_cookie())
        return res

    @app_commands.command(name="balance", description="Check your balance of gems.")
    async def balance(self, interaction : discord.Interaction):

        member = interaction.user

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT crystals FROM currencies WHERE userID = %s", (member.id))
                balance = await cursor.fetchone()

                try:
                    balance = balance[0]
                except TypeError:
                    em = discord.Embed()
                    em.add_field(name="Error", value="Sorry, your current balance cannot be viewed as you have not sent any messages.")
                    await interaction.response.send_message(embed=em, ephemeral=True)
                    return
                
                await interaction.response.send_message(f"Your balance is: {balance}")

    @app_commands.command(name="daily", description="Recieve your daily bonus!")
    async def daily(self, interaction : discord.Interaction):
        '''
        Needs time restraint for usage
        '''

        member = interaction.user

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT crystals FROM currencies WHERE userID = %s", (member.id,))
                balance = await cursor.fetchone()

                dailyAmount = random.randrange(1200, 3601)
                currentTime = datetime.datetime.utcnow()
                
                if not balance:
                    await cursor.execute("INSERT INTO currencies (userID, crystals) VALUES (%s, %s)", (member.id, dailyAmount,))

                await cursor.execute("SELECT lastDaily FROM currencies WHERE userID = %s", (member.id,))
                last_message_sent = await cursor.fetchone()

                if last_message_sent[0] == None or (currentTime - last_message_sent[0]).total_seconds() > self.DAILYCOOLDOWN:
                    try:
                        balance = balance[0]
                    except TypeError:
                        em = discord.Embed()
                        em.add_field(name="Error", value="Sorry, you cannot claim a daily login as you have not sent any messages.")
                        await interaction.response.send_message(embed=em, ephemeral=True)
                        return

                    balance += dailyAmount
                    
                    await cursor.execute("UPDATE currencies SET crystals = %s WHERE userID = %s", (balance, member.id,))
                    await cursor.execute("UPDATE currencies SET lastDaily = %s WHERE userID = %s", (datetime.datetime.strftime(currentTime, '%Y-%m-%d %H:%M:%S'), member.id,))

                    await interaction.response.send_message(f"You earned **{dailyAmount}** crystals!\nYour new balance is: __{balance}__")

                else:
                    time_remaining = 82800 - (currentTime - last_message_sent[0]).total_seconds()
                    if time_remaining > 3600:
                        time_remaining_str = f'{math.ceil(time_remaining/3600)} hours'
                    elif time_remaining > 60:
                        time_remaining_str = f'{math.ceil(time_remaining/60)} minutes'
                    else:
                        time_remaining_str = f'{time_remaining} seconds'
                    em = discord.Embed()
                    em.add_field(name="Claimed Daily", value=f"Sorry, you have already collected your daily login bonus today, try again in {time_remaining_str}!")
                    await interaction.response.send_message(embed=em, ephemeral=False)

            await conn.commit()

class Gacha:
    '''
    gacha logic and computations

    functions -->
        - a pull function for gacha (cost, check if can afford, result)

    '''
    async def pull_cookie(self):
        probability = random.random()
        rarity = ""

        if balance <= 300:
            if 0 <= probability < 0.4:
                ''' Give user Common Rarity Cookie '''
            if 0.4 <= probability < 0.65:
                ''' Give user Rare Rarity Cookie '''
            if 0.65 <= probability < 0.83:
                ''' Give user Epic Rarity Cookie '''
            if 0.83 <= probability < 0.93:
                ''' Give user Super Epic Rarity Cookie '''
            if 0.93 <= probability < 0.98:
                ''' Give user Legendary, Dragon, or Special Rarity Cookie '''
            if 0.98 <= probability < 1:
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
