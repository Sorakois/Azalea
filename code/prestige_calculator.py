# prestige_calculator.py
import discord
from datetime import datetime, timedelta
from collections import defaultdict

CHANNEL_IDS = {
    'help_channels': [
                        1311893774921629696, # gen-help
                        1071439126106214430, # crk-help
                        1137935183904002099, # crob-help
                        1256297372841938954, # wc-toa-help
                        1241400557550309497, # hsr-help
                        1310098607273279528, # wuwa-help
                        1352690549823639605, # zzz-help
                        1310097356448075776, # genshin-help
                    ],               
    'flex_channels': [
                        1236670332967059557, # gen-flex
                        1120850734582353992, # cr-flex
                        1241400905505575003, # hsr-flex
                        1310098840979902475, # wuwa-flex
                        1352691005371187322, # zzz-flex
                        1310097448638742588, # genshin-flex

                    ],  
    'fail_channels': [
                        1269705262474985574, # gen-fail
                        1269176341090275368, # cr-fail
                        1269181382056476733, # hsr-fail
                        1310098903974281308, # wuwa-fail
                        1352691098044076156, # zzz-fail
                        1310097639857066024, # genshin-fail
                    ],  
    'animanga_channel': 1236664936856420462,
    'art_channels': [
                        1393317317424840724, # art-pile
                        1181801331565002784, # art-contest
                        1232152392666058885 # art-collections
                    ], 
    'vent_channels': [1118287233112350780],
    'leak_channels': [
                        1404199748855922729, # cr-rumors
                        1244685281425227838, # hsr-rumors
                        1310099203871215656, # wuwa-rumors
                        1352691166813880350, # zzz-rumors
                        1310096371092820090, # genshin-rumors
                    ],
}

# Bot ID for quest system
AZALEA_BOT_ID = 1082486461103878245
EXCLUDED_USER_ID = 836367313502208040  # Your Discord ID - excluded from all counts

async def calculate_monthly_prestige(bot, guild_id, interaction=None):
    """Calculate prestige statistics for the past 30 days"""
    guild = bot.get_guild(guild_id)
    if not guild:
        return None
    
    # Get the date 30 days ago
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Initialize counters
    stats = {
        'chatter': defaultdict(int),      # Message count per user
        'mentor': defaultdict(int),       # Help responses per user
        'student': defaultdict(int),      # Help requests per user
        'yapper': defaultdict(int),       # Voice channel time per user
        'confidant': defaultdict(int),    # Vent responses per user
        'lucky': defaultdict(int),        # Flex posts per user
        'unlucky': defaultdict(int),      # Fail posts per user
        'cultured': defaultdict(int),     # Animanga posts per user
        'sleuth': defaultdict(int),       # Investigative posts per user
        'artistic': defaultdict(int),     # Art posts per user
    }
    
    # Debug counters
    quest_messages_found = 0
    quest_messages_with_mentions = 0
    
    # Process text channels
    for channel in guild.text_channels:
        try:
            async for message in channel.history(after=thirty_days_ago, limit=None):
                user_id = message.author.id
                
                # Handle bot messages (specifically Azalea for quest detection)
                if message.author.bot:
                    # Only process Azalea bot messages for quest detection
                    if message.author.id == AZALEA_BOT_ID and channel.id in CHANNEL_IDS['help_channels']:
                        # Check if this is a quest message from Azalea bot
                        if any(keyword in message.content.upper() for keyword in ["QUEST", "REQUESTED BY", "HELP"]):
                            quest_messages_found += 1
                            # Extract the requester from the quest message using the raw format
                            if "Requested by:" in message.content:
                                # Parse the user mention from the quest message to get the original requester
                                import re
                                # Look for any user mention - very flexible pattern
                                mention_matches = re.findall(r'<@!?(\d+)>', message.content)
                                if mention_matches:
                                    quest_messages_with_mentions += 1
                                    # Take the first user mention found (should be the requester)
                                    requester_id = int(mention_matches[0])
                                    # Don't count the excluded user
                                    if requester_id != EXCLUDED_USER_ID:
                                        stats['student'][requester_id] += 1
                    continue  # Skip other bot processing
                
                # Skip counting for excluded user
                if user_id == EXCLUDED_USER_ID:
                    continue
                
                # Count all messages for chatter prestige
                stats['chatter'][user_id] += 1
                
                # Help channels logic - check for replies to Azalea
                if channel.id in CHANNEL_IDS['help_channels']:
                    # Check if this is a reply to a quest message (help response) 
                    if message.reference and user_id != EXCLUDED_USER_ID:
                        try:
                            # Get the referenced message
                            referenced_msg = await channel.fetch_message(message.reference.message_id)
                            # Check if the referenced message is a quest from Azalea
                            if referenced_msg.author.id == AZALEA_BOT_ID:
                                # This is a help response to any Azalea message
                                stats['mentor'][user_id] += 1
                        except:
                            # If we can't fetch the referenced message, skip
                            pass
                
                # Flex channels
                elif channel.id in CHANNEL_IDS['flex_channels']:
                    stats['lucky'][user_id] += 1
                
                # Fail channels
                elif channel.id in CHANNEL_IDS['fail_channels']:
                    stats['unlucky'][user_id] += 1
                
                # Animanga channel
                elif channel.id == CHANNEL_IDS['animanga_channel']:
                    stats['cultured'][user_id] += 1
                
                # Art channels
                elif channel.id in CHANNEL_IDS['art_channels']:
                    # Count ONLY based on number of images/files attached
                    if message.attachments:
                        stats['artistic'][user_id] += len(message.attachments)
                    # Don't count messages without attachments in art channels
                
                # Vent channels
                elif channel.id in CHANNEL_IDS['vent_channels']:
                    # Check if message is a response (not the original vent)
                    if message.reference or len(message.content.split()) > 10:  # Assume longer messages are responses
                        stats['confidant'][user_id] += 1
                
                # LEAK CHANNELS - Investigative behavior (SLEUTH)
                elif channel.id in CHANNEL_IDS['leak_channels']:
                    # Investigative behavior (mentions, links, detailed analysis)
                    sleuth_points = 0
                    
                    # Links give points
                    if 'http' in message.content:
                        sleuth_points += 2
                    
                    # User mentions give points
                    if len(message.mentions) > 0:
                        sleuth_points += len(message.mentions)
                    
                    # Multiple questions suggest investigation
                    if message.content.count('?') > 1:
                        sleuth_points += 1
                    
                    # File/image attachments give points (evidence!)
                    if len(message.attachments) > 0:
                        sleuth_points += len(message.attachments) * 2
                    
                    # Long messages suggest detailed analysis
                    if len(message.content) > 200:
                        sleuth_points += 1
                    
                    # Add all sleuth points for this message
                    if sleuth_points > 0:
                        stats['sleuth'][user_id] += sleuth_points
                    
        except discord.Forbidden:
            print(f"No access to channel: {channel.name}")
            continue
        except Exception as e:
            print(f"Error processing channel {channel.name}: {e}")
            continue
    
    # Send debug info to channel if interaction provided
    if interaction:
        debug_msg = f"**DEBUG INFO:**\n"
        debug_msg += f"Quest messages found: {quest_messages_found}\n"
        debug_msg += f"Quest messages with mentions: {quest_messages_with_mentions}\n"
        debug_msg += f"Total students counted: {sum(stats['student'].values())}\n"
        debug_msg += f"Azalea Bot ID being searched for: {AZALEA_BOT_ID}\n"
        debug_msg += f"Total Azalea messages found in help channels: {quest_messages_found}\n"
        debug_msg += f"Help channel IDs being checked: {CHANNEL_IDS['help_channels']}\n"
        debug_msg += f"Total sleuth points awarded: {sum(stats['sleuth'].values())}\n"
        debug_msg += f"Leak channel IDs being checked: {CHANNEL_IDS['leak_channels']}\n\n"
        debug_msg += f"**ALL CHANNELS IN SERVER:**\n"
        for channel in guild.text_channels:
            debug_msg += f"{channel.name}: {channel.id}\n"
        
        try:
            await interaction.followup.send(debug_msg)
        except:
            pass  # Don't let debug messages break the command
    
    return stats

