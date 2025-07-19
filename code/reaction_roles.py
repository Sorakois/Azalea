import discord
from discord.ext import commands
from enum import Enum
from debug import Prompt

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Store message_id: {emoji: role_id} mappings
        self.reaction_roles = {}
        self.setup_channel_id = 1393934563725541457
        # Store embed_name: message_id mappings
        self.embed_messages = {}
        
        # Predefined embed configurations
        self.embed_configs = {
            "colors": {
                "title": "Aesthetic Color Roles ❤️",
                "description": "Pick what color your username should be!",
                "color": 0xff6b6b,
                "image_url": "https://c.tenor.com/nd9ZgHOIpegAAAAd/tenor.gif",
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
                    "🍪": ("Cookie Run: Kingdom", "1123025025847525416"),
                    "<a:FireflyLick:1302060973888245884>": ("Honkai: Star Rail", "1171960652886196234"),
                    "💤": ("Zenless Zone Zero", "1352663789983502467"),
                    "🌊": ("Wuthering Waves", "1244076568922554469"),
                    "🔥": ("Cookie Run: Ovenbreak", "1119148366857764904"),
                    "✨": ("Genshin Impact", "1241399923543511171"),
                    "🏯": ("Cookie Run: TOA / WC", "1269275014876631092"),
                    "🟥": ("Roblox", "1198817459709427762"),
                    "🏡": ("Minecraft", "1275507109001166999"),
                    "🌱": ("Terraria", "1379511241151615139"),
                    "🪙": ("Nintendo", "1379511158414774282")
                }
            },
            "notifications": {
                "title": "Notification Roles 🔔",
                "description": "Select what you'd like to recieve notifications for!",
                "color": 0x45b7d1,
                "image_url": "https://c.tenor.com/EFqSNRfgGi4AAAAd/tenor.gif",
                "roles": {
                    "<:gladge:1275504053681520660>": ("Server Updates", "1033467117246353478"),
                    "☕": ("Server Polls", "1133794178405515316"),
                    "❓": ("Question of the Day", "1190712932338782249"),
                    "🎙️": ("Ping for VC", "1157867750098735115"),
                    "🎪": ("Event Ping", "1379321754476085248"),
                    "<:NekoParty:1069497120199020635>": ("Game Contest Ping", "1305273489648783410"),
                    "🍿": ("Movie Night Ping", "1185749242439028786"),
                    "🎮": ("Game Night Ping", "1185749286487601283"),
                    "🔔": ("CRK Guild Boss Reminder", "1042250208534343763"),
                    "<:NekoCool:1120607491819061349>": ("Sorakoi Video Upload", "1136301329535484004")
                }
            },
            "helpers": {
                "title": "Helper Roles 🪴",
                "description": "IMPORTANT: All roles are publically pingable! Select to be pinged to help others, ping to ask for help.",
                "color": 0xf39c12,
                "image_url": "https://media.tenor.com/VprYhfrdZroAAAAi/pure-vanilla-cookie-crk.gif",
                "roles": {
                    "🍪": ("CRK Helper", "1138170342498648064"),
                    "<:SundayAngel:1302061544980484177>": ("HSR Helper", "1241410436662820905"),
                    "🔥": ("CROB Helper", "1144445141529145355"),
                    "<:CrepeWoah:1072377413943705660>": ("CR WC/TOA Helper", "1370468801774227679"),
                    "🌏": ("Genshin Helper", "1310385900865196092"),
                    "🌊": ("WuWa Helper", "1310385836012863518"),
                    "💤": ("ZZZ Helper", "1352691719069634631")
                }
            },
            "regions": {
                "title": "Misc. Roles 🛒🪄",
                "description": "Other random roles that you might like... 👀",
                "color": 0x9b59b6,
                "image_url": "https://media.tenor.com/s32xQPXxDX8AAAAj/miyabi-zenless.gif",
                "roles": {
                    "🕵️": ("Venting Access", "1118288707724771409"),
                    "🏴‍☠️": ("CR TOA Raid", "1324098035369902160"),
                    "👑": ("CR TOA Champion Raid", "1324105581174460487"),
                }
            }
        }
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle when a user adds a reaction"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a reaction roles message
        if payload.message_id not in self.reaction_roles:
            return
        
        # Get the emoji string
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
        
        # Get the role ID and role object
        role_id = self.reaction_roles[payload.message_id][emoji]
        role = guild.get_role(int(role_id)) if role_id.isdigit() else discord.utils.get(guild.roles, name=role_id)
        
        if not role:
            print(f"Role {role_id} not found!")
            return
        
        # Add the role to the member
        try:
            await member.add_roles(role, reason="Reaction role")
            print(f"Added role {role.name} to {member.display_name}")
        except discord.Forbidden:
            print(f"Bot doesn't have permission to add role {role.name}")
        except discord.HTTPException as e:
            print(f"Failed to add role {role.name}: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle when a user removes a reaction"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a reaction roles message
        if payload.message_id not in self.reaction_roles:
            return
        
        # Get the emoji string
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
        
        # Get the role ID and role object
        role_id = self.reaction_roles[payload.message_id][emoji]
        role = guild.get_role(int(role_id)) if role_id.isdigit() else discord.utils.get(guild.roles, name=role_id)
        
        if not role:
            print(f"Role {role_id} not found!")
            return
        
        # Remove the role from the member
        try:
            await member.remove_roles(role, reason="Reaction role removed")
            print(f"Removed role {role.name} from {member.display_name}")
        except discord.Forbidden:
            print(f"Bot doesn't have permission to remove role {role.name}")
        except discord.HTTPException as e:
            print(f"Failed to remove role {role.name}: {e}")
    
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
            await message.add_reaction(emoji)
            role_mappings[emoji] = role_id
        
        self.reaction_roles[message.id] = role_mappings
        
        print(f"Created embed '{embed_name}' with message ID: {message.id}")
        return f"Successfully created embed '{embed_name}'"
    
    async def add_reaction_role(self, embed_name: str, emoji: str, role_id: str, role_name: str = None):
        """Add a new reaction role mapping to a specific embed"""
        if embed_name not in self.embed_messages:
            return f"Embed '{embed_name}' doesn't exist. Create it first!"
        
        message_id = self.embed_messages[embed_name]
        
        if message_id not in self.reaction_roles:
            self.reaction_roles[message_id] = {}
        
        # Check if we're at the 10 reaction limit
        if len(self.reaction_roles[message_id]) >= 10:
            return f"Embed '{embed_name}' already has 10 reactions (Discord limit)!"
        
        self.reaction_roles[message_id][emoji] = role_id
        
        # Add the reaction to the message
        try:
            channel = self.bot.get_channel(self.setup_channel_id)
            message = await channel.fetch_message(message_id)
            await message.add_reaction(emoji)
            
            # Update the embed if role_name is provided
            if role_name:
                embed = message.embeds[0]
                embed.add_field(
                    name=f"{emoji}",
                    value=f"{role_name}",
                    inline=True
                )
                await message.edit(embed=embed)
            
            return f"Added reaction role to '{embed_name}': {emoji} -> {role_name or role_id}"
        except Exception as e:
            return f"Error adding reaction: {e}"
    
    async def update_embed_image(self, embed_name: str, image_url: str):
        """Update the image of an existing embed"""
        if embed_name not in self.embed_messages:
            return f"Embed '{embed_name}' doesn't exist!"
        
        try:
            message_id = self.embed_messages[embed_name]
            channel = self.bot.get_channel(self.setup_channel_id)
            message = await channel.fetch_message(message_id)
            
            # Get the current embed
            embed = message.embeds[0]
            
            # Update image
            embed.set_image(url=image_url)
            # Update the config too
            if embed_name in self.embed_configs:
                self.embed_configs[embed_name]["image_url"] = image_url
            
            # Edit the message with updated embed
            await message.edit(embed=embed)
            
            return f"Updated embed '{embed_name}' with new image"
        except Exception as e:
            return f"Error updating embed image: {e}"
    
    async def list_embeds(self):
        """List all created embeds"""
        if not self.embed_messages:
            return "No embeds created yet!"
        
        embed_list = []
        for embed_name, message_id in self.embed_messages.items():
            role_count = len(self.reaction_roles.get(message_id, {}))
            embed_list.append(f"• {embed_name}: {role_count} roles")
        
        return "Created embeds:\n" + "\n".join(embed_list)
    
    async def delete_embed(self, embed_name: str):
        """Delete a specific embed"""
        if embed_name not in self.embed_messages:
            return f"Embed '{embed_name}' doesn't exist!"
        
        try:
            message_id = self.embed_messages[embed_name]
            channel = self.bot.get_channel(self.setup_channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
            
            # Clean up stored data
            del self.embed_messages[embed_name]
            if message_id in self.reaction_roles:
                del self.reaction_roles[message_id]
            
            return f"Deleted embed '{embed_name}'"
        except Exception as e:
            return f"Error deleting embed: {e}"
    
    def get_reaction_role_handler(self):
        """Return the handler function for declare command integration"""
        async def handle_reaction_role_prompt(interaction, prompt):
            split = prompt.split(' ')
            
            try:
                if prompt == Prompt.RR_Setup.value:
                    # Defer the response first since this might take a while
                    await interaction.response.defer()
                    result = await self.setup_all_reaction_roles()
                    await interaction.followup.send(result)
                    
                elif split[0] == Prompt.RR_SetupEmbed.value:
                    if len(split) < 2:
                        available_embeds = ", ".join(self.embed_configs.keys())
                        await interaction.response.send_message(f"Usage: rr_setup_embed <embed_name>\nAvailable: {available_embeds}")
                        return True
                    
                    # Defer for potentially long operations
                    await interaction.response.defer()
                    embed_name = split[1]
                    result = await self.setup_single_embed(embed_name)
                    await interaction.followup.send(result)
                    
                elif split[0] == Prompt.RR_AddRole.value:
                    if len(split) < 4:
                        await interaction.response.send_message("Usage: rr_add_role <embed_name> <emoji> <role_id> [role_name]")
                        return True
                    
                    await interaction.response.defer()
                    embed_name = split[1]
                    emoji = split[2]
                    role_id = split[3]
                    role_name = " ".join(split[4:]) if len(split) > 4 else None
                    
                    result = await self.add_reaction_role(embed_name, emoji, role_id, role_name)
                    await interaction.followup.send(result)
                    
                elif split[0] == Prompt.RR_UpdateImage.value:
                    if len(split) < 3:
                        await interaction.response.send_message("Usage: rr_update_image <embed_name> <image_url>")
                        return True
                    
                    await interaction.response.defer()
                    embed_name = split[1]
                    image_url = split[2]
                    
                    result = await self.update_embed_image(embed_name, image_url)
                    await interaction.followup.send(result)
                    
                elif prompt == Prompt.RR_List.value:
                    # This should be quick, so we can respond immediately
                    result = await self.list_embeds()
                    await interaction.response.send_message(result)
                    
                elif split[0] == Prompt.RR_Delete.value:
                    if len(split) < 2:
                        await interaction.response.send_message("Usage: rr_delete <embed_name>")
                        return True
                    
                    await interaction.response.defer()
                    embed_name = split[1]
                    result = await self.delete_embed(embed_name)
                    await interaction.followup.send(result)
                    
                else:
                    return False  # Not handled by this cog
                
                return True  # Handled by this cog
                
            except discord.errors.NotFound:
                # Interaction has already been responded to or expired
                print(f"Interaction expired or already responded to for prompt: {prompt}")
                return True
            except Exception as e:
                print(f"Error in handle_reaction_role_prompt: {e}")
                # Try to send an error message if we haven't responded yet
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"An error occurred: {e}")
                    else:
                        await interaction.followup.send(f"An error occurred: {e}")
                except:
                    pass  # If we can't send an error message, just log it
                return True
        
        return handle_reaction_role_prompt