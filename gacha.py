import discord
from discord import app_commands
from discord.ext import commands
import aiomysql
import datetime
import random
import math
from typing import Literal

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
            em = discord.Embed(title=f"Best Cookie Recieved: \n*__{self.best_cookie}__*")
            em.set_thumbnail(url=self.user.avatar.url)
            em.add_field(name="Rarity:", value=f"{self.cookies[self.best_cookie]['rarity']}")
            em.set_image(url=self.cookies[self.best_cookie]['image'])
            em.set_footer(text=f"Check the next page to see everything else you pulled! To recycle cookies, do /crumble.")
            return em
        else:
            em = discord.Embed(title=f"Total Recieved:")
            em.set_thumbnail(url="https://static.wikia.nocookie.net/cookierunkingdom/images/a/a1/Icon_usable_decor.png/revision/latest/scale-to-width-down/50?cb=20221111042019")
            empty = ""
            emp2 = ""
            for i in self.cookies.keys():
                empty += i + "\n"
                emp2 += self.cookies[i]['rarity'] + "\n"
            em.add_field(name=f"Cookies:", value=f"{empty}", inline = True)
            em.add_field(name=f"Rarities:", value=f"{emp2}", inline = True)
            em.add_field(name=f"Essence Gained:", value=f"{self.essence} <:essence:1295791325094088855>", inline = False)
            em.set_footer(text=f"To recycle cookies, do /crumble. Go back?")
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
        em.set_thumbnail(url=self.user.avatar.url)
        
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

async def fetch_essence_balance(cursor, member, interaction):
    await cursor.execute("SELECT USER_ESSENCE FROM USER WHERE USER_ID = %s", (member.id))
    ebalance = await cursor.fetchone()

    try:
        ebalance = ebalance[0]
    except TypeError:
        em = discord.Embed()
        em.add_field(name="Error", value="Sorry your cannot use that command, as you have not recieved any essence yet.")
        await interaction.response.send_message(embed=em, ephemeral=True)
        return None # No value detected
    
    return ebalance


