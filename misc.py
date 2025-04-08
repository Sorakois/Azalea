import re
import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
import json
#from buildcommand import HSRCharacter
import logging

import requests

def cleanse_name(character:str):
    #format query
    character = character.upper()
    character = character.strip()
    character = character.replace('-', ' ')

    #quick CRK fix
    if character.upper == "CUSTARD COOKIE III":
        character = "Custard Cookie III"
    #fix weird characters
    if character == "DR. RATIO" or character == "RATIO" or character == "DOCTOR RATIO":
        character = "dr ratio"
    #characters with abreviations or other names
    if character == "DHIL" or character == "DAN HENG IMBIBITOR LUNAE":
        character = "imbibitor lunae"
    if character == "BHILL":
        character = "boothill"
    if character == "FEI XIAO":
        character = "feixiao"
    if character == "FUGUE"or character == "FUGUE TINGYUN":
        character = "nihility tingyun"
    if character == "TOPAZ" or character == "TOPAZ & NUMBY" or character == "TOPAZ AND NUMBY" or character == "TOPASS":
        character = "topaz numby"
    if character == "SILVERWOLF" or character == "SW" or character == "WOLFIE" or character == "SWOLF" or character == "SILVER":
        character = "silver wolf"
    if character == "THERTA" or  character == "Madam Herta":
        character = "the herta"

    #pure abreviations
    if character == "FF" or character == "SAM":
        character = "firefly"
    if character == "DTB":
        character = "destruction trailblazer"
    if character == "PTB":
        character = "preservation trailblazer"
    if character == "RTB":
        character = "remembrance trailblazer"
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
    if character == "PRESERVATION MC" or character == "FIREBLAZER" or character == "FMC"  or character == "FTB" or character == "FIRE MC" or character == "FIRE TB" or character== "TRAILBLAZER PRESERVATION":
        character = "preservation trailblazer"
    if character == "DESTRUCTION MC" or character == "DESTRUCTION TB" or character == "PHYSICAL TRAILBLAZER" or character == "TRAILBLAZER DESTRUCTION" or character == "PHYS MC" or character == "PHYS TB" or character == "DMC" or  character == "DTB":
        character = "destruction trailblazer"
    if character == "REMEMBRANCE MC" or character == "REMEMBRANCE TB" or character == "REMEMBRANCE TRAILBLAZER" or character == "TRAILBLAZER REMEMBRANCE" or character == "REMEM MC" or character == "REMEM TB" or character == "RMC" or  character == "RTB":
        character = "remembrance trailblazer"

    return character.lower()

def fix_rarity(rarity):
    if rarity == "Feat_Four" or rarity == "Stand_Four":
        rarity = "★★★★"
    if rarity == "Feat_Five" or rarity == "Stand_Five":
        rarity = "★★★★★"

    if rarity == "Feat_Epic":
        rarity = "Epic"
    if rarity == "Feat_Leg":
        rarity = "Legendary"

    return rarity

