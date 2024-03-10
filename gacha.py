import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random
import math


class InventoryView(discord.ui.View):

    page = 1
    COOKIE_PER_PAGE = 8

    def __init__(self, inventory, last_interaction: discord.Interaction, name: discord.User, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.inventory = inventory
        self.pages = math.ceil(len(self.inventory)/self.COOKIE_PER_PAGE)
        self.last_interaction = last_interaction
        self.user = name

    async def view_page(self, page_num) -> discord.Embed:
        first_of_page = (page_num - 1) * self.COOKIE_PER_PAGE
        last_of_page = self.COOKIE_PER_PAGE * page_num
        if last_of_page > len(self.inventory):
            last_of_page = len(self.inventory)

        em = discord.Embed(title=f"{self.user.name}'s inventory")

        names = ''
        raritys = ''
        for item in range(first_of_page, last_of_page):
            names += self.inventory[item][1] + '\n'
            raritys += self.inventory[item][0] + '\n'
        
        em.add_field(name="Name", value=names)
        em.add_field(name="Rarity", value=raritys)
        em.set_footer(text=f"{self.page}/{self.pages}")
        return em

    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple)
    async def left_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.pages if self.page == 1 else self.page - 1
        await interaction.response.send_message(embed=await self.view_page(self.page), view=self)
        await self.last_interaction.delete_original_response()
        self.last_interaction = interaction

    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def right_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 1 if self.page == self.pages else self.page + 1
        await interaction.response.send_message(embed=await self.view_page(self.page), view=self)
        await self.last_interaction.delete_original_response()
        self.last_interaction = interaction

    async def on_timeout(self) -> None:
        await self.last_interaction.delete_original_response()
        return await super().on_timeout()

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

    @discord.app_commands.checks.cooldown(1, 3)
    @app_commands.command(name="pull", description="Pull once.")
    async def pull(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                if await check_full_inventory(cursor, member, 1):
                    await interaction.response.send_message("Sorry, you do not have enough inventory slots to do another pull.")
                    return
                
                balance = await fetch_balance(cursor, member, interaction)
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
                        await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED + 1 WHERE USER_ID = %s", (member.id,))

                else:
                    await interaction.response.send_message(f"Not enough crystals. Current Balance: {balance}")

                await conn.commit()

    @pull.error
    async def on_pull_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    @discord.app_commands.checks.cooldown(1, 3)
    @app_commands.command(name="multipull", description="Pull multiple times.")
    async def multipull(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                if await check_full_inventory(cursor, member, 11):
                    await interaction.response.send_message("Sorry, you do not have enough inventory slots to do another pull.")
                    return

                balance = await fetch_balance(cursor, member, interaction)
                if balance is None:
                    return

                if balance >= 3000:
                    res = []
                    for i in range(0, 11):    
                        res.append(await Gacha().pull_cookie())

                        await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                        
                        if isinstance(res[i], int): # If integer, must mean essence
                            balance += res[i]
                            await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                        elif isinstance(res[i], str): # If string, must mean rarity
                            await cursor.execute("INSERT INTO ITEM (ITEM_INFO_ID, USER_ID) VALUES ((SELECT ITEM_INFO_ID FROM ITEM_INFO WHERE ITEM_RARITY = %s ORDER BY RAND() LIMIT 1), %s)", (res[i], member.id,))
                            await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED + 1 WHERE USER_ID = %s", (member.id,))
                    balance -= 3000
                    await interaction.response.send_message(f"{res}")
                else:
                    await interaction.response.send_message(f"Not enough crystals. Current Balance: {balance}")

                await conn.commit()

    @multipull.error
    async def on_multipull_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    @discord.app_commands.checks.cooldown(2, 15)
    @app_commands.command(name="balance", description="Check your balance of gems.")
    async def balance(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                balance = await fetch_balance(cursor, member, interaction)
                
                await interaction.response.send_message(f"Your balance is: {balance}")

    @balance.error
    async def on_balance_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    @app_commands.command(name="daily", description="Receive your daily bonus!")
    async def daily(self, interaction : discord.Interaction):
        '''
        Needs time restraint for usage
        '''

        member = interaction.user

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                balance = await fetch_balance(cursor, member, interaction)
                if not balance:
                    await cursor.execute("INSERT INTO USER (USER_ID, USER_GEMS) VALUES (%s, %s)", (member.id, dailyAmount,))

                dailyAmount = random.randrange(self.DAILY_MIN, self.DAILY_MAX + 1)
                currentTime = datetime.datetime.utcnow()

                await cursor.execute("SELECT USER_LAST_DAILY FROM USER WHERE USER_ID = %s", (member.id,))
                last_message_sent = await cursor.fetchone()

                if last_message_sent[0] == None or (currentTime - last_message_sent[0]).total_seconds() > self.DAILYCOOLDOWN:
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

    @app_commands.command(name="inventory", description="Check your inventory")
    async def inventory(self, interaction : discord.Interaction, name: discord.User= None):
        if name is None:
            member = interaction.user
        else:
            member = name
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT ITEM_INFO.ITEM_RARITY, ITEM_INFO.ITEM_NAME FROM ITEM NATURAL JOIN ITEM_INFO WHERE USER_ID = %s ORDER BY ITEM.ITEM_INFO_ID ASC", (member.id,))
                inventory_items = await cursor.fetchall()

                if not inventory_items:
                    interaction.response.send_message("You currently do not own any cookies. Consider using /daily or sending messages to earn crystals to use /pull or /multipull to pull cookies! Have fun :]")
                    return
        
        view = InventoryView(inventory=inventory_items, last_interaction=interaction, name=member, timeout=50)

        await interaction.response.send_message(embed=await view.view_page(1), view=view)

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
