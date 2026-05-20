#!/usr/bin/env python3
"""
Unified HoYoLab Auto Check-in System
Combines Discord bot functionality with multi-game standalone support
Performance optimized with async operations and connection pooling
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Literal, Optional, Dict, List
import aiohttp
import json
import hashlib
import time
import random
import string
import asyncio
import os
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameType(Enum):
    ZZZ = "zzz"
    GENSHIN = "gi"
    HSR = "hsr"
    HONKAI = "hi3"
    TOT = "tot"

@dataclass
class GameConfig:
    name: str
    display_name: str
    endpoint: str
    act_id: str
    sign_game_header: str

# Game configurations - centralized and optimized
GAME_CONFIGS = {
    GameType.ZZZ: GameConfig(
        name="zzz",
        display_name="Zenless Zone Zero",
        endpoint="https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/sign",
        act_id="e202406031448091",
        sign_game_header="zzz"
    ),
    GameType.GENSHIN: GameConfig(
        name="gi",
        display_name="Genshin Impact",
        endpoint="https://sg-hk4e-api.hoyolab.com/event/sol/sign",
        act_id="e202102251931481",
        sign_game_header="gi"
    ),
    GameType.HSR: GameConfig(
        name="hsr",
        display_name="Honkai: Star Rail",
        endpoint="https://sg-public-api.hoyolab.com/event/luna/os/sign",
        act_id="e202303301540311",
        sign_game_header="hsr"
    ),
    GameType.HONKAI: GameConfig(
        name="hi3",
        display_name="Honkai Impact 3rd",
        endpoint="https://sg-public-api.hoyolab.com/event/mani/sign",
        act_id="e202110291205111",
        sign_game_header="hi3"
    ),
    GameType.TOT: GameConfig(
        name="tot",
        display_name="Tears of Themis",
        endpoint="https://sg-public-api.hoyolab.com/event/luna/os/sign",
        act_id="e202202281857121",
        sign_game_header="tot"
    )
}

class HoYoLabAPI:
    """Optimized HoYoLab API client with connection pooling and rate limiting"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_common_headers(self, game_config: GameConfig) -> Dict[str, str]:
        """Get optimized headers for all requests"""
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://act.hoyolab.com',
            'Referer': 'https://act.hoyolab.com/',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'X-Rpc-Signgame': game_config.sign_game_header,
        }

    def _generate_ds_token(self, query: str = "", body: str = "") -> str:
        """Generate DS token for authentication (HSR specific)"""
        salt = "6s25p5ox5y14umn1p61aqyyvbvvl3lrt"
        timestamp = str(int(time.time()))
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        hash_content = f"salt={salt}&t={timestamp}&r={random_str}&b={body}&q={query}"
        hash_value = hashlib.md5(hash_content.encode('utf-8')).hexdigest()
        
        return f"{timestamp},{random_str},{hash_value}"

    async def check_in(self, game_type: GameType, cookies: str) -> Dict:
        """Perform check-in for specified game"""
        async with self._rate_limit:
            config = GAME_CONFIGS[game_type]
            
            # HSR uses different API structure
            if game_type == GameType.HSR:
                return await self._hsr_checkin(config, cookies)
            else:
                return await self._generic_checkin(config, cookies)

    async def _hsr_checkin(self, config: GameConfig, cookies: str) -> Dict:
        """HSR-specific check-in with proper headers and DS token"""
        try:
            # Use the exact endpoints from your original working code
            base_url = "https://sg-hk4e-api.hoyolab.com/event/luna/os"
            info_url = f"{base_url}/info"
            sign_url = f"{base_url}/sign"
            
            # Create query parameters for DS token generation
            query_params = f"lang=en&act_id={config.act_id}"
            
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json;charset=UTF-8',
                'Origin': 'https://act.hoyolab.com',
                'Referer': 'https://act.hoyolab.com/',
                'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'Cookie': cookies,
                'DS': self._generate_ds_token(query=query_params),
                'x-rpc-app_version': '2.34.1',
                'x-rpc-client_type': '4',
                'x-rpc-language': 'en-us'
            }
            
            # Debug logging
            logger.info(f"HSR Info URL: {info_url}?{query_params}")
            logger.info(f"DS Token: {headers['DS']}")
            
            # Get current sign info
            async with self.session.get(f"{info_url}?{query_params}", headers=headers) as response:
                logger.info(f"Info response status: {response.status}")
                
                if response.status == 404:
                    # If 404, try the alternative endpoint from index.js
                    logger.info("Trying alternative endpoint from index.js...")
                    alt_sign_url = "https://sg-public-api.hoyolab.com/event/luna/os/sign"
                    return await self._hsr_simple_signin(alt_sign_url, config, cookies)
                
                if response.status != 200:
                    return {"success": False, "error": "network_error", "message": f"HTTP {response.status}", "game": config.display_name}
                
                info_result = await response.json()
                logger.info(f"Info response: {info_result}")
                
                if info_result.get("retcode") != 0:
                    result = self._process_response(info_result, config.display_name)
                    result["debug_info"] = {
                        "retcode": info_result.get("retcode"),
                        "raw_message": info_result.get("message"),
                        "ds_token": headers['DS']
                    }
                    return result
                
                sign_info = info_result.get("data", {})
                is_signed = sign_info.get("is_sign", False)
                total_sign_day = sign_info.get("total_sign_day", 0)
                
                # Check if already signed in today
                if is_signed:
                    return {
                        "success": True,
                        "already_signed": True,
                        "message": "Already checked in today!",
                        "total_sign_day": total_sign_day,
                        "game": config.display_name
                    }
            
            # Perform the sign-in
            sign_data = {
                "act_id": config.act_id,
                "lang": "en"
            }
            
            body = json.dumps(sign_data, separators=(',', ':'))
            headers['DS'] = self._generate_ds_token(body=body)
            
            logger.info(f"Sign URL: {sign_url}")
            
            async with self.session.post(sign_url, headers=headers, data=body) as response:
                logger.info(f"Sign response status: {response.status}")
                
                if response.status != 200:
                    return {"success": False, "error": "network_error", "message": f"HTTP {response.status}", "game": config.display_name}
                
                result = await response.json()
                logger.info(f"Sign response: {result}")
                
                if result.get("retcode") == 0:
                    return {
                        "success": True,
                        "already_signed": False,
                        "message": "Successfully checked in!",
                        "total_sign_day": total_sign_day + 1,
                        "game": config.display_name
                    }
                else:
                    return self._process_response(result, config.display_name)
                    
        except Exception as e:
            logger.error(f"HSR check-in exception: {str(e)}")
            return {
                "success": False,
                "error": "network_error",
                "message": f"Network error: {str(e)}",
                "game": config.display_name
            }

    async def _hsr_simple_signin(self, sign_url: str, config: GameConfig, cookies: str) -> Dict:
        """Fallback simple sign-in method matching index.js style"""
        try:
            logger.info(f"Using simple sign-in method: {sign_url}")
            
            # Debug cookie parsing
            cookie_parts = cookies.split(';')
            logger.info(f"Cookie parts count: {len(cookie_parts)}")
            for i, part in enumerate(cookie_parts):
                if '=' in part:
                    key, value = part.strip().split('=', 1)
                    logger.info(f"Cookie {i}: {key} = {value[:20]}...")
            
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br, zstd', 
                'accept-language': 'en-US,en;q=0.6',
                'connection': 'keep-alive',
                'origin': 'https://act.hoyolab.com',
                'referer': 'https://act.hoyolab.com',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': cookies,
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
                'sec-ch-ua-mobile': '?0', 
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'sec-gpc': '1',
                'x-rpc-signgame': 'hsr',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
            
            body = json.dumps({
                'lang': 'en-us',
                'act_id': config.act_id
            })
            
            url_with_params = f"{sign_url}?act_id={config.act_id}&lang=en-us"
            logger.info(f"Simple sign-in URL: {url_with_params}")
            
            async with self.session.post(url_with_params, headers=headers, data=body) as response:
                logger.info(f"Simple sign response status: {response.status}")
                
                if response.status != 200:
                    return {"success": False, "error": "network_error", "message": f"HTTP {response.status}", "game": config.display_name}
                
                result = await response.json()
                logger.info(f"Simple sign response: {result}")
                
                return self._process_response(result, config.display_name)
                
        except Exception as e:
            logger.error(f"Simple HSR sign-in exception: {str(e)}")
            return {
                "success": False,
                "error": "network_error", 
                "message": f"Network error: {str(e)}",
                "game": config.display_name
            }

    async def _generic_checkin(self, config: GameConfig, cookies: str) -> Dict:
        """Generic check-in for non-HSR games"""
        try:
            headers = self._get_common_headers(config)
            headers['Cookie'] = cookies
            
            body_data = json.dumps({
                "act_id": config.act_id,
                "lang": "en-us"
            })

            url = f"{config.endpoint}?act_id={config.act_id}&lang=en-us"
            async with self.session.post(url, headers=headers, data=body_data) as response:
                result = await response.json()
                return self._process_response(result, config.display_name)
                
        except Exception as e:
            return {
                "success": False,
                "error": "network_error", 
                "message": f"Network error: {str(e)}",
                "game": config.display_name
            }

    def _process_response(self, result: Dict, game_name: str) -> Dict:
        """Process API response and standardize format"""
        retcode = result.get("retcode", -1)
        
        response = {
            "game": game_name,
            "retcode": retcode,
            "raw_message": result.get("message", "Unknown error")
        }
        
        if retcode == 0:
            response.update({
                "success": True,
                "message": "Successfully checked in!",
                "already_signed": False
            })
        elif retcode == -5003:
            response.update({
                "success": True,
                "message": "Already checked in today",
                "already_signed": True
            })
        elif retcode == -100:
            response.update({
                "success": False,
                "error": "invalid_cookies",
                "message": "Invalid cookies. Please update your authentication."
            })
        elif retcode == -10002:
            response.update({
                "success": False,
                "error": "game_not_found",
                "message": "You haven't played this game or it's not bound to your account."
            })
        else:
            response.update({
                "success": False,
                "error": "unknown_error",
                "message": f"Unknown error (code: {retcode})"
            })
            
        return response

    async def batch_check_in(self, games: List[GameType], cookies: str) -> List[Dict]:
        """Perform batch check-ins with optimized concurrency"""
        tasks = [self.check_in(game, cookies) for game in games]
        return await asyncio.gather(*tasks, return_exceptions=True)