def get_top_user(stats_dict, guild):
    """Get the user with the highest count from a stats dictionary"""
    if not stats_dict:
        return None, 0
    
    top_user_id = max(stats_dict, key=stats_dict.get)
    top_count = stats_dict[top_user_id]
    top_user = guild.get_member(top_user_id)
    
    return top_user, top_count

async def handle_monthly_prestige_command(bot, interaction):
    """Main function to handle the monthly prestige command"""
    await interaction.response.defer()  # Defer the response as this might take time
    
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Guild not found!")
        return
    
    # Calculate stats
    stats = await calculate_monthly_prestige(bot, guild.id, interaction)  # Pass interaction for debug
    if not stats:
        await interaction.followup.send("Failed to calculate prestige statistics!")
        return
    
    # Build the embed
    embed = discord.Embed(
        title="🏆 **Prestige Roles**",
        description="## This Month's Prestigious Members:",
        color=0xFFD700  # Gold color
    )
    
    prestige_categories = [
        ('chatter', 'PRESTIGE: Chatter', ':HoundHack:', 'Most active chatter of the month'),
        ('mentor', 'PRESTIGE: Mentor', ':NekoThink:', 'Has responded the most to help requests (any help chat)'),
        ('student', 'PRESTIGE: Student', ':noted:', 'Has pinged helpers the most (for actual question) (any help chat)'),
        ('yapper', 'PRESTIGE: Yapper', ':speaking_head:', 'VCed the most in the past month'),
        ('confidant', 'PRESTIGE: Confidant', ':NekoLove:', 'Responded to most vents'),
        ('lucky', 'PRESTIGE: Lucky', ':PepeMoney:', 'Most flex channel posts (any flex chat)'),
        ('unlucky', 'PRESTIGE: Unlucky', ':skull:', 'Most fail channel posts (any fail chat)'),
        ('cultured', 'PRESTIGE: Cultured', ':chad:', 'Most #📺┃animanga channel post'),
        ('sleuth', 'PRESTIGE: Sleuth', ':SW_Cool:', 'Most investigative user in leak channels!'),
        ('artistic', 'PRESTIGE: Artistic', ':RappaWow:', 'Most art channel posts')
    ]
    
    for stat_key, title, emoji, description in prestige_categories:
        top_user, count = get_top_user(stats[stat_key], guild)
        
        if top_user and count > 0:
            user_mention = top_user.mention
            field_title = f"**@{title} {emoji}**"
        else:
            user_mention = "No qualifying users"
            field_title = f"**@{title} {emoji}**"
            count = 0
        
        field_value = f"> ### {user_mention}\n> -# {description}\n> **Count: {count}**"
        embed.add_field(name=field_title, value=field_value, inline=False)
    
    embed.set_footer(text=f"Stats calculated for the past 30 days • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    
    await interaction.followup.send(embed=embed)