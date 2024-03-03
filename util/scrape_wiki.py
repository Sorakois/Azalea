import requests
from bs4 import BeautifulSoup

###############################################################
# Customizable variables:
#
## csv file relative path name
cookieCSVFile = 'cookies.csv'
# 
###############################################################

base_url = "https://cookierunkingdom.fandom.com"

class Cookie:
	'''
	Cookie object to store all information of each of cookie
	'''

	def __init__(self, name, link):
		'''
		Assign the known names

		params:
			name (str) : name of cookie
			link (str) : url destination to cookie
		'''
		self.name = name
		self.link = link
		self.identify_released()
		self.identify_type()

	def __str__(self):
		'''
		Allows for name to be called when referenced.

		returns:
			self.name (str) : name of cookie
		'''
		return self.name
	
	def to_list(self):
		'''
		Converts Cookie object into list format

		returns:
			cookie_info (list[str]) : list formatted object
		'''
		return [self.name, self.link, self.pronouns, self.release, self.ctype, self.position, self.img_link, self.rarity]
	
	def identify_released(self):
		r = requests.get(base_url + self.link)
		soup = BeautifulSoup(r.content, 'html5lib')

		try:
			releasediv = soup.findAll('div', attrs={'data-source':'releasedate'})
			self.release = releasediv[-1].find('div').getText()
		except (AttributeError, IndexError):
			try:
				releasediv = soup.findAll('div', attrs={'data-source':'release_date'})
				self.release = releasediv[-1].find('div').getText()
			except (AttributeError, IndexError):
				self.release = 'Unreleased/TBA'

	def identify_type(self):
		r = requests.get(base_url + self.link)
		soup = BeautifulSoup(r.content, 'html5lib')

		try:
			typediv = soup.find('td', attrs={'data-source':'role'})
			self.ctype = typediv.findAll('a')[1].getText()
		except IndexError:
			self.ctype = 'Unknown'

	def find_info(self):
		'''
		Search through cookie's link to scrape the information.
		Sets: image link, gender, release date, type, position
		'''
		
		r = requests.get(base_url + self.link)
		soup = BeautifulSoup(r.content, 'html5lib')

		self.img_link = soup.find('img', attrs={'class':'pi-image-thumbnail'})['src']

		pronoundiv = soup.find('div', attrs={'data-source':'pronouns'})
		self.pronouns = pronoundiv.findAll('a')[1].getText()

		try:
			posdiv = soup.find('td', attrs={'data-source':'position'})
			self.position = posdiv.findAll('a')[1].getText()
		except IndexError:
			self.position = 'Unknown'

		self.rarity = soup.find('div', attrs={'data-source':'rarity'}).div.a.img['alt']
		if self.rarity[:2] == 'Ep':
			self.rarity = 'Epic'


def basic_cookie_scrape():
	'''
	Function to scrape the cookies information.

	returns:
		cookies (list[Cookie]) : a list of Cookie objects
	'''
	r = requests.get(base_url + "/wiki/List_of_Cookies")

	soup = BeautifulSoup(r.content, 'html5lib')
	cookies = []

	for div in soup.findAll("div", attrs = {'class' : 'scrolly scrollyflex'}):
		div = div.div
		for div2 in div.findAll("div", attrs= {'style' : 'background-color:var(--theme-table-content-2); padding:0; margin:10px; overflow:hidden; width:165px; display:inline-flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid var(--theme-dark-accent); box-shadow:3px 3px var(--theme-table-outline),-3px 3px var(--theme-table-outline),-3px -3px var(--theme-table-outline),3px -3px var(--theme-table-outline); border-radius:3px;'}):
			name = div2.div.a['title']
			link = div2.div.a['href']
			c = Cookie(name, link)
			cookies.append(c)
	
	return cookies


async def indepth_cookie_scrape(cookies: list[Cookie], cookieCSV, bot):
	'''
	Deep dives each cookie info if information is not known yet

	params:
		cookies (list[Cookie]): list of basic Cookie objects
		cookieCSV (str): csv file of known cookie info

	returns:
		cookies (list[Cookie]): list of all required updated cookies
	'''
	# Open the data
	async with bot.db.acquire() as conn:
		async with conn.cursor() as cursor:
			await cursor.execute("SELECT Name, Link, Released, Type FROM cookie_info")
			cookies_db = await cursor.fetchall()
			

			# Identify what cookies are new!
			# Check if name is not found first. If name found, check the release date for difference. Otherwise add to list.
			new_cookies = []
			update_cookies = []

			for cookie in cookies:
				releaseChange = False
				found = False
				for row in cookies_db:
					if cookie.name == row[0] or cookie.link == row[1]:
						found = True
					if found and cookie.release != row[3]:
						releaseChange = True
					if found:
						break
					
				if not found:
					new_cookies.append(cookie)
				if releaseChange:
					update_cookies.append(cookie)

			# Register information and add new cookies
			for cookie in new_cookies:
				cookie.find_info()
				await cursor.execute("INSERT INTO cookie_info (Name,Link,Gender,Released,Type,Position,Picture,Rarity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", tuple(cookie.to_list()))
			for cookie in update_cookies:
				await cursor.execute("UPDATE cookie_info SET Released = %s, Type = %s WHERE Name = %s AND Link = %s", (cookie.release, cookie.ctype, cookie.name, cookie.link))
		await conn.commit()

	return new_cookies
		
async def scrape_cookies(bot):
	cookies = basic_cookie_scrape()

	cookies_to_update = await indepth_cookie_scrape(cookies=cookies, cookieCSV=cookieCSVFile, bot=bot)
	return cookies_to_update
