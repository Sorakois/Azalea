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
from misc import cleanse_name, fix_rarity, chrono_image

cookie_rarity_rankings = {
    'Common' : 1,
    'Rare' : 2,
    'Epic' : 3,
    'Super Epic': 4,
    'Legendary' : 5,
    'Dragon' : 5,
    'Special' : 5,
    'Ancient' : 6,
    'Stand_Four': 7,
    'Feat_Four': 7,
    'Stand_Five': 8,
    'Feat_Five': 8
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
            try:
                em = discord.Embed(title=f"Best Character Recieved: \n*__{cleanse_name(self.best_cookie).title()}__*")
                em.set_thumbnail(url=self.user.avatar.url)
                local_fix_rar = fix_rarity(self.cookies[self.best_cookie]['rarity'])
                em.add_field(name="Rarity:", value=f"{local_fix_rar}")
                em.set_image(url=self.cookies[self.best_cookie]['image'])
                em.set_footer(text=f"Check the next page to see everything else you pulled! To recycle characters, do /crumble.")
            except:
                em = discord.Embed(title=f"No Characters Recieved")
                em.set_thumbnail(url=self.user.avatar.url)
                em.add_field(name=f"Essence Gained:", value=f"{self.essence} <:essence:1295791325094088855>", inline = False)
                em.set_image(url="https://static.wikia.nocookie.net/cookierunkingdom/images/6/61/Common_soul_essence.png/revision/latest?cb=20220707172739")
                em.set_footer(text=f"Better luck next time!")
            return em
        else:
            em = discord.Embed(title=f"Total Recieved:")
            em.set_thumbnail(url="https://static.wikia.nocookie.net/cookierunkingdom/images/a/a1/Icon_usable_decor.png/revision/latest/scale-to-width-down/50?cb=20221111042019")
            empty = ""
            emp2 = ""
            for i in self.cookies.keys():
                empty += cleanse_name(i).title() + "\n"
                emp2 += fix_rarity(self.cookies[i]['rarity']) + "\n"

            em.add_field(name=f"Characters:", value=f"{empty}", inline = True)
            em.add_field(name=f"Rarities:", value=f"{emp2}", inline = True)
            em.add_field(name=f"Essence Gained:", value=f"{self.essence} <:essence:1295791325094088855>", inline = False)
            em.set_footer(text=f"To recycle characters, do /crumble. Go back?")
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

class HelpView(discord.ui.View):
    page = 1
    COMMANDS_PER_PAGE = 5

    def __init__(self, com_and_info, last_interaction: discord.Interaction, name: discord.User, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.com_and_info = com_and_info
        self.page = 1
        self.pages = math.ceil(len(self.com_and_info) / self.COMMANDS_PER_PAGE)
        self.last_interaction = last_interaction
        self.user = name
        self.bot = discord.Client

    async def view_page(self, page_num) -> discord.Embed:
        first_of_page = (page_num - 1) * self.COMMANDS_PER_PAGE
        last_of_page = self.COMMANDS_PER_PAGE * page_num
        if last_of_page > len(self.com_and_info):
            last_of_page = len(self.com_and_info)

        sorted_commands = sorted(self.com_and_info, key=lambda x: x[0].lower())

        em = discord.Embed(title=f"Azalea's Commands")
        bot_pfp = self.last_interaction.client.user.avatar.url
        em.set_thumbnail(url=bot_pfp)

        
        commands = ''
        descriptions = ''
        
        for item in range(first_of_page, last_of_page):
            commands += sorted_commands[item][0] + '\n'
            descriptions += sorted_commands[item][1] + '\n'

        em.add_field(name="Command", value=commands)
        em.add_field(name="Description", value=descriptions)
        em.set_footer(text=f"Page {self.page}/{self.pages}")
        
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

class InventoryView(discord.ui.View):

    page = 1
    COOKIE_PER_PAGE = 5

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

        sorted_inventory = sorted(self.inventory, key=lambda x: (cookie_rarity_rankings.get(x[0], 0), cleanse_name(x[1]).lower(), -x[2]), reverse=False)

        em = discord.Embed(title=f"{self.user.display_name}'s inventory")
        em.set_thumbnail(url=self.user.avatar.url)
        
        names = ''
        raritys = ''
        chronos = ''
        for item in range(first_of_page, last_of_page):
            '''if isinstance(names, str):
                names = names.title()'''
            if cleanse_name(sorted_inventory[item][1]).title() == "Topaz Numby":
                names += "Topaz" + '\n'
            else:
                names += cleanse_name(sorted_inventory[item][1]).title() + '\n'
            raritys += fix_rarity(sorted_inventory[item][0]) + '\n'
            chronos += chrono_image(sorted_inventory[item][2]) + '\n'
        em.add_field(name="Name", value=names)
        em.add_field(name="Rarity", value=raritys)
        em.add_field(name="Chrono", value=chronos)
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
        em = discord.Embed(title=f"Character Crumbled")
        em.set_thumbnail(url=interaction.user.avatar.url)
        em.add_field(name=f"Essence Recieved: {self.add*self.amt}", value="Do /balance do check your new balance! <:essence:1295791325094088855>")
        em.set_footer(text=f"Reminder: Crumbling PERMANENTLY DELETES a character")

        await self.last_interaction.delete_original_response()

        await interaction.response.send_message(embed=em, ephemeral=True)

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                for c in self.crumble_data:
                    await cursor.execute("DELETE FROM ITEM WHERE USER_ID = %s AND ITEM_ID = %s", (c[0], c[1],))
                    await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s, USER_INV_SLOTS_USED = USER_INV_SLOTS_USED - %s WHERE USER_ID = %s", (self.add, len(self.crumble_data), c[0],))

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
        self.lock = Lock()

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
    async def pull(self, interaction : discord.Interaction, game: Literal['Cookie Run', 'Honkai: Star Rail']):            

        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                if await check_full_inventory(cursor, member, 1):
                    await interaction.response.send_message("Sorry, you do not have enough inventory slots to do another pull.")
                    return
                
                await cursor.execute("SELECT FIFTY_FIFTY FROM USER WHERE USER_ID = %s", (member.id,))
                fifty_fifty = await cursor.fetchone()
                if not fifty_fifty:
                    await interaction.response.send_message("Error: Could not fetch fifty_fifty value.", ephemeral=True)
                    return
                fifty_fifty_value = fifty_fifty[0]
                
                balance = await fetch_balance(cursor, member, interaction)
                if balance is None:
                    return
                    
                if balance >= 300:
                    if game == 'Cookie Run':
                        res = await Gacha().pull_cookie()
                    if game == 'Honkai: Star Rail':
                        if fifty_fifty_value == 0:
                            res = await Gacha().won_fifty_hsr()
                        elif fifty_fifty_value == 1:
                            res = await Gacha().lost_fifty_hsr()
                        else:
                            await interaction.response.send_message("Error: invalid 50.", ephemeral=True)
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
                        item_info = await cursor.fetchone() # item_info[2] = name, item_info[3] = image

                        #update 50/50 if needed
                        if 'Feat_Five' in res:
                            await cursor.execute("UPDATE USER SET FIFTY_FIFTY = 0 WHERE USER_ID = %s ", (member.id,))
                            await conn.commit() 
                        elif 'Stand_Five' in res:
                            await cursor.execute("UPDATE USER SET FIFTY_FIFTY = 1 WHERE USER_ID = %s ", (member.id,))
                            await conn.commit()
                        winner_gacha = item_info[2].title()
                        em = discord.Embed(title=f"Character Recieved: \n*__{winner_gacha}__*")
                        em.set_thumbnail(url=interaction.user.avatar.url)
                        new_rarity = fix_rarity(item_info[1])
                        em.add_field(name="Rarity:", value=f"{new_rarity}")
                        em.set_image(url=item_info[3])
                        em.set_footer(text=f"To recycle characters, do /crumble. Want to pull more? Do /pull or /multpull!")

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
    async def multipull(self, interaction : discord.Interaction, game: Literal['Cookie Run', 'Honkai: Star Rail']):
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

                    await cursor.execute("SELECT FIFTY_FIFTY FROM USER WHERE USER_ID = %s", (member.id,))
                    fifty_fifty = await cursor.fetchone()
                    if not fifty_fifty:
                        await interaction.response.send_message("Error: Could not fetch fifty_fifty value.", ephemeral=True)
                        return
                    fifty_fifty_value = fifty_fifty[0]

                    for i in range(0, 11):    
                        if game == 'Cookie Run':
                            res.append(await Gacha().pull_cookie())
                        if game == 'Honkai: Star Rail':
                            if fifty_fifty_value == 0:
                                res.append(await Gacha().won_fifty_hsr())
                            elif fifty_fifty_value == 1:
                                res.append(await Gacha().lost_fifty_hsr())
                            else:
                                await interaction.response.send_message("Error: invalid 50.", ephemeral=True)


                        await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))

                        if isinstance(res[i], int): # If integer, must mean essence
                            essence_add += res[i]
                        elif isinstance(res[i], str): # If string, must mean rarity
                            
                            await cursor.execute("SELECT ITEM_INFO_ID, ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = %s ORDER BY RAND() LIMIT 1", res[i])
                            item_info = await cursor.fetchone()
                            if 'Feat_Five' in res:
                                await cursor.execute("UPDATE USER SET FIFTY_FIFTY = 0 WHERE USER_ID = %s ", (member.id,))
                                await conn.commit() 
                            elif 'Stand_Five' in res:
                                await cursor.execute("UPDATE USER SET FIFTY_FIFTY = 1 WHERE USER_ID = %s ", (member.id,))
                                await conn.commit()
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

                #See how long [in days] user's /daily streak is, then multiply!
                await cursor.execute("SELECT DAILY_STREAK FROM USER WHERE USER_ID = %s", (member.id,))
                current_streak = await cursor.fetchone()
                current_streak = current_streak[0]
                
                #quick bug check and fix
                if current_streak < 0:
                    await cursor.execute("UPDATE USER SET DAILY_STREAK = 0 WHERE USER_ID = %s", (member.id))

                #range = 0 day to 1 week
                if current_streak <= 7:
                    dailyAmount += ((current_streak/10 * dailyAmount) * 1.5)
                #range = 8 day to 15 day
                else:
                    dailyAmount += ((current_streak/10 * dailyAmount) * 1.25)

                if last_message_sent[0] == None or (currentTime - last_message_sent[0]).total_seconds() > self.DAILYCOOLDOWN:
                    balance += dailyAmount
                
                    await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                    await cursor.execute("UPDATE USER SET USER_LAST_DAILY = %s WHERE USER_ID = %s", (datetime.datetime.strftime(currentTime, '%Y-%m-%d %H:%M:%S'), member.id,))
                    await cursor.execute("UPDATE USER SET DAILY_STREAK = DAILY_STREAK + 1 WHERE USER_ID = %s", (member.id))
                    em = discord.Embed(title=f"Daily Reward Claimed!")
                    em.add_field(name=f"Current Streak:", value= f"{current_streak} days!")
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
                    em.add_field(name=f"Daily has recently been claimed. You currently have a streak of {current_streak} days!", value=f"Sorry, you have already collected your daily login bonus today. Try again in **__{time_remaining_str}__**!")
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
                await cursor.execute("SELECT ITEM_RARITY, ITEM_NAME, PROMO FROM ITEM NATURAL JOIN ITEM_INFO WHERE USER_ID = %s ORDER BY CASE ITEM_RARITY WHEN 'Common' THEN 1 WHEN 'Rare' THEN 2 WHEN 'Epic' THEN 3 WHEN 'Super Epic' THEN 4 WHEN 'Dragon' THEN 5 WHEN 'Legendary' THEN 6 WHEN 'Ancient' THEN 7 ELSE 8 END, ITEM_NAME DESC", (member.id,))
                inventory_items = await cursor.fetchall()

                if not inventory_items:
                    interaction.response.send_message("You currently do not own any cookies. Consider using /daily or sending messages to earn crystals to use /pull or /multipull to pull cookies! Have fun :]")
                    return
        
        view = InventoryView(inventory=inventory_items, last_interaction=interaction, name=member, timeout=50)

        await interaction.response.send_message(embed=await view.view_page(1), view=view)
    
    @app_commands.command(name="set_fav", description="Set your favorite character")
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
            
    @app_commands.command(name="profile_color", description="Set your profile's RGB color")
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
                        em.add_field(name=f"Level:", value= f"{profile_1[0]} <:exp_jelly:1295791594204823562>")
                        em.add_field(name=f"Gem Balanace:", value= f"{profile_1[1]} <:gem:1295956837241458749>")
                        em.add_field(name=f"Essence Balance:", value= f"{profile_1[2]} <:essence:1295791325094088855>")
                        em.add_field(name=f"Characters Collected:", value= f"{profile_1[3]} <:cookie_base:1295792901548281921>")
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
                            em.add_field(name=f"Level:", value= f"{profile_1[0]} <:exp_jelly:1295791594204823562>")
                            em.add_field(name=f"Gem Balanace:", value= f"{profile_1[1]} <:gem:1295956837241458749>")
                            em.add_field(name=f"Essence Balance:", value= f"{profile_1[2]} <:essence:1295791325094088855>")
                            em.add_field(name=f"Characters Collected:", value= f"{profile_1[3]} <:cookie_base:1295792901548281921>")

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
                            elif member.id == 784169727043174410:
                                em.set_image(url=f"https://static.wikia.nocookie.net/cookierunkingdom/images/a/ab/Shadow_milk_sing.png/revision/latest?cb=20240207163806")
                                em.set_footer(text=f"All in vain, the looney in sane will face annihilation")
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
                    await interaction.response.send_message("Cannot crumble nothing/negative characters, silly!")
                if len(crumble_cookie) < amount:
                    amount  = len(crumble_cookie)

                if not crumble_cookie:
                    await interaction.response.send_message("You currently do not own this character or it does not exist. Consider using /daily or sending messages to earn crystals to use /pull or /multipull to pull cookies! Have fun :]", ephemeral=True)
                    return

                crumble_essence = 0
                
                # Replace values with some sort of significance
                try:
                    #CRK and CROB
                    if crumble_cookie[0][3] == "Common":
                        crumble_essence = 30
                    elif crumble_cookie[0][3] == "Rare":
                        crumble_essence = 35
                    elif crumble_cookie[0][3] == "Epic":
                        crumble_essence = 80
                    elif crumble_cookie[0][3] == "Super Epic":
                        crumble_essence = 250
                    elif crumble_cookie[0][3] == "Legendary" or "Special" or "Dragon" or "Ancient":
                        crumble_essence = 3000
                    #HSR
                    elif crumble_cookie[0][3] == "Stand_Four" or "Feat_Four":
                        crumble_essence = 150
                    elif crumble_cookie[0][3] == "Stand_Five" or "Feat_Five":
                        crumble_essence = 3000
                except TypeError:
                    await interaction.response.send_message("Character does not exist", ephemeral=True)
                    return
                    
                view = CrumbleView(bot=self.bot, crumble_data=crumble_cookie, add=crumble_essence, last_interaction=interaction, amt=amount)
                em = discord.Embed()
                await interaction.response.send_message(embed=await view.embed(), view = view, ephemeral=True)
            await conn.commit()

    @app_commands.command(name="mass_crumble", description="Expand your inventory slots!")
    async def mass_crumble(self, interaction : discord.Interaction, rarity : str):
        member = interaction.user
        async with self.lock:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(f"SELECT USER_ID, ITEM_ID, ITEM_NAME, ITEM_RARITY FROM ITEM NATURAL JOIN ITEM_INFO WHERE ITEM_RARITY LIKE '{rarity}%' AND USER_ID = {member.id} AND PROMO = 0 LIMIT 20;")
                    all_rarity_select = await cursor.fetchall()
                    
                    item_ids = []
                    crumble_essence = 0
                    for unique_item in all_rarity_select:
                        char_id = unique_item[1]
                        char_rarity = unique_item[3]
                        
                        #add id to list of ids to remove
                        item_ids.append(char_id)

                        #rarity to essence (crk)
                        if char_rarity == "Common":
                            crumble_essence += 30
                        elif char_rarity == "Rare":
                            crumble_essence += 35
                        elif char_rarity == "Epic":
                            crumble_essence += 80
                        elif char_rarity == "Super Epic":
                            crumble_essence += 250
                        elif char_rarity == "Legendary" or char_rarity == "Special" or char_rarity == "Dragon" or char_rarity == "Ancient":
                            crumble_essence += 750
                        
                        #rarity to essence (hsr)
                        if char_rarity == "Stand_Four" or char_rarity == "Feat_Four":
                            crumble_essence += 150
                        elif char_rarity == "Stand_Five" or char_rarity == "Feat_Five":
                            crumble_essence += 750
                    
                    #remove each item from database
                    for id in item_ids:
                        await cursor.execute("DELETE FROM ITEM WHERE USER_ID = %s and ITEM_ID = %s", (member.id, id))
                        await conn.commit()

                    #add essence
                    await cursor.execute("UPDATE USER SET USER_ESSENCE = USER_ESSENCE + %s, USER_INV_SLOTS_USED = USER_INV_SLOTS_USED - %s WHERE USER_ID = %s", (crumble_essence, len(item_ids), member.id))

                    #grab new balance
                    await cursor.execute("SELECT USER_ESSENCE FROM USER WHERE USER_ID = %s ", (member.id))
                    new_bal = await cursor.fetchone()
                    new_bal = new_bal[0] if new_bal else 0 

                await conn.commit()
                await interaction.response.send_message(f"Success!\n\nYou recieved {crumble_essence} essence by crumbling {len(all_rarity_select)} characters of rarity {char_rarity}.\nYou now have {new_bal} <:essence:1295791325094088855>", ephemeral=False)

                    #debug line
                    #await interaction.response.send_message(f"All item ids: {item_ids}", ephemeral=False)

    @app_commands.command(name="expand", description="Expand your inventory slots!")
    async def expand(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                
                await cursor.execute("SELECT EXPAND_PURCHASES FROM USER WHERE USER_ID = %s", (member.id,))
                TimesPurchased = await cursor.fetchone()

                EssenceCostEquation = (8*(TimesPurchased[0]**2)) + 60

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
                    em.set_footer(text=f"Want more slots? Do the command again! Your next expand will cost {NextExpand} essence.")
                    await interaction.response.send_message(embed=em, ephemeral=False)

            await conn.commit()

    @app_commands.command(name="view_character", description="View a character in the gacha pool!")
    async def viewcharacter(self, interaction: discord.Interaction, character: str):

        #characters with multiple "branches"
        if character.upper() == "TINGYUN":
            await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Harmony Tingyun', 'Nihility Tingyun', or 'Fugue'", ephemeral=True)
            return 
        if character.upper() == "MARCH":
            await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Hunt March' or 'Preservation March", ephemeral=True)
            return
        if character.upper() == "TRAILBLAZER" or character.upper() == "TB" or character.upper() == "MC" or character.upper() == "CAELUS" or character.upper() == "STELLE" or character.upper() == "RACCOON" or character.upper() == "TRASH" or character.upper() == "TRASHBLAZER":
            await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Destruction/Preservation/Harmony Caelus/Stelle.", ephemeral=True)
            return
        
        #fix name to db format
        character = cleanse_name(character)
        
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT * FROM ITEM_INFO WHERE ITEM_NAME LIKE %s", (character + "%"))
                ViewGachaChar = await cursor.fetchone()

        #catch invalid entries
        if not ViewGachaChar:
            await interaction.response.send_message(f"{character} does not exist. Try again?", ephemeral=True)
            return
        
        try:
            #make pretty for user
            true_rarity = fix_rarity(ViewGachaChar[1])
            fixed_name = ViewGachaChar[2].title()

            em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=fixed_name)
            em.set_thumbnail(url=interaction.user.guild.icon.url)
            em.set_image(url=ViewGachaChar[4])
            em.add_field(name="Rarity: ", value=true_rarity, inline=True)
            em.set_footer(text="Brought to you by... discord.gg/nurture")
            await interaction.response.send_message(embed=em)
        except ValueError as e:
            await interaction.response.send_message("No Image Exists! Ping <@836367313502208040>", ephemeral=False)
            return
        
    @app_commands.command(name="promote", description="Promote the Chrono of your character!")
    async def promote(self, interaction : discord.Interaction, character : str):
        member = interaction.user
        '''
        Promotion System

        Needed in DB:
            ~> Column for "character promotion level", default it to 0 and incriment by 1 up to 10
        
        Promo Logic:
            Amount of copies per promo level [once per level]:
                ~> {0 -> 1 = +1 copy [1 total]}
                ~> {1 -> 2 = +2 copies [3 total]}
                ~> {2 -> 3 = +3 copies [6 total]}
                ~> {3 -> 4 = +4 copies [10 total]}
                ~> {4 -> 5 = +5 copies [15 total]}
                ----------------------------------
                ~> {5 -> 6 = +6 copies [21 total]}
                ~> {6 -> 7 = +7 copies [28 total]}
                ~> {7 -> 8 = +8 copies [36 total]}
                ~> {8 -> 9 = +9 copies [45 total]}
                ~> {9 -> 10 = +10 copies [55 total]}
        Promo Process:
            cleanse string
            given string, check for highest promo and check for how many copies owned
            increase promo level by corresponding units needed
                if cant afford, say "you need X more copies to increase promo level to Y"
            remove copies of characcter
            say "Z is now Chrono Y"
            
        '''
        async with self.lock:
            #characters with multiple "branches"
            if character.upper() == "TINGYUN":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Harmony Tingyun', 'Nihility Tingyun', or 'Fugue'", ephemeral=True)
                return 
            if character.upper() == "MARCH":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Hunt March' or 'Preservation March", ephemeral=True)
                return
            if character.upper() == "TRAILBLAZER" or character.upper() == "TB" or character.upper() == "MC" or character.upper() == "CAELUS" or character.upper() == "STELLE" or character.upper() == "RACCOON" or character.upper() == "TRASH" or character.upper() == "TRASHBLAZER":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Destruction/Preservation/Harmony Caelus/Stelle.", ephemeral=True)
                return
            
            #fix name
            character = cleanse_name(character)

            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    #grab all copies
                    await cursor.execute("SELECT USER_ID, ITEM_INFO_ID, ITEM_NAME, ITEM_RARITY, PROMO FROM ITEM NATURAL JOIN ITEM_INFO WHERE ITEM_NAME LIKE %s AND USER_ID = %s ORDER BY PROMO DESC;", (f'{character}%', member.id))
                    try:
                        char_copies = await cursor.fetchall()

                        if not char_copies:
                            await interaction.response.send_message(f"No copies of {character} found in your inventory.", ephemeral=True)
                            return

                        #make an array of all promo levels in descending order (high -> low)
                        character_id_p1 = [c_id[1] for c_id in char_copies]
                        char_id = character_id_p1.pop(0) #just grab one ID

                        namelist = [name[2] for name in char_copies]
                        namechar =namelist.pop(0) #just grab one name

                        all_promo_levels = [promo[4] for promo in char_copies]
                        highest_promo = all_promo_levels.pop(0) #grab highest
                        og_highest = highest_promo

                        #logic for how many coppies needed for promotion
                        promo_thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    
                        #DEBUGGING
                        copies_returned = 0
                        i = all_promo_levels[0]
                        while i > 0:
                            copies_returned += promo_thresholds[i]
                            i-=1

                        for promo in all_promo_levels:
                            if promo != 0:
                                #remove dupes that are more than promo 1 that isnt highest, and return coppies
                                await cursor.execute("DELETE FROM ITEM WHERE ITEM_INFO_ID = %s AND USER_ID = %s AND PROMO = %s LIMIT 1;", (char_id, member.id, promo))
                                #update slots
                                await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED - %s WHERE USER_ID = %s", (1, member.id))
                                
                                #add dupes for each number of promo the character had
                                for item in range(copies_returned):
                                    await cursor.execute("INSERT INTO ITEM (ITEM_INFO_ID, USER_ID, PROMO) VALUES (%s, %s, 0)", (char_id, member.id,))

                        if highest_promo == 10:
                            await interaction.response.send_message(f"{character} is already Chrono 10. Please crumble remaining copies for essence.", ephemeral=True)

                        #see how many copies owned for calculation
                        copies_owned = len(all_promo_levels)
                        required_copies =  promo_thresholds[highest_promo]

                        if highest_promo < len(promo_thresholds):

                            if copies_owned >= required_copies:
                                    try:
                                        highest_promo += 1
                                        #debug
                                        #await interaction.response.send_message(f"Highest Promo: {highest_promo}\nChar_id: {char_id}\nMember.id: {member.id}\nOG_highest: {og_highest}\nRequired Copies: {required_copies}", ephemeral=False)

                                        await cursor.execute("UPDATE ITEM SET PROMO = %s WHERE ITEM_INFO_ID = %s AND USER_ID = %s AND PROMO = %s LIMIT 1;", ((highest_promo), char_id, member.id, og_highest))
                                        await cursor.execute("DELETE FROM ITEM WHERE ITEM_INFO_ID = %s AND USER_ID = %s AND PROMO = 0 LIMIT %s;", (char_id, member.id, required_copies))
                                        await cursor.execute("UPDATE USER SET USER_INV_SLOTS_USED = USER_INV_SLOTS_USED - %s WHERE USER_ID = %s", (1, member.id))
                                        await conn.commit()
                                        local_chrono_img = chrono_image(highest_promo)
                                        await interaction.response.send_message(f"{namechar.title()} is now Chrono {highest_promo} {local_chrono_img}", ephemeral=False)
                                    except:
                                        await interaction.response.send_message(f"ERROR! Please contact sorakoi, invalid code.", ephemeral=True)

                            else:
                                copies_needed = required_copies - copies_owned
                                await interaction.response.send_message(f"{namechar.title()} is Chrono {highest_promo}. You need {copies_needed} more copies to further promote.", ephemeral=True)

                        await conn.commit()
                    except:
                        await interaction.response.send_message(f"INVALID CODE:\nCharacter: {character}\nHighest Promo: {highest_promo}\nChar copies: {char_copies}", ephemeral=True)


    '''
    HSR Specific Gacha
    '''    
    @app_commands.command(name="fiftyfifty", description="Check to see if you won your last 50/50!")
    async def fiftyfifty(self, interaction : discord.Interaction):
        member = interaction.user
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT FIFTY_FIFTY FROM USER WHERE USER_ID = %s", (member.id,))
                check_fifty = await cursor.fetchone()
                
                if check_fifty is None:
                    await interaction.response.send_message(f"User data not found. Please make sure you have pulled before.", ephemeral=True)
                    return
                if check_fifty[0] == 1:
                    await interaction.response.send_message(f"You have LOST your last 50/50. Your next HSR 5 star is guranteed to be a featured character!", ephemeral=True)
                elif check_fifty[0] == 0:
                    await interaction.response.send_message(f"You have WON your last 50/50. Your next HSR 5 star can be any character.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Invalid database structuring, please alert sorakoi.", ephemeral=True)

    @app_commands.command(name="featured", description="Check to see the current rate-up characters for HSR gacha!")
    async def featured(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail']):
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                # Fetch featured five and four-star characters
                await cursor.execute("SELECT ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = 'Feat_Five' LIMIT 1;")
                top_featured_five = await cursor.fetchone()

                await cursor.execute("SELECT ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = 'Feat_Five'")
                featured_five = await cursor.fetchall()

                await cursor.execute("SELECT ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO WHERE ITEM_RARITY = 'Feat_Four'")
                featured_four = await cursor.fetchall()

                try:
                    em = discord.Embed(color=discord.Colour.from_rgb(0, 255, 255), title="Featured Characters:")
                    em.set_image(url=top_featured_five[0])
                    # Add featured 5-star characters to the embed
                    for character in featured_five:
                        em.add_field(name=f"{cleanse_name(character[0]).title()}", value=f"★★★★★", inline=True)
                        ##em.set_image(url={character[1]})
                    # Add featured 4-star characters to the embed
                    for character in featured_four:
                        em.add_field(name=f"{cleanse_name(character[0]).title()}", value=f"★★★★", inline=True)
                        ##em.set_image(url={character[1]})
                    await interaction.response.send_message(embed=em)
                except:
                    await interaction.response.send_message("No featured characters currently.", ephemeral=False)
                    return

        '''
    Below are all ways to get gems!
    '''

    #First Way (1), Trivia!
    @discord.app_commands.checks.cooldown(1, 120)
    @app_commands.command(name="trivia", description="Answer anime questions, get gems!")
    async def trivia(self, interaction: discord.Interaction):
        member = interaction.user
        '''
        Get trivia [for now, only anime]
        Later, make what type of question a prompt above: Literal['Anime', 'Science', etc.]
        Then, return correct trivia from APIs

        make later into a function

        later, show user how much time left until cmd can be executed again
        '''
       
        #grab API informatiom
        anime_trivia = requests.get("https://opentdb.com/api.php?amount=1&category=31&type=boolean")
        json_data = json.loads(anime_trivia.text)
        trivia_question = json_data['results'][0]['question'].replace("&quot;", '"')
        trivia_question = trivia_question.replace("&#039;", '\'')
        trivia_question = trivia_question.replace("&eacute;", 'é')
        trivia_answer = json_data['results'][0]['correct_answer']
        await interaction.response.send_message(f"**__True or False:__**\n{trivia_question}")

        # Wait for the next message
        def check(message: discord.Message):
            return message.author.id == member.id and message.channel.id == interaction.channel.id
    
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=30.0)

            if msg.content.title() == trivia_answer:
                async with self.bot.db.acquire() as conn:
                    async with conn.cursor() as cursor:
                        correct_answer_gems = 300
                        #grab user's current balance
                        balance = await fetch_balance(cursor, member, interaction)
                        if balance == 0:
                            pass
                        elif not balance:
                            await cursor.execute("INSERT INTO USER (USER_ID, USER_GEMS) VALUES (%s, %s)", (member.id, correct_answer_gems,))

                        balance += correct_answer_gems
                        await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance, member.id,))
                    await conn.commit()
                await interaction.channel.send(f"***Correct! :white_check_mark:***\n\nYou have gained __{correct_answer_gems} :gem:__! Your new balance is __**{balance}**__. Please wait 2 minutes before doing this command again!")
                
            else:
                await interaction.channel.send(f"***Wrong! :x:***\n\nTry again in 2 minutes :alarm_clock:")
        except asyncio.TimeoutError:
            await interaction.channel.send("You didn't send a message in time! Try again in 2 minutes.")     

    @trivia.error
    async def on_trivia_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    #Second way, Guess a random number!
    @discord.app_commands.checks.cooldown(1, 120)
    @app_commands.command(name="guessing_game", description="Guess correctly, get gems!")
    async def guessing_game(self, interaction : discord.Interaction, other_user : discord.User):
            #bot cant be teammate... yet?
            if other_user.id == 1160998311264796714 or other_user.id == 1082486461103878245:
                await interaction.response.send_message(f"Azalea is busy :(", ephemeral=True)
            else:   
                #make number for random guessing, make it be 25 gap always
                lower_guess = 0
                higher_guess = 25
                guess_this_rangerandomizer = random.randint(0,100)
                lower_guess += guess_this_rangerandomizer
                higher_guess += guess_this_rangerandomizer
                guess_this = random.randint(lower_guess,higher_guess)

                await interaction.response.defer()
                while True:
                    if other_user.id != interaction.user.id:
                        #user 2, the one pinged, goes first
                        await interaction.followup.send(f"<@{other_user.id}>, guess a whole number between {lower_guess} and {higher_guess} :game_die:\n[Will keep repeating until correct].")
                        def check_user2(message: discord.Message):
                            return message.author.id == other_user.id and message.channel.id == interaction.channel.id

                        try:
                            user2_msg = await interaction.client.wait_for('message', check=check_user2, timeout=45.0)
                            user2_guess = int(user2_msg.content)
                            if user2_guess == guess_this:
                                user_correct = other_user.id
                                other_correct = interaction.user.id
                                break
                            else:
                                # Second user was incorrect, now let the first user guess
                                await interaction.followup.send(f"<@{interaction.user.id}>, guess a whole number between {lower_guess} and {higher_guess} :game_die:\n[Will keep repeating until correct]")
                                
                                def check_user1(message: discord.Message):
                                    return message.author.id == interaction.user.id and message.channel.id == interaction.channel.id
                                
                                try:
                                    user1_msg = await interaction.client.wait_for('message', check=check_user1, timeout=45.0)
                                    user1_guess = int(user1_msg.content)
                                    if user1_guess == guess_this:
                                        user_correct = interaction.user.id
                                        other_correct = other_user.id
                                        break
                                except asyncio.TimeoutError:
                                    await interaction.followup.send(f"<@{interaction.user.id}> didn't send a message in time! Try again in 2 minutes.")
                                    break
                        except asyncio.TimeoutError:
                            await interaction.followup.send(f"<@{other_user.id}> didn't send a message in time! Try again in 2 minutes.")
                            break
                    else:
                        await interaction.followup.send(f"<@{interaction.user.id}>, guess a whole number between {lower_guess} and {higher_guess} :game_die:\n[Will keep repeating until correct].")
                        def check_user1(message: discord.Message):
                            return message.author.id == interaction.user.id and message.channel.id == interaction.channel.id
                        try:
                            user1_msg = await interaction.client.wait_for('message', check=check_user1, timeout=45.0)
                            user1_guess = int(user1_msg.content)
                            if user1_guess == guess_this:
                                user_correct = interaction.user.id
                                other_correct = other_user.id
                                break
                        except asyncio.TimeoutError:
                            await interaction.followup.send(f"<@{interaction.user.id}> didn't send a message in time! Try again in 2 minutes.")
                            break

            
            async with self.lock:
                #now loop is done, give gems!
                async with self.bot.db.acquire() as conn:
                    async with conn.cursor() as cursor:
                        correct_answer_gems = 750 #solo default amt
                        if other_user.id != interaction.user.id:
                            correct_answer_gems = 1500 #duo amt
                        
                        #grab user's current balance
                        balance_user1 = await fetch_balance(cursor, interaction.user, interaction)
                        if other_user.id != interaction.user.id:
                            alance_user2 = await fetch_balance(cursor, other_user, interaction)
                        
                        #quick bug check
                        if balance_user1 is None:
                            await cursor.execute("INSERT INTO USER (USER_ID, USER_GEMS) VALUES (%s, %s)", (interaction.user.id, correct_answer_gems,))
                        if other_user.id != interaction.user.id:
                            if balance_user2 is None:
                                await cursor.execute("INSERT INTO USER (USER_ID, USER_GEMS) VALUES (%s, %s)", (other_user.id, correct_answer_gems,))

                        #add gems
                        balance_user1 += correct_answer_gems
                        if other_user.id != interaction.user.id:
                            balance_user2 += correct_answer_gems
                        await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance_user1, interaction.user.id,))
                        await conn.commit()
                        if other_user.id != interaction.user.id:
                            await cursor.execute("UPDATE USER SET USER_GEMS = %s WHERE USER_ID = %s", (balance_user2, other_user.id,))
                            await conn.commit()

                    await conn.commit()
                await interaction.followup.send(f"***{guess_this} is correct! :white_check_mark:*** Good job <@{user_correct}>!\n\nYou and <@{other_correct}> both gained __{correct_answer_gems} :gem:__!\nPlease wait 2 minutes before doing this command again!")
    
    @guessing_game.error
    async def on_guessing_game_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))

    #Third way, do a thing!
    '''@discord.app_commands.checks.cooldown(1, 120)
    @app_commands.command(name="guessing_game", description="Guess correctly, get gems!")
    async def guessing_game(self, interaction : discord.Interaction, other_user : discord.User):'''

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

        if 0 <= probability < 0.3750:
            # Give user essence
            essence = await self.handle_essence()
            return essence

        elif 0.3750 <= probability < 0.6750:
            # Give user a common cookie
            rarity = 'Common'

        elif 0.6750 <= probability < 0.8750:
            # Give user a rare cookie
            rarity = 'Rare'

        elif 0.8750 <= probability < 0.9550:
            # Give user a epic cookie
            rarity = 'Epic'

        elif 0.9550 <= probability < 0.9800:
            #Give user a super epic cookie
            rarity = 'Super Epic'

            '''
            WAY TOO LOW
            '''

        elif 0.9800 <= probability < 1:
            # Give user Legendary, Dragon, Ancient, or Special cookie
            with random.randrange(0,4) as r:
                match r:
                    case 0:
                        rarity = 'Legendary'
                    case 1:
                        rarity = 'Dragon'
                    case 2:
                        rarity = 'Special'
                    case 3:
                        rarity = 'Ancient'
    
        return rarity
    
    # Honkai Star Rail Gacha 1/2
    '''
    
    WON LAST 50/50
    
    '''
    async def won_fifty_hsr(self):
        probability = random.random()
        rarity = ""

        if 0 <= probability < 0.8600:
            # Give user essence
            essence = await self.handle_essence()
            return essence

        elif 0.8600 <= probability < 0.9300:
            # Give user a standard ★★★★ charater
            rarity = 'Stand_Four' 

        elif 0.9300 <= probability < 0.9800:
            # Give user a featured ★★★★ charater
            rarity = 'Feat_Four' 
            # ★★★★

        elif 0.9800 <= probability < 0.9900:
            # Give user a standard ★★★★★ charater
            rarity = 'Stand_Five'
            # ★★★★★

        elif 0.9900 <= probability < 1:
            # Give user a featured ★★★★★ charater
            rarity = 'Feat_Five'
            # ★★★★★
        return rarity

    # Honkai Star Rail Gacha:
    '''
    
    LOST LAST 50/50
    
    '''
    async def lost_fifty_hsr(self):
        probability = random.random()
        rarity = ""

        if 0 <= probability < 0.8600:
            # Give user essence
            essence = await self.handle_essence()
            return essence

        elif 0.8600 <= probability < 0.9300:
            # Give user a standard ★★★★ charater
            rarity = 'Stand_Four' 

        elif 0.9300 <= probability < 0.9800:
            # Give user a featured ★★★★ charater
            rarity = 'Feat_Four' 
            # ★★★★

        elif 0.9800 <= probability < 1:
            # Give user a featured ★★★★★ charater
            rarity = 'Feat_Five'
            # ★★★★★
        return rarity
    
    async def handle_essence(self):
        return random.randrange(25,51)