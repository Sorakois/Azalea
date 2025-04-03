''' 
We can "curl" this website
    # https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#
    # to see source code: view-source:https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#
to get ALL the html code.
(or just go and copy/paste the source code)

We can parse through the HTML to find names, and all materials we need for the /build command.
All the data is there, it's just a matter of, well, parse it and get what we need!
'''
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

def getHSRMetaData():
    '''
    Scrapes information from a community-made Google Sheet
    '''
    # This is the url to the HSR meta sheet guide
    # Made by community members, scraped by us!
    meta_sheet_url = "https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#"

    # Setup FirefoxDriver
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    # Open the Google Sheets page
    driver.get(meta_sheet_url)

    # Give it some time to load the content (adjust if needed)
    driver.implicitly_wait(5)  # Wait 5 seconds to let JavaScript load content

    # Now we can scrape the rendered HTML
    html = driver.page_source
    build_soup = BeautifulSoup(html, 'html.parser')

    # Find all <tr> elements
    build_bowl = build_soup.findAll('tr')

    # Write the remaining <tr> data to a text file, removing the leading digits and non-alphabet characters
    with open('testing-scrape.txt', 'w', encoding='utf-8') as file:
        for tr in build_bowl:
            # Extract non-empty <td> elements, stripping whitespace
            td_texts = [td.text.strip() for td in tr.find_all('td') if td.text.strip()]

            # Join non-empty <td> elements with a space
            cleaned_text = ' '.join(td_texts)

            # Remove leading digits and any non-alphabet characters immediately after them
            cleaned_text = re.sub(r'^\d+[^A-Za-z]*', '', cleaned_text)

            # Skip lines that start with specific keywords
            if re.match(r'^(added|removed|updated|fixed|Completely|lowered)\b', cleaned_text, re.IGNORECASE):
                continue

            # Skip empty lines
            if cleaned_text:
                file.write(cleaned_text + '\n')

    # Close the driver after scraping
    driver.quit()


def getHSRWikiNames():
    '''
    Get a list of currently/soon-to-be playable HSR characters
    '''
    # URL for valid character list
    valid_char_check_url = "https://honkai-star-rail.fandom.com/wiki/Character/List"

    # Fetch the page content
    response = requests.get(valid_char_check_url)
    checking_soup = BeautifulSoup(response.content, 'html.parser')

    # Find all tables with the class 'article-table sortable'
    check_tables = checking_soup.find_all("table", class_="article-table sortable")

    # Initialize a list to store valid character names
    valid_char_names = []

    for table in check_tables:
        # Find all links <a> within the table
        links = table.find_all('a', href=True)
        
        # Extract character names from the links
        for link in links:
            link_text = link.get_text().strip()

            # Check if the character name is valid (not empty or a number)
            if link_text and not re.match(r'^\d+(\.\d+)?$', link_text):  # Ignore empty or numeric text
                valid_char_names.append(link_text)

    # Open the file in write mode
    with open("valid_chars.txt", "w") as file:
        # Now every 1st entry is the character name, and every 2nd is their path
        # We will write each character name along with its corresponding path to the file
        for i in range(0, len(valid_char_names), 2):  # Iterate in steps of 2
            char_name = valid_char_names[i]

            # Handle "Dan Heng • Imbibitor Lunae" case
            if char_name.lower() == "dan heng • imbibitor lunae":
                char_name = "Imbibitor Lunae"
            elif char_name.lower() == "dan heng":
                char_name = "Dan Heng"  # Keep it unchanged
            
            path = valid_char_names[i+1] if i+1 < len(valid_char_names) else ''  # Get path or empty if none
            path = "Hunt" if (path.lower() == "the hunt") else path
                
            file.write(f"{char_name} {path}\n")
    
    
    
# Test run
try:
    getHSRMetaData()
    print("SUCCESS: HSR Wiki Data")
    getHSRWikiNames()
    print("SUCCESS: Google Sheet Data")
except Exception as e:
    print(f"{e}")