class StandaloneRunner:
    """Standalone runner for environment-based execution"""
    
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK')
        self.discord_user = os.getenv('DISCORD_USER')
        self.cookies = self._parse_env_list('COOKIE')
        self.games = self._parse_env_list('GAMES')
        self.messages = []
        self.has_errors = False

    def _parse_env_list(self, env_name: str) -> List[str]:
        """Parse environment variable as list"""
        value = os.getenv(env_name, '')
        return [s.strip() for s in value.split('\n') if s.strip()]

    def _parse_games(self, game_string: str) -> List[GameType]:
        """Parse game string to GameType list"""
        games = []
        for game_name in game_string.split():
            try:
                games.append(GameType(game_name.lower()))
            except ValueError:
                self.log('error', f"Invalid game: {game_name}")
        return games

    def log(self, level: str, *args):
        """Custom logging with message storage"""
        message = ' '.join(str(arg) for arg in args)
        logger.log(getattr(logging, level.upper()), message)
        
        if level == 'error':
            self.has_errors = True
            
        if level != 'debug':
            self.messages.append({
                'type': level,
                'message': message
            })

    async def send_discord_webhook(self):
        """Send results to Discord webhook"""
        if not self.webhook_url or not self.webhook_url.startswith('https://discord.com/api/webhooks/'):
            self.log('error', 'Invalid Discord webhook URL')
            return

        content = ""
        if self.discord_user:
            content += f"<@{self.discord_user}>\n"
        
        content += "\n".join(f"({msg['type'].upper()}) {msg['message']}" for msg in self.messages)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json={'content': content}) as response:
                    if response.status == 204:
                        self.log('info', 'Discord webhook sent successfully')
                    else:
                        self.log('error', 'Failed to send Discord webhook')
            except Exception as e:
                self.log('error', f'Discord webhook error: {str(e)}')

    async def run(self):
        """Main execution method for standalone mode"""
        if not self.cookies:
            raise ValueError("COOKIE environment variable not set!")
        if not self.games:
            raise ValueError("GAMES environment variable not set!")

        async with HoYoLabAPI() as api:
            for i, cookie in enumerate(self.cookies):
                self.log('info', f"-- CHECKING ACCOUNT {i + 1} --")
                
                # Get games for this account (or use default)
                account_games = self.games[i] if i < len(self.games) else self.games[0]
                game_types = self._parse_games(account_games)
                
                results = await api.batch_check_in(game_types, cookie)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.log('error', f"Unexpected error: {str(result)}")
                        continue
                        
                    game = result['game']
                    if result['success']:
                        status = "already checked in" if result['already_signed'] else "checked in successfully"
                        self.log('info', f"{game}: {status}")
                    else:
                        self.log('error', f"{game}: {result['message']}")

        # Send Discord notification if configured
        if self.webhook_url:
            await self.send_discord_webhook()

        if self.has_errors:
            raise RuntimeError("One or more check-ins failed")

