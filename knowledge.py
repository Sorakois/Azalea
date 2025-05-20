# imports
import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
import logging

# class Smart(commands.Cog):
    
#     # meta command keeps users up to date with the best current strategies
#     @app_commands.command(name="meta", description="Check the current HSR/CRK Metas!")
#     async def featured(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom']):
#         member = interaction.user
#         await interaction.response.defer()

#         # list containing all games as keys and valid meta information user can look up
#         valid_options = {
#             "Honkai: Star Rail": ['Memory of Chaos', 'Pure Fiction', 'Apocalyptic Shadow', 'General Tier List'],
#             "Cookie Run Kingdom": ['Arena', 'Guild Boss', 'Alliance', 'Limited Time Mode', 'Story', 'Bounties', '...']
#         }
#         # dictionary for sub options for a mode (ex. guild boss -> LA, RVD, AOD)
#         sub_options = {
#             "Guild Boss" : ["RVD", "AOD", "LA"]
#         }

#         if game in valid_options:
#             #use a while loop to keep looking for a valid user input
#             get_mode = True
#             while(get_mode):
#                 # output options given the choice user makes
#                 await interaction.followup.send("Which would you like to learn more about?:\n",ephemeral=True)
#                 options = valid_options[game]
#                 formatted_options = '\n'.join(f"{index + 1}. {option}" for index, option in enumerate(options))
#                 await interaction.followup.send(formatted_options,ephemeral=True)

#                 # grab user response
#                 def check(message: discord.Message):
#                         return message.author.id == member.id and message.channel.id == interaction.channel.id

#                 # only keep going if user input is valid
#                 try:
#                     msg = await interaction.client.wait_for('message', check=check, timeout=90.0)
#                     learn_more = int(msg.content)

#                     #check if valid input
#                     if 1<= learn_more <= len(options):
#                         mode_look = valid_options[game][learn_more-1]
#                         get_mode = False

#                         # check for sub-options
#                         if mode_look in sub_options:
#                             get_mode = True
#                             while(get_mode):
#                                 await interaction.followup.send("Please specify:\n",ephemeral=True)
#                                 sub_options_list = sub_options[mode_look]
#                                 formatted_sub_options = '\n'.join(f"{index + 1}. {option}" for index, option in enumerate(sub_options_list))
#                                 await interaction.followup.send(formatted_sub_options, ephemeral=True)

#                                 # grab user response
#                                 def check(message: discord.Message):
#                                         return message.author.id == member.id and message.channel.id == interaction.channel.id
#                                 try:
#                                     msg = await interaction.client.wait_for('message', check=check, timeout=90.0)
#                                     sub_choice = int(msg.content)

#                                     if 1 <= sub_choice <= len(sub_options_list):
#                                         mode_look = sub_options_list[sub_choice - 1]
#                                         get_mode = False
#                                     else:
#                                         await interaction.followup.send("Invalid input! Try again.",ephemeral=True)
#                                 except:
#                                     await interaction.followup.send("Invalid input! Try again.",ephemeral=True)
#                     else:
#                         await interaction.followup.send("Invalid input! Try again.",ephemeral=True)
#                 except:
#                     await interaction.followup.send("Error! Invalid input. Try again.",ephemeral=True)
                    
#             await interaction.followup.send(f"YOU CHOSE: {mode_look}",ephemeral=True)
#             # get corresponding info from DB
#             async with self.bot.db.acquire() as conn:
#                 async with conn.cursor() as cursor:
#                     await cursor.execute("SELECT LINK1, LINK2, LINK3 FROM META WHERE GAME = %s and MODE = %s", (game,))
#                     links = await cursor.fetchall()
#                     try:
#                         em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=valid_options[game][learn_more-1])
#                         em.set_thumbnail(url=interaction.user.guild.icon.url)

#                         # gifs that will randomly be chosen to be sent alongside the meta info
#                         game_gifs = {
#                             "Honkai: Star Rail" : [
#                                 "https://media.tenor.com/AM2qQ1ErSesAAAAj/pom-pom-pom-pom-honkai-star-rail.gif",
#                                 "https://media.tenor.com/3oOJfWP8Rf0AAAAj/bronya-hsr.gif"],
#                             "Cookie Run Kingdom" : [
#                                 "https://media1.tenor.com/m/Pn1VrqlAC6oAAAAd/cookierun-milky-way-cookie.gif",
#                                 "https://media1.tenor.com/m/6O2uFeYTDOMAAAAd/cookierun-milky-way-cookie.gif"],
#                         }

#                         # randomly assign corresponding image
#                         gifs_length = len(game_gifs[game])
#                         r = random.randrange(0,gifs_length)
#                         embed_img = game_gifs[game][r]
#                         em.set_image(url=embed_img)
#                         # only send source if it exists in the database
#                         if links[0] is not None:
#                             em.add_field(name="First Source: ", value=links[0], inline=True)
#                         if links[1] is not None:
#                             em.add_field(name="Second Source: ", value=links[0], inline=True)
#                         if links [2] is not None: 
#                             em.add_field(name="Third Source: ", value=links[0], inline=True)
#                         em.set_footer(text="Brought to you by... discord.gg/nurture")
#                     except:
#                             await interaction.followup.send("Error with embed! Here are the links instead:\n")
#             await interaction.response.send_message(embed=em)
#         else:
#             await interaction.followup.send("Invalid input! Try again.\n")
