# imports
import discord
from discord import app_commands, Colour
from discord.ext import commands
from typing import Literal, List, Dict, Optional
import random
import logging
import aiohttp
import asyncio
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup
import json

# Helper Functions
def cleanse_name(character:str):
    """Formats character names for database queries."""
    character = character.upper().strip().replace('-', ' ')

    # Quick fixes and aliases
    if character == "CUSTARD COOKIE III":
        character = "Custard Cookie III"
    if character in ["DR. RATIO", "RATIO", "DOCTOR RATIO"]:
        character = "dr ratio"
    if character in ["DHIL", "DAN HENG IMBIBITOR LUNAE"]:
        character = "imbibitor lunae"
    if character == "BHILL":
        character = "boothill"
    if character == "FEI XIAO":
        character = "feixiao"
    if character in ["FUGUE", "FUGUE TINGYUN"]:
        character = "nihility tingyun"
    if character in ["TOPAZ", "TOPAZ & NUMBY", "TOPAZ AND NUMBY", "TOPASS"]:
        character = "topaz numby"
    if character in ["SILVERWOLF", "SW", "WOLFIE", "SWOLF", "SILVER"]:
        character = "silver wolf"
    if character in ["THERTA", "MADAM HERTA"]:
        character = "the herta"
    if character in ["FF", "SAM"]:
        character = "firefly"
    if character == "BS":
        character = "black swan"
    if character == "AVEN":
        character = "aventurine"
    if character == "BLADIE":
        character = "blade"
    if character == "GEPPIE":
        character = "gepard"
    if character in ["GAMBLE", "MAHJONG", "CASINO"]:
        character = "qingque"
    if character == "RM":
        character = "ruan mei"
    if character in ["MONDAY", "SATURDAY"]:
        character = "sunday"
    if character in ["MARCH 8TH", "MARCH 8", "MARCH HUNT", "3/8"]:
        character = "hunt march"
    if character in ["MARCH 7TH", "MARCH 7", "3/7"]:
        character = "preservation march"
    if character in ["HTB", "HARMONY MC", "HMC", "HARMONY TB", "TRAILBLAZER HARMONY", "HATBLAZER", "HARMBLAZER"]:
        character = "harmony trailblazer"
    if character in ["PRESERVATION MC", "FIREBLAZER", "FMC", "FTB", "FIRE MC", "FIRE TB", "TRAILBLAZER PRESERVATION", "PTB"]:
        character = "preservation trailblazer"
    if character in ["DESTRUCTION MC", "DESTRUCTION TB", "PHYSICAL TRAILBLAZER", "TRAILBLAZER DESTRUCTION", "PHYS MC", "PHYS TB", "DMC", "DTB"]:
        character = "destruction trailblazer"
    if character in ["REMEMBRANCE MC", "REMEMBRANCE TB", "REMEMBRANCE TRAILBLAZER", "TRAILBLAZER REMEMBRANCE", "REMEM MC", "REMEM TB", "RMC", "RTB"]:
        character = "remembrance trailblazer"

    return character.lower()

def fix_rarity(rarity):
    """Formats rarity strings into star ratings."""
    if rarity in ["Feat_Four", "Stand_Four"]:
        return "★★★★"
    if rarity in ["Feat_Five", "Stand_Five"]:
        return "★★★★★"
    if rarity == "Feat_Epic":
        return "Epic"
    if rarity == "Feat_Leg":
        return "Legendary"
    return rarity

def chrono_image(chrono: int):
    """Returns a string of star emojis based on a number."""
    chrono_img_ids = [
        " ", ":star:", ":star::star:", ":star::star::star:", ":star::star::star::star:",
        ":star::star::star::star::star:", ":star2:", ":star2::star2:", ":star2::star2::star2:",
        ":star2::star2::star2::star2:", ":star2::star2::star2::star2::star2:"
    ]
    if 0 <= chrono < len(chrono_img_ids):
        return chrono_img_ids[chrono]
    return ""

