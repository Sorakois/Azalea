import requests
from bs4 import BeautifulSoup

base_url =  "https://cookierun.fandom.com"

#Name, Link, Image, Rarity, Pronouns, 
#Tags, *Combi Pets [image + name], *Combi Treasure [image + name], Release Date

class Cookie:
    def __init__(self, name, link) -> None:
        self.name = name
        self.link = link
	
    def find_info(self):
        pass
    
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
			await cursor.execute("SELECT C_NAME, C_LINK, C_IMAGE, C_RELEASE FROM cookie_info_ob")
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
				await cursor.execute("INSERT INTO cookie_info_ob (C_NAME, C_LINK, C_IMAGE, C_RARITY, C_PRONOUNS, COMBI_PETS1, COMBI_PETS2, COMBI_TRES1, COMBI_TRES2, C_RELEASE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", tuple(cookie.to_list()))
			for cookie in update_cookies:
				await cursor.execute("UPDATE cookie_info_ob SET C_RELEASE = %s WHERE C_NAME = %s AND C_LINK = %s", (cookie.release, cookie.name, cookie.link))
		await conn.commit()

	return new_cookies

def scrape_cookies(bot):
    cookies = basic_cookie_scrape()
    print (len(cookies))

scrape_cookies(5)