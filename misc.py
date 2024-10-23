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

            #symbols
            if character.upper() == "DR. RATIO" or character.upper() == "RATIO" or character.upper() == "DOCTOR RATIO":
                character = "dr ratio"
            #characters with abreviations or other names
            if character.upper() == "DHIL" or character.upper() == "DAN HENG IMBIBITOR LUNAE":
                character = "imbibitor lunae"
            if character.upper() == "FEI XIAO":
                character = "feixiao"
            if character.upper() == "TINGYUN":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Harmony Tingyun', 'Nihility Tingyun', or 'Fugue'", ephemeral=True)
                return
            if character.upper() == "FUGUE"or character.upper() == "FUGUE TINGYUN":
                character = "nihility tingyun"
            if character.upper() == "TOPAZ" or character.upper() == "TOPAZ & NUMBY" or character.upper() == "TOPAZ AND NUMBY" or character.upper() == "TOPASS":
                character = "topaz numby"
            if character.upper() == "SILVERWOLF" or character.upper() == "SW" or character.upper() == "WOLFIE" or character.upper() == "SWOLF" or character.upper() == "SILVER":
                character = "silver wolf"
            #pure abreviations
            if character.upper() == "FF" or character.upper() == "SAM":
                character = "firefly"
            if character.upper() == "DTB":
                character = "destruction trailblazer"
            if character.upper() == "PTB":
                character = "preservation trailblazer"
            if character.upper() == "BS":
                character = "black swan"
            if character.upper() == "AVEN":
                character = "aventurine"
            if character.upper() == "BLADIE":
                character = "blade"
            if character.upper() == "GEPPIE":
                character = "gepard"
            if character.upper() == "GAMBLE" or character.upper() == "MAHJONG" or character.upper() == "CASINO":
                character = "qingque"
            if character.upper() == "RM":
                character = "ruan mei"
            if character.upper() == "MONDAY" or character.upper() == "SATURDAY":
                character = "sunday"
            #characters with multiple "branches"
            if character.upper() == "MARCH":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Hunt March' or 'Preservation March", ephemeral=True)
                return
            if character.upper () == "MARCH 8TH" or character.upper () == "MARCH 8" or character.upper() == "MARCH HUNT" or character.upper() == "3/8":
                character = "hunt march"
            if character.upper() == "MARCH 7TH" or character.upper () == "MARCH 7" or character.upper() == "3/7":
                character = "preservation march"

            if character.upper() == "TRAILBLAZER" or character.upper() == "TB" or character.upper() == "MC" or character.upper() == "CAELUS" or character.upper() == "STELLE" or character.upper() == "RACCOON" or character.upper() == "TRASH" or character.upper() == "TRASHBLAZER":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Destruction Trailblazer', 'Preservation Trailblazer' or 'Harmony Trailblazer.", ephemeral=True)
                return
            if character.upper() == "HTB" or character.upper() == "HARMONY MC" or character.upper() == "HMC" or character.upper() == "HARMONY TB" or character.upper() == "TRAILBLAZER HARMONY" or character.upper() == "HATBLAZER" or character.upper() == "HARMBLAZER":
                character = "harmony trailblazer"
            if character.upper () == "Preservation MC" or character.upper() == "FIREBLAZER" or character.upper() == "FMC"  or character.upper() == "FTB" or character.upper() == "FIRE MC" or character.upper() == "FIRE TB" or character.upper() == "TRAILBLAZER PRESERVATION":
                character = "preservation trailblazer"
            if character.upper() == "Destruction MC" or character.upper() == "DESTRUCTION TB" or character.upper() == "PHYSICAL TRAILBLAZER" or character.upper() == "TRAILBLAZER DESTRUCTION" or character.upper() == "PHYS MC" or character.upper() == "PHYS TB" or character.upper() == "DMC" or  character.upper() == "DTB":
                character = "destruction trailblazer"

            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT * FROM HSR_BUILD")
                    HSRBuildInfo = await cursor.fetchall()

            res = ''
            for row in HSRBuildInfo:
                temp = row[0]
                if character == temp:
                    res = row
                    break
            try:
                #add a hyphen so that URL works

                #embed for build
                if character.upper() == "TOPAZ-NUMBY":
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"__Ideal Build of:__ Topaz")
                else:
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"__Ideal Build of:__ {character}")

                #grab server pfp and set up base of embed
                em.set_thumbnail(url=interaction.user.guild.icon.url)
                em.add_field(name="Recommended Stats: ", value=f"{res[1]}", inline=True)
                em.add_field(name="Trace Priority: ", value=f"{res[2]}", inline=False)
                em.add_field(name="Best LCs: ", value=f"{res[3]}", inline=True)
                em.add_field(name="Best Relics: ", value=f"{res[4]}", inline=False)
                em.add_field(name="Best Planar Relics: ", value=f"{res[5]}", inline=True)
                em.add_field(name="Best Team Synergy: ", value=f"{res[6]}", inline=False)

                #catch irregularities
                character_image_check = character.upper()
                character = character.replace(" ", "-")

                #Characters with Multiple Paths
                if character_image_check == "HUNT-MARCH":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/march-7th-character-2_scpecial_action_icon.webp?x30775")
                elif character_image_check == "PRESERVATION-MARCH":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/march-7th-character_scpecial_action_icon.webp?x30775")

                elif character_image_check == "DESTRUCTION-TRAILBLAZER":
                    trailblaze_decide = random.randint(1, 2)
                    if trailblaze_decide == 1:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character_gacha_result_bg.webp?x30775")
                    else:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-2_gacha_result_bg.webp?x30775")
                elif character_image_check == "PRESERVATION-TRAILBLAZER":
                    trailblaze_decide = random.randint(1, 2)
                    if trailblaze_decide == 1:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-3_gacha_result_bg.webp?x30775")
                    else:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-4_gacha_result_bg.webp?x30775")
                elif character_image_check == "HARMONY-TRAILBLAZER":
                    trailblaze_decide = random.randint(1, 2)
                    if trailblaze_decide == 1:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-5_shop_icon.webp?x30775")
                    else:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-6_shop_icon.webp?x30775")

                elif character_image_check == "IMBIBITOR-LUNAE":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/dan-heng-imbibitor-lunae-character_gacha_result_bg.webp?x30775")

                elif character_image_check == "SUNDAY":
                    em.set_image(url=f"https://static.wikia.nocookie.net/houkai-star-rail/images/2/21/Character_Sunday_Splash_Art.png")
                elif character_image_check == "NIHILITY-TINGYUN":
                    em.set_image(url=f"https://static.wikia.nocookie.net/houkai-star-rail/images/4/4c/Character_Fugue_Splash_Art.png")
                elif character_image_check == "HARMONY-TINGYUN":
                    em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/tingyun-character_gacha_result_bg.webp?x33576")

                #Easter Eggs    
                #elif character_image_check == "HERTA":
                #    em.set_image(url=f"https://media1.tenor.com/m/VtFUW-durpoAAAAC/kururin-kuru-kuru.gif")

                #default image
                else:
                    try:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/{character.lower()}-character_gacha_result_bg.webp?x30775")
                    except ValueError as e:
                        await interaction.response.send_message(f"'{character}'s image is messed up :(... PLEASE let @sorakoi know ASAP [<@836367313502208040>]", ephemeral=False)
                        return


                em.set_footer(text=f"Wrote by: {res[7].capitalize()}... in discord.gg/nurture")
                await interaction.response.send_message(embed=em, ephemeral=False)
            except IndexError as e:
                await interaction.response.send_message(f"The character you entered, __**{character}**__ , was not found. Please check the name and try again.", ephemeral=True)
            return

        if game == "CRK":
            '''character = character.replace(" ", "_")
            em = discord.Embed(title=f"{" ".join(character.split("_")).capitalize()}'s Ideal Build")
            em.set_thumbnail(url=interaction.user.avatar.url)
            em.set_image(url=f"https://www.noff.gg/cookie-run-kingdom/res/img/cookies-standing/{character}.png")
            #em.add_field(name="Your balance is:", value=f"**__{balance}__** :gem:")
            await interaction.response.send_message(embed=em, ephemeral=False)'''
            await interaction.response.send_message(f"'Feature still in development! Try again later!", ephemeral=True)

            

    #new ways to get gems
    '''@discord.app_commands.checks.cooldown(1, 60)
    @app_commands.command(name="build", description="Check the optimal build for each character!")
    async def build(self, interaction : discord.Interaction):
        member = interaction.user'''
    
    '''
    Make user do an action repeatedly... maybe use modulus 5 -> gems?
    '''

    @build.error
    async def OnBuildError(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))
            