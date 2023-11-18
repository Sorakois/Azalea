import csv
import discord
from discord.ext import commands
from discord import app_commands

class CookieInfo(commands.Cog):

	def __init__(self, bot : commands.Bot):
		self.bot = bot

	@app_commands.command(name="wiki" , description="Search wiki for a cookie")
	async def cookie_wiki(self, interaction: discord.Interaction, query: str):

		if query.upper().find('COOKIE') != -1:
			query = query[:-7]

		f = open('util/cookies.csv')
		csvReader = list(csv.reader(f, delimiter=','))

		res = ''

		for row in csvReader:
			temp = row[0]
			if row[0].upper().find('COOKIE') != -1:
				if row[0] == 'Custard Cookie III':
					temp = 'Custard'
				else:
					temp = temp[:-7]
			if query.capitalize() == temp.capitalize():
				res = row
				break

		await interaction.response.send_message(f'Hello {res}')
