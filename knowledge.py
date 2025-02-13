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
    
    # meta command keeps users up to date with the best current strategies
    @app_commands.command(name="meta", description="Check the current HSR/CRK Metas!")
    async def featured(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom']):
        member = interaction.user
        await interaction.response.defer()

        valid_options = {
            "Honkai: Star Rail": ['Memory of Chaos', 'Pure Fiction', 'Apocalyptic Shadow', 'General Tier List'],
            "Cookie Run Kingdom": ['Arena', 'Guild Boss', 'Alliance', 'Limited Time Mode', 'Story', 'Bounties', '...']
        }

        if game in valid_options:
            await interaction.followup.send("Which would you like to learn more about?:\n")
            options = valid_options[game]
            formatted_options = '\n'.join(f"{index + 1}. {option}" for index, option in enumerate(options))
            await valid_options.followup.send(formatted_options)

            def check(message: discord.Message):
                    return message.author.id == member.id and message.channel.id == interaction.channel.id
            msg = await interaction.client.wait_for('message', check=check, timeout=90.0)
            learn_more = msg.content

            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT LINK1, LINK2, LINK3 FROM META WHERE GAME = %s and MODE = %s", (game,))
                    links = await cursor.fetchall()
        else:
            await interaction.followup.send("Invalid input! Try again.\n")
