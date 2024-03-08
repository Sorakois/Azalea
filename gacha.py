import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random
import math


async def check_full_inventory(cursor, member, threshold):
    await cursor.execute("SELECT USER_INV_SLOTS, USER_INV_SLOTS_USED FROM USER WHERE USER_ID = %s", (member.id,))
    inventory = await cursor.fetchone()
    return inventory[0] < inventory[1] + threshold # Maxed out inventory if True

async def fetch_balance(cursor, member, interaction):
    await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (member.id,))
    balance = await cursor.fetchone()

    try:
        balance = balance[0]
    except TypeError:
        em = discord.Embed()
        em.add_field(name="Error", value="Sorry your cannot use that command, as you have not recieved any gems yet.")
        await interaction.response.send_message(embed=em, ephemeral=True)
        return None # No value detected
    
    return balance

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

    DAILY_MIN = 1200
    DAILY_MAX = 3600
    DAILYCOOLDOWN = 82800 # 23 hours in seconds

    def __init__(self, bot) -> None:
        self.bot = bot

    async def crystalOnMessage(self, message: discord.Message, valid_time):
        if message.author.bot:
            return
        
        author = message.author

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (author.id,))
                crystals = await cursor.fetchone()

                if valid_time:
                    try:
                        crystals = crystals[0]
                    except ValueError:
                        crystals = 0
                    
                    crystals += random.randrange(self.MINCRYS, self.MAXCRYS)
                    await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (crystals, author.id,))
        
            await conn.commit()
            await self.bot.process_commands(message)  

    @app_commands.command(name="pull", description="Pull once.")
    async def pull(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                if await check_full_inventory(cursor, member, 1):
                    interaction.response.send_message("Sorry, you do not have enough inventory slots to do another pull.")
                    return
                
                balance = fetch_balance(cursor, member, interaction)
                if balance is None:
                    return
                    
                if balance >= 300:
                    res = await Gacha().pull_cookie()
                    balance -= 300
                    await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                    await interaction.response.send_message(f"{res}")

                    if isinstance(res, int): # If integer, must mean essence
                        balance += res
                        await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                    elif isinstance(res, str): # If string, must mean rarity
                        await cursor.execute("INSERT INTO ITEM (ITEM_INFO_ID, USER_ID) VALUES ((SELECT ITEM_INFO_ID FROM ITEM_INFO WHERE ITEM_RARITY = %s ORDER BY RAND() LIMIT 1), %s)", (res, member.id,))

                else:
                    await interaction.response.send_message(f"Not enough crystals. Current Balance: {balance}")

                await conn.commit()

    
    @app_commands.command(name="multipull", description="Pull multiple times.")
    async def multipull(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                if await check_full_inventory(cursor, member, 11):
                    interaction.response.send_message("Sorry, you do not have enough inventory slots to do another pull.")
                    return

                balance = fetch_balance(cursor, member, interaction)
                if balance is None:
                    return

                if balance >= 3000:
                    res = []
                    for i in range(0, 11):    
                        res.append(Gacha().pull_cookie()) #Make into an larger embed later
        return res

    @app_commands.command(name="balance", description="Check your balance of gems.")
    async def balance(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                balance = fetch_balance(cursor, member, interaction)
                
                await interaction.response.send_message(f"Your balance is: {balance}")

    @app_commands.command(name="daily", description="Receive your daily bonus!")
    async def daily(self, interaction : discord.Interaction):
        '''
        Needs time restraint for usage
        '''

        member = interaction.user

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_GEMS FROM USER WHERE USER_ID = %s", (member.id,))
                balance = await cursor.fetchone()

                dailyAmount = random.randrange(self.DAILY_MIN, self.DAILY_MAX + 1)
                currentTime = datetime.datetime.utcnow()
                
                if not balance:
                    await cursor.execute("INSERT INTO USER (USER_ID, USER_GEMS) VALUES (%s, %s)", (member.id, dailyAmount,))

                await cursor.execute("SELECT USER_LAST_DAILY FROM USER WHERE USER_ID = %s", (member.id,))
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
                    
                    await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                    await cursor.execute("UPDATE USER SET USER_LAST_DAILY = %s WHERE USER_ID = %s", (datetime.datetime.strftime(currentTime, '%Y-%m-%d %H:%M:%S'), member.id,))

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

        if 0 <= probability < 0.35525:
            # Give user essence
            essence = await self.handle_essence()
            return essence

        elif 0.35525 <= probability < 0.62525:
            # Give user a common cookie
            rarity = 'Common'

        elif 0.62525 <= probability < 0.86525:
            # Give user a rare cookie
            rarity = 'Rare'

        elif 0.86525 <= probability < 0.96525:
            # Give user a epic cookie
            rarity = 'Epic'

        elif 0.96525 <= probability < 0.99825:
            #Give user a super epic cookie
            rarity = 'Super Epic'

        elif 0.99825 <= probability < .99950:
            # Give user Legendary, Dragon, or Special cookie
            with random.randrange(0,3) as r:
                match r:
                    case 0:
                        rarity = 'Legendary'
                    case 1:
                        rarity = 'Dragon'
                    case 2:
                        rarity = 'Special'
            
        elif .99950 <= probability < 1:
            # Give user Ancient cookie
            rarity = 'Ancient'
    
        return rarity
    
    async def handle_essence(self):
        return random.randrange(25,51)


