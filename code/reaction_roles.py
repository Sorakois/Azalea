import discord
from discord.ext import commands
from enum import Enum
from debug import Prompt
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)

class ReactionRoleError(Exception):
    """Custom exception for reaction role debugging"""
    pass

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Store message_id: {emoji: role_id} mappings
        self.reaction_roles = {}
        self.setup_channel_id = 1393934563725541457
        # Store embed_name: message_id mappings
        self.embed_messages = {}
        self.data_file = "reaction_roles_data.json"
       
        # Predefined embed configurations
        self.embed_configs = {
            "colors": {
                "title": "Aesthetic Color Roles ❤️",
                "description": "Pick what color your username should be!",
                "color": 0xff6b6b,
                "image_url": "https://c.tenor.com/FpkLsxSt-Y8AAAAC/tenor.gif",
                "roles": {
                    "🍎": ("Red", "1033481143745527869"),
                    "🍊": ("Orange", "1033481146748649594"),
                    "🍋": ("Yellow", "1033481147251970048"),
                    "🍋‍🟩": ("Green", "1033481145750388776"),
                    "🫐": ("Blue", "1033481147851747448"),
                    "🍇": ("Purple", "1033481144919916724"),
                    "🍫": ("Brown", "1067973797405274152"),
                    "🖤": ("Black", "1124466003875737621"),
                    "🤍": ("White", "1384289909568704612"),
                    "🩶": ("Gray/Grey", "1067976728938565773")
                }
            },
            "games": {
                "title": "Game Roles 🎮",
                "description": "Select the games you play to unlock related chats!",
                "color": 0x4ecdc4,
                "image_url": "https://c.tenor.com/dLQPMW_IVJoAAAAd/tenor.gif",
                "roles": {
                    "<a:FireflyLick:1302060973888245884>": ("Honkai: Star Rail", "1171960652886196234"),
                    "🌊": ("Wuthering Waves", "1244076568922554469"),
                    "💤": ("Zenless Zone Zero", "1352663789983502467"),
                    "🌆": ("Neverness to Everness", "1506388929933349005"),
                    "✨": ("Genshin Impact", "1241399923543511171"),
                    "⚜️": ("Arknights", "1506389004399022133"),
                    "🏭": ("Endfield", "1506389059612835991"),
                    "🍪": ("Cookie Run: Kingdom", "1123025025847525416"),
                    "🤖": ("NIKKE", "1506389147856928848"),
                    "🕰️": ("Reverse: 1999", "1506389123718578197"),
                    "🏇": ("Uma Musume", "1506871273333063850"),
                    "🎹": ("Hatsune Miku: Colorful Stage", "1506389283081158717"),
                }
            },
            "notifications": {
                "title": "Notification Roles 🔔",
                "description": "Select what you'd like to recieve notifications for!",
                "color": 0x45b7d1,
                "image_url": "https://c.tenor.com/2lLCyJMgAkIAAAAC/tenor.gif",
                "roles": {
                    "<:gladge:1275504053681520660>": ("Server Updates", "1033467117246353478"),
                    "☕": ("Server Polls", "1133794178405515316"),
                    "❓": ("Question of the Day", "1190712932338782249"),
                    "🎙️": ("Ping for VC", "1157867750098735115"),
                    "🎪": ("Event Ping", "1379321754476085248"),
                    "<:NekoParty:1069497120199020635>": ("Game Contest Ping", "1305273489648783410"),
                    "🍿": ("Movie Watch-a-long Ping", "1185749242439028786"),
                    "🎮": ("CO-OP Game Ping", "1185749286487601283"),
                    "<:NekoCool:1120607491819061349>": ("Sorakoi Video Upload", "1136301329535484004")
                }
            },
            "helpers": {
                "title": "Helper Roles 🪴",
                "description": "IMPORTANT: All roles are publically pingable! Select to be pinged to help others, ping to ask for help.",
                "color": 0xf39c12,
                "image_url": "https://media.tenor.com/r3NhpqJPpNAAAAAi/wuwa.gif",
                "roles": {
                    "🎮": ("Gameplay Helper", "1506387878807208057"),
                    "🔧": ("Technical/Hardware/Software Helper", "1506521575376289822"),
                }
            },
            "regions": {
                "title": "Misc. Roles 🛒🪄",
                "description": "Other random roles that you might like... 👀",
                "color": 0x9b59b6,
                "image_url": "https://c.tenor.com/d27gEByLFVUAAAAC/tenor.gif",
                "roles": {
                    "🕵️": ("Venting Access", "1118288707724771409"),
                }
            }
        }
   
    async def load_data(self):
        """Load persistent data from file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                # Convert string keys back to integers for message IDs
                self.reaction_roles = {int(k): v for k, v in data.get('reaction_roles', {}).items()}
                self.embed_messages = data.get('embed_messages', {})
                logger.info(f"Loaded {len(self.reaction_roles)} reaction role mappings from file")
        except FileNotFoundError:
            logger.info("No data file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    async def save_data(self):
        """Save persistent data to file"""
        try:
            data = {
                'reaction_roles': {str(k): v for k, v in self.reaction_roles.items()},
                'embed_messages': self.embed_messages
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Load data and validate message mappings when bot starts"""
        try:
            logger.info("Bot ready, initializing reaction roles...")
            await self.load_data()
            
            # Wait a bit for guild data to be fully loaded
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=3))
            
            await self.validate_message_mappings()
            logger.info("Reaction roles initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize reaction roles: {e}")
            logger.info("You can manually run 'rr_startup' command to retry initialization")

    async def validate_message_mappings(self):
        """Validate that stored message IDs still exist and clean up invalid ones"""
        channel = self.bot.get_channel(self.setup_channel_id)
        if not channel:
            logger.error(f"Setup channel {self.setup_channel_id} not found")
            return
        
        logger.info("Validating message mappings...")
        
        invalid_messages = []
        
        for message_id in list(self.reaction_roles.keys()):
            try:
                await channel.fetch_message(message_id)
                logger.debug(f"Message {message_id} is valid")
            except discord.NotFound:
                logger.warning(f"Message {message_id} no longer exists, removing from mappings")
                invalid_messages.append(message_id)
            except Exception as e:
                logger.error(f"Error validating message {message_id}: {e}")
        
        # Clean up invalid messages
        for message_id in invalid_messages:
            del self.reaction_roles[message_id]
            # Also remove from embed_messages if it exists there
            for embed_name, stored_id in list(self.embed_messages.items()):
                if stored_id == message_id:
                    del self.embed_messages[embed_name]
                    break
        
        if invalid_messages:
            await self.save_data()
            logger.info(f"Cleaned up {len(invalid_messages)} invalid message mappings")
        
        logger.info(f"Validation complete. Active mappings: {len(self.reaction_roles)}")

    async def rebuild_reaction_mappings(self):
        """Scan the setup channel for existing reaction role messages - enhanced version"""
        channel = self.bot.get_channel(self.setup_channel_id)
        if not channel:
            raise ReactionRoleError(f"Setup channel {self.setup_channel_id} not found")
        
        logger.info("Rebuilding reaction role mappings from channel history...")
        
        # Clear existing mappings
        self.reaction_roles.clear()
        self.embed_messages.clear()
        
        found_messages = 0
        
        # Scan more messages to be thorough
        async for message in channel.history(limit=200):
            if message.author != self.bot.user or not message.embeds:
                continue
                
            embed = message.embeds[0]
            if not embed.title:
                continue
                
            # Try to match embed titles to our configs
            for embed_name, config in self.embed_configs.items():
                if embed.title == config["title"]:
                    logger.info(f"Found existing embed: {embed_name} (ID: {message.id})")
                    
                    # Store the message mapping
                    self.embed_messages[embed_name] = message.id
                    
                    # Rebuild reaction mappings based on config
                    role_mappings = {}
                    for emoji, (role_name, role_id) in config["roles"].items():
                        role_mappings[emoji] = role_id
                    
                    self.reaction_roles[message.id] = role_mappings
                    found_messages += 1
                    break
        
        logger.info(f"Rebuilt mappings for {found_messages} messages")
        
        # Save the rebuilt data
        await self.save_data()
        
        return found_messages
   
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle when a user adds a reaction"""
        try:
            # Ignore bot reactions
            if payload.user_id == self.bot.user.id:
                return
            
            logger.debug(f"Reaction add: {payload.emoji} on {payload.message_id} by {payload.user_id}")
            
            # Check if this is a reaction roles message
            if payload.message_id not in self.reaction_roles:
                logger.debug(f"Message {payload.message_id} not in reaction_roles")
                return
            
            # Get the emoji string - handle both unicode and custom emojis
            if payload.emoji.id:
                # Custom emoji
                emoji = f"<{'a' if payload.emoji.animated else ''}:{payload.emoji.name}:{payload.emoji.id}>"
            else:
                # Unicode emoji
                emoji = str(payload.emoji)
            
            logger.info(f"Processing reaction: '{emoji}' on message {payload.message_id}")
            
            # Check if this emoji is mapped to a role
            if emoji not in self.reaction_roles[payload.message_id]:
                logger.debug(f"Emoji '{emoji}' not mapped for message {payload.message_id}")
                return
            
            # Get the guild and member
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                raise ReactionRoleError(f"Guild {payload.guild_id} not found")
            
            member = guild.get_member(payload.user_id)
            if not member:
                logger.warning(f"Member {payload.user_id} not found in guild")
                return
            
            # Get the role
            role_id = self.reaction_roles[payload.message_id][emoji]
            role = guild.get_role(int(role_id))
            
            if not role:
                logger.error(f"Role {role_id} not found in guild")
                return
            
            # Check if member already has the role
            if role in member.roles:
                logger.debug(f"Member {member.display_name} already has role {role.name}")
                return
            
            # Check bot permissions and hierarchy
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member.guild_permissions.manage_roles:
                logger.error("Bot missing 'Manage Roles' permission")
                return
            
            if role.position >= bot_member.top_role.position:
                logger.error(f"Role {role.name} is too high in hierarchy")
                return
            
            # Add the role
            await member.add_roles(role, reason="Reaction role")
            logger.info(f"✅ Added role {role.name} to {member.display_name}")
            
        except Exception as e:
            logger.error(f"Error in on_raw_reaction_add: {e}")
   
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle when a user removes a reaction"""
        try:
            # Ignore bot reactions
            if payload.user_id == self.bot.user.id:
                return
            
            logger.debug(f"Reaction remove: {payload.emoji} on {payload.message_id} by {payload.user_id}")
            
            # Check if this is a reaction roles message
            if payload.message_id not in self.reaction_roles:
                return
            
            # Get the emoji string
            if payload.emoji.id:
                emoji = f"<{'a' if payload.emoji.animated else ''}:{payload.emoji.name}:{payload.emoji.id}>"
            else:
                emoji = str(payload.emoji)
            
            # Check if this emoji is mapped to a role
            if emoji not in self.reaction_roles[payload.message_id]:
                return
            
            # Get the guild and member
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if not member:
                return
            
            # Get the role
            role_id = self.reaction_roles[payload.message_id][emoji]
            role = guild.get_role(int(role_id))
            
            if not role:
                return
            
            # Check if member has the role
            if role not in member.roles:
                return
            
            # Remove the role
            await member.remove_roles(role, reason="Reaction role removed")
            logger.info(f"❌ Removed role {role.name} from {member.display_name}")
            
        except Exception as e:
            logger.error(f"Error in on_raw_reaction_remove: {e}")
   
    async def setup_all_reaction_roles(self):
        """Create all 5 reaction role embeds"""
        channel = self.bot.get_channel(self.setup_channel_id)
        if not channel:
            return "Channel not found!"
       
        results = []
        for embed_name, config in self.embed_configs.items():
            result = await self.setup_single_embed(embed_name, config)
            results.append(f"{embed_name}: {result}")
       
        return "\n".join(results)
   
    async def setup_single_embed(self, embed_name, config=None):
        """Create a single reaction role embed"""
        channel = self.bot.get_channel(self.setup_channel_id)
        if not channel:
            return "Channel not found!"
       
        # Use provided config or get from predefined configs
        if config is None:
            if embed_name not in self.embed_configs:
                return f"Unknown embed name: {embed_name}"
            config = self.embed_configs[embed_name]
       
        # Check if embed already exists
        if embed_name in self.embed_messages:
            try:
                message_id = self.embed_messages[embed_name]
                await channel.fetch_message(message_id)
                return f"Embed '{embed_name}' already exists!"
            except discord.NotFound:
                del self.embed_messages[embed_name]
       
        # Create embed
        embed = discord.Embed(
            title=config["title"],
            description=config["description"],
            color=config["color"]
        )
       
        # Add image if provided
        if config.get("image_url"):
            embed.set_image(url=config["image_url"])
       
        # Add fields for each role
        for emoji, (role_name, role_id) in config["roles"].items():
            embed.add_field(
                name=f"{emoji}",
                value=f"{role_name}",
                inline=True
            )
       
        embed.set_footer(text="Click the reactions below to toggle your roles!")
       
        # Send the message
        message = await channel.send(embed=embed)
       
        # Store the message ID
        self.embed_messages[embed_name] = message.id
       
        # Add reactions and store mappings
        role_mappings = {}
        for emoji, (role_name, role_id) in config["roles"].items():
            try:
                await message.add_reaction(emoji)
                role_mappings[emoji] = role_id
                logger.info(f"Added reaction {emoji} for role {role_name}")
            except discord.HTTPException as e:
                logger.error(f"Failed to add reaction {emoji}: {e}")
       
        self.reaction_roles[message.id] = role_mappings
       
        # Save data after creating embed
        await self.save_data()
       
        logger.info(f"Created embed '{embed_name}' with message ID: {message.id}")
        return f"Successfully created embed '{embed_name}'"

    async def create_test_embed(self):
        """Create a simple test embed with basic emojis"""
        channel = self.bot.get_channel(self.setup_channel_id)
        if not channel:
            return "Channel not found!"
        
        embed = discord.Embed(
            title="🧪 Test Reaction Roles",
            description="Simple test with basic emojis",
            color=0xff0000
        )
        
        # Use simple emojis and existing role IDs
        test_roles = {
            "🔴": "1033481143745527869",  # Red role
            "🟢": "1033481145750388776",  # Green role
        }
        
        for emoji, role_id in test_roles.items():
            # Get role name for display
            guild = channel.guild
            role = guild.get_role(int(role_id))
            role_name = role.name if role else f"Role {role_id}"
            embed.add_field(name=emoji, value=role_name, inline=True)
        
        embed.set_footer(text="Test embed - react to test functionality!")
        
        message = await channel.send(embed=embed)
        
        # Add reactions and store mappings
        self.reaction_roles[message.id] = test_roles
        for emoji in test_roles.keys():
            await message.add_reaction(emoji)
        
        # Save data
        await self.save_data()
        
        logger.info(f"Test embed created with message ID: {message.id}")
        return f"Test embed created with message ID: {message.id}"
   
    def get_reaction_role_handler(self):
        """Return the handler function for declare command integration"""
        async def handle_reaction_role_prompt(interaction, prompt):
            split = prompt.split(' ')
           
            try:
                if prompt == Prompt.RR_Setup.value:
                    await interaction.response.defer()
                    result = await self.setup_all_reaction_roles()
                    await interaction.followup.send(result)
                   
                elif split[0] == Prompt.RR_SetupEmbed.value:
                    if len(split) < 2:
                        available_embeds = ", ".join(self.embed_configs.keys())
                        await interaction.response.send_message(f"Usage: rr_setup_embed <embed_name>\nAvailable: {available_embeds}")
                        return True
                   
                    await interaction.response.defer()
                    embed_name = split[1]
                    result = await self.setup_single_embed(embed_name)
                    await interaction.followup.send(result)

                elif prompt == Prompt.RR_Test.value:#"rr_test":
                    await interaction.response.defer()
                    result = await self.create_test_embed()
                    await interaction.followup.send(result)

                elif prompt == Prompt.RR_Rebuild.value:#"rr_rebuild":
                    # Add rebuild command
                    await interaction.response.defer()
                    count = await self.rebuild_reaction_mappings()
                    await interaction.followup.send(f"Rebuilt {count} reaction role mappings from channel history.")

                elif prompt == Prompt.RR_Status.value:#"rr_status":
                    # Add status command
                    status = f"**Reaction Roles Status:**\n"
                    status += f"Active messages: {len(self.reaction_roles)}\n"
                    status += f"Embed mappings: {len(self.embed_messages)}\n"
                    if self.reaction_roles:
                        status += f"Message IDs: {list(self.reaction_roles.keys())}\n"
                    await interaction.response.send_message(status)
                   
                else:
                    return False  # Not handled by this cog
               
                return True  # Handled by this cog
               
            except discord.errors.NotFound:
                logger.error(f"Interaction expired for prompt: {prompt}")
                return True
            except Exception as e:
                logger.error(f"Error in handle_reaction_role_prompt: {e}")
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"An error occurred: {e}")
                    else:
                        await interaction.followup.send(f"An error occurred: {e}")
                except:
                    pass
                return True
       
        return handle_reaction_role_prompt