# Classes for Banner Command
class BannerInfo:
    """Holds information about a single gacha banner."""
    def __init__(self, character_name: str, start_date: datetime, end_date: datetime, image_url: str, rarity: str = "5⭐", element: str = "", path: str = ""):
        self.character_name = character_name
        self.start_date = start_date
        self.end_date = end_date
        self.image_url = image_url
        self.rarity = rarity
        self.element = element
        self.path = path

    def get_time_until_start(self) -> str:
        """Get formatted time until banner starts."""
        now = datetime.now(timezone.utc)
        if self.start_date <= now:
            return "Available now"
        delta = self.start_date - now
        days, hours = delta.days, delta.seconds // 3600
        return f"{days} days, {hours} hours" if days > 0 else f"{hours} hours"

    def get_time_until_end(self) -> str:
        """Get formatted time until banner ends."""
        now = datetime.now(timezone.utc)
        if self.end_date <= now:
            return "Banner ended"
        delta = self.end_date - now
        days, hours = delta.days, delta.seconds // 3600
        return f"{days} days, {hours} hours" if days > 0 else f"{hours} hours"

class BannerView(discord.ui.View):
    """A Discord UI View to navigate between multiple banners."""
    def __init__(self, banners: List[BannerInfo], game_name: str):
        super().__init__(timeout=300)
        self.banners = banners
        self.current_index = 0
        self.game_name = game_name
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current index."""
        self.previous_button.disabled = self.current_index == 0
        self.next_button.disabled = self.current_index >= len(self.banners) - 1

    def create_embed(self) -> discord.Embed:
        """Create embed for the current banner."""
        banner = self.banners[self.current_index]
        embed = discord.Embed(title=f"{self.game_name} - Upcoming Banner", color=0x7289DA)
        
        character_info = f"{banner.rarity} {banner.character_name}"
        if banner.element: character_info += f" ({banner.element})"
        if banner.path: character_info += f" - {banner.path}"
        
        embed.add_field(name="Character", value=character_info, inline=False)
        embed.add_field(name="Start Date", value=f"{banner.start_date.strftime('%Y-%m-%d %H:%M UTC')}\n*{banner.get_time_until_start()}*", inline=True)
        embed.add_field(name="End Date", value=f"{banner.end_date.strftime('%Y-%m-%d %H:%M UTC')}\n*{banner.get_time_until_end()}*", inline=True)
        if banner.image_url: embed.set_image(url=banner.image_url)
        embed.set_footer(text=f"Banner {self.current_index + 1} of {len(self.banners)}")
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_index < len(self.banners) - 1:
            self.current_index += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.primary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

class BannerDataFetcher:
    """Handles fetching real banner data from various sources."""
    def __init__(self):
        self.session = None

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        if self.session:
            await self.session.close()

    def parse_date(self, date_str: str) -> datetime:
        """Parse various date formats into datetime objects."""
        formats = ["%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return datetime.now(timezone.utc)

    async def _fetch_and_process_banners(self, url: str, data_list: List[Dict], image_base_url: str, name_key: str, start_key: str, end_key: str, rarity_key: str, element_key: str, path_key: str, path_name: str) -> List[BannerInfo]:
        """Generic banner fetching logic."""
        banners = []
        for banner_data in data_list:
            image_url = image_base_url.format(name=banner_data[name_key].lower().replace(' ', '-'))
            banner = BannerInfo(
                character_name=banner_data[name_key],
                start_date=self.parse_date(banner_data[start_key]),
                end_date=self.parse_date(banner_data[end_key]),
                image_url=image_url,
                rarity=banner_data[rarity_key],
                element=banner_data.get(element_key, ""),
                path=banner_data.get(path_key, "")
            )
            banners.append(banner)
        return banners
    
    async def fetch_honkai_star_rail_banners(self) -> List[BannerInfo]:
        """Fetch real Honkai Star Rail banner data."""
        # This data would ideally be scraped or from an API. Using static data for now.
        current_banners = [
            {"name": "Cipher", "element": "Quantum", "path": "Nihility", "start": "June 11, 2025", "end": "July 1, 2025", "rarity": "5⭐"},
            {"name": "Phainon", "element": "Physical", "path": "Destruction", "start": "July 1, 2025", "end": "July 22, 2025", "rarity": "5⭐"},
        ]
        return await self._fetch_and_process_banners("", current_banners, "https://starrail.honeyhunterworld.com/img/character/{name}-character_gacha_result_bg.webp", 'name', 'start', 'end', 'rarity', 'element', 'path', 'Path')

    async def fetch_genshin_impact_banners(self) -> List[BannerInfo]:
        """Fetch Genshin Impact banner data."""
        upcoming_banners = [
            {"name": "Neuvillette", "element": "Hydro", "weapon": "Catalyst", "start": "July 5, 2025", "end": "July 26, 2025", "rarity": "5⭐"},
            {"name": "Xianyun", "element": "Anemo", "weapon": "Catalyst", "start": "July 26, 2025", "end": "August 16, 2025", "rarity": "5⭐"}
        ]
        return await self._fetch_and_process_banners("", upcoming_banners, "https://webstatic.hoyoverse.com/upload/event/2024/genshin/{name}.jpg", 'name', 'start', 'end', 'rarity', 'element', 'weapon', 'Weapon')

    async def fetch_zenless_zone_zero_banners(self) -> List[BannerInfo]:
        """Fetch Zenless Zone Zero banner data."""
        zzz_banners = [
             {"name": "Yixuan", "element": "Auric Ink", "specialty": "Rupture", "start": "July 16, 2025", "end": "August 6, 2025", "rarity": "S-Rank"},
             {"name": "Astra Yao", "element": "Ether", "specialty": "Support", "start": "July 16, 2025", "end": "August 6, 2025", "rarity": "S-Rank"}
        ]
        return await self._fetch_and_process_banners("", zzz_banners, "https://act.hoyoverse.com/app/mihoyo-zzz-game-record/images/{name}.jpg", 'name', 'start', 'end', 'rarity', 'element', 'specialty', 'Specialty')

    async def fetch_wuthering_waves_banners(self) -> List[BannerInfo]:
        """Fetch Wuthering Waves banner data."""
        ww_banners = [
            {"name": "Camellya", "element": "Havoc", "weapon": "Gauntlets", "start": "July 20, 2025", "end": "August 10, 2025", "rarity": "5⭐"}
        ]
        return await self._fetch_and_process_banners("", ww_banners, "https://wutheringwaves.kurogames.com/assets/images/{name}.jpg", 'name', 'start', 'end', 'rarity', 'element', 'weapon', 'Weapon')

    async def fetch_cookie_run_kingdom_banners(self) -> List[BannerInfo]:
        """Fetch Cookie Run Kingdom banner data."""
        crk_banners = [
            {"name": "Mystic Flour Cookie", "type": "Ancient", "class": "Magic", "start": "July 15, 2025", "end": "August 5, 2025", "rarity": "Ancient"}
        ]
        return await self._fetch_and_process_banners("", crk_banners, "https://cookierun-kingdom.fandom.com/wiki/File:{name}.png", 'name', 'start', 'end', 'rarity', 'type', 'class', 'Class')

# Main Cog
class Smart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banner_fetcher = BannerDataFetcher()

    async def cog_unload(self):
        await self.banner_fetcher.close_session()

    # --- UI Classes for Meta Command ---
    class MetaView(discord.ui.View):
        def __init__(self, bot, game, valid_options, sub_options, user):
            super().__init__(timeout=90)
            self.bot = bot
            self.game = game
            self.valid_options = valid_options
            self.sub_options = sub_options
            self.user = user
            self.mode_look = None
            self.add_item(Smart.ModeSelect(valid_options[game]))

        async def interaction_check(self, interaction: discord.Interaction):
            return interaction.user.id == self.user.id

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True

    class ModeSelect(discord.ui.Select):
        def __init__(self, options):
            formatted = [discord.SelectOption(label=opt, value=opt) for opt in options]
            super().__init__(placeholder="Choose a mode...", options=formatted)

        async def callback(self, interaction: discord.Interaction):
            view: Smart.MetaView = self.view
            mode = self.values[0]
            if mode in view.sub_options:
                view.clear_items()
                view.add_item(Smart.SubModeSelect(mode, view.sub_options[mode]))
            else:
                view.mode_look = mode
                view.stop()
            await interaction.response.edit_message(view=view)

    class SubModeSelect(discord.ui.Select):
        def __init__(self, parent_mode, options):
            self.parent_mode = parent_mode
            formatted = [discord.SelectOption(label=opt, value=opt) for opt in options]
            super().__init__(placeholder="Choose a sub-mode...", options=formatted)

        async def callback(self, interaction: discord.Interaction):
            view: Smart.MetaView = self.view
            view.mode_look = self.values[0]
            view.stop()
            await interaction.response.edit_message(view=view)
    
    # --- Commands ---
    @app_commands.command(name="meta", description="Check the current metas [hsr/crk/zzz]")
    async def meta(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom', 'Zenless Zone Zero']):
        member = interaction.user
        await interaction.response.defer(ephemeral=True)

        valid_options = {
            "Honkai: Star Rail": ['Memory of Chaos', 'Pure Fiction', 'Apocalyptic Shadow', 'General Tier List'],
            "Cookie Run Kingdom": ['Arena', 'Arcane Arena', 'Guild Boss', 'Alliance', 'Limited Time Mode', 'Story'],
            "Zenless Zone Zero": ['Deadly Assault', 'Shiyu Defense']
        }
        sub_options = {"Guild Boss" : ["RVD", "AOD", "LA"], "Story": ["..."]}

        view = self.MetaView(self.bot, game, valid_options, sub_options, member)
        await interaction.followup.send("Which would you like to learn more about?:", view=view, ephemeral=True)
        await view.wait()

        if not view.mode_look:
            return await interaction.followup.send("You didn't select a mode in time.", ephemeral=True)

        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT LINK1, LINK2, LINK3, LAST_EDIT, EDIT_AUTH FROM META WHERE GAME = %s and MODE = %s", (game, view.mode_look))
                data = await cursor.fetchone()
                if not data:
                    em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{view.mode_look} | {game}")
                    em.add_field(name="Will update soon!!!", value="Ping a guide or @sorakoi to remind us to work on this :)", inline=True)
                    em.set_footer(text="Brought to you by... discord.gg/nurture")
                    return await interaction.followup.send(embed=em, ephemeral=False)

                links = (data[0], data[1], data[2])
                edit_data = (data[3], data[4])
                em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=f"{view.mode_look} | {game}")
                em.set_thumbnail(url=interaction.user.guild.icon.url)

                if links[0]: em.add_field(name="First Team:", value=links[0], inline=True)
                if links[1]: em.add_field(name="Second Team:", value=links[1], inline=True)
                if links[2]: em.add_field(name="Third Team:", value=links[2], inline=True)
                
                last_edit = edit_data[0].strftime("%B %d, %Y")
                who_did_edit = edit_data[1]
                em.add_field(name=f"Last edited: {last_edit}", value= f"Edited by <@{who_did_edit}>", inline=False)
                em.set_footer(text="Brought to you by... discord.gg/nurture")
                await interaction.followup.send(embed=em, ephemeral=False)

    @discord.app_commands.checks.cooldown(5, 15)
    @app_commands.command(name="build", description="Check the optimal build for each character")
    async def build(self, interaction : discord.Interaction, game: Literal['HSR', 'CRK'], character: str):
        original_input = character
        character = character.lower().replace('caelus', 'trailblazer').replace('stelle', 'trailblazer')

        if game == "HSR":
            if character.upper() in ["TINGYUN", "MARCH", "TRAILBLAZER", "TB", "MC", "RACCOON", "TRASH", "TRASHBLAZER"]:
                return await interaction.response.send_message(f"'{character}' is ambiguous. Please specify the character's path (e.g., 'Harmony Tingyun').", ephemeral=True)
            
            character = cleanse_name(character)

            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT stats, trapri, bestlc, bestrelics, bestplanar, gear_mainstats, buildauthor, notes, name FROM HSR_BUILD WHERE name LIKE %s", f"%{character}%")
                    build_info = await cursor.fetchone()

            if not build_info:
                return await interaction.response.send_message(f"The character you entered, __**{original_input}**__, was not found. Please check the name and try again.", ephemeral=True)
            
            build_info = [info if info is not None and info != "" else "N/A" for info in build_info]

            em_title = f"__Ideal Build of:__ {build_info[8].title()}"
            if "topaz" in character: em_title = "__Ideal Build of:__ Topaz"
            em = discord.Embed(color=discord.Colour.from_rgb(78, 150, 94), title=em_title)
            
            em.add_field(name="Trace Priority:", value=build_info[1], inline=False)
            em.add_field(name="Best LCs:", value=build_info[2], inline=True)
            em.add_field(name="Best Relics:", value=build_info[3], inline=False)
            em.add_field(name="Best Planar Relics:", value=build_info[4], inline=True)
            em.add_field(name="Best Gear Mainstats:", value=build_info[5], inline=False)
            em.add_field(name="Recommended Stats:", value=build_info[0], inline=True)
            em.set_footer(text=f"Created by: {build_info[6].capitalize()} in discord.gg/nurture")
            em.set_thumbnail(url=interaction.user.guild.icon.url)

            # Set Image
            character_url_name = character.strip().replace(" ", "-")
            image_url = f"https://starrail.honeyhunterworld.com/img/character/{character_url_name}-character_gacha_result_bg.webp"
            # Add specific image exceptions here if needed
            em.set_image(url=image_url)

            await interaction.response.send_message(embed=em, ephemeral=False)

        elif game == "CRK":
            await interaction.response.send_message("CRK builds are still in development! Try again later!", ephemeral=True)

    @build.error
    async def on_build_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)
        else:
            await interaction.response.send_message("An unexpected error occurred. Please try again later.", ephemeral=True)
            print(f"Error in build command: {error}")

    @app_commands.command(name="upcoming", description="See how long until the next banner(s) arrive")
    async def upcoming(self, interaction: discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom', 'Zenless Zone Zero', 'Wuthering Waves', 'Genshin Impact']):
        await interaction.response.defer()
        
        banners = []
        fetcher_map = {
            'Honkai: Star Rail': self.banner_fetcher.fetch_honkai_star_rail_banners,
            'Genshin Impact': self.banner_fetcher.fetch_genshin_impact_banners,
            'Zenless Zone Zero': self.banner_fetcher.fetch_zenless_zone_zero_banners,
            'Wuthering Waves': self.banner_fetcher.fetch_wuthering_waves_banners,
            'Cookie Run Kingdom': self.banner_fetcher.fetch_cookie_run_kingdom_banners
        }
        
        if game in fetcher_map:
            banners = await fetcher_map[game]()

        if not banners:
            embed = discord.Embed(title="No Upcoming Banners Found", description=f"Could not fetch banner information for {game}.", color=0xFF0000)
            return await interaction.followup.send(embed=embed)
            
        now = datetime.now(timezone.utc)
        future_banners = sorted([b for b in banners if b.end_date > now], key=lambda x: x.start_date)

        if not future_banners:
            embed = discord.Embed(title="No Upcoming Banners", description=f"All announced banners for {game} have ended.", color=0xFFAA00)
            return await interaction.followup.send(embed=embed)
            
        view = BannerView(future_banners, game)
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="missing", description="See how close you are to ideal builds")
    async def missing(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom', 'Zenless Zone Zero']):
        await interaction.response.send_message("This command is under construction.", ephemeral=True)

    @app_commands.command(name="simulate", description="Mimic in-game gacha to see your luck")
    async def simulate(self, interaction : discord.Interaction, game: Literal['Honkai: Star Rail', 'Cookie Run Kingdom', 'Zenless Zone Zero']):
        await interaction.response.send_message("This command is under construction.", ephemeral=True)
