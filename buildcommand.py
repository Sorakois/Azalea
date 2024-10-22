import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Literal
import misc

class HSRCharacter:
  def __init__(self, name, stats, trapri, bestlc, bestrelics, bestplanar, bestteam, buildauthor):
    self.name = name
    self.stats = stats
    self.trapri = trapri
    self.bestlc = bestlc
    self.bestrelics = bestrelics
    self.bestplanar = bestplanar
    self.bestteam = bestteam
    self.buildauthor = buildauthor

'''HSRCharacterList = [
    HSRCharacter(
      "acheron",
      "3000 ATK, 70% Crit Rate, 140% Crit DMG",
      "Ultimate > Talen > Skill > Basic",
      "Along the Passing Shore, Incessant Rain",
      "4P Pioneer Diver of Dead Waters or 4P Genius of Brilliant Stars",
      "Izumo Gensei and Takama Divine Realm, Inert Salsotto",
      "Pela, Silver Wolf, Jiaoqiu, Black Swan, Kafka, Fu Xuan, Sparkle, Aventurine",
    ),
    HSRCharacter(
      "argenti",
      "2500 ATK, 55% Crit Rate, 160% Crit DMG, 134+ SPD",
      "Ultimate > Skill > Talent > Basic",
      "An Instant Before a Gaze, Before Dawn",
      "4P Champion of Streetwise Boxing or 2PC Champion + Musketeer/Prisoner/Valorous",
      "Inert Salsotto; Sigonia, the Unclaimed Desolation",
      "Sparkle, Tingyun, Huohuo, Robin, Aventurine"
    )
]'''

