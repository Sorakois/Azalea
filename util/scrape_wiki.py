import requests
from bs4 import BeautifulSoup

###############################################################
# Customizable variables:
#
## csv file relative path name
csvFile = './cookies.csv'
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

	def __str__(self):
		return self.name

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
	r = requests.get(base_url + "/wiki/List_of_Cookies")

	soup = BeautifulSoup(r.content, 'html5lib')
	cookies = []

	for table in soup.findAll("table", attrs = {'class' : 'fandom-table'}):
		for tr in table.findAll("tr"):
			name = tr.th.b.a['title']
			link = tr.th.b.a['href']
			c = Cookie(name, link)
			cookies.append(c)
	
	return cookies


def indepth_cookie_scrape(cookies: list[Cookie], cookieCSV):
	'''
	Deep dives each cookie info if information is not known yet

	params:
		cookies (list[Cookie]): list of basic Cookie objects
		cookieCSV (str): csv file of known cookie info

	returns:
		cookies (list[Cookie]): list of all required updated cookies
	'''
	try:
		f1 = open(cookieCSV, 'r')
	except FileNotFoundError as e:
		print("csv file does not exist, creating new csv.")
	finally:
		f2 = open(cookieCSV, 'w')

	



cookies = basic_cookie_scrape()

cookies_to_update = indepth_cookie_scrape(cookies=cookies, cookieCSV=csvFile)
