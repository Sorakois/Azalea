import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
import logging

def cleanse_name(character:str):
    #format query
    character = character.upper()
    character = character.strip()
    character = character.replace('-', ' ')

    #fix weird characters
    if character == "DR. RATIO" or character == "RATIO" or character == "DOCTOR RATIO":
        character = "dr ratio"
    #characters with abreviations or other names
    if character == "DHIL" or character == "DAN HENG IMBIBITOR LUNAE":
        character = "imbibitor lunae"
        
    if character == "FEI XIAO":
        character = "feixiao"
    if character == "FUGUE"or character == "FUGUE TINGYUN":
        character = "nihility tingyun"
    if character == "TOPAZ" or character == "TOPAZ & NUMBY" or character == "TOPAZ AND NUMBY" or character == "TOPASS":
        character = "topaz numby"
    if character == "SILVERWOLF" or character == "SW" or character == "WOLFIE" or character == "SWOLF" or character == "SILVER":
        character = "silver wolf"

    #pure abreviations
    if character == "FF" or character == "SAM":
        character = "firefly"
    if character == "DTB":
        character = "destruction trailblazer"
    if character == "PTB":
        character = "preservation trailblazer"
    if character == "BS":
        character = "black swan"
    if character == "AVEN":
        character = "aventurine"
    if character == "BLADIE":
        character = "blade"
    if character == "GEPPIE":
        character = "gepard"
    if character == "GAMBLE" or character == "MAHJONG" or character == "CASINO":
        character = "qingque"
    if character == "RM":
        character = "ruan mei"
    if character == "MONDAY" or character == "SATURDAY":
        character = "sunday"
    if character == "MARCH 8TH" or character == "MARCH 8" or character == "MARCH HUNT" or character == "3/8":
        character = "hunt march"
    if character == "MARCH 7TH" or character == "MARCH 7" or character == "3/7":
        character = "preservation march"
    if character == "HTB" or character == "HARMONY MC" or character == "HMC" or character == "HTB" or character == "HARMONY TB" or character == "TRAILBLAZER HARMONY" or character == "HATBLAZER" or character == "HARMBLAZER":
        character = "harmony trailblazer"
    if character == "Preservation MC" or character == "FIREBLAZER" or character == "FMC"  or character == "FTB" or character == "FIRE MC" or character == "FIRE TB" or character== "TRAILBLAZER PRESERVATION":
        character = "preservation trailblazer"
    if character == "Destruction MC" or character == "DESTRUCTION TB" or character == "PHYSICAL TRAILBLAZER" or character == "TRAILBLAZER DESTRUCTION" or character == "PHYS MC" or character == "PHYS TB" or character == "DMC" or  character == "DTB":
        character = "destruction trailblazer"

    return character.lower()

def fix_rarity(rarity):
    if rarity == "Feat_Four" or rarity == "Stand_Four":
        rarity = "★★★★"
    if rarity == "Feat_Five" or rarity == "Stand_Five":
        rarity = "★★★★★"

    return rarity

