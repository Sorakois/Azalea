#import requests
import aiohttp
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

    def __init__(self, name, position, ctype, link):
        '''
        Assign the known names

        params:
            name (str) : name of cookie
            link (str) : url destination to cookie
        '''
        self.name = name
        self.link = link # a path --> /Wiki/cookie_cookie
        self.position = position
        self.ctype = ctype
        self.identify_released()
        # self.identify_type()


    def __str__(self):
        '''
        Allows for name to be called when referenced.

        returns:
            self.name (str) : name of cookie
        '''
        return f"Cookie('{self.name}', position={self.position}, type={self.ctype})"

    def to_list(self):
        '''
        Converts Cookie object into list format
        '''
        # Ensure this order matches: (Name, Link, Gender, Released, Type, Position, Picture, Rarity)
        return [self.name, self.link, self.pronouns, self.release, self.ctype, self.position, self.img_link, self.rarity]

    def identify_released(self):
        r = requests.get(base_url + self.link)
        soup = BeautifulSoup(r.content, 'html5lib')

        # The wiki changes a lot since its open source...
        try:
            releasediv = soup.findAll('div', attrs={'class': 'pi-item pi-data pi-item-spacing pi-border-color', 'data-source': 'releasedate'})
            self.release = releasediv[-1].getText()

        except (AttributeError, IndexError):
            try:
                releasediv = soup.findAll('div', attrs={'data-source':'releasedate'})
                self.release = releasediv[-1].find('div').getText()

            except (AttributeError, IndexError):
                    try:
                        releasediv = soup.findAll('div', attrs={'data-source':'release_date'})
                        self.release = releasediv[-1].find('div').getText()
        
                    except (AttributeError, IndexError):
                        self.release = 'Unreleased/TBA'


    # def identify_type(self):
    # 	r = requests.get(base_url + self.link)
    # 	soup = BeautifulSoup(r.content, 'html5lib')
    # 	# The wiki changes a lot since its open source...

    # 	try:
    # 		# Type (Magic, Defense, etc.)
    # 		typediv = soup.find('td', attrs={'data-source': 'role'})
    # 		img_element = typediv.find('img')

    # 		# See if data-src, otherwise get src url
    # 		self.ctype_img_url = img_element['data-src'] if 'data-src' in img_element.attrs else img_element['src']

    # 		# Get the name of the type
    # 		self.ctype_alt_text = img_element['alt'].upper()
    # 	except IndexError:
    # 		self.ctype = 'Unknown'

    def find_info(self):
        '''
        Search through cookie's link to scrape the information.
        Sets: image link, gender, release date, type, position
        '''
        
        r = requests.get(base_url + self.link)
        soup = BeautifulSoup(r.content, 'html5lib')

        # Get cookie's image
        img_container = soup.find('div', {'class': 'wds-tab__content wds-is-current'})
        self.img_link = img_container.find('a', {'class': 'image image-thumbnail'})['href']
        
        # Get cookie's pronouns
        pronoundiv = soup.find('div', attrs={'data-source': 'pronouns'})
        self.pronouns = pronoundiv.find('div', class_='pi-data-value').find('a').getText()

        try:
            # Get table with the position and type info
            table = soup.find('table', {'class': 'pi-horizontal-group'})

            # Get type
            type_cell = table.find('td', {'data-source': 'role'})
            type_img = type_cell.find('img')
            self.type_img_url = type_img['src']
            self.ctype = type_img['alt'].upper()
            #self.type_text = type_cell.find_all('a')[-1].getText()  # Get the last 'a' tag which contains the text

            # Get position
            position_cell = table.find('td', {'data-source': 'position'})
            position_img = position_cell.find('img')
            self.position_img_url = position_img['src']
            self.position = position_img['alt'].upper()
            #self.position_text = position_cell.find_all('a')[-1].getText()  # Get the last 'a' tag which contains the text
        except IndexError:
            self.position = 'Unknown'
            self.ctype = 'Unknown'

        # Get cookie's rarity
        rarity_img = soup.find('div', class_='pi-data-value pi-font').find('a').find('img')
        self.rarity = rarity_img['alt']
        self.rarity_img_url = rarity_img['src']



def basic_cookie_scrape():

    base_url = "https://cookierunkingdom.fandom.com"
    '''
    Function to scrape the cookies information.
    returns:
        cookies (list[Cookie]) : a list of Cookie objects
    '''
    
    r = requests.get(base_url + "/wiki/List_of_Cookies")
    soup = BeautifulSoup(r.content, 'html5lib')
    cookies = []
    
    for cookie_card in soup.select(".scrolly.scrollyflex > div > div[class*='loccard']"):
        try:
            name = cookie_card.select_one("div[style*='text-align:center'] a").get('title')
            link = cookie_card.select_one("div[style*='text-align:center'] a").get('href')
            
            position_div = cookie_card.select_one("div[style*='Front_Cookies'] a, div[style*='Middle_Cookies'] a, div[style*='Rear_Cookies'] a")
            position = position_div.get('title').replace("_Cookies", "") if position_div else "Unknown"
            
            type_div = cookie_card.select_one("div[style*='Charge_Cookies'] a, div[style*='Defense_Cookies'] a, div[style*='Magic_Cookies'] a, div[style*='Support_Cookies'] a, div[style*='Ambush_Cookies'] a, div[style*='Bombing_Cookies'] a, div[style*='Healing_Cookies'] a, div[style*='Ranged_Cookies'] a")
            ctype = type_div.get('title').replace("_Cookies", "") if type_div else "Unknown"
            
            cookies.append(Cookie(name, position, ctype, link))
        except Exception as e:
            print(f"Error processing a cookie: {e}")
    
    return cookies


async def indepth_cookie_scrape(cookies: list[Cookie], bot):
    '''
    Deep dives each cookie info if information is not known yet
    params:
        cookies (list[Cookie]): list of basic Cookie objects
        bot: bot instance with database connection
    returns:
        new_cookies (list[Cookie]): list of newly added cookies
    '''
    
    new_cookies = []
    
    async with bot.db.acquire() as conn:
        async with conn.cursor() as cursor:
            # Open the data
            await cursor.execute("SELECT Name, Link, Released, Type FROM cookie_info")
            cookies_db = await cursor.fetchall()
            
            # Create lookup dictionaries
            db_names = {row[0]: row for row in cookies_db}
            db_links = {row[1]: row for row in cookies_db}
            
            # Identify what cookies are new!
            for cookie in cookies:
                try:
                    db_cookie = db_names.get(cookie.name) or db_links.get(cookie.link)
                    
                    if not db_cookie:
                        # Make sure identify_released has been called first
                        cookie.identify_released()
                        # Then fetch all the detailed info
                        cookie.find_info()
                        new_cookies.append(cookie)
                        await cursor.execute("INSERT INTO cookie_info (Name, Link, Gender, Released, Type, Position, Picture, Rarity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", tuple(cookie.to_list()))
                    elif hasattr(cookie, 'release') and cookie.release != db_cookie[2]:
                        # Update existing cookie with new release date
                        await cursor.execute("UPDATE cookie_info SET Released = %s, Type = %s WHERE Name = %s", (cookie.release, cookie.ctype, cookie.name))
                except Exception:
                    # Continue with next cookie if there's an error
                    continue
            
            await conn.commit()
    
    return new_cookies
		
async def scrape_cookies(bot):
    cookies = basic_cookie_scrape()
    cookies_to_update = await indepth_cookie_scrape(cookies=cookies, bot=bot)
    return cookies_to_update