from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Resampling
from io import BytesIO
import numpy as np
import requests

def rankingHandler(level, highest_level, ranking, user_id) -> (str, int):
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
    elif level >= highest_level*.6 and level > 20:
        rank = defaultDir + 'ranks/Master-1.png'
    elif level >= highest_level*.5 and level > 20:
        rank = defaultDir + 'ranks/Master-2.png'
    elif level >= highest_level*.3 and level > 20:
        rank = defaultDir + 'ranks/Master-3.png'
    elif level >= highest_level*.2 and level > 20:
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

    font1 = ImageFont.truetype('assets/cookieRunFont.ttf', size=30)
    font2 = ImageFont.truetype('assets/cookieRunFont.ttf', size=20)

    with Image.open('assets/level/Nurture_XP_Bot.jpg') as background:
        
        # load background
        background.load()

        # Open the PFP
        if url:
            pfpImg = Image.open(requests.get(pfp, stream=True).raw)
        else:
            pfpImg = Image.open(pfp)
        
        # Resizing PFP
        pfpImg = pfpImg.resize((176,176), resample=Resampling.LANCZOS)

        # Add a circular mask to the PFP image
        bigsize = (pfpImg.size[0] * 3, pfpImg.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(pfpImg.size, Resampling.LANCZOS)
        pfpImg.putalpha(mask)

        # Paste pfp into background
        background.paste(pfpImg, (18, 23), mask)

        # Place the rank icon
        rank, rankNum = rankingHandler(level, highest_level, ranking, user_id)

        rankImg = Image.open(rank)

        background.paste(rankImg, (207, 25), rankImg)

        # determine the xp needed and pasting the current progression
        xpStr = xp
        if xp >= 1000:
             xpStr = str(xp//1000) + '.' + str(xp)[-3:-1] + 'k'
        xpNeeded = 12*level**2+60
        xpNeededStr = xpNeeded
        if xpNeeded >= 1000:
            xpNeededStr = str(xpNeeded//1000) + '.' + str(xpNeeded)[-3:-1] + 'k'

        # Crop the progression bar
        percentage = int((xp/xpNeeded)*320)
        xpStatus = Image.open('assets/level/Green-XP-Bar.png')
        xpStatus = xpStatus.crop((0,0,percentage,21))

        background.paste(xpStatus, (255,162), xpStatus)
        
        # Create ImageDraw to add text 
        backgroundDraw = ImageDraw.Draw(background)

        # Drawing all of the text
        backgroundDraw.text((575,154), f"{xpStr}/{xpNeededStr}", (7,114,42), font=font2, align='left', anchor='rb')
        backgroundDraw.text((260,32), f"# {rankNum}", (7,114,42), font=font1)
        backgroundDraw.text((312,102), f'{level}', (7,114,42), font=font1)

        # save to a file-like data
        buffer = BytesIO()     
        background.save(buffer, 'png') 
        buffer.seek(0)  

        return buffer