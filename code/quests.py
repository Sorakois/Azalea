import discord
from discord.ext import commands
import logging
import textwrap
import datetime
from typing import Set

class QuestSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.helper_roles = [
            1160999588048683070, # test

            1138170342498648064, # crk helper
            1144445141529145355, # crob helper
            1370468801774227679, # crob wc/toa helper

            1241410436662820905, # hsr helper
            1352691719069634631, # zzz helper
            1310385836012863518, # wuwa helper
            1310385900865196092  # genshin helper
        ]
        self.active_quests: Set[int] = set()
        self.quest_participants: dict = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listen for messages that mention helper roles and start quests
        Also handle quest participation
        """
        if message.author.bot:
            return
            
        # Check if this is a response to an active quest
        if message.reference and message.reference.message_id in self.active_quests:
            await self.handle_quest_participation(message)
            return
            
        # Check if helper roles are mentioned
        if self.helper_roles and message.role_mentions:
            mentioned_role_ids = [role.id for role in message.role_mentions]
            if any(role_id in self.helper_roles for role_id in mentioned_role_ids):
                await self.start_quest(message)

    async def start_quest(self, original_message: discord.Message):
        """
        Starts a quest, forwarding any images or videos.
        """
        try:
            content = original_message.content

            # role objects for the message creation
            mentioned_roles = original_message.role_mentions
            for role in mentioned_roles:
                content = content.replace(f'<@&{role.id}>', '').strip()
                
            quest_content = content or "Help needed!"

            # pings all mentioned roles from the original message.
            def _create_message(text, author_mention, roles_to_ping):
                pings = ' '.join([role.mention for role in roles_to_ping])
                
                lines = [
                    f"# **NEW QUEST** <:swordge:1388933538044313662>\n",
                    f"### {pings}\n", 
                    "-----------------------------------------------\n",
                    *textwrap.wrap(text, width=50),
                    "",
                    "-----------------------------------------------",
                    "# <a:NOTICE:1388934793198174381> **REPLY TO THIS MSG TO HELP!**\n",
                    f"__**Requested by:**__ {author_mention}",
                    "__**Reward:**__ 1 <:ticket:1382853326080839701> to each helper!\n",
                    "*(Rewards are available for 24 hours)*"
                ]
                message_body = "\n".join(lines)
                return f"\n{message_body}\n"

            quest_message = _create_message(quest_content, original_message.author.mention, mentioned_roles)
            
            if len(quest_message) > 4000:
                await original_message.channel.send("Quest content is too long to display.")
                return

            files_to_send = []
            if original_message.attachments:
                logging.info(f"Found {len(original_message.attachments)} attachments to forward.")
                for attachment in original_message.attachments:
                    try:
                        files_to_send.append(await attachment.to_file())
                    except discord.HTTPException as e:
                        logging.error(f"Failed to process attachment {attachment.url}: {e}")
                        await original_message.channel.send(f"⚠️ Could not re-upload attachment: `{attachment.filename}`")

            quest_msg = await original_message.channel.send(
                content=quest_message,
                files=files_to_send
            )
            
            self.active_quests.add(quest_msg.id)
            self.quest_participants[quest_msg.id] = {
                'author_id': original_message.author.id,
                'participants': set(),
                'channel_id': original_message.channel.id,
                'guild_id': original_message.guild.id if original_message.guild else None
            }
            
            try:
                await original_message.delete()
            except discord.HTTPException as e:
                logging.warning(f"Could not delete original quest message (ID: {original_message.id}): {e}")

            logging.info(f"Quest {quest_msg.id} started by {original_message.author} in channel {original_message.channel.id}")

        except Exception as e:
            logging.error(f"Error in start_quest: {e}", exc_info=True)

    async def handle_quest_participation(self, response_message: discord.Message):
        """
        Handles a user's reply to an active quest, checking the quest's age.
        """
        quest_id = response_message.reference.message_id
        quest_data = self.quest_participants.get(quest_id)

        if not quest_data:
            return

        responder_id = response_message.author.id
        author_id = quest_data['author_id']

        # Prevent the quest author from participating in their own quest
        if responder_id == author_id:
            return
            
        # Prevent a user from participating multiple times
        if responder_id in quest_data['participants']:
            return
        
        # Add a reaction to the user's reply message 
        try:
            # You can use any standard emoji or a custom one your bot has access to
            await response_message.add_reaction('✅')
        except discord.Forbidden:
            logging.warning(f"Bot does not have permission to add reactions in channel {response_message.channel.id}")
        except Exception as e:
            logging.error(f"Failed to add reaction: {e}")

            
        # Check if the quest is older than 24 hours
        try:
            # Fetch the original quest message to get its creation time
            quest_msg = await response_message.channel.fetch_message(quest_id)
            now = datetime.datetime.now(datetime.timezone.utc)
            quest_age = now - quest_msg.created_at
            
            is_expired = quest_age > datetime.timedelta(hours=24)

        except discord.NotFound:
            logging.warning(f"Could not find original quest message {quest_id}. Cannot check age.")
            # Decide what to do if the message is deleted. Safest to assume no rewards.
            is_expired = True
        except Exception as e:
            logging.error(f"Error checking quest age for message {quest_id}: {e}")
            is_expired = True # Fail safe

        # Add participant to the set
        quest_data['participants'].add(responder_id)

        # Notify the quest author via DM (this happens regardless of expiration)
        await self.notify_quest_author(author_id, response_message.author, response_message)

        # Award ticket only if the quest is NOT expired
        if not is_expired:
            ticket = 1  # Define your reward amount
            success = await self.award_gems(responder_id, ticket)
            if success:
                logging.info(f"Awarded ticket to {response_message.author} for participating in quest {quest_id}")
        else:
            logging.info(f"Quest {quest_id} is older than 24 hours. No rewards given to {response_message.author}.")

    async def notify_quest_author(self, author_id: int, responder: discord.Member, response_message: discord.Message):
        """
        Send a DM to the quest author notifying them of a response.
        """
        try:
            quest_author = self.bot.get_user(author_id) or await self.bot.fetch_user(author_id)
            if not quest_author:
                logging.error(f"Could not find user with ID {author_id} to send DM")
                return
            
            message_link = response_message.jump_url
            
            dm_message = (
                f"<a:NOTICE:1388934793198174381> **Quest Update!** \n\n"
                f"**{responder.display_name}** has responded to your help request!\n\n"
                f"Come see [here]({message_link})"
            )
            
            await quest_author.send(dm_message)
            logging.info(f"DM notification sent to {quest_author} (ID: {author_id}) about response from {responder}")
            
        except discord.Forbidden:
            logging.warning(f"Could not send DM to user {author_id} - DMs might be disabled")
        except Exception as e:
            logging.error(f"Error sending DM notification to user {author_id}: {e}")

    async def award_gems(self, user_id: int, ticket_amount: int) -> bool:
        """
        Award gems to a user.
        (This is your implementation and assumes you have self.bot.db configured)
        """
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT MENTOR_TICKETS FROM USER WHERE USER_ID = %s", (user_id,))
                    user_exists = await cursor.fetchone()
                    
                    if user_exists:
                        await cursor.execute(
                            "UPDATE USER SET MENTOR_TICKETS = MENTOR_TICKETS + %s WHERE USER_ID = %s", 
                            (ticket_amount, user_id)
                        )
                    else:
                        await cursor.execute(
                            "INSERT INTO USER (USER_ID, MENTOR_TICKETS) VALUES (%s, %s)",
                            (user_id, ticket_amount)
                        )
                    
                    await conn.commit()
                    return True
                    
        except Exception as e:
            logging.error(f"Error awarding gems to user {user_id}: {e}")
            return False