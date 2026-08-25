import discord
from discord import app_commands
from discord.ext import commands
import datetime
import logging

class Partners(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # --- ACTIVE COLLABORATIONS ---
        # Add new collabs to this dictionary as needed.
        # The bot will match the user's input keys to the correct collab automatically.
        self.ACTIVE_COLLABS = {
            "PAIN_WORKSHOP": {
                "home": "NURTUREPAIN",
                "partner": "PAINFULCOLLAB",
                "start": datetime.datetime(2026, 8, 20, 0, 0, 0),
                "end": datetime.datetime(2026, 8, 31, 23, 59, 59),
                "xp_active": 2000,
                "xp_late": 200
            },
        }

    @app_commands.command(name="collab_claim", description="Claim your limited-time collaboration reward!")
    @app_commands.describe(
        home_key="The secret key found in our server announcement",
        partner_key="The secret key found in the partner server announcement"
    )
    async def collab_claim(self, interaction: discord.Interaction, home_key: str, partner_key: str):
        """
        Validates both keys against active collabs, ensures one-time claim per collab,
        applies XP reward, and computes level-ups/role updates.
        """
        home_input = home_key.strip().upper()
        partner_input = partner_key.strip().upper()
        
        matched_collab_id = None
        collab_data = None
        
        # 1. Check if the keys match ANY of our active collabs
        for c_id, c_info in self.ACTIVE_COLLABS.items():
            if home_input == c_info["home"].upper() and partner_input == c_info["partner"].upper():
                matched_collab_id = c_id
                collab_data = c_info
                break
                
        if not matched_collab_id:
            await interaction.response.send_message(
                "❌ **Invalid keys.** Make sure you have entered the exact keys from both announcements!", 
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        current_time = datetime.datetime.utcnow()
        
        # 2. Determine reward amount based on the matched collab's timeframe
        if collab_data["start"] <= current_time <= collab_data["end"]:
            xp_reward = collab_data["xp_active"]
            time_status = "active"
        else:
            xp_reward = collab_data["xp_late"]
            time_status = "late"

        try:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Create a new robust tracking table that includes COLLAB_ID
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS COLLAB_REWARDS (
                            USER_ID BIGINT,
                            COLLAB_ID VARCHAR(50),
                            CLAIMED_AT DATETIME,
                            PRIMARY KEY (USER_ID, COLLAB_ID)
                        )
                    """)
                    
                    # Prevent duplicate claims for THIS SPECIFIC collab
                    await cursor.execute(
                        "SELECT USER_ID FROM COLLAB_REWARDS WHERE USER_ID = %s AND COLLAB_ID = %s", 
                        (user_id, matched_collab_id)
                    )
                    if await cursor.fetchone():
                        await interaction.response.send_message(
                            f"⚠️ You have already claimed the XP reward for the **{matched_collab_id}** collaboration!", 
                            ephemeral=True
                        )
                        return

                    # Record this specific claim
                    await cursor.execute(
                        "INSERT INTO COLLAB_REWARDS (USER_ID, COLLAB_ID, CLAIMED_AT) VALUES (%s, %s, %s)", 
                        (user_id, matched_collab_id, current_time.strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    
                    # Fetch current user XP and Level
                    await cursor.execute("SELECT USER_LEVEL, USER_XP FROM USER WHERE USER_ID = %s", (user_id,))
                    user_data_db = await cursor.fetchone()
                    
                    if not user_data_db:
                        current_level = 1
                        current_xp = 0
                        await cursor.execute(
                            "INSERT INTO USER (USER_ID, USER_LEVEL, USER_XP) VALUES (%s, %s, %s)", 
                            (user_id, current_level, current_xp)
                        )
                    else:
                        current_level, current_xp = user_data_db

                    # Calculate new XP and handle multiple level-ups
                    total_xp = current_xp + xp_reward
                    initial_level = current_level
                    
                    while True:
                        next_level_req = 12 * (current_level ** 2) + 60
                        if total_xp >= next_level_req:
                            total_xp -= next_level_req
                            current_level += 1
                        else:
                            break
                    
                    # Save updated Level and XP
                    await cursor.execute(
                        "UPDATE USER SET USER_LEVEL = %s, USER_XP = %s WHERE USER_ID = %s",
                        (current_level, total_xp, user_id)
                    )
                    await conn.commit()

            # 3. Post-Database Level & Role Updates
            leveling_cog = self.bot.get_cog("Leveling")
            if current_level > initial_level and leveling_cog:
                # Announce level up in the designated level up channel
                levelup_chan = self.bot.get_channel(leveling_cog.levelUpChannel)
                if levelup_chan:
                    await levelup_chan.send(
                        f"🎉 {interaction.user.mention} leveled up from level **{initial_level}** to **{current_level}** by claiming a collaboration reward!"
                    )

                # Update server roles if highest level changed or tier was crossed
                async with self.bot.db.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT MAX(USER_LEVEL) FROM USER")
                        highest_level_res = await cursor.fetchone()
                        highest_level = highest_level_res[0] if highest_level_res else current_level

                await leveling_cog.assign_role(interaction.user, current_level, highest_level, interaction.guild)

            # 4. Respond to user
            if time_status == "active":
                msg = f"🎉 **Collab Reward Claimed!** You received **{xp_reward} XP**!"
            else:
                msg = f"✅ **Keys Accepted!** The main event has ended, but you received a late claim reward of **{xp_reward} XP**."
                
            if current_level > initial_level:
                msg += f"\n🆙 You leveled up to **Level {current_level}**!"

            await interaction.response.send_message(msg, ephemeral=True)

        except Exception as e:
            logging.exception(f"Error in collab_claim for user {user_id}: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your reward. Please contact an admin.", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Partners(bot))