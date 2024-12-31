# Use ollama:
# general ver -> https://github.com/ollama/ollama
# python ver -> https://github.com/ollama/ollama-python

# "Train" with something like this:
'''
code
code
code
prompt(f"Write a response to the following in this mindset: {prompt}")
'''

# Ideas:
# Randomly talk in gen chat?
# Be able to join voice chat on command and be able to talk

import discord
from discord import app_commands
from discord.ext import commands
from discord import Colour
import random
from typing import Literal
from buildcommand import HSRCharacter
import logging

class Persona(commands.Cog):
    #wow!
     a = 1