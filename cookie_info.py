import csv
import discord
from discord.ext import commands
from discord import app_commands

class CookieInfo(commands.Cog):

	emoji_ids1 = {
		'Rear': '<:Rear:1175532619509809312>',
		'Middle': '<:Middle:1175532618410893383>',
		'Front': '<:Front:1175532616624119948>'
	}
	emoji_ids2 = {
		'Support': '<:Support:1175532593089884270>',
		'Ranged': '<:Ranged:1175532591701557248>',
		'Magic': '<:Magic:1175532589432459324>',
		'Healing': '<:Support:1175532593089884270>',
		'Defense': '<:Defense:1175532587121381436>',
		'Charge': '<:Charge:1175532586253164704>',
		'BTS': '<:BTS:1175532584583835748>',
		'Bomber': '<:Bomber:1175532583526871040>',
		'Ambush': '<:Ambush:1175532580062376067>'
	}

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
		try:
			em = discord.Embed(title=res[0])
			em.set_image(url=row[6])
			em.add_field(name='Pronouns', value=row[2], inline=True)
			em.add_field(name='Type', value=f'{self.emoji_ids2[row[4]]}{row[4]}', inline=True)
			em.add_field(name='Position', value=f'{self.emoji_ids1[row[5]]}{row[5]}', inline=True)
			em.set_footer(text=f'Release Date: {row[3]}')

			await interaction.response.send_message(embed=em)
		except IndexError as e:
			await interaction.response.send_message("Cookie does not exist.")

		
