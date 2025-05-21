from PIL import Image, ImageDraw, ImageFont, ImageSequence
from PIL.Image import Resampling
from io import BytesIO
import numpy as np
import requests

def rankingHandler(level, highest_level, ranking, user_id):
    '''
    Badge ranking image

    params:
        level (int) : current user level
        highest_level (int) : highest level of the current server
        ranking (int) : ranking within the server
        user_id (int) : ID of the user

    returns:
        rank (str) : directory of image to use
        rankNum (int) : rank number
    '''

    defaultDir = 'assets/level/'

    rank = ''

    if level <= 3:
        rank = defaultDir + 'ranks/Chocolate-2.png'
    elif level <= 6:
        rank = defaultDir + 'ranks/Chocolate-1.png'
    elif level == 7:
        rank = defaultDir + 'ranks/Bronze-2.png'
    elif level == 8:
        rank = defaultDir + 'ranks/Bronze-1.png'
    elif level == 9:
        rank = defaultDir + 'ranks/Silver-3.png'
    elif level == 10:
        rank = defaultDir + 'ranks/Silver-2.png'
    elif level == 11:
        rank = defaultDir + 'ranks/Silver-1.png'
    elif level == 12:
        rank = defaultDir + 'ranks/Gold-3.png'
    elif level == 13:
        rank = defaultDir + 'ranks/Gold-2.png'
    elif level == 14:
        rank = defaultDir + 'ranks/Gold-1.png'
    elif level == 15:
        rank = defaultDir + 'ranks/Crystal-3.png'
    elif level == 16:
        rank = defaultDir + 'ranks/Crystal-2.png'
    elif level == 17:
        rank = defaultDir + 'ranks/Crystal-1.png'
    elif level == 18:
        rank = defaultDir + 'ranks/Diamond-3.png'
    elif level == 19:
        rank = defaultDir + 'ranks/Diamond-2.png'
    elif level == 20:
        rank = defaultDir + 'ranks/Diamond-1.png'
    elif level == highest_level and level >= 50:
        rank = defaultDir + 'ranks/Grandmaster-1.png'
    elif level >= highest_level*.9 and level >= 50:
        rank = defaultDir + 'ranks/Grandmaster-2.png'
    elif level >= highest_level*.8 and level >= 50:
        rank = defaultDir + 'ranks/Grandmaster-3.png'
    elif level >= highest_level*.7 and level > 20:
        rank = defaultDir + 'ranks/Elite-1.png'
    elif level >= highest_level*.6 and level > 20:
        rank = defaultDir + 'ranks/Elite-2.png'
    elif level >= highest_level*.5 and level > 20:
        rank = defaultDir + 'ranks/Elite-3.png'
    elif level >= highest_level*.4 and level > 20:
        rank = defaultDir + 'ranks/Elite-4.png'
    elif level >= highest_level*.3 and level > 20:
        rank = defaultDir + 'ranks/Elite-5.png'
    elif level >= highest_level*.25 and level > 20:
        rank = defaultDir + 'ranks/Master-1.png'
    elif level >= highest_level*.2 and level > 20:
        rank = defaultDir + 'ranks/Master-2.png'
    elif level >= highest_level*.15 and level > 20:
        rank = defaultDir + 'ranks/Master-3.png'
    elif level >= highest_level*.1 and level > 20:
        rank = defaultDir + 'ranks/Master-4.png'
    elif level > 20:
        rank = defaultDir + 'ranks/Master-5.png'

    rankNum = 0
    for i in ranking:
        if int(i[1]) == user_id:
            rankNum = i[0]
            break
    
    return rank, rankNum

