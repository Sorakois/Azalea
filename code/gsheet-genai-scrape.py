''' 
We can "curl" this website
    # https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#
to get ALL the html code.

We use Selenium to get the raw HTML, strip the tags, and pass the raw text to the Gemini API 
to dynamically identify characters, their paths, and sort everything into a structured format for the /build command.
'''

from knowledge import cleanse_name
import asyncio
import re
import os
import json
import time
from discord import Interaction
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

# NEW IMPORT FOR THE UPDATED GOOGLE SDK
from google import genai
from google.genai import types

class BuildScrape():
    def __init__(self, char_name, path, stat_focus, substats, trace_prio, gear_mainstats, best_lc, best_relics, best_planar, best_team, notes):
        self.char_name = char_name
        self.path = path
        self.stat_focus = stat_focus 
        self.trace_prio = trace_prio
        self.substats = substats 
        self.gear_mainstats = gear_mainstats 
        self.best_lc = best_lc
        self.best_relics = best_relics
        self.best_planar = best_planar
        self.best_team = best_team
        self.notes = notes

    def __str__(self):
        return f"\n=== {self.char_name.upper()} ===\nPath: {self.path}\nStat Focus: {self.stat_focus}\nTrace Prio: {self.trace_prio}\nGear Mainstats: {self.gear_mainstats}\nBest LCs: {self.best_lc}\nBest Relics: {self.best_relics}\nBest Planar: {self.best_planar}\nBest Team: {self.best_team if self.best_team else 'N/A'}\nNotes: {self.notes if self.notes else 'N/A'}\n"
        
    @staticmethod
    def getHSRMetaData():
        '''
        Scrapes raw text information from the community-made Google Sheet.
        Returns the raw string data. Gemini will handle the parsing.
        '''
        meta_sheet_url = "https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#"

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
        driver.get(meta_sheet_url)
        
        print("Waiting 10 seconds for Google Sheets to fully render data...")
        
        # BRUTE FORCE WAIT: Give the JS plenty of time to build the table
        time.sleep(10)

        html = driver.page_source
        build_soup = BeautifulSoup(html, 'html.parser')
        build_bowl = build_soup.findAll('tr')

        print(f"=== SELENIUM DEBUG ===")
        print(f"Found {len(build_bowl)} <tr> elements")

        raw_text_lines = []

        with open('testing-scrape.txt', 'w', encoding='utf-8') as file:
            for i, tr in enumerate(build_bowl):
                td_texts = [td.text.strip() for td in tr.find_all('td') if td.text.strip()]
                cleaned_text = ' '.join(td_texts)

                # Skip header/update rows
                if re.match(r'^(added|removed|updated|fixed|Completely|lowered)\b', cleaned_text, re.IGNORECASE):
                    continue

                if cleaned_text:
                    file.write(cleaned_text + '\n')
                    raw_text_lines.append(cleaned_text)
                        
        driver.quit()
        raw_text_block = "\n".join(raw_text_lines)
        
        return raw_text_block

    @staticmethod
    def getHSRWikiNames():
        '''
        Get a list of currently/soon-to-be playable HSR characters from the Wiki.
        Returns just the names, as we want Gemini to dynamically extract the paths.
        '''
        valid_char_check_url = "https://honkai-star-rail.fandom.com/wiki/Character/List"
        response = requests.get(valid_char_check_url)
        checking_soup = BeautifulSoup(response.content, 'html.parser')

        check_tables = checking_soup.find_all("table", class_="article-table sortable")
        valid_char_names = []

        for table in check_tables:
            links = table.find_all('a', href=True)
            for link in links:
                link_text = link.get_text().strip()
                if link_text and not re.match(r'^\d+(\.\d+)?$', link_text):  
                    valid_char_names.append(link_text)

        clean_names = []
        for i in range(0, len(valid_char_names), 2): 
            name = valid_char_names[i]
            if name.lower() == "dan heng • imbibitor lunae":
                name = "Imbibitor Lunae"
            elif name.lower() == "dan heng":
                name = "Dan Heng"
            elif name.lower().strip() == "trailblazer":
                path = valid_char_names[i+1] if i+1 < len(valid_char_names) else ''
                name = f"{path} Trailblazer"
            
            clean_names.append(name)

        return clean_names

    @staticmethod
    def parse_with_gemini(raw_text, characters_to_find):
        """
        Uses Gemini API to parse the unstructured raw text into structured JSON, organized by character.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable not set.")
            return {}

        client = genai.Client(api_key=api_key)
        
        char_list_str = ", ".join(characters_to_find)

        prompt = f"""
        You are a Honkai Star Rail data extraction assistant. I am providing you with raw, scraped text from a community build sheet.
        
        Your task is to extract the build information for the following characters:
        {char_list_str}

        Instead of me hard-coding the character Paths, I need YOU to dynamically identify and extract the correct Path for each character based on the raw text. 
        
        CRITICAL HINT FOR FINDING DATA: You can tell the names by a consistent format in the raw text. The {{character name}} is directly to the left of the {{path}} table data. 
        (e.g., "Acheron Nihility", "Kafka Nihility", "Seele Hunt"). Use this structure to anchor where a character's build data begins.

        Return the data strictly as a JSON object where each key is the Character's Name, and the value is an object containing their build info. 
        Format Example:
        {{
            "Acheron": {{
                "path": "Nihility",
                "stat_focus": ["CRIT Rate: 70%", "SPD: 134"],
                "trace_prio": ["Ultimate", "Skill", "Talent"],
                "gear_mainstats": ["Chest: CRIT Rate", "Boots: SPD", "Orb: ATK%", "Rope: ERR"],
                "best_lc": ["1 - Along the Passing Shore", "2 - Good Night and Sleep Well"],
                "best_relics": ["1.) Pioneer Diver of Dead Waters"],
                "best_planar": ["1.) Izumo Gensei and Takama Divine Realm"],
                "best_team": "Acheron, Pela, Silver Wolf, Gallagher",
                "notes": "E2 allows running a Harmony character."
            }}
        }}

        Extract the data cleanly. If a character from the list is completely missing from the raw text, omit them entirely.

        RAW TEXT:
        {raw_text}
        """

        print("Sending raw text to Gemini for parsing... (This may take a minute depending on the length of the text)")
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            parsed_data = json.loads(response.text)
            
            char_objs = {}
            for char_name, item in parsed_data.items():
                char_obj = BuildScrape(
                    char_name=char_name,
                    path=item.get("path", "Unknown"),
                    stat_focus=item.get("stat_focus", []),
                    substats=[], 
                    trace_prio=item.get("trace_prio", []),
                    gear_mainstats=item.get("gear_mainstats", []),
                    best_lc=item.get("best_lc", []),
                    best_relics=item.get("best_relics", []),
                    best_planar=item.get("best_planar", []),
                    best_team=item.get("best_team", None),
                    notes=item.get("notes", None)
                )
                char_objs[char_name] = char_obj
            return char_objs

        except Exception as e:
            print(f"Failed to fetch or parse JSON from Gemini. Error: {e}")
            return {}


class fullScrape(BuildScrape):
    @staticmethod
    async def fullScrapeBuild():
        print("==================== Starting to scrape... ====================\n")
        
        wiki_chars = BuildScrape.getHSRWikiNames()
        raw_text = BuildScrape.getHSRMetaData()

        if not raw_text:
            print("ERROR: Failed to scrape raw text from the meta sheet!")
            return

        print(f"Found {len(wiki_chars)} valid characters to search for on the Fandom Wiki.")
        print("\n==================== Calling Gemini API to dynamically parse data... ====================\n")
        
        builtCharacters_dict = BuildScrape.parse_with_gemini(raw_text, wiki_chars)
        
        print("\n==================== Parsing Complete! Database interactions are disabled. ====================\n")
        
        sorted_char_names = sorted(builtCharacters_dict.keys())
        
        for name in sorted_char_names:
            print(builtCharacters_dict[name])
        
        print(f"\nSuccessfully parsed {len(builtCharacters_dict)} characters via API.")
        print("Database insertion logic is currently disabled for credential changes.")

                            
async def main():
    await fullScrape.fullScrapeBuild()
    print("\nDone! Scraping and parsing completed.")

if __name__ == "__main__":
    asyncio.run(main())