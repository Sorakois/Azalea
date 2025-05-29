# imports
import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
import logging

class Smart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # class to handle the select menu interaction view
    class MetaView(discord.ui.View):
        def __init__(self, bot, game, valid_options, sub_options, user):
            super().__init__(timeout=90)
            self.bot = bot
            self.game = game
            self.valid_options = valid_options
            self.sub_options = sub_options
            self.user = user
            self.mode_look = None

            # add dropdown for the main game mode selection
            self.add_item(Smart.ModeSelect(valid_options[game]))

        async def interaction_check(self, interaction: discord.Interaction):
            return interaction.user.id == self.user.id

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True

    # dropdown for main mode selection
    class ModeSelect(discord.ui.Select):
        def __init__(self, options):
            formatted = [discord.SelectOption(label=opt, value=opt) for opt in options]
            super().__init__(placeholder="Choose a mode...", options=formatted)

        async def callback(self, interaction: discord.Interaction):
            view: Smart.MetaView = self.view
            mode = self.values[0]
            # check for sub-options
            if mode in view.sub_options:
                view.clear_items()
                # dropdown for sub-options
                view.add_item(Smart.SubModeSelect(mode, view.sub_options[mode]))
            else:
                view.mode_look = mode
                view.stop()
            await interaction.response.edit_message(view=view)

    # dropdown for sub-mode selection
    class SubModeSelect(discord.ui.Select):
        def __init__(self, parent_mode, options):
            self.parent_mode = parent_mode
            formatted = [discord.SelectOption(label=opt, value=opt) for opt in options]
            super().__init__(placeholder="Choose a sub-mode...", options=formatted)

        async def callback(self, interaction: discord.Interaction):
            view: Smart.MetaView = self.view
            view.mode_look = self.values[0]
            view.stop()
            await interaction.response.edit_message(view=view)

    @app_commands.command(name="meta", description="Check the current metas [hsr/crk/zzz]!")
    async def featured(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom', 'Zenless Zone Zero']):
        ''' 
        meta command keeps users up to date with the best current strategies
        '''
        member = interaction.user
        await interaction.response.defer(ephemeral=True)

        # list containing all games as keys and valid meta information user can look up
        valid_options = {
            "Honkai: Star Rail": ['Memory of Chaos', 'Pure Fiction', 'Apocalyptic Shadow', 'General Tier List'],
            "Cookie Run Kingdom": ['Arena', 'Arcane Arena', 'Guild Boss', 'Alliance', 'Limited Time Mode', 'Story'],
            "Zenless Zone Zero": ['Deadly Assault', 'Hollow Zero']
        }
        # dictionary for sub options for a mode (ex. guild boss -> LA, RVD, AOD)
        sub_options = {
            "Guild Boss" : ["RVD", "AOD", "LA"],
            "Story": ["..."]
        }

        # create the dropdown UI view
        view = Smart.MetaView(self.bot, game, valid_options, sub_options, member)
        await interaction.followup.send("Which would you like to learn more about?:", view=view, ephemeral=True)
        await view.wait()

        # return if no valid choice was made
        if not view.mode_look:
            return await interaction.followup.send("You didn't select a mode in time.", ephemeral=True)

        # get corresponding info from DB
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:

                # Get links and who did the editing
                await cursor.execute("SELECT LINK1, LINK2, LINK3, LAST_EDIT, EDIT_AUTH FROM META WHERE GAME = %s and MODE = %s", (game, view.mode_look))
                link_and_data = await cursor.fetchone()
                links = (link_and_data[0], link_and_data[1], link_and_data[2])
                edit_data = (link_and_data[3], link_and_data[4])

                try:
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{view.mode_look} | {game}")
                    em.set_thumbnail(url=interaction.user.guild.icon.url)

                    # gifs that will randomly be chosen to be sent alongside the meta info
                    game_gifs = {
                        "Honkai: Star Rail" : [
                            "https://media.tenor.com/AM2qQ1ErSesAAAAj/pom-pom-pom-pom-honkai-star-rail.gif",
                            "https://media.tenor.com/3oOJfWP8Rf0AAAAj/bronya-hsr.gif"],
                        "Cookie Run Kingdom" : [
                            "https://c.tenor.com/Pn1VrqlAC6oAAAAd/tenor.gif",
                            "https://c.tenor.com/6O2uFeYTDOMAAAAd/tenor.gif"],
                        "Zenless Zone Zero" : [
                            "https://c.tenor.com/ZOtfR1oVJRAAAAAd/tenor.gif",
                            r"https://media.tenor.com/u3mqzhX4JcwAAAAj/anby-%EC%A0%A0%EB%A0%88%EC%8A%A4.gif"
                        ]
                    }

                    # randomly assign corresponding image
                    gifs_length = len(game_gifs.get(game, []))
                    if gifs_length > 0:
                        r = random.randrange(0, gifs_length)
                        embed_img = game_gifs[game][r]
                        em.set_image(url=embed_img)

                    # only send source if it exists in the database
                    if links:
                        if links[0]:
                            em.add_field(name="First Source: ", value=links[0], inline=True)
                        if links[1]:
                            em.add_field(name="Second Source: ", value=links[1], inline=True)
                        if links[2]: 
                            em.add_field(name="Third Source: ", value=links[2], inline=True)
                        
                        # Who done did it and when
                        last_edit = edit_data[0].strftime("%B %d, %Y")
                        who_did_edit = edit_data[1]

                        em.add_field(name=f"Last edited: {last_edit}", value= f"Edited by <@{who_did_edit}>", inline=True)
                    else:
                        em.add_field(name="Will update soon!!! ", value="Ping a guide or @sorakoi to remind us to work on this :)", inline=True)
                    em.set_footer(text="Brought to you by... discord.gg/nurture")
                    await interaction.followup.send(embed=em, ephemeral=False)
                except:
                    await interaction.followup.send(f"Error with embed! Here are the links instead:\n{links}", ephemeral=True)
