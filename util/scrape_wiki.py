import requests
from bs4 import BeautifulSoup
import csv
import time

###############################################################
# Customizable variables:
#
## csv file relative path name
cookieCSVFile = 'util/cookies.csv'
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
		return [self.name, self.link, self.pronouns, self.release, self.ctype, self.position, self.img_link]

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
			releasediv = soup.find('div', attrs={'data-source':'release_date'})
			self.release = releasediv.find('div').getText()
		except AttributeError:
			try:
				releasediv = soup.find('div', attrs={'data-source':'releasedate'})
				self.release = releasediv.find('div').getText()
			except AttributeError:
				self.release = 'Unreleased/TBA'
		
		try:
			typediv = soup.find('td', attrs={'data-source':'role'})
			self.ctype = typediv.findAll('a')[1].getText()
		except IndexError:
			self.ctype = 'Unknown'

		try:
			posdiv = soup.find('td', attrs={'data-source':'position'})
			self.position = posdiv.findAll('a')[1].getText()
		except IndexError:
			self.position = 'Unknown'


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
		with open(cookieCSV, 'w') as f:
			f.write('Name, Link, Gender, Release, Type, Position, Picture\n')
		f1 = open(cookieCSV, 'r')


	# Identify what cookies are new!
	new_cookies = []
	csvReader = list(csv.reader(f1, delimiter=','))

	for cookie in cookies:
		found = False
		for row in csvReader:
			if cookie.name == row[0] or cookie.link == row[1]:
				found = True
				break
		if not found:
			new_cookies.append(cookie)
	
	f1.close()

	for cookie in new_cookies:
		cookie.find_info()
		with open(cookieCSV, 'a', newline='') as f:
			writer = csv.writer(f)
			writer.writerow(cookie.to_list())

	return new_cookies
		
def scrape_cookies():
	cookies = basic_cookie_scrape()

	cookies_to_update = indepth_cookie_scrape(cookies=cookies, cookieCSV=cookieCSVFile)
	return "updated"