class AutomationCog(commands.Cog):
    """Discord bot cog for interactive check-ins"""
    
    def __init__(self, bot):
        self.bot = bot
        self.api_sessions = {}  # Cache API sessions per user

    async def get_user_cookies(self, user_id: int, game_type: GameType) -> Optional[str]:
        """Get user cookies from database"""
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                column_map = {
                    GameType.HSR: "HSR_COOKIES",
                    GameType.GENSHIN: "GI_COOKIES", 
                    GameType.ZZZ: "ZZZ_COOKIES",
                    GameType.HONKAI: "HI3_COOKIES",
                    GameType.TOT: "TOT_COOKIES"
                }
                
                column = column_map.get(game_type)
                if not column:
                    return None
                    
                await cursor.execute(f"SELECT {column} FROM USER WHERE USER_ID = %s", (user_id,))
                result = await cursor.fetchone()
                return result[0] if result else None

    @app_commands.command(name="automate", description="Automate daily check-ins for HoYoLab games")
    async def automate(self, interaction: discord.Interaction, 
                      game: Literal["hsr", "genshin", "zzz", "honkai", "tot", "all"]):
        """Perform automated check-ins"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            game_types = []
            if game == "all":
                game_types = list(GameType)
            else:
                game_types = [GameType(game)]

            async with HoYoLabAPI() as api:
                results = []
                missing_cookies = []
                
                for game_type in game_types:
                    cookies = await self.get_user_cookies(interaction.user.id, game_type)
                    if not cookies:
                        missing_cookies.append(GAME_CONFIGS[game_type].display_name)
                        continue
                        
                    result = await api.check_in(game_type, cookies)
                    results.append(result)
                
                # Create response embed
                embed = discord.Embed(
                    title="🎮 HoYoLab Check-in Results",
                    color=0x00ff00 if all(r.get('success', False) for r in results) else 0xff9900
                )
                
                for result in results:
                    game_name = result['game']
                    if result['success']:
                        status = "✅ Already checked in" if result['already_signed'] else "✅ Check-in successful"
                        embed.add_field(name=game_name, value=status, inline=False)
                    else:
                        error_msg = f"❌ {result['message']}"
                        # Add debug info if available
                        if 'debug_info' in result:
                            debug = result['debug_info']
                            error_msg += f"\n**Debug:** RetCode: {debug.get('retcode')}, Raw: {debug.get('raw_message', 'N/A')}"
                        embed.add_field(name=game_name, value=error_msg, inline=False)
                
                if missing_cookies:
                    embed.add_field(
                        name="⚠️ Missing Setup", 
                        value=f"No cookies found for: {', '.join(missing_cookies)}\nRun `/setup` to configure.",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="setup", description="Setup cookies for HoYoLab games")
    async def setup(self, interaction: discord.Interaction,
                   game: Literal["hsr", "genshin", "zzz", "honkai", "tot"]):
        """Setup game cookies"""
        game_type = GameType(game)
        config = GAME_CONFIGS[game_type]
        
        # Check existing setup
        existing_cookies = await self.get_user_cookies(interaction.user.id, game_type)
        
        embed = discord.Embed(
            title=f"🔧 {config.display_name} Setup",
            description=f"To automate {config.display_name} daily check-ins, I need your complete HoYoLAB cookie string.\n\n"
                       "**New Method (Recommended):**\n"
                       "1. Go to [HoYoLAB](https://www.hoyolab.com/accountCenter/postList)\n"
                       "2. Press **F12** → **Console** tab\n"
                       "3. Type: `document.cookie` and press Enter\n"
                       "4. **Copy the entire output** (everything in quotes)\n"
                       "5. Paste it in the setup modal\n\n"
                       "**Alternative Method:**\n"
                       "• F12 → Application → Cookies → hoyolab.com\n"
                       "• Copy ALL cookies as: `name1=value1; name2=value2; ...`\n\n"
                       f"{'**Current status:** ✅ Configured' if existing_cookies else '**Current status:** ❌ Not configured'}",
            color=0x3498db
        )
        
        view = CookieSetupView(self.bot, game_type, bool(existing_cookies))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @tasks.loop(hours=24)
    async def auto_daily_checkin(self):
        """Automated daily check-in task"""
        logger.info("Starting automated daily check-ins")
        
        # Get all users with cookies from database
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT USER_ID, HSR_COOKIES, GI_COOKIES, ZZZ_COOKIES, HI3_COOKIES, TOT_COOKIES FROM USER")
                users = await cursor.fetchall()
        
        async with HoYoLabAPI() as api:
            for user_data in users:
                user_id = user_data[0]
                cookies_data = user_data[1:6]  # All cookie columns
                
                for i, game_type in enumerate(GameType):
                    if cookies_data[i]:  # If user has cookies for this game
                        try:
                            result = await api.check_in(game_type, cookies_data[i])
                            logger.info(f"User {user_id} - {result['game']}: {result['message']}")
                        except Exception as e:
                            logger.error(f"Auto check-in failed for user {user_id}, game {game_type.value}: {str(e)}")

class CookieSetupView(discord.ui.View):
    """View for cookie setup interaction"""
    
    def __init__(self, bot, game_type: GameType, is_update=False):
        super().__init__(timeout=300)
        self.bot = bot
        self.game_type = game_type
        self.is_update = is_update

    @discord.ui.button(label="Enter Cookies", style=discord.ButtonStyle.primary, emoji="🍪")
    async def enter_cookies(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CookieModal(self.bot, self.game_type, self.is_update)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Test Current Setup", style=discord.ButtonStyle.secondary, emoji="🧪")
    async def test_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_update:
            await interaction.response.send_message("❌ No cookies to test! Please enter your cookies first.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        # Get current cookies and test them
        cookies = await self.get_user_cookies(interaction.user.id, self.game_type)
        
        if not cookies:
            await interaction.followup.send("❌ No cookies found in database.", ephemeral=True)
            return
        
        # Test the cookies
        async with HoYoLabAPI() as api:
            result = await api.check_in(self.game_type, cookies)
        
        if result.get("success") or result.get("already_signed"):
            embed = discord.Embed(
                title="✅ Cookie Test Successful",
                description="Your cookies are working correctly!",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="❌ Cookie Test Failed",
                description=f"Error: {result.get('message', 'Unknown error')}",
                color=0xff0000
            )
            embed.add_field(name="Solution", value="Your cookies may have expired. Click 'Enter Cookies' to update them.", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def get_user_cookies(self, user_id: int, game_type: GameType) -> Optional[str]:
        """Get user cookies from database"""
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                column_map = {
                    GameType.HSR: "HSR_COOKIES",
                    GameType.GENSHIN: "GI_COOKIES", 
                    GameType.ZZZ: "ZZZ_COOKIES",
                    GameType.HONKAI: "HI3_COOKIES",
                    GameType.TOT: "TOT_COOKIES"
                }
                
                column = column_map.get(game_type)
                if not column:
                    return None
                    
                await cursor.execute(f"SELECT {column} FROM USER WHERE USER_ID = %s", (user_id,))
                result = await cursor.fetchone()
                return result[0] if result else None

class CookieModal(discord.ui.Modal, title="HoYoLab Cookie Setup"):
    """Modal for entering cookies"""
    
    def __init__(self, bot, game_type: GameType, is_update=False):
        super().__init__()
        self.bot = bot
        self.game_type = game_type
        self.is_update = is_update
        
        # Update title based on game
        config = GAME_CONFIGS[game_type]
        self.title = f"{config.display_name} Cookie Setup"

    full_cookie_string = discord.ui.TextInput(
        label="Complete Cookie String",
        placeholder="Paste the ENTIRE cookie string from document.cookie here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    # Remove the old individual cookie fields - they're no longer needed

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        cookie_string = self.full_cookie_string.value.strip()
        
        # Basic validation
        if not cookie_string:
            await interaction.followup.send("❌ Cookie string is required!", ephemeral=True)
            return
        
        # Check if it looks like a cookie string
        if '=' not in cookie_string:
            await interaction.followup.send("❌ Invalid cookie format. Please paste the complete cookie string from your browser.", ephemeral=True)
            return
        
        # Test cookies before saving
        async with HoYoLabAPI() as api:
            test_result = await api.check_in(self.game_type, cookie_string)
        
        if not test_result.get("success") and not test_result.get("already_signed"):
            # If test failed, show error but still offer to save
            embed = discord.Embed(
                title="⚠️ Cookie Validation Warning",
                description=f"Cookie test failed: {test_result.get('message', 'Unknown error')}\n\n"
                           "This might be because:\n"
                           "• Cookies are invalid or expired\n"
                           "• HoYoLAB is temporarily unavailable\n"
                           f"• You haven't bound {GAME_CONFIGS[self.game_type].display_name} to your HoYoLAB account\n\n"
                           "Do you still want to save these cookies?",
                color=0xff9900
            )
            view = ConfirmSaveView(self.bot, self.game_type, cookie_string, interaction.user.id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            return
        
        # Cookies work, save them
        try:
            await self.save_cookies(interaction.user.id, cookie_string)
            
            # Success message
            embed = discord.Embed(
                title="✅ Setup Complete!",
                description=f"Your {GAME_CONFIGS[self.game_type].display_name} cookies have been saved successfully!\n\n"
                           f"You can now use `/automate {self.game_type.value}` to automatically check in daily.",
                color=0x00ff00
            )
            
            if test_result.get("already_signed"):
                embed.add_field(name="Status", value="✅ Already checked in today", inline=False)
            elif test_result.get("success"):
                embed.add_field(name="Status", value="✅ Check-in completed during setup", inline=False)
            
            embed.set_footer(text="💡 Tip: You can update your cookies anytime by running this setup again")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Failed to save cookies: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def save_cookies(self, user_id: int, cookie_string: str):
        """Save cookies to database"""
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cursor:
                column_map = {
                    GameType.HSR: "HSR_COOKIES",
                    GameType.GENSHIN: "GI_COOKIES", 
                    GameType.ZZZ: "ZZZ_COOKIES",
                    GameType.HONKAI: "HI3_COOKIES",
                    GameType.TOT: "TOT_COOKIES"
                }
                
                column = column_map.get(self.game_type)
                if not column:
                    raise ValueError(f"Unsupported game type: {self.game_type}")
                
                # Check if user exists, insert or update accordingly
                await cursor.execute("SELECT USER_ID FROM USER WHERE USER_ID = %s", (user_id,))
                user_exists = await cursor.fetchone()
                
                if user_exists:
                    await cursor.execute(f"UPDATE USER SET {column} = %s WHERE USER_ID = %s", 
                                       (cookie_string, user_id))
                else:
                    await cursor.execute(f"INSERT INTO USER (USER_ID, {column}) VALUES (%s, %s)", 
                                       (user_id, cookie_string))
                
                await conn.commit()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(error)}",
            color=0xff0000
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfirmSaveView(discord.ui.View):
    """View for confirming cookie save when validation fails"""
    
    def __init__(self, bot, game_type: GameType, cookie_string: str, user_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.game_type = game_type
        self.cookie_string = cookie_string
        self.user_id = user_id

    @discord.ui.button(label="Save Anyway", style=discord.ButtonStyle.danger)
    async def save_anyway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            modal = CookieModal(self.bot, self.game_type)
            await modal.save_cookies(self.user_id, self.cookie_string)
            
            embed = discord.Embed(
                title="✅ Cookies Saved",
                description="Your cookies have been saved despite the validation warning.\n\n"
                           f"You can test them later with `/setup {self.game_type.value}` → 'Test Current Setup'",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Failed to save cookies: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_save(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Setup Cancelled",
            description="Cookies were not saved. Please check your cookie values and try again.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Enhanced Automation cog that extends/replaces the existing one
class EnhancedAutomation(AutomationCog):
    """Enhanced automation cog that includes both old HSR functionality and new multi-game support"""
    
    def __init__(self, bot):
        super().__init__(bot)
        # If you want to preserve any methods from your existing Automation class,
        # you can add them here or merge them

# Setup function for Discord bot integration
async def setup(bot):
    """Setup function for adding cogs to existing bot"""
    await bot.add_cog(AutomationCog(bot))

# Standalone execution function
async def run_standalone():
    """Standalone execution function for direct script running"""
    logger.info("Starting standalone mode")
    runner = StandaloneRunner()
    await runner.run()

# Direct execution support (if needed)
if __name__ == "__main__":
    asyncio.run(run_standalone())