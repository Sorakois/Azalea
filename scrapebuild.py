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

class BuildScrape():
    def __init__(self, char_name, stat_focus, trace_prio, substats, gear_mainstats, best_lc, best_relics, best_planar, best_team, notes):
        
        self.char_name = char_name

        self.stat_focus = stat_focus # Overall character stats to "reach"
        self.trace_prio = trace_prio
    
        self.substats = substats # Each relic has 4 sub-stats
        self.gear_mainstats = gear_mainstats # Each relic has 1 main stat
        

        self.best_lc = best_lc

        self.best_relics = best_relics
        self.best_planar = best_planar

        self.best_team = best_team

        self.notes = notes

def getHSRMetaData():#
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
                
            file.write(f"{valid_char_names[i]} {valid_char_names[i+1]}\n") # NAME | PATH

    return valid_char_names

def grabInfo(released_chars, meta_sheet_data):
    # List of "BuildScrape" objects, each object contains all info needed for Azalea
    char_list = []
    count = 0
    with open('scraped-buildinfo.txt', 'w', encoding='utf-8') as file:
        for i in range(0, len(meta_sheet_data)): # Iterate through EVERY character
            char_name_path = meta_sheet_data[i] # Format: "Character Path"
        
            for released in released_chars:
            
                if char_name_path.lower().strip() == released.lower().strip():
                    # Initialize defaults in case parsing fails
                    stat_focus = ""
                    trace_prio = []
                    substats = []
                    gear_mainstats = []
                    best_lc = ""
                    best_relics = ""
                    best_planar = ""
                    notes = ""

                    #print(f"Found build info for {released}. Processing...")

                    # Grab the name of the character. 
                    # This is "origin" (when they match in both lists, stop and look around for details)
                    name = meta_sheet_data[i]
                    file.write(f"Build of {meta_sheet_data[i]}:\n")
                    
                    #for f in range(0, 15, 1): #exists for the sake of debugging
                    #    file.write(f"TESTING index{f}: {meta_sheet_data[i+f]}\n")


                    # I+2 -> Light Cone Info | Relic Set Info
                    lc_relic_info = meta_sheet_data[i + 2]
                    # Find the position of "1.)" which separates LC from relics
                    split_pos = lc_relic_info.find("1.)")
                    if split_pos != -1:
                        best_lc = lc_relic_info[:split_pos].strip()
                        best_relics = lc_relic_info[split_pos:].strip()
                    else:
                        # Fallback if "1.)" not found
                        best_lc = lc_relic_info
                    
                    file.write(f"best_lc: {best_lc}\n") 
                    file.write(f"best_relics: {best_relics}\n")
                    
                    # I+6 -> Best Planar | Stat Focus
                    planar_stat_info = meta_sheet_data[i+6]
                    # Define stat keywords that indicate the start of stat_focus
                    stat_keywords = ["ATK:", "CRIT Rate:", "CRIT DMG:", "SPD:", "DEF:", "EHR:", "HP:", "Break"]
                    
                    # Find first occurrence of any stat keyword
                    split_pos = -1
                    for keyword in stat_keywords:
                        pos = planar_stat_info.find(keyword)
                        if pos != -1 and (split_pos == -1 or pos < split_pos):
                            split_pos = pos
                    
                    if split_pos != -1:
                        best_planar = planar_stat_info[:split_pos]
                        stat_focus = planar_stat_info[split_pos:]
                    else:
                        # Fallback if no stat keyword found
                        best_planar = planar_stat_info
                    
                    file.write(f"best_planar: {best_planar}\n") 
                    file.write(f"stat_focus: {stat_focus}\n")

                    # I+3, I+4, I+7, I+8 all look like -> gear_mainstats | ability_prio 
                    # (all are in order)
                    gear_mainstats = []
                    trace_prio= []
                    for num in [3,4,7,8]:
                        for idx, char in enumerate(meta_sheet_data[i+num]):
                            if char.isdigit() or char == "~":
                                if char in "⁰¹²³⁴⁵⁶⁷⁸⁹":
                                    # Skip supersripts for notes
                                    continue
                                gear_mainstats.append(meta_sheet_data[i+num][:idx])
                                trace_prio.append(meta_sheet_data[i+num][idx:])
                                break 
                    file.write(f"gear_mainstats: {gear_mainstats}\n") 
                    file.write(f"trace_prio: {trace_prio}\n")

                    # NOTES PARSING
                    # Check both i+9 and i+10 for notes sections
                    notes = []
                    for offset in [9, 10]:
                        if i+offset < len(meta_sheet_data):
                            note_text = meta_sheet_data[i+offset]
                            if note_text.startswith("Relic") or note_text.startswith("Other"):
                                # NOTE: Boothill -> Boothill\'s ... please fix?
                                notes.append(note_text.strip())
                    
                    file.write(f"Notes: {notes}\n")
  
                    # We have to get teams from Pydrwen!
                    file.write("\n")

                    # Create a BuildScrape object
                    '''
                    NOTE:
                        Find out where the hell "substat" went? it's not in my parse, but should be right below/near relics
                    '''
                    char_obj = BuildScrape(
                        char_name=name,
                        stat_focus=stat_focus,
                        trace_prio=trace_prio,
                        substats=None,
                        gear_mainstats=gear_mainstats,
                        best_lc=best_lc,
                        best_relics=best_relics,
                        best_planar=best_planar,
                        best_team=None,
                        notes=notes
                    )

                    count += 1

                    # Store in the list
                    char_list.append(char_obj)

    print(f"Out of {len(released_chars)} characters, we got the info for {count} of them.")
    return char_list


# Compare characters from Wiki and Meta Data and print matches or non-matches
wiki_chars = getHSRWikiNames()
meta_chars = getHSRMetaData()

# Initialize list to track missing entries in meta
released_chars = []
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
        print(f"This characters are unreleased and will be ignored: {wiki_entry}")
        
        count2 += 1
    else:
        counted += 1
        if char_name.lower() == "anaxa" or char_name.lower() == "castorice":
            print(f"This characters is coming soon, but no build exists yet: {wiki_entry}")
        else:
            released_chars.append(wiki_entry)

needed_still = 71 - counted if counted < 71 else 0        
print(f"Found in both: {counted} characters / 71 possible characters.\n{needed_still} still need found. {count2} of those {needed_still} are found in wiki and not meta.")

# Now that debugging is done, let's call another function
# We now want to systemically gnaw out table row data
idk_what_to_name = grabInfo(released_chars, meta_chars)