async def createImage(pfp, level, xp, url, highest_level, ranking, user_id):
    '''
    Implements template of the leveling banner

    params:
        pfp (str) : directory of user pfp
        level (int) : current user level
        xp (int) : current user xp
        highest_level (int) : highest level of the current server
        ranking (int) : ranking of current user
        user_id (int) : ID of the current user

    returns:
        buffer (BytesIO) : Byte stream of the generated image
    '''

    # Load fonts | 1 for level and rank, 2 for level progress
    font1 = ImageFont.truetype('assets/cookieRunFont.ttf', size=50)
    font2 = ImageFont.truetype('assets/cookieRunFont.ttf', size=25)

    # Load animated background and get dimensions
    gif = Image.open('assets/level/testing-me.gif')
    width, height = gif.size
    
    # Set fixed framerate for stability (24 fps = ~41.67ms per frame)
    fixed_duration = round(1000 / 24)  # Calculate ms per frame for 24fps
    loop = 0  # 0 means infinite loop
    
    # Load static overlay (azalea-level-page)
    overlay = Image.open('assets/level/azalea-level-page.png').convert("RGBA")

    # Prepare PFP
    if url:
        pfpImg = Image.open(requests.get(pfp, stream=True).raw).convert("RGBA")
    else:
        pfpImg = Image.open(pfp).convert("RGBA")

    pfpImg = pfpImg.resize((195, 195), resample=Resampling.LANCZOS)

    # Circular mask for PFP
    bigsize = (pfpImg.size[0] * 3, pfpImg.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfpImg.size, Resampling.LANCZOS)
    pfpImg.putalpha(mask)

    # Load rank icon
    rank, rankNum = rankingHandler(level, highest_level, ranking, user_id)
    rankImg = Image.open(rank).convert("RGBA")
    rankImg = rankImg.resize((90, 98), Image.LANCZOS)

    # XP bar processing
    xpStr = f"{xp//1000}.{str(xp)[-3:-1]}k" if xp >= 1000 else str(xp)
    xpNeeded = 12 * level**2 + 60
    xpNeededStr = f"{xpNeeded//1000}.{str(xpNeeded)[-3:-1]}k" if xpNeeded >= 1000 else str(xpNeeded)
    percentage = int((xp / xpNeeded) * 320)

    fullXPBar = Image.open('assets/level/Azalea-XP-Bar.png').convert("RGBA")
    xpStatus = fullXPBar.crop((0, 0, percentage, 80))

    # Create a palette-based version for better GIF compatibility
    # Get all frames from the source GIF first
    source_frames = []
    for frame in ImageSequence.Iterator(gif):
        source_frames.append(frame.copy())
    
    # Limit to max frames for stability
    max_frames = min(24, len(source_frames))  # Limit to 24 frames or less
    source_frames = source_frames[:max_frames]
    
    # Create output frames
    frames = []
    
    # Process each frame
    for i, source_frame in enumerate(source_frames):
        # Create a new RGB background with white (for proper GIF handling)
        composed = Image.new("RGB", (width, height), (255, 255, 255))
        
        # Convert source frame to RGB and paste it
        if hasattr(source_frame, 'convert'):
            bg_frame = source_frame.convert("RGB")
            composed.paste(bg_frame, (0, 0))
        
        # Now overlay all the UI elements
        # Using Image.alpha_composite requires RGBA mode
        composed_rgba = composed.convert("RGBA")
        
        # Create a separate RGBA image for all the UI elements
        ui_layer = Image.new("RGBA", composed.size, (0, 0, 0, 0))
        
        # Add all UI elements to the UI layer
        ui_layer.paste(xpStatus, (240, 146), xpStatus)
        ui_layer.paste(pfpImg, (15, 13), pfpImg)
        ui_layer.paste(overlay, (0, 0), overlay)
        ui_layer.paste(rankImg, (150, 121), rankImg)

        
        # Add text to UI layer
        draw = ImageDraw.Draw(ui_layer)
        draw.text((615, 140), f"{xpStr}/{xpNeededStr}", (240, 217, 108), font=font2, align='left', anchor='rb')
        draw.text((370, 70), f"{rankNum}", (240, 217, 108), font=font1)
        draw.text((440, 5), f'{level}', (240, 217, 108), font=font1)
        
        # Composite the UI layer onto the background
        composed_final = Image.alpha_composite(composed_rgba, ui_layer)
        
        # Convert back to RGB mode for GIF compatibility
        frames.append(composed_final.convert("RGB"))

    # Save animated GIF to buffer
    buffer = BytesIO()
    
    # Use PIL's GIF-specific save parameters
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=fixed_duration,
        loop=loop,
        optimize=False,
        disposal=2  # Restore to background color
    )
    buffer.seek(0)

    return buffer