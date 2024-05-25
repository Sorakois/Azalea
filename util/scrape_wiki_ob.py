import requests
import asyncio
from bs4 import BeautifulSoup

base_url =  "https://cookierun.fandom.com"

#Name, Link, Image, Rarity, Pronouns, 
#Tags, *Combi Pets [image + name], *Combi Treasure [image + name], Release Date

class Cookie:
    def __init__(self, name, link) -> None:
        self.name = name
        self.link = link
	
    def find_info(self):
        r = requests.get(base_url + self.link)
        soup = BeautifulSoup(r.content, "html5lib")
		
        image_div = soup.find("div", attrs = {'class' : 'mw-parser-output'})
        self.image = image_div.aside.figure.a.img["src"]
		
        try:
            rarity_div = soup.find("div", attrs = {'class' : 'wds-tab__content wds-is-current'})
            self.rarity = rarity_div.section.table.tbody.tr.td.a.img["alt"]
        except AttributeError:
            rarity_div = soup.findAll("div", attrs = {'class' : 'wds-tab__content wds-is-current'})[1]
            self.rarity = rarity_div.section.table.tbody.tr.td.a.img["alt"]
			
    
def basic_cookie_scrape():
    r = requests.get(base_url + "/wiki/List_of_Cookies")
    soup = BeautifulSoup(r.content, "html5lib")

    cookies = []

    for table in soup.findAll("table", attrs={"style":"text-align:center; margin:auto;"}):
        tb = table.tbody
        tr = tb.findAll("tr")[::2]
        for i in tr:
            for td in i.findAll("td"):
                link = td.a["href"]
                name = td.a["title"]
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
			await cursor.execute("SELECT ITEM_RARITY, ITEM_NAME, ITEM_IMAGE FROM ITEM_INFO")
			cookies_db = await cursor.fetchall()
			

			# Identify what cookies are new!
			# Check if name is not found first. If name found, check the release date for difference. Otherwise add to list.
			new_cookies = []
			update_cookies = []

			for cookie in cookies:
				releaseChange = False
				found = False
				for row in cookies_db:
					if cookie.name == row[1]:
						found = True
					if found:
						break
					
				if not found:
					new_cookies.append(cookie)
				if releaseChange:
					update_cookies.append(cookie)

			# Register information and add new cookies
			for cookie in new_cookies:
				cookie.find_info()
				await cursor.execute("INSERT INTO ITEM_INFO (ITEM_RARITY, ITEM_NAME, ITEM_IMAGE) VALUES (%s, %s, %s)", (cookie.rarity, cookie.name, cookie.image))
		await conn.commit()

	return new_cookies

async def scrape_cookies(bot):
    cookies = basic_cookie_scrape()
    await indepth_cookie_scrape(cookies=cookies, cookieCSV=1, bot=bot)