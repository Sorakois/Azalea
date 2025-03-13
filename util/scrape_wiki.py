import aiohttp  # Async HTTP requests library
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
        self.link = link
        self.position = position
        self.ctype = ctype
        
        self.pronouns = "Unknown"
        self.release = "Unreleased/TBA"
        self.img_link = ""
        self.rarity = "Unknown"
        # Note: identify_released() is now async, so we don't call it here

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

    async def identify_released(self, session):
        '''
        Identify the release date of the cookie - async version
        '''
        async with session.get(base_url + self.link) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html5lib')
            
            try:
                # Look for the release date div
                releasediv = soup.find('div', attrs={'data-source': 'releasedate'})
                if releasediv:
                    # Extract only the value part
                    value_div = releasediv.find('div', class_='pi-data-value')
                    if value_div:
                        self.release = value_div.getText().strip()
                    else:
                        raise AttributeError("No value div found")
                else:
                    # Try alternative format
                    releasediv = soup.find('div', attrs={'data-source':'release_date'})
                    if releasediv:
                        value_div = releasediv.find('div', class_='pi-data-value')
                        if value_div:
                            self.release = value_div.getText().strip()
                        else:
                            self.release = 'Unreleased/TBA'
                    else:
                        self.release = 'Unreleased/TBA'
            except (AttributeError, IndexError):
                self.release = 'Unreleased/TBA'

    async def find_info(self, session):
        '''
        Search through cookie's link to scrape the information.
        Sets: image link, gender, release date, type, position
        '''
        
        async with session.get(base_url + self.link) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html5lib')

            # Get cookie's image (keeping existing code)
            img_container = soup.find('div', {'class': 'wds-tab__content wds-is-current'})
            if img_container and img_container.find('a', {'class': 'image image-thumbnail'}):
                self.img_link = img_container.find('a', {'class': 'image image-thumbnail'})['href']
            else:
                self.img_link = ""

            # Get cookie's pronouns (keeping existing code)
            try:
                pronoundiv = soup.find('div', attrs={'data-source': 'pronouns'})
                if pronoundiv and pronoundiv.find('div', class_='pi-data-value') and pronoundiv.find('div', class_='pi-data-value').find('a'):
                    self.pronouns = pronoundiv.find('div', class_='pi-data-value').find('a').getText().strip()
                else:
                    self.pronouns = "Unknown"
            except Exception:
                self.pronouns = "Unknown"

            # NEW TARGETED METHOD for finding the cookie type
            try:
                # Look for main paragraphs that have both type and position info
                for paragraph in soup.find_all('p'):
                    # Find links to category pages for cookie types
                    type_link = paragraph.find('a', title=lambda t: t and t.startswith('Category:') and t.endswith('_Cookies'))
                    
                    if type_link:
                        # Extract type from the title attribute
                        title = type_link.get('title', '')
                        if 'Category:' in title and '_Cookies' in title:
                            self.ctype = title.split('Category:')[1].split('_Cookies')[0].upper()
                            break
                        
                        # If no title found with the pattern, check the text content
                        if type_link.text.strip():
                            self.ctype = type_link.text.strip().upper()
                            break
                    
                    # If we haven't found the type yet, try looking for images with alt text
                    # that matches cookie types
                    if self.ctype == "Unknown":
                        type_img = paragraph.find('img', alt=lambda alt: alt in [
                            'Magic', 'Charge', 'Defense', 'Support', 
                            'Ambush', 'Bombing', 'Healing', 'Ranged'
                        ])
                        
                        if type_img and type_img.get('alt'):
                            self.ctype = type_img.get('alt').upper()
                            break
            except Exception:
                pass  # Keep default type
                
            # Similar approach for position
            try:
                for paragraph in soup.find_all('p'):
                    position_link = paragraph.find('a', title=lambda t: t and t.startswith('Category:') and 
                                                ('Front_Cookies' in t or 'Middle_Cookies' in t or 'Rear_Cookies' in t))
                    
                    if position_link:
                        title = position_link.get('title', '')
                        if 'Category:' in title and '_Cookies' in title:
                            self.position = title.split('Category:')[1].split('_Cookies')[0].upper()
                            break
                    
                    # Try from image alt text
                    if self.position == "Unknown":
                        position_img = paragraph.find('img', alt=lambda alt: alt in ['Front', 'Middle', 'Rear'])
                        if position_img and position_img.get('alt'):
                            self.position = position_img.get('alt').upper()
                            break
            except Exception:
                pass  # Keep default position

            # Rarity (keeping existing code)
            try:
                rarity_div = soup.find('div', class_='pi-data-value pi-font')
                if rarity_div and rarity_div.find('a') and rarity_div.find('a').find('img', alt=True):
                    self.rarity = rarity_div.find('a').find('img')['alt']
                    self.rarity_img_url = rarity_div.find('a').find('img')['src']
                else:
                    self.rarity = "Unknown"
            except Exception:
                self.rarity = "Unknown"


