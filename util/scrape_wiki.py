import requests
from bs4 import BeautifulSoup

base_url = "https://cookierunkingdom.fandom.com/wiki/"

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

	def find_info(self):
		'''
		Search through cookie's link to scrape the information.
		Sets: image link, gender, release date, type, position
		'''
		pass


def basic_cookie_scrape():
	'''
	Function to scrape the cookies information.

	returns:
		cookies (list[Cookie]) : a list of Cookie objects
	'''
	r = requests.get(base_url + "List_of_Cookies")

	soup = BeautifulSoup(r.content, 'html5lib')
	cookies = []

	for table in soup.findAll("table", attrs = {'class' : 'fandom-table'}):
		for tr in table.findAll("tr"):
			name = tr.th.b.a['title']
			link = tr.th.b.a['href']
			c = Cookie(name, link)
			cookies.append(c)
	
	return cookies


def indepth_cookie_scrape(cookies: list[Cookie], cookieCSV = None):
	'''
	Deep dives each cookie info if information is not known yet

	params:
		cookies (list[Cookie]): list of basic Cookie objects
		cookieCSV (str): csv file of known cookie info

	returns:
		cookies (list[Cookie]): list of all required updated cookies
	'''
	pass


cookies = basic_cookie_scrape()

cookies_to_update = indepth_cookie_scrape(cookies=cookies, cookieCSV=None)