'''Argenti = ""
Arlan = ""
Asta = ""
Aventurine = ""
Bailu = ""
Black_Swan = ""
Blade = ""
Boothill = ""
Bronya = ""
Clara = ""
Dan_Heng = ""
#Dr. Ratio
Dr_Ratio = ""
Feixiao = ""
Firefly = ""
Fu_Xuan = ""
Gallagher = ""
Gepard = ""
Guinaifen = ""
Hanya = ""
Herta = ""
Himeko = ""
Hook = ""
Huohuo = ""
Imbibitor_Lunae = ""
Jade = ""
Jingliu = ""
Jiaoqiu = ""
Jing_Yuan = ""
Kafka = ""
Lingsha = ""
Luka = ""
Luocha = ""
Lynx = ""
#Account for 2 types
March_7th = ""
Misha = ""
Moze = ""
Natasha = ""
Pela = ""
Qingque = ""
Rappa = ""
Robin = ""
Ruan_Mei = ""
Sampo = ""
Seele = ""
Serval = ""
Silver_Wolf = ""
Sparkle = ""
Sushang = ""
Tingyun = ""
Topaz = ""
#Account for 3 types
Trailblazer = ""
Welt = ""
Xueyi = ""
Yanqing = ""
Yukong = ""
Yunli = ""

#characterlist.append(Character(<name>, <stats>, <trapri>, <bestlc>, <bestrelics>, <bestteam>))
''''''Character = ["Recommended Stats", 
              "Trace Priority",   
              "Best LCs", 
              "Best Relics", 
              "Best Teams/Synergy"]''''''

    
        

class CRKBuilds:
    ''''''Common Rarity''''''
    GingerBrave = ""
    Strawberry_Cookie = ""
    Ninja_Cookie = ""
    Angel_Cookie = ""
    Muscle_Cookie = ""
    Wizard_Cookie = ""
    Beet_Cookie = ""
    ''''''Rare Rarity''''''
    Devil_Cookie = ""
    Custard_Cookie_III = ""
    Clover_Cookie = ""
    Carrot_Cookie = ""
    Avacado_Cookie = ""
    Pancake_Cookie = ""
    Onion_Cookie = ""
    Gumball_Cookie = ""
    Blueberry_Cookie = ""
    Adventure_Cookie = ""
    Alchemist_Cookie = ""
    Cherry_Cookie = ""
    Knight_Cookie = ""
    Princess_Cookie = ""
    ''''''Special Rarity''''''
    Cream_Ferret_Cookie = ""
    Icicle_Yeti_Cookie = ""
    Snapdragon_Cookie = ""
    Jung_Kook_Cookie = ""
    V_Cookie = ""
    Jimin_Cookie = ""
    #j-hope
    j_hope_Cookie = ""
    SUGA_Cookie = ""
    Jin_Cookie = ""
    RM_Cookie = ""
    Tails_Cookie = ""
    Sonic_Cookie = ""
    ''''''''Epic Rarity''''''
    Star_Coral_Cookie = ""
    Peach_Blossom_Cookie = ""
    Cloud_Haetae_Cookie = ""
    Street_Urchin_Cookie = ""
    Caramel_Choux_Cookie = ""
    Butter_Roll_Cookie = ""
    Matcha_Cookie = ""
    Mercurial_Knight_Cookie = ""
    Silverbell_Cookie = ""
    Rebel_Cookie = ""
    #creme brulee
    Crème_Brûlée_Cookie = ""
    Linzer_Cookie = ""
    Olive_Cookie = ""
    Mozzarella_Cookie = ""
    Fettuccine_Cookie = ""
    Burnt_Cheese_Cookie = ""
    Frilled_Jellyfish_Cookie = ""
    Peppermint_Cookie = ""
    Black_Lemonade_Cookie = ""
    Rockstar_Cookie = ""
    Tarte_Tatin_Cookie = ""
    Royal_Margarine_Cookie = ""
    #Kouign-Amann
    Kouign_Amann_Cookie = ""
    Prune_Juice_Cookie = ""
    Space_Doughnut = ""
    Blueberry_Pie_Cookie = ""
    Milky_Way_Cookie = ""
    Prophet_Cookie = ""
    Pinecone_Cookie = ""
    Carol_Cookie = ""
    Macaron_Cookie = ""
    #Schwarzwälder, Brute, Choco Werehound Brute
    Schwarzwalder = ""
    Candy_Diver_Cookie = ""
    Captain_Caviar_Cookie = ""
    Cream_Unicorn_Cookie = ""
    Financier_Cookie = ""
    Crunchy_Chip_Cookie = ""
    Wildberry_Cookie = ""
    Cherry_Blossom_Cookie = ""
    Caramel_Arrow_Cookie = ""
    Affogato_Cookie = ""
    Tea_Knight_Cookie = ""
    Eclair_Cookie = ""
    Cocoa_Cookie = ""
    Cotton_Cookie = ""
    Pumpkin_Pie_Cookie = ""
    Twizzly_Gummy_Cookie = ""
    Mala_Sauce_Cookie = ""
    Moon_Rabbit_Cookie = ""
    Raspberry_Cookie = ""
    Parfait_Cookie = ""
    Sorbet_Shark_Cookie = ""
    Squid_Ink_Cookie = ""
    Lilac_Cookie = ""
    Mango_Cookie = ""
    Red_Velvet_Cookie = ""
    Pastry_Cookie = ""
    Fig_Cookie = ""
    Strawberry_Crepe_Cookie = ""
    Black_Raisin_Cookie = ""
    Almond_Cookie = ""
    Cream_Puff_Cookie = ""
    Latte_Cookie = ""
    Kumiho_Cookie = ""
    Rye_Cookie = ""
    Espresso_Cookie = ""
    Madeleine_Cookie = ""
    Licorice_Cookie = ""
    Poison_Mushroom_Cookie = ""
    Milk_Cookie = ""
    Purple_Yam_Cookie = ""
    Pomegranate_Cookie = ""
    Chili_Pepper_Cookie = ""
    Sparkling_Cookie = ""
    Dark_Choco_Cookie = ""
    Herb_Cookie = ""
    Mint_Choco_Cookie = ""
    Werewolf_Cookie = ""
    Tiger_Lily_Cookie = ""
    Vampire_Cookie = ""
    Snow_Sugar_Cookie = ""
    ''''''Super Epic Rarity''''''
    Elder_Faerie_Cookie = ""
    Crimson_Coral_Cookie = ""
    Shining_Glitter_Cookie = ""
    Capsaicin_Cookie = ""
    Stardust_Cookie = ""
    Sherbet_Cookie = ""
    Oyster_Cookie = ""
    Clotted_Cream_Cookie = ""
    ''''''Dragon Rarity''''''
    Pitaya_Dragon_Cookie = ""
    ''''''Legendary Rarity''''''
    Stormbringer_Cookie = ""
    Moonlight_Cookie = ""
    Black_Pearl_Cookie = ""
    Frost_Queen_Cookie = ""
    Sea_Fairy_Cookie = ""
    Wind_Archer_Cookie = ""
    ''''''Ancient Rarity''''''
    Pure_Vanilla_Cookie = ""
    Hollyberry_Cookie = ""
    Dark_Cacao_Cookie = ""
    Golden_Cheese_Cookie = ""
    White_Lily_Cookie = ""
    ''''''Beast Rarity''''''
    Mystic_Flour_Cookie = ""'''