async def basic_cookie_scrape(session):
    '''
    Function to scrape the cookies information.
    returns:
        cookies (list[Cookie]) : a list of Cookie objects
    '''
    
    async with session.get(base_url + "/wiki/List_of_Cookies") as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'html5lib')
        cookies = []
        
        for cookie_card in soup.select(".scrolly.scrollyflex > div > div[class*='loccard']"):
            try:
                name = cookie_card.select_one("div[style*='text-align:center'] a").get('title')
                link = cookie_card.select_one("div[style*='text-align:center'] a").get('href')
                
                position_div = cookie_card.select_one("div[style*='Front_Cookies'] a, div[style*='Middle_Cookies'] a, div[style*='Rear_Cookies'] a")
                position = position_div.get('title').replace("_Cookies", "") if position_div else "Unknown"
                
                # FOR TYPE: First try to find a link to the cookie's details page
                cookie_link = cookie_card.select_one("div[style*='text-align:center'] a").get('href')
                
                # Set a default type
                ctype = "Unknown"
                
                # Enhanced type detection - look for divs containing category links
                type_div = cookie_card.select_one("div:has(a[href*='Category:Magic_Cookies']), " + 
                                               "div:has(a[href*='Category:Charge_Cookies']), " +
                                               "div:has(a[href*='Category:Defense_Cookies']), " +
                                               "div:has(a[href*='Category:Support_Cookies']), " +
                                               "div:has(a[href*='Category:Ambush_Cookies']), " +
                                               "div:has(a[href*='Category:Bombing_Cookies']), " +
                                               "div:has(a[href*='Category:Healing_Cookies']), " +
                                               "div:has(a[href*='Category:Ranged_Cookies'])")
                
                if type_div:
                    type_link = type_div.select_one("a")
                    if type_link and 'href' in type_link.attrs:
                        href = type_link['href']
                        if 'Category:' in href and '_Cookies' in href:
                            ctype = href.split('Category:')[1].split('_Cookies')[0].upper()
                
                # If we couldn't find the type through the div approach, try direct link detection
                if ctype == "Unknown":
                    type_link = cookie_card.select_one("a[href*='Category:Magic_Cookies'], a[href*='Category:Charge_Cookies'], a[href*='Category:Defense_Cookies'], a[href*='Category:Support_Cookies'], a[href*='Category:Ambush_Cookies'], a[href*='Category:Bombing_Cookies'], a[href*='Category:Healing_Cookies'], a[href*='Category:Ranged_Cookies']")
                    
                    if type_link:
                        # Extract type from href - something like "/wiki/Category:Magic_Cookies"
                        href = type_link.get('href', '')
                        if 'Category:' in href and '_Cookies' in href:
                            ctype = href.split('Category:')[1].split('_Cookies')[0].upper()
                        else:
                            # Try to get from text content
                            ctype = type_link.text.strip().upper()
                
                cookies.append(Cookie(name, position, ctype, link))
            except Exception as e:
                # Skip this cookie if there's an error
                pass
        
        return cookies

async def indepth_cookie_scrape(cookies, bot):
    '''
    Deep dives each cookie info if information is not known yet
    params:
        cookies (list[Cookie]): list of basic Cookie objects
        bot: bot instance with database connection
    returns:
        new_cookies (list[Cookie]): list of newly added cookies
    '''
    new_cookies = []
    
    # Create HTTP session for all requests
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        # First, get release dates and info for all cookies
        for cookie in cookies:
            try:
                # Get full info first
                await cookie.find_info(session)
                # Then get release date
                await cookie.identify_released(session)
            except Exception as e:
                print(f"Error processing cookie {cookie.name}: {e}")
                # Set defaults if we couldn't get the info
                cookie.release = 'Unreleased/TBA'
        
        # Get all cookies from the database
        cookies_db = []
        try:
            # Create a fresh connection with a longer timeout
            async with bot.db.acquire() as conn:
                # Set a longer wait_timeout for this connection
                async with conn.cursor() as cursor:
                    await cursor.execute("SET SESSION wait_timeout=300")  # 5 minutes
                    await cursor.execute("SELECT Name, Link, Released, Type FROM cookie_info")
                    cookies_db = await cursor.fetchall()
        except Exception as e:
            pass
            #print(f"Database error when fetching cookies: {e}")
            # If we can't get the database entries, we'll assume all cookies are new
        
        # Create lookup dictionaries
        db_names = {row[0]: row for row in cookies_db}
        db_links = {row[1]: row for row in cookies_db}
        
        # Process cookies in smaller batches to avoid long transactions
        batch_size = 5
        cookie_batches = [cookies[i:i+batch_size] for i in range(0, len(cookies), batch_size)]
        
        for batch in cookie_batches:
            try:
                # Get a fresh connection for each batch
                async with bot.db.acquire() as conn:
                    async with conn.cursor() as cursor:
                        # Set a longer wait_timeout
                        await cursor.execute("SET SESSION wait_timeout=300")
                        
                        # Process this batch of cookies
                        for cookie in batch:
                            try:
                                db_cookie = db_names.get(cookie.name) or db_links.get(cookie.link)
                                
                                if not db_cookie:
                                    # New cookie - add to database
                                    new_cookies.append(cookie)
                                    await cursor.execute("INSERT INTO cookie_info (Name, Link, Gender, Released, Type, Position, Picture, Rarity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", tuple(cookie.to_list()))
                                elif hasattr(cookie, 'release') and cookie.release != db_cookie[2]:
                                    # Update existing cookie with new release date and type
                                    await cursor.execute("UPDATE cookie_info SET Released = %s, Type = %s WHERE Name = %s", 
                                                        (cookie.release, cookie.ctype, cookie.name))
                            except Exception as e:
                                #print(f"Error processing cookie {cookie.name} in database: {e}")
                                continue
                        
                        # Commit after each batch
                        await conn.commit()
            except Exception as e:
                pass
                #print(f"Database error processing batch: {e}")
                # Continue with the next batch if there's an error
    
    return new_cookies
		
async def scrape_cookies(bot):
    '''
    Main scraping function
    '''
    # Use a single session for all HTTP requests
    async with aiohttp.ClientSession() as session:
        cookies = await basic_cookie_scrape(session)
        cookies_to_update = await indepth_cookie_scrape(cookies=cookies, bot=bot)
        return cookies_to_update