class CrumbleView(discord.ui.View):
    def __init__(self, bot, crumble_data, add, last_interaction, amt):
        super().__init__()
        self.bot = bot
        self.crumble_data = crumble_data
        self.add = add
        self.last_interaction = last_interaction
        self.amt = amt

    async def embed(self):
        em = discord.Embed(title=f"Are you sure you want to crumble {self.amt} {self.crumble_data[0][2]}(s)?")
        em.add_field(name=f"You will receive {self.add*self.amt} <:essence:1295791325094088855> essence if you do.", value="This process cannot be undone, so please take a moment to think about this.")
        em.set_footer(text=f"Reminder: Crumbling PERMANENTLY DELETES a cookie")
        return em

    @discord.ui.button(label = f"Crumble", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        em = discord.Embed(title=f"Cookie Crumbled")
        em.set_thumbnail(url=interaction.user.avatar.url)
        em.add_field(name=f"Essence Recieved: {self.add*self.amt}", value="Do /balance do check your new balance! <:essence:1295791325094088855>")
        em.set_footer(text=f"Reminder: Crumbling PERMANENTLY DELETES a cookie")

        await self.last_interaction.delete_original_response()

        await interaction.response.send_message(embed=em, ephemeral=True)

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                for c in self.crumble_data:
                    await cursor.execute("DELETE FROM ITEM WHERE USER_ID = %s AND ITEM_ID = %s", (c[0], c[1],))
                    await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s, USER_INV_SLOTS_USED = USER_INV_SLOTS_USED - 1 WHERE USER_ID = %s", (self.add, c[0],))

            await conn.commit()

    @discord.ui.button(label = "Cancel", style=discord.ButtonStyle.danger, emoji="✖")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.last_interaction.delete_original_response()
        await interaction.response.send_message("Crumble canceled.", ephemeral=True) 


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
            
    #ADD other games, like HSR
    #async def pull(self, interaction : discord.Interaction, gachagame: Literal['Cookie Run', 'Honkai: Star Rail', 'All']):
    
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
                        em.set_thumbnail(url=interaction.user.avatar.url)
                        em.set_image(url="https://static.wikia.nocookie.net/cookierunkingdom/images/6/61/Common_soul_essence.png/revision/latest?cb=20220707172739")
                        em.set_footer(text=f"Want to pull more? Do /pull or /multpull!")
                        await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s WHERE USER_ID = %s", (res, member.id,))
                    elif isinstance(res, str): # If string, must mean rarity
                        await cursor.execute("SELECT ITEM_INFO_ID, ITEM_RARITY, ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = %s ORDER BY RAND() LIMIT 1", res)
                        item_info = await cursor.fetchone() # item_info[1] = name, item_info[2] = image
                        em = discord.Embed(title=f"Cookie Recieved: \n*__{item_info[2]}__*")
                        em.set_thumbnail(url=interaction.user.avatar.url)
                        em.add_field(name="Rarity:", value=f"{item_info[1]}")
                        em.set_image(url=item_info[3])
                        em.set_footer(text=f"To recycle cookies, do /crumble. Want to pull more? Do /pull or /multpull!")

                        await cursor.execute("INSERT INTO ITEM (ITEM_INFO_ID, USER_ID) VALUES (%s, %s)", (item_info[0], member.id,))
                        await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED + 1 WHERE USER_ID = %s", (member.id,))

                else:
                    await interaction.response.send_message(f"Not enough crystals. Current Balance: {balance}")
                    return

                await interaction.response.send_message(embed=em)

                await conn.commit()

    @pull.error
    async def on_pull_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    @discord.app_commands.checks.cooldown(1, 3)
    @app_commands.command(name="multipull", description="Pull 11 times for 3000 gems.")
    async def multipull(self, interaction : discord.Interaction):

    #ADD other games, like HSR
    #async def pull(self, interaction : discord.Interaction, gachagame: Literal['Cookie Run', 'Honkai: Star Rail', 'All']):

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
                    await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
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
    @app_commands.command(name="balance", description="Check your balance of currencies")
    async def balance(self, interaction : discord.Interaction, currency: Literal['gem', 'essence']):
       member=interaction.user
       if currency == 'gem':
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                balance = await fetch_balance(cursor, member, interaction)
                em = discord.Embed(title=f"Gem Balance")
                em.set_thumbnail(url=interaction.user.avatar.url)
                em.add_field(name="Your balance is:", value=f"**__{balance}__** :gem:")
                await interaction.response.send_message(embed=em, ephemeral=False)
       if currency == 'essence':
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                ebalance = await fetch_essence_balance(cursor, member, interaction)
                em = discord.Embed(title=f"Essence Balance")
                em.set_thumbnail(url=interaction.user.avatar.url)
                em.add_field(name="You have collected:", value=f"**__{ebalance}__** <:essence:1295791325094088855>")
                await interaction.response.send_message(embed=em, ephemeral=False)

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
                dailyAmount = random.randrange(self.DAILY_MIN, self.DAILY_MAX + 1)
                currentTime = datetime.datetime.utcnow()

                balance = await fetch_balance(cursor, member, interaction)
                if balance == 0:
                    pass
                elif not balance:
                    await cursor.execute("INSERT INTO USER (USER_ID, USER_GEMS) VALUES (%s, %s)", (member.id, dailyAmount,))

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
                await cursor.execute("SELECT ITEM_RARITY, ITEM_NAME FROM ITEM NATURAL JOIN ITEM_INFO WHERE USER_ID = %s ORDER BY CASE ITEM_RARITY WHEN 'Common' THEN 1 WHEN 'Rare' THEN 2 WHEN 'Epic' THEN 3 WHEN 'Super Epic' THEN 4 WHEN 'Dragon' THEN 5 WHEN 'Legendary' THEN 6 WHEN 'Ancient' THEN 7 ELSE 8 END, ITEM_NAME DESC", (member.id,))
                inventory_items = await cursor.fetchall()

                if not inventory_items:
                    interaction.response.send_message("You currently do not own any cookies. Consider using /daily or sending messages to earn crystals to use /pull or /multipull to pull cookies! Have fun :]")
                    return
        
        view = InventoryView(inventory=inventory_items, last_interaction=interaction, name=member, timeout=50)

        await interaction.response.send_message(embed=await view.view_page(1), view=view)
    
    @app_commands.command(name="setfav", description="Set your favorite character")
    async def setfav(self, interaction : discord.Interaction, favchar: str):
        member=interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                #given name, grab ID
                #given ID, check if user has matching ID
                #set that character as user_fav_char

                #check if the character exists
                await cursor.execute("SELECT ITEM_INFO_ID, ITEM_NAME FROM `ITEM_INFO` WHERE ITEM_NAME LIKE %s;", ('%' + favchar + '%',))
                match_fav_exist = await cursor.fetchone()

                if match_fav_exist is None:
                    await interaction.response.send_message("This character does not exist! Try the command again.")
                    return
                else:
                    #now, use the ID and check if user has character
                    await cursor.execute("SELECT ITEM_ID FROM `ITEM` WHERE ITEM_INFO_ID = %s AND USER_ID = %s;", (match_fav_exist[0], member.id))
                    check_favchar = await cursor.fetchone()
                    
                    if check_favchar is None:
                        await interaction.response.send_message("You do not own this character. Explore other commands on Azalea like /pull.")
                        return
                    else:
                        try:
                            await cursor.execute("UPDATE USER SET USER_FAV_CHAR = %s WHERE USER_ID = %s;", (match_fav_exist[1], member.id))
                            await interaction.response.send_message(f"Success! Your new favorite character is **__{match_fav_exist[1]}__**. Check /profile!")
                        except:
                            await interaction.response.send_message("Unable to set favorite character! This is a bug... Ping @Sorakoi!")
                            return
                        
            await conn.commit()
            
    @app_commands.command(name="profilecolor", description="Set your profile's RGB color")
    async def profilecolor(self, interaction: discord.Interaction, user_red_value: int, user_green_value: int, user_blue_value: int):
        member = interaction.user

        if not (0 <= user_red_value <= 255):
            await interaction.response.send_message(f"Invalid RGB code! Currently False: 0<=Red Value<=255. Your Red Value is: {user_red_value}")
            return
        if not (0 <= user_green_value <= 255):
            await interaction.response.send_message(f"Invalid RGB code! Currently False: 0<=Green Value<=255. Your Green Value is: {user_green_value}")
            return
        if not (0 <= user_blue_value <= 255):
            await interaction.response.send_message(f"Invalid RGB code! Currently False: 0<=Blue Value<=255. Your Blue Value is: {user_blue_value}")
            return
        
        new_fav_color = f'{user_red_value}, {user_green_value}, {user_blue_value}'

        try:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE `USER` SET PROFILE_COLOR = %s WHERE USER_ID = %s;", (new_fav_color, member.id))
                await conn.commit()

            await interaction.response.send_message(f"Success <:white_check_mark:1298120271143895051>\nCheck out /profile !", ephemeral=True)
        except:
            await interaction.response.send_message(f"Error, Database issue! DM <@836367313502208040>", ephemeral=False)


    '''
    Add Command to change profile footer
    or
    keep booster only
    '''

    @app_commands.command(name="profile", description="View your profile")
    async def profile(self, interaction : discord.Interaction, name: discord.User= None):
        if name is None:
            member = interaction.user
        else:
            member = name
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                #check if user exists
                await cursor.execute("SELECT USER_ID FROM `USER` WHERE USER_ID = %s;", (member.id,))
                check_user_exist = await cursor.fetchone()

                if check_user_exist is None:
                    await interaction.response.send_message("User does not exist... Try again?", ephemeral=True)
                    return
                
                await cursor.execute("SELECT USER_LEVEL, USER_GEMS, USER_ESSENCE, USER_INV_SLOTS_USED, USER_FAV_CHAR, PROFILE_COLOR FROM `USER` WHERE USER_ID = %s;", (member.id,))
                profile_1 = await cursor.fetchone()

                #what to display if user has no favorite character set
                if profile_1[4] is None:
                    try:
                        formatted_name = member.display_name

                        #take string of RGB, break into 3 ints
                        user_custom_rgb = profile_1[5]
                        if user_custom_rgb is not None:
                            rgb_values = list(map(int, user_custom_rgb.split(',')))
                            if len(rgb_values) == 3:
                                em = discord.Embed(color=discord.Colour.from_rgb(*rgb_values), title=f"{formatted_name}'s Profile")
                            else:
                                em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{formatted_name}'s Profile")
                        else:
                            em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{formatted_name}'s Profile")

                        em.set_thumbnail(url=member.avatar.url)
                        em.add_field(name=f"Level:", value= f"{profile_1[0]} <:exp_jelly:1295954909371564033>")
                        em.add_field(name=f"Gem Balanace:", value= f"{profile_1[1]} <:gem:1295956837241458749>")
                        em.add_field(name=f"Essence Balance:", value= f"{profile_1[2]} <:essence:1295791325094088855>")
                        em.add_field(name=f"Characters Collected:", value= f"{profile_1[3]} <:cookie_base:1295954922562654229>")
                        em.set_footer(text=f"To set a favorite character to appear here, use /setfav.")
                        await interaction.response.send_message(embed=em, ephemeral=False)
                    except:
                        await interaction.response.send_message(f"Sorry! Please interact more with Azalea before doing this command.")
                        return
                else:
                    #now, match fav char with an image to put as footer
                    try:
                        await cursor.execute("SELECT ITEM_IMAGE FROM `ITEM_INFO` WHERE ITEM_NAME = %s", (profile_1[4]))
                        fav_char_pic = await cursor.fetchone()
                        
                        if fav_char_pic is None:
                            await interaction.response.send_message("No image is set! Please DM <@836367313502208040>")
                            return
                        else:
                            formatted_name = member.display_name

                            #take string of RGB, break into 3 ints
                            user_custom_rgb = profile_1[5]
                            if user_custom_rgb is not None:
                                rgb_values = list(map(int, user_custom_rgb.split(',')))
                                if len(rgb_values) == 3:
                                    em = discord.Embed(color=discord.Colour.from_rgb(*rgb_values), title=f"{formatted_name}'s Profile")
                                else:
                                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{formatted_name}'s Profile")
                            else:
                                em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{formatted_name}'s Profile")

                            em.set_thumbnail(url=member.avatar.url)
                            em.add_field(name=f"Level:", value= f"{profile_1[0]} <:exp_jelly:1295954909371564033>")
                            em.add_field(name=f"Gem Balanace:", value= f"{profile_1[1]} <:gem:1295956837241458749>")
                            em.add_field(name=f"Essence Balance:", value= f"{profile_1[2]} <:essence:1295791325094088855>")
                            em.add_field(name=f"Characters Collected:", value= f"{profile_1[3]} <:cookie_base:1295954922562654229>")

                            '''
                            Custom Images for BOOSTERS of Nurture
                            '''

                            #User = thomasunex
                            if member.id == 400443611105460234:
                                em.set_image(url=f"https://media1.tenor.com/m/yx7pASaizeEAAAAC/robozz-electro-man.gif")
                                em.set_footer(text=f"Brainrot-maxxing Thomas")
                            #User = sorakoi
                            elif member.id == 836367313502208040:
                                em.set_image(url=f"https://i.imgur.com/uW9PIib.gif")
                                em.set_footer(text=f"Shoutout to Croissant")
                            #User = technoblade_fan
                            elif member.id == 742498512398319625:
                                em.set_image(url=f"https://i.imgur.com/Hkovwhu.gif")
                                em.set_footer(text=f"DHIL is your character of choice. Thanks for boosting!")
                            #User = flowerily
                            elif member.id == 684946339259613302:
                                em.set_image(url=f"https://static.wikia.nocookie.net/cookierunkingdom/images/5/50/Cookie0049-call_user.gif")
                                em.set_footer(text=f"The REAL (enough) Moonlight Cookie!")
                            #Default Image
                            else:
                                em.set_image(url=fav_char_pic[0])
                                em.set_footer(text=f"Your favorite character is: {profile_1[4]}! (Server boost to set custom images)")

                            await interaction.response.send_message(embed=em, ephemeral=False)
                    except:
                        await interaction.response.send_message(f"Error! No valid image is set, please DM/ping <@836367313502208040>. profile_1[5] is {profile_1[5]}", ephemeral=False)
                        #await interaction.response.send_message(f"Your current array is {profile_1}", ephemeral=False)
                        return
                    
    @app_commands.command(name="crumble", description="Crumble a cookie from your inventory for essence")
    async def crumble(self, interaction : discord.Interaction, cookie: str, amount: int):
        member = interaction.user

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"SELECT USER_ID, ITEM_ID, ITEM_NAME, ITEM_RARITY FROM ITEM NATURAL JOIN ITEM_INFO WHERE ITEM_NAME LIKE '{cookie}%' AND USER_ID = {member.id} LIMIT {amount};")
                crumble_cookie = await cursor.fetchall()
                if amount < 1:
                    await interaction.response.send_message("Cannot crumble nothing/negative cookies, silly!")
                if len(crumble_cookie) < amount:
                    amount  = len(crumble_cookie)

                if not crumble_cookie:
                    await interaction.response.send_message("You currently do not own this cookie or it does not exist. Consider using /daily or sending messages to earn crystals to use /pull or /multipull to pull cookies! Have fun :]", ephemeral=True)
                    return

                crumble_essence = 0
                
                # Replace values with some sort of significance
                try:
                    if crumble_cookie[0][3] == "Common":
                        crumble_essence = 30
                    elif crumble_cookie[0][3] == "Rare":
                        crumble_essence = 35
                    elif crumble_cookie[0][3] == "Epic":
                        crumble_essence = 80
                    elif crumble_cookie[0][3] == "Super Epic":
                        crumble_essence = 250
                    elif crumble_cookie[0][3] == "Legendary" or "Special" or "Dragon":
                        crumble_essence = 3000
                    elif crumble_cookie[0][3] == "Ancient":
                        crumble_essence = 10000
                except TypeError:
                    await interaction.response.send_message("Cookie does not exist", ephemeral=True)
                    return
                    
                view = CrumbleView(bot=self.bot, crumble_data=crumble_cookie, add=crumble_essence, last_interaction=interaction, amt=amount)
                em = discord.Embed()
                await interaction.response.send_message(embed=await view.embed(), view = view, ephemeral=True)
            await conn.commit()

    @app_commands.command(name="expand", description="Expand your inventory slots!")
    async def expand(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                
                await cursor.execute("SELECT EXPAND_PURCHASES FROM USER WHERE USER_ID = %s", (member.id,))
                TimesPurchased = await cursor.fetchone()

                EssenceCostEquation = (125*(TimesPurchased[0]**2)) + 150

                essence = await fetch_essence_balance(cursor, member, interaction)
                
                if essence <= EssenceCostEquation:
                    await interaction.response.send_message(f"You cannot expand your inventory at this time. You only have {essence}/{EssenceCostEquation} <:essence:1295791325094088855>. Please gain more essence by gacha or crumbling.", ephemeral=True)
                    return
                else:
                    ExpandNewBalance = essence - EssenceCostEquation
                    await cursor.execute("UPDATE USER SET USER_ESSENCE = %s WHERE USER_ID = %s", (ExpandNewBalance, member.id))

                    await cursor.execute("UPDATE USER SET EXPAND_PURCHASES = EXPAND_PURCHASES + 1 WHERE USER_ID = %s", (member.id))
                    await cursor.execute("UPDATE USER SET USER_INV_SLOTS = USER_INV_SLOTS + 8 WHERE USER_ID = %s", (member.id))

                    await cursor.execute("SELECT USER_INV_SLOTS FROM USER WHERE USER_ID = %s", (member.id))
                    NewInvSlots = await cursor.fetchone()

                    em = discord.Embed(title="Inventory EXPANDED!")
                    em.add_field(name=f"By spending {EssenceCostEquation} <:essence:1295791325094088855>, you have increased your inventory slots by 8!", value=f"Your new balance is {ExpandNewBalance} <:essence:1295791325094088855> and now have __{NewInvSlots[0]}__ inventory slots! ")
                    em.set_image(url="https://static.wikia.nocookie.net/cookierunkingdom/images/d/dd/Standard_cookie_gacha_reveal.png/revision/latest?cb=20221109024120")
                    NextExpand = (125*((TimesPurchased[0]+1)**2)) + 150
                    em.set_footer(text=f"Want more slots? Do the command again! Your next expand will cost {NextExpand} <:essence:1295791325094088855>.")
                    await interaction.response.send_message(embed=em, ephemeral=False)

            await conn.commit()

    '''
    add command to set color for your profile's embed [/profilecolor]
    '''

class Gacha:
    '''
    gacha logic and computations

    functions -->
        - a pull function for gacha (cost, check if can afford, result)

    '''

    #Cookie Run Gacha
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
    
    # Honkai Star Rail Gacha:
    '''async def pull_hsr(self):
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
    
        return rarity'''
    
    async def handle_essence(self):
        return random.randrange(25,51)
