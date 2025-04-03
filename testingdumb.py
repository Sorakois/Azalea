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

    # Initialize a list to store character names and their paths
    meta_characters = []

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

                # Add character name and path to the list
                if len(td_texts) >= 2:  # Ensure there's both a character name and a path
                    # Formatiting is off for Rememberance Traiblazer.
                    # For some reason, their name is "RememberanceTrailblazer"
                    td_texts[0] = "Remembrance Trailblazer" if td_texts[0].lower().strip() == "remembrancetrailblazer" else td_texts[0]
                    
                    meta_characters.append(f"{td_texts[0]} {td_texts[1]}")  # charname |  path
    # Close the driver after scraping
    driver.quit()

    return meta_characters


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

    # Initialize a list to store valid character names and paths
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
            # For simplicity, but we have to be careful
            # Only use when pass-by-copy is ok
            
            # valid_char_names[i] = char_name
            # valid_char_names[i+1] = path

            # Handle "Dan Heng • Imbibitor Lunae" vs "Dan Heng"
            if valid_char_names[i].lower() == "dan heng • imbibitor lunae":
                valid_char_names[i] = "Imbibitor Lunae"
            elif valid_char_names[i].lower() == "dan heng":
                valid_char_names[i] = "Dan Heng"
            
            # Get path or empty if none
            path = valid_char_names[i+1] if i+1 < len(valid_char_names) else ''
            # "The Hunt" in wiki, but "Hunt" in meta sheet
            if path.lower().strip() == "the hunt":
                valid_char_names[i+1] = "Hunt"
                
            # Trailblazer and March 7th have multiple paths and don't follow the same format
            # So, we fix.
            if valid_char_names[i].lower().strip() == "trailblazer":
                # In wiki, Trailblazer -> PATH TRAILBLAZER | PATH
                valid_char_names[i] = f"{path} Trailblazer"
                print(f"Fixed! {valid_char_names[i]} {valid_char_names[i+1]}")
                
            file.write(f"{valid_char_names[i+1]} {valid_char_names[i]}\n")

    return valid_char_names


# Compare characters from Wiki and Meta Data and print matches or non-matches
wiki_chars = getHSRWikiNames()
meta_chars = getHSRMetaData()

# Initialize list to track missing entries in meta
not_found_in_meta = []
counted = 0
count2 = 0

# Check for character name and path matches and print if they exist
for i in range(0, len(wiki_chars), 2):  # Iterate in steps of 2 for character names and paths
    char_name = wiki_chars[i]
    path = wiki_chars[i+1] if i+1 < len(wiki_chars) else ''  # Get path or empty if none

    # Handle special cases like "Dan Heng • Imbibitor Lunae"
    if char_name.lower() == "dan heng • imbibitor lunae":
        char_name = "Imbibitor Lunae"
    elif char_name.lower() == "dan heng":
        char_name = "Dan Heng"

    # Format "charname path" for comparison
    wiki_entry = f"{char_name} {path}"

    # Print the characters found in wiki but not in meta
    if wiki_entry not in meta_chars:
        print(f"Found in wiki but not in meta: {wiki_entry}")
        count2 += 1
    else:
        counted += 1

needed_still = 71 - counted if counted < 71 else 0        
print(f"\nFound in both: {counted} characters / 71 possible characters.\n{needed_still} still need found. {count2} of those {needed_still} are found in wiki and not meta.")

