import discord
from discord.ext import commands
import logging
import textwrap
import datetime
from typing import Set, List

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
        Handles quest creation and participation.
        NEW: Can now start a quest by replying to a message with a helper ping.
        """
        if message.author.bot:
            return
            
        # 1. Handle participation in an existing quest
        if message.reference and message.reference.message_id in self.active_quests:
            await self.handle_quest_participation(message)
            return
            
        # 2. Handle quest creation
        if self.helper_roles and message.role_mentions:
            mentioned_helper_roles = [role for role in message.role_mentions if role.id in self.helper_roles]
            if not mentioned_helper_roles:
                return

            # SCENARIO A: A helper role is pinged in a REPLY.
            # The quest is created for the message being replied to.
            if message.reference:
                try:
                    # Fetch the message that was replied to, this will be our quest source.
                    quest_target_message = await message.channel.fetch_message(message.reference.message_id)
                    
                    # Prevent starting a quest on a bot's message or on an existing quest
                    if quest_target_message.author.bot or quest_target_message.id in self.active_quests:
                        return

                    logging.info(f"Starting quest from reply by {message.author} for message {quest_target_message.id}")
                    # Pass the target message and the roles from the reply to start_quest
                    await self.start_quest(quest_target=quest_target_message, roles_to_ping=mentioned_helper_roles)
                    
                    # Clean up the user's reply message that contained the ping
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        logging.warning("Could not delete user's reply message (missing permissions).")

                except discord.NotFound:
                    logging.warning(f"User {message.author} tried to start a quest by replying to a deleted message.")
                except Exception as e:
                    logging.error(f"Error starting quest from reply: {e}", exc_info=True)

            # SCENARIO B: A helper role is pinged in a STANDALONE message.
            # The quest is created for the message that contains the ping itself.
            else:
                logging.info(f"Starting quest from standalone message by {message.author}")
                # Pass the message itself as the target and its own roles
                await self.start_quest(quest_target=message, roles_to_ping=mentioned_helper_roles)

    # MODIFIED: The function now takes the target message and roles to ping as arguments
    async def start_quest(self, quest_target: discord.Message, roles_to_ping: List[discord.Role]):
        """
        Starts a quest for a given target message.
        """
        try:
            # The content for the quest now comes from the quest_target
            content = quest_target.content
            
            # If the target message itself has pings, they should be stripped for the quest body
            for role in quest_target.role_mentions:
                content = content.replace(f'<@&{role.id}>', '').strip()
            
            quest_content = content or "Help needed!"

            def _create_message(text, author_mention, pings):
                ping_mentions = ' '.join([role.mention for role in pings])
                
                lines = [
                    f"# **NEW QUEST** <:swordge:1388933538044313662>\n",
                    #f"### {ping_mentions}\n", 
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

            # The author of the quest is the author of the target message
            quest_message_text = _create_message(quest_content, quest_target.author.mention, roles_to_ping)
            
            if len(quest_message_text) > 4000:
                await quest_target.channel.send("Quest content is too long to display.")
                return

            # Prepare attachments from the target message
            files_to_send = []
            if quest_target.attachments:
                for attachment in quest_target.attachments:
                    files_to_send.append(await attachment.to_file())

            quest_msg = await quest_target.channel.send(
                content=quest_message_text,
                files=files_to_send
            )
            
            self.active_quests.add(quest_msg.id)
            self.quest_participants[quest_msg.id] = {
                'author_id': quest_target.author.id, # The author of the original message
                'participants': set(),
                'channel_id': quest_target.channel.id,
                'guild_id': quest_target.guild.id if quest_target.guild else None
            }
            
            # If the quest was started from a standalone message (i.e. not a reply), delete it.
            # We determine this by checking if the message we are processing is the same as the one we are launching the quest for.
            # The reply-based trigger already deletes the user's reply in the on_message listener.
            is_standalone = any(role.id in [r.id for r in roles_to_ping] for role in quest_target.role_mentions)
            if is_standalone:
                try:
                    await quest_target.delete()
                except discord.HTTPException as e:
                    logging.warning(f"Could not delete original quest message (ID: {quest_target.id}): {e}")

            logging.info(f"Quest {quest_msg.id} started for user {quest_target.author}.")

        except Exception as e:
            logging.error(f"Error in start_quest: {e}", exc_info=True)

    # (The rest of your code: handle_quest_participation, notify_quest_author, award_gems remains the same)
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