import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random
import math

cookie_rarity_rankings = {
    'Common' : 1,
    'Rare' : 2,
    'Epic' : 3,
    'Super Epic': 4,
    'Legendary' : 5,
    'Dragon' : 5,
    'Special' : 5,
    'Ancient' : 6
}

class MultipullView(discord.ui.View):
    page = 1

    def __init__(self, last_interaction: discord.Interaction, essence: int, cookies: dict, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.essence = essence
        self.cookies = cookies
        self.last_interaction = last_interaction
        self.user = last_interaction.user
        
    async def eval_best_cookie(self):
        self.best_cookie = ''
        best_cookie_rarity = ''
        for c in self.cookies.keys():
            if best_cookie_rarity == '':
                self.best_cookie = c
                best_cookie_rarity = self.cookies[c]['rarity']
            elif cookie_rarity_rankings[self.cookies[c]['rarity']] > cookie_rarity_rankings[best_cookie_rarity]:
                self.best_cookie = c
                best_cookie_rarity = self.cookies[c]['rarity']
        return

    async def view_page(self, page_num):
        if page_num == 1:
            em = discord.Embed(title=f"Best Cookie Recieved: \n***__{self.best_cookie}__***")
            em.set_thumbnail(url=self.user.avatar.url)
            em.set_image(url=self.cookies[self.best_cookie]['image'])
            em.set_footer(text=f"Check the next page to see everything else you pulled!")
            return em
        else:
            #mention the user?
            em = discord.Embed(title=f"Total Recieved:")
            em.set_thumbnail(url="https://static.wikia.nocookie.net/cookierunkingdom/images/a/a1/Icon_usable_decor.png/revision/latest/scale-to-width-down/50?cb=20221111042019")
            empty = ""
            emp2 = ""
            for i in self.cookies.keys():
                empty += i + "\n"
                emp2 += self.cookies[i]['rarity'] + "\n"
            em.add_field(name=f"Cookies:", value=f"{empty}", inline = True)
            em.add_field(name=f"Rarities:", value=f"{emp2}", inline = True)
            em.add_field(name=f"Essence Gained:", value=f"{self.essence}", inline = False)
            em.set_footer(text=f"Go back?")
            return em

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.success, disabled=True)
    async def highlight(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page == 1:
            return
        self.page = 1

        button.disabled = True
        
        await self.last_interaction.delete_original_response()
        self.last_interaction = interaction
        await interaction.response.send_message(embed=await self.view_page(self.page), view=self)
        
        button.disabled = False
        
    @discord.ui.button(label="📜", style=discord.ButtonStyle.secondary)
    async def summary(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page == 2:
            return
        self.page = 2

        self.highlight.disabled = False
        button.disabled = True

        await self.last_interaction.delete_original_response()
        self.last_interaction = interaction
        await interaction.response.send_message(embed=await self.view_page(self.page), view=self)
        button.disabled = False
        
        

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
    @app_commands.command(name="pull", description="Pull once for 300 gems.")
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

                    if isinstance(res, int): # If integer, must mean essence
                        em = discord.Embed(title=f"Essence Recieved: \n***__{res}__***")
                        em.set_thumbnail(url=self.user.avatar.url)
                        em.set_image(url="https://static.wikia.nocookie.net/cookierunkingdom/images/6/61/Common_soul_essence.png/revision/latest?cb=20220707172739")
                        em.set_footer(text=f"Pull more? Do /pull or /multpull!")
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s WHERE USER_ID = %s", (res, member.id,))
                    elif isinstance(res, str): # If string, must mean rarity
                        await cursor.execute("SELECT ITEM_INFO_ID, ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = %s ORDER BY RAND() LIMIT 1", res)
                        item_info = await cursor.fetchone() # item_info[1] = name, item_info[2] = image
                        em = discord.Embed(title=f"Cookie Recieved: \n***__{item_info[1]}__***")
                        em.set_thumbnail(url=self.user.avatar.url)
                        em.set_image(url=item_info[2])
                        em.set_footer(text=f"Pull more? Do /pull or /multpull!")

                        await cursor.execute("INSERT INTO ITEM (ITEM_INFO_ID, USER_ID) VALUES (%s, %s)", (item_info[0], member.id,))
                        await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED + 1 WHERE USER_ID = %s", (member.id,))

                else:
                    await interaction.response.send_message(f"Not enough crystals. Current Balance: {balance}")
                    return

                await interaction.response.send_message(res)

                await conn.commit()

    @pull.error
    async def on_pull_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    @discord.app_commands.checks.cooldown(1, 3)
    @app_commands.command(name="multipull", description="Pull 11 times for 3000 gems.")
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
                    cookies_received = {}
                    essence_add = 0
                    for i in range(0, 11):    
                        res.append(await Gacha().pull_cookie())

                        await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))

                        if isinstance(res[i], int): # If integer, must mean essence
                            essence_add += res[i]
                        elif isinstance(res[i], str): # If string, must mean rarity
                            
                            await cursor.execute("SELECT ITEM_INFO_ID, ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = %s ORDER BY RAND() LIMIT 1", res[i])
                            item_info = await cursor.fetchone()
                            cookies_received[item_info[1]] = {'image': item_info[2], 'rarity' : res[i]}

                            await cursor.execute("INSERT INTO ITEM (ITEM_INFO_ID, USER_ID) VALUES (%s, %s)", (item_info[0], member.id,))
                            await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED + 1 WHERE USER_ID = %s", (member.id,))
                    balance -= 3000

                    if essence_add != 0:
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s WHERE USER_ID = %s", (essence_add, member.id,))

                    view = MultipullView(last_interaction=interaction, essence=essence_add, cookies=cookies_received)
                    await view.eval_best_cookie()

                    await interaction.response.send_message(embed=await view.view_page(1) ,view=view)
                else:
                    await interaction.response.send_message(f"Not enough crystals. Current Balance: {balance}")
                    return
                

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
                
                    em = discord.Embed(title="Daily Reward Claimed!")
                    em.add_field(name=f"You have recieved ***{dailyAmount}*** crystals!", value="Your new balance is: __" + str(balance) + "__")
                    em.set_image(url="https://static.wikia.nocookie.net/cookierunkingdom/images/b/bd/Daily_gift.png/revision/latest?cb=20221112035115")
                    em.set_footer(text=f"Return in 24 hours to recieve another!")
                    await interaction.response.send_message(embed=em, ephemeral=False)

                else:
                    time_remaining = 82800 - (currentTime - last_message_sent[0]).total_seconds()
                    if time_remaining > 3600:
                        time_remaining_str = f'{math.ceil(time_remaining/3600)} hours'
                    elif time_remaining > 60:
                        time_remaining_str = f'{math.ceil(time_remaining/60)} minutes'
                    else:
                        time_remaining_str = f'{time_remaining} seconds'
                    em = discord.Embed()
                    em.add_field(name="Daily has recently been claimed.", value=f"Sorry, you have already collected your daily login bonus today. Try again in **__{time_remaining_str}__**!")
                    em.set_image(url="https://static.wikia.nocookie.net/cookierunkingdom/images/b/bd/Common_witch_gacha.png/revision/latest?cb=20221112035138")
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
                await cursor.execute("SELECT ITEM_RARITY ,ITEM_NAME FROM ITEM NATURAL JOIN ITEM_INFO WHERE USER_ID = %s ORDER BY CASE ITEM_RARITY WHEN 'Common' THEN 1 WHEN 'Rare' THEN 2 WHEN 'Epic' THEN 3 WHEN 'Super Epic' THEN 4 WHEN 'Dragon' THEN 5 WHEN 'Legendary' THEN 6 WHEN 'Ancient' THEN 7 ELSE 8 END, ITEM_NAME DESC", (member.id,))
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
    async def pull_cookie(self#, interaction : discord.Interaction, name: discord.User= None
                          ):
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
