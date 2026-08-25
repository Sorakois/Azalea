import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import random
import json
import os
import asyncio
import logging

GIVEAWAYS_FILE = "giveaways.json"

def load_giveaways():
    """Loads giveaway data from the local JSON file."""
    if os.path.exists(GIVEAWAYS_FILE):
        try:
            with open(GIVEAWAYS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_giveaways(data):
    """Saves giveaway data to the local JSON file."""
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_time(duration_str):
    """Converts a string like '1h', '2d', or '30m' into seconds."""
    unit = duration_str[-1].lower()
    try:
        value = int(duration_str[:-1])
        if unit == 's': return value
        elif unit == 'm': return value * 60
        elif unit == 'h': return value * 3600
        elif unit == 'd': return value * 86400
        else: return int(duration_str) * 60 # Default to minutes
    except ValueError:
        return None

class CollabModal(discord.ui.Modal, title='Enter Collaboration Keys'):
    """Modal for Collab giveaways requiring secret keys."""
    home_key = discord.ui.TextInput(
        label='Home Server Key', 
        placeholder='Enter the key from our announcement...',
        required=True
    )
    partner_key = discord.ui.TextInput(
        label='Partner Server Key', 
        placeholder='Enter the key from their announcement...',
        required=True
    )
    
    def __init__(self, message_id: str, required_home: str, required_partner: str):
        super().__init__()
        self.message_id = message_id
        self.required_home = required_home
        self.required_partner = required_partner
        
    async def on_submit(self, interaction: discord.Interaction):
        # Verify keys (case-insensitive)
        if self.home_key.value.strip().upper() != self.required_home.upper() or \
           self.partner_key.value.strip().upper() != self.required_partner.upper():
            await interaction.response.send_message("❌ **Invalid keys.** Please check the announcements and try again!", ephemeral=True)
            return

        # Keys are correct, add user to JSON
        data = load_giveaways()
        if self.message_id not in data or data[self.message_id].get("ended", True):
            await interaction.response.send_message("⚠️ This giveaway has already ended or does not exist.", ephemeral=True)
            return
            
        entrants = data[self.message_id]["entrants"]
        user_id = interaction.user.id
        
        if user_id in entrants:
            await interaction.response.send_message("You are already entered in this giveaway!", ephemeral=True)
            return
            
        entrants.append(user_id)
        save_giveaways(data)
        
        await interaction.response.send_message("🎉 **Success!** Your keys were correct and you have been entered into the giveaway!", ephemeral=True)

class GiveawayJoinView(discord.ui.View):
    """Persistent view attached to all giveaway messages."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.blurple, custom_id="persistent_giveaway_join_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = str(interaction.message.id)
        data = load_giveaways()
        
        if message_id not in data:
            await interaction.response.send_message("This giveaway could not be found in the database.", ephemeral=True)
            return
            
        giveaway = data[message_id]
        
        if giveaway.get("ended", False):
            await interaction.response.send_message("This giveaway has already ended!", ephemeral=True)
            return
            
        user_id = interaction.user.id
        if user_id in giveaway["entrants"]:
            await interaction.response.send_message("You have already entered this giveaway!", ephemeral=True)
            return

        giveaway_type = giveaway.get("type", "general")

        # --- CHECK 1: GENERAL (Requires sending a message previously) ---
        if giveaway_type == "general":
            try:
                # Use the existing Leveling database connection to see if they are in the USER table
                async with self.bot.db.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT USER_ID FROM USER WHERE USER_ID = %s", (user_id,))
                        result = await cursor.fetchone()
                        
                        if not result:
                            await interaction.response.send_message(
                                "❌ **Requirement Not Met:** You must have sent at least one message in this server to join general giveaways!", 
                                ephemeral=True
                            )
                            return
            except Exception as e:
                logging.exception(f"DB Error checking user {user_id} for giveaway: {e}")
                await interaction.response.send_message("An error occurred checking your eligibility. Please try again.", ephemeral=True)
                return
                
            # Requirements met, add to JSON
            giveaway["entrants"].append(user_id)
            save_giveaways(data)
            await interaction.response.send_message("🎉 You have successfully entered the giveaway!", ephemeral=True)

        # --- CHECK 2: COLLAB (Requires Keys via Modal) ---
        elif giveaway_type == "collab":
            keys = giveaway.get("keys", ["", ""])
            modal = CollabModal(message_id=message_id, required_home=keys[0], required_partner=keys[1])
            # Send the modal to the user; the modal handles saving the entry on submit
            await interaction.response.send_modal(modal)

class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.giveaway_task.start()
        
    def cog_unload(self):
        self.giveaway_task.cancel()

    @tasks.loop(seconds=15)
    async def giveaway_task(self):
        """Checks the JSON file every 15 seconds to see if any giveaways have ended."""
        await self.bot.wait_until_ready()
        data = load_giveaways()
        current_time = int(datetime.datetime.utcnow().timestamp())
        changes_made = False

        for msg_id, g_data in data.items():
            if not g_data.get("ended", False) and current_time >= g_data["end_time"]:
                # The giveaway has ended
                channel = self.bot.get_channel(g_data["channel_id"])
                g_data["ended"] = True
                changes_made = True
                
                if not channel:
                    continue
                    
                try:
                    msg = await channel.fetch_message(int(msg_id))
                except discord.NotFound:
                    continue

                entrants = g_data["entrants"]
                winners_count = g_data["winners_count"]
                prize = g_data["prize"]

                if len(entrants) == 0:
                    await channel.send(f"Nobody entered the giveaway for **{prize}**! 😢")
                    # Update embed
                    em = msg.embeds[0]
                    em.description = f"Ended.\nHosted by: <@{msg.author.id}>\nWinners: None"
                    await msg.edit(embed=em, view=None)
                    continue

                # Pick winners
                winners_count = min(winners_count, len(entrants))
                winners = random.sample(entrants, winners_count)
                
                winner_mentions = ", ".join([f"<@{w}>" for w in winners])
                
                # Announce
                await msg.reply(f"🎉 Congratulations {winner_mentions}! You won **{prize}**!")
                
                # Update original message embed to show it's over
                em = msg.embeds[0]
                em.description = f"Ended.\nHosted by: <@{msg.author.id}>\nWinners: {winner_mentions}"
                em.color = discord.Color.dark_grey()
                await msg.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=em, view=None)

        if changes_made:
            save_giveaways(data)

async def setup(bot):
    # Register the persistent view so buttons work after bot restarts
    bot.add_view(GiveawayJoinView(bot))
    await bot.add_cog(Giveaways(bot))