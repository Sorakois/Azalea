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
		Sets: Gender, 
		'''
		pass


def scrape_cookies():
	'''
	Function to scrape the cookies information.

	returns:
		cookies (List[Cookie]) : a list of Cookie objects
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


cookies = scrape_cookies()