def chrono_image(chrono: int):
    chrono_img_ids = ["<a:Promo_0:1308482940669263994>", #0
                      "<a:Promo_1_5:1308482953407631462>", #1
                      "<a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #2
                      "<a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #3
                      "<a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #4
                      "<a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #5
                      "<a:Promo_6_10:1308482961888509972><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #6
                      "<a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #7
                      "<a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_1_5:1308482953407631462><a:Promo_1_5:1308482953407631462>", #8
                      "<a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_1_5:1308482953407631462>", #9
                      "<a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972><a:Promo_6_10:1308482961888509972>", #10
                    ]
    if chrono > 10:
        return
    return chrono_img_ids[chrono]

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
        original_input = character

        #fix if mix up with viewcharacter command inputs
        character = character.lower() 
        character = character.replace('caelus', 'trailblazer').replace('stelle', 'trailblazer')

        if game == "HSR":

            #characters with multiple "branches"
            if character.upper() == "TINGYUN":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Harmony Tingyun', 'Nihility Tingyun', or 'Fugue'", ephemeral=True)
                return 
            if character.upper() == "MARCH":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Hunt March' or 'Preservation March", ephemeral=True)
                return
            if character.upper() == "TRAILBLAZER" or character.upper() == "TB" or character.upper() == "MC" or character.upper() == "CAELUS" or character.upper() == "STELLE" or character.upper() == "RACCOON" or character.upper() == "TRASH" or character.upper() == "TRASHBLAZER":
                await interaction.response.send_message(f"'{character}' is invalid. Please specify the path of this character: 'Destruction Trailblazer', 'Preservation Trailblazer' or 'Harmony Trailblazer.", ephemeral=True)
                return

            #fix name inputs
            character.lower()
            character = cleanse_name(character)

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
                if character.upper() == "TOPAZ NUMBY":
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"__Ideal Build of:__ Topaz")
                else:
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"__Ideal Build of:__ {character.title()}")
                

                #grab server pfp and set up base of embed
                em.set_thumbnail(url=interaction.user.guild.icon.url)
                em.add_field(name="Recommended Stats: ", value=f"{res[1]}", inline=True)
                em.add_field(name="Trace Priority: ", value=f"{res[2]}", inline=False)
                em.add_field(name="Best LCs: ", value=f"{res[3]}", inline=True)
                em.add_field(name="Best Relics: ", value=f"{res[4]}", inline=False)
                em.add_field(name="Best Planar Relics: ", value=f"{res[5]}", inline=True)
                em.add_field(name="Best Team Synergy: ", value=f"{res[6]}", inline=False)

                #catch irregularities
                character = character.strip()
                character = character.replace(" ", "-")
                try:
                    #Characters with Multiple Paths
                    if character.upper() == "HUNT-MARCH":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/march-7th-character-2_scpecial_action_icon.webp?x30775")
                    elif character == "PRESERVATION-MARCH":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/march-7th-character_scpecial_action_icon.webp?x30775")

                    elif character.upper() == "DESTRUCTION-TRAILBLAZER":
                        trailblaze_decide = random.randint(1, 2)
                        if trailblaze_decide == 1:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character_gacha_result_bg.webp?x30775")
                        else:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-2_gacha_result_bg.webp?x30775")
                    elif character.upper() == "PRESERVATION-TRAILBLAZER":
                        trailblaze_decide = random.randint(1, 2)
                        if trailblaze_decide == 1:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-3_gacha_result_bg.webp?x30775")
                        else:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-4_gacha_result_bg.webp?x30775")
                    elif character.upper() == "HARMONY-TRAILBLAZER":
                        trailblaze_decide = random.randint(1, 2)
                        if trailblaze_decide == 1:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-5_shop_icon.webp?x30775")
                        else:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-6_shop_icon.webp?x30775")

                    elif character.upper() == "IMBIBITOR-LUNAE":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/dan-heng-imbibitor-lunae-character_gacha_result_bg.webp?x30775")
                    elif character.upper() == "THE-HERTA":
                        em.set_image(url=f"https://i.imgur.com/31AYOa2.png")

                    elif character.upper() == "NIHILITY-TINGYUN":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/fugue-character_gacha_result_bg.webp?x58483")
                    elif character.upper() == "HARMONY-TINGYUN":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/tingyun-character_gacha_result_bg.webp?x33576")
                except:
                    await interaction.response.send_message(f"The character you entered, __**{original_input}**__ , was not found. Please check the name and try again.", ephemeral=True)


                #Easter Eggs    
                #elif character == "HERTA":
                #    em.set_image(url=f"https://media1.tenor.com/m/VtFUW-durpoAAAAC/kururin-kuru-kuru.gif")

                #default image
                    try:
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/{character.lower()}-character_gacha_result_bg.webp?x30775")
                        #await interaction.response.send_message(f"{character}", ephemeral=False)

                    except ValueError as e:
                        await interaction.response.send_message(f"'{character}'s image is messed up :(... PLEASE let @sorakoi know ASAP [<@836367313502208040>]", ephemeral=False)
                        return


                em.set_footer(text=f"Wrote by: {res[7].capitalize()}... in discord.gg/nurture")
                await interaction.response.send_message(embed=em, ephemeral=False)
            except IndexError as e:
                await interaction.response.send_message(f"The character you entered, __**{original_input}**__, was not found. Please check the name and try again.", ephemeral=True)
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
            