def chrono_image(chrono: int):
    chrono_img_ids = [" ", #0
                      ":star:", #1
                      ":star::star:", #2
                      ":star::star::star:", #3
                      ":star::star::star::star:", #4
                      ":star::star::star::star::star:", #5
                      ":star2:", #6
                      ":star2::star2:", #7
                      ":star2::star2::star2:", #8
                      ":star2::star2::star2::star2:", #9
                      ":star2::star2::star2::star2::star2:", #10
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

    
    '''
    Hug Command:
        Just randomly sends a hug gif from above. No need for a database for them... yet.
    '''
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

    '''
    BUILD COMMAND!
        Allow users to see how to build characters (best equipment) in:
            - Honkai Star Rail
            - Cookie Run Kingdom (in development)
            - Zenless Zone Zero (in development)
            - Genshin Impact (in development)
            - Wuthering Waves (in development)
    '''
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
                    await cursor.execute("SELECT stats, trapri, bestlc, bestrelics, bestplanar, gear_mainstats, buildauthor FROM HSR_BUILD WHERE name LIKE %s", f"%{character.lower()}%")
                    HSRBuildInfo = await cursor.fetchone()
                    if HSRBuildInfo:
                        HSRBuildInfo = list(HSRBuildInfo)
                        
                        # Replace None or empty strings with "N/A"
                    for i in range(len(HSRBuildInfo)):
                        if HSRBuildInfo[i] is None or HSRBuildInfo[i] == "":
                            HSRBuildInfo[i] = "N/A"
                        else:
                            if i != 0:
                                HSRBuildInfo[i] = HSRBuildInfo[i].replace("(", "").replace(")", "\n").replace("'", "").replace(",","")
                            else:
                                HSRBuildInfo[i] = re.sub(r'(?<!\d\.)\(|\)', '', HSRBuildInfo[i]) \
                                .replace("'", "").replace(",", "").replace(")", "\n").replace("~~","==").replace("==", " or")

            # res = ''
            # for row in HSRBuildInfo:
            #     temp = row[0]
            #     if character == temp:
            #         res = row
            #         break

            try:
                #add a hyphen so that URL works
                #embed for build
                if character.upper() == "TOPAZ NUMBY":
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"__Ideal Build of:__ Topaz")
                else:
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"__Ideal Build of:__ {character.title()}")
                

                #grab server pfp and set up base of embed
                em.set_thumbnail(url=interaction.user.guild.icon.url)
                em.add_field(name="Recommended Stats: ", value=f"{HSRBuildInfo[0]}", inline=True)
                em.add_field(name="Trace Priority: ", value=f"{HSRBuildInfo[1]}", inline=False)
                em.add_field(name="Best LCs: ", value=f"{HSRBuildInfo[2]}", inline=True)
                em.add_field(name="Best Relics: ", value=f"{HSRBuildInfo[3]}", inline=False)
                em.add_field(name="Best Planar Relics: ", value=f"{HSRBuildInfo[4]}", inline=True)
                em.add_field(name="Best Gear Mainstats: ", value=f"{HSRBuildInfo[5]}", inline=False)

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
                    elif character.upper() == "REMEMBRANCE-TRAILBLAZER":
                        trailblaze_decide = random.randint(1, 2)
                        if trailblaze_decide == 1:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-7_gacha_result_bg.webp")
                        else:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/trailblazer-character-8_gacha_result_bg.webp")


                    elif character.upper() == "IMBIBITOR-LUNAE":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/dan-heng-imbibitor-lunae-character_gacha_result_bg.webp?x30775")
                    elif character.upper() == "THE-HERTA":
                        em.set_image(url=f"https://i.imgur.com/31AYOa2.png")

                    elif character.upper() == "NIHILITY-TINGYUN":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/fugue-character_gacha_result_bg.webp?x58483")
                    elif character.upper() == "HARMONY-TINGYUN":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/tingyun-character_gacha_result_bg.webp?x33576")
                    
                    #temp until available on the site
                    elif character.upper() == "AGLAEA":
                        em.set_image(url=f"https://i.imgur.com/dNiSmlm.png")
                    elif character.upper() == "CASTORICE":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/castorice-character_cut_in_front.webp")
                    elif character.upper() == "ANAXA":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/anaxa-character_cut_in_front.webp")
                    elif character.upper() == "CIPHER":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/cipher-character_gacha_result_bg.webp")
                    elif character.upper() == "HYACINE":
                        em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/hyacine-character_gacha_result_bg.webp")
                    else:   #default images
                        try:
                            em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/{character.lower()}-character_gacha_result_bg.webp?x30775")
                            #await interaction.response.send_message(f"{character}", ephemeral=False)

                        except ValueError as e:
                            await interaction.response.send_message(f"'{character}'s image is messed up :(... PLEASE let @sorakoi know ASAP [<@836367313502208040>]", ephemeral=False)
                            return

                except:
                    await interaction.response.send_message(f"The character you entered, __**{original_input}**__ , was not found. Please check the name and try again.", ephemeral=True)



                em.set_footer(text=f"Created by: {HSRBuildInfo[6].capitalize()} in discord.gg/nurture")
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

    @build.error
    async def OnBuildError(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))
            
    '''
    Fun fact command!
        Do the command, get a fun fact. That's it!
    '''
    @app_commands.command(name="funfact", description="View a random fact!")
    async def hug(self, interaction: discord.Interaction):
        member = interaction.user
        try:
            # Websites for API 
            #   --> https://thefact.space/random
            #   --> https://uselessfacts.jsph.pl/api/v2/facts/random
            
            fun_facts = requests.get("https://thefact.space/random", timeout=10)
                
            json_data = json.loads(fun_facts.text)
            fun_fact = json_data['text']
            source = json_data['source']
            
            await interaction.response.send_message(f"## Fun Fact!\n\n{fun_fact}\n-# Source: <{source}>")
            
        except Exception as e:
            # Handle potential errors
            await interaction.response.send_message(f"Oops! Something went wrong.\n{e}", ephemeral=True)