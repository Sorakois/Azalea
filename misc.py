import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
import logging

# Database of gifs (links)
hugging_gifs = [
    "https://media1.tenor.com/m/8YhtDI2-uTQAAAAd/topaz-numby.gif",
    "https://media1.tenor.com/m/uiak6BECN_sAAAAC/emunene-emu.gif",
    "https://media1.tenor.com/m/qVWUEYImyKAAAAAC/sad-hug-anime.gif",
    "https://media1.tenor.com/m/UnpQCW40JekAAAAC/anime-hug.gif",
    "https://media1.tenor.com/m/b3Qvt--s_i0AAAAC/hugs.gif",
    "https://tenor.com/view/sami-en-dina-sami-dina-dina-sami-dina-en-sami-gif-15422575992980791421",
    "https://cdn.weeb.sh/images/S1DyFuQD-.gif",
    "https://cdn.weeb.sh/images/Bkta0ExOf.gif"
]

class MiscCMD(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="hug", description="Receive a hug!")
    async def hug(self, interaction: discord.Interaction):
        # Optionally: Log or handle user interaction data here if needed
        member = interaction.user
        try:
            # Send a random hug gif
            chosen_gif = random.choice(hugging_gifs)
            await interaction.response.send_message(chosen_gif, ephemeral=False)
        except Exception as e:
            # Handle potential errors
            await interaction.response.send_message("Oops! Something went wrong.", ephemeral=True)
            print(f"Error [/hug]: {e}")

    @discord.app_commands.checks.cooldown(5, 15)
    @app_commands.command(name="build", description="Check the optimal build for each character!")
    async def build(self, interaction : discord.Interaction, game: Literal['HSR', 'CRK'], character: str):
        character = character.lower()
        if game == "HSR":
            #Cleansing Queries
            if character.upper() == "DR. RATIO" or character.upper() == "RATIO" or character.upper() == "DOCTOR RATIO":
                character = "dr ratio"
            if character.upper() == "DHIL" or character.upper() == "DAN HENG IMBIBITOR LUNAE":
                character = "imbibitor lunae"
            if character.upper() == "FEI XIAO":
                character = "feixiao"

            if character.upper() == "MARCH":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Hunt March' or 'Preservation March", ephemeral=True)
                return
            if character.upper () == "MARCH 8TH" or character.upper () == "MARCH 8" or character.upper() == "MARCH HUNT":
                character = "hunt march"
            if character.upper() == "MARCH 7TH" or character.upper () == "MARCH 7":
                character = "preservation march"

            if character.upper() == "TRAILBLAZER":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Destruction Trailblazer', 'Preservation Trailblazer' or 'Harmony Trailblazer.", ephemeral=True)
                return
            if character.upper() == "HTB" or character.upper() == "HARMONY MC" or character.upper() == "HMC" or character.upper() == "HARMONY TB" or character.upper() == "TRAILBLAZER HARMONY":
                character = "harmony trailblazer"
            if character.upper () == "Preservation MC" or character.upper() == "FIRE MC" or character.upper() == "FIRE TB" or character.upper() == "TRAILBLAZER PRESERVATION":
                character = "preservation trailblazer"
            if character.upper() == "Destruction MC" or character.upper() == "DESTRUCTION TB" or character.upper() == "PHYSICAL TRAILBLAZER" or character.upper() == "TRAILBLAZER DESTRUCTION":
                character = "destruction trailblazer"

            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT * FROM HSR_BUILD") #WHERE name = %s", (character)
                    HSRBuildInfo = await cursor.fetchall()

            res = ''
            for row in HSRBuildInfo:
                temp = row[0]
                if character == temp:
                    res = row
                    break
            try:
                #add a hyphen for URL
                character = character.replace(" ", "-")
                #embed for build
                #maybe try capitilizaiton for each word later
                em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"Ideal Build of: {" ".join(character.split("-")).upper()}")
                em.add_field(name="Recommended Stats: ", value=f"{res[1]}")
                em.add_field(name="Trace Priority: ", value=f"{res[2]}")
                em.add_field(name="Best LCs: ", value=f"{res[3]}")
                em.add_field(name="Best Relics: ", value=f"{res[4]}")
                em.add_field(name="Best Planar Relics: ", value=f"{res[5]}")
                em.add_field(name="Best Team Synergy: ", value=f"{res[6]}")

                #catch irregularities
                character_image_check = character.upper()

                #Characters with Multiple Paths
                if character_image_check == "HUNT-MARCH":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/march-7th-character-2_action_side_icon.webp?x30775")
                elif character_image_check == "PRESERVATION-MARCH":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/march-7th-character_action_side_icon.webp?x30775")

                elif character_image_check == "DESTRUCTION-TRAILBLAZER":
                    trailblaze_decide = random.randint(1, 2)
                    if trailblaze_decide == 1:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character_action_side_icon.webp?x33576")
                    else:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-2_action_side_icon.webp?x33576")
                elif character_image_check == "PRESERVATION-TRAILBLAZER":
                    trailblaze_decide = random.randint(1, 2)
                    if trailblaze_decide == 1:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-3_action_side_icon.webp?x33576")
                    else:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-4_action_side_icon.webp?x33576")
                elif character_image_check == "HARMONY-TRAILBLAZER":
                    trailblaze_decide = random.randint(1, 2)
                    if trailblaze_decide == 1:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-5_action_side_icon.webp?x33576")
                    else:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-6_action_side_icon.webp?x33576")

                elif character_image_check == "IMBIBITOR-LUNAE":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/dan-heng-imbibitor-lunae-character_action_side_icon.webp?x30775")

                #Easter Eggs    
                elif character_image_check == "HERTA":
                    em.set_image(url=f"https://media1.tenor.com/m/VtFUW-durpoAAAAC/kururin-kuru-kuru.gif")

                #default image
                else:
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/{character.lower()}-character_action_side_icon.webp?x33576")

                em.set_footer(text=f"Wrote by: {res[7].capitalize()}")
                await interaction.response.send_message(embed=em, ephemeral=False)
            except IndexError as e:
                await interaction.response.send_message(f"The character you entered, __**{character}**__ , was not found. Please check the name and try again.", ephemeral=True)
            return

        '''add what to do when error [invalid character], add meat'''
        if game == "CRK":
            character = character.replace(" ", "_")
            em = discord.Embed(title=f"{" ".join(character.split("_")).capitalize()}'s Ideal Build")
            em.set_thumbnail(url=interaction.user.avatar.url)
            em.set_image(url=f"https://www.noff.gg/cookie-run-kingdom/res/img/cookies-standing/{character}.png")
            #em.add_field(name="Your balance is:", value=f"**__{balance}__** :gem:")
            await interaction.response.send_message(embed=em, ephemeral=False)

    #new ways to get gems
    '''@discord.app_commands.checks.cooldown(1, 15)
    @app_commands.command(name="build", description="Check the optimal build for each character!")
    async def build(self, interaction : discord.Interaction, game: Literal['HSR', 'CRK'], character: str=""):
        character = character.lower()
        member = interaction.user'''

    @build.error
    async def OnBuildError(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))
            