import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
from buildcommand import HSRCharacterList

# Database of gifs (links)
hugging_gifs = [
    "https://media1.tenor.com/m/8YhtDI2-uTQAAAAd/topaz-numby.gif",
    "https://media1.tenor.com/m/uiak6BECN_sAAAAC/emunene-emu.gif",
    "https://media1.tenor.com/m/qVWUEYImyKAAAAAC/sad-hug-anime.gif",
    "https://media1.tenor.com/m/UnpQCW40JekAAAAC/anime-hug.gif",
    "https://media1.tenor.com/m/b3Qvt--s_i0AAAAC/hugs.gif"
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
    async def build(self, interaction : discord.Interaction, game: Literal['HSR', 'CRK'], character: str=""):
        character = character.lower()
        member=interaction.user
        if game == 'HSR':

            selected = None
            for c in HSRCharacterList:
                if c.name == character.lower():
                    selected = c
                break
            
            if selected is None:
                await interaction.response.send_message("Invalid character. Please check the name and try again.", ephemeral=True)
                return
            else:
                character = character.replace(" ", "-")

                em = discord.Embed(color=discord.Colour.brand_green(), title=f"{" ".join(character.split("-")).capitalize()}'s Ideal Build")
                em.set_image(url=f"https://starrail.honeyhunterworld.com/img/character/{character}-character_action_side_icon.webp?x34722")
                em.add_field(name="Recommended Stats: ", value=f"{selected.stats}")
                em.add_field(name="Trace Priority: ", value=f"{selected.trapri}")
                em.add_field(name="Best LCs: ", value=f"{selected.bestlc}")
                em.add_field(name="Best Relics: ", value=f"{selected.bestrelics}")
                em.add_field(name="Best Planar Relics: ", value=f"{selected.bestplanar}")
                em.add_field(name="Best Team Synergy: ", value=f"{selected.bestteam}")
                await interaction.response.send_message(embed=em, ephemeral=False)

        '''add what to do when error [invalid character], add meat'''
        if game == 'CRK':
            character = character.replace(" ", "_")
            em = discord.Embed(title=f"{" ".join(character.split("_")).capitalize()}'s Ideal Build")
            em.set_thumbnail(url=interaction.user.avatar.url)
            em.set_image(url=f"https://www.noff.gg/cookie-run-kingdom/res/img/cookies-standing/{character}.png")
            #em.add_field(name="Your balance is:", value=f"**__{balance}__** :gem:")
            await interaction.response.send_message(embed=em, ephemeral=False)

    @build.error
    async def OnBuildError(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error))