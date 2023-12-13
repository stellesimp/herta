from typing import Optional
import typing
import discord
from discord import Client, Guild, app_commands
import json
from mihomo import Language, MihomoAPI, tools
from mihomo import errors as MihomoErrors
from mihomo.models import StarrailInfoParsed
import gspread
import requests as req
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests as req
from io import BytesIO
from threading import Thread
import time
import genshin
from genshin import errors as GenshinErrors
import os
from webserver import keep_alive

keep_alive()

imagepath = os.path.dirname(__file__) + '/'

scope = ['https://www.googleapis.com/auth/spreadsheets',
   'https://www.googleapis.com/auth/drive']
Credentials = ServiceAccountCredentials.from_json_keyfile_name('Herta.json', scope)
database = gspread.authorize(Credentials)
# pity = database.open('Herta DB').Pity

TOKEN = ''

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents, allowmention = discord.AllowedMentions(everyone= True))
tree = app_commands.CommandTree(client=bot)
member = discord.Member

bc = genshin.Client(game = genshin.Game.STARRAIL)
bc.set_cookies({'ltuid': 236918609, 'ltoken':'t2xW0Gl4CvCHnwT4SEWH8eFsZYWRmiMvRxvbQ3v5'})

@bot.event
async def on_ready():
  await bot.change_presence(status=discord.Status.online, activity=discord.Activity(application_id=1103660074272034886, name='/builds and /moc', type= discord.ActivityType.playing, state= 'Controlling Herta Space Station', details= 'x2 Planar right now', assets= {'large_image': 'kurukuru'}))
  await tree.sync()
  print('hi')

@tree.command(name = 'egg', description='Easter Egg')
async def res(interaction: discord.Interaction):
  channel = bot.get_channel(interaction.channel.id)
  await channel.send('Ai có lòng hảo tâm xin hãy gift ' + '<@' + str(526231610312359957) + '>' + ' 1 tháng Discord Nitro')

@tree.command(name= 'builds', description= 'Hiển thị build nhân vật của bạn')
@app_commands.describe(uid = 'Honkai: Star Rail UID', lang = 'Your Prefered Language')
@app_commands.rename(lang = 'language')
async def v2(interaction: discord.Interaction, uid: int, lang: str):
  commanduser = interaction.user.id
  match lang:
    case 'VI':
      await interaction.response.send_message('Đang lấy thông tin...')
      client = MihomoAPI(language=Language.VI)	
      try:
        user = await bc.get_starrail_challenge(uid = uid, lang = 'vi-vn')
      except:
        pass
    case 'EN':
      await interaction.response.send_message('Fetching Data...')
      client = MihomoAPI(language=Language.EN)
      try:
        user = await bc.get_starrail_challenge(uid = uid, lang = 'en-us')
      except:
        pass
  try:
    data: StarrailInfoParsed = await client.fetch_user(uid, replace_icon_name_with_url=True)
  except MihomoErrors.InvalidParams:
    match lang:
      case 'VI':
        await interaction.edit_original_response(content= 'UID không hợp lệ!', view = None)
        raise
      case 'EN':
        await interaction.edit_original_response(content= 'Invalid UID!', view = None)
        raise
  except MihomoErrors.UserNotFound:
    match lang:
      case 'VI':
        await interaction.edit_original_response(content= 'Không tìm thấy người dùng!', view = None)
        raise
      case 'EN':
        await interaction.edit_original_response(content= 'User not Found!', view = None)
        raise
  except IndexError:
    match lang:
      case 'VI':
        await interaction.edit_original_response(content= 'Hãy public thông tin builds của nhân vật trong cài đặt trước khi sử dụng bot!', view = None)
        raise
      case 'EN':
        await interaction.edit_original_response(content= "Please public your characters' build data first before using the bot!", view = None)
        raise
  data = tools.remove_duplicate_character(data)
  characters = []
  for i in range(len(data.characters)):
    characters.append(discord.SelectOption(label = data.characters[i].name, value = str(i)))
  async def select_callback(interaction: discord.Interaction):
    def card(chardata, R: int, G: int, B: int):
      global builds
      builds = Image.new('RGBA',size=(1200, 600), color=(R, G, B, 255))
      path = Image.open(req.get(chardata.path.icon, stream = True).raw)
      path = path.resize((24, int(path.height*(24/float(path.width)))), Image.Resampling.LANCZOS)
      drip = Image.open(req.get(chardata.portrait, stream = True).raw)
      drip = drip.resize((int(drip.width*(425/float(drip.height))), 425), Image.Resampling.LANCZOS)
      element = Image.open(req.get(chardata.element.icon, stream = True).raw)
      element = element.resize((24, int(element.height*(24/float(element.width)))), Image.Resampling.LANCZOS)
      overlay = Image.open(req.get('https://enka.network/img/overlay.jpg', stream = True).raw)
      overlay = overlay.crop((0,0,1200,600))
      overlay = overlay.convert('RGBA')
      builds = Image.blend(builds, overlay, alpha=0.40)
      builds.alpha_composite(drip.filter(ImageFilter.GaussianBlur(2.5)), (0, 160))
      builds.alpha_composite(drip, (0, 160))
      ImageDraw.Draw(builds).text((19,180), f'{chardata.name}   -   Lv. {chardata.level}/{chardata.max_level}', font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), fill= (255, 255, 255), stroke_width=1, stroke_fill=(0,0,0))
      ImageDraw.Draw(builds).text((48,206), chardata.element.name, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), fill= (255, 255, 255), stroke_width=1, stroke_fill=(0,0,0))
      ImageDraw.Draw(builds).text((48,236), chardata.path.name, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), fill= (255, 255, 255), stroke_width=1, stroke_fill=(0,0,0))
      builds.alpha_composite(element, (16,202))
      builds.alpha_composite(path, (16,232))
      attributefield = []
      attributevalue = []
      for index, item in enumerate(chardata.attributes):
        cache = Image.open(req.get(item.icon, stream = True).raw)
        cache = cache.resize((int(cache.width * (25/float(cache.height))), 25), Image.Resampling.LANCZOS)
        builds.alpha_composite(cache, (450, (243 + 30 * index)))
        ImageDraw.Draw(builds).text((475, (257 + 30 * index)), item.name, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor='lm')
        attributefield.append(item.field)
        attributevalue.append(item.displayed_value) #fixing, decorate the code later
      counter = 0
      check = []
      for index, item in enumerate(chardata.additions):
        if item.field not in attributefield:
          if item.field == 'sp_rate':
            cache = Image.open(req.get(item.icon, stream = True).raw)
            cache = cache.resize((int(cache.width * (25/float(cache.height))), 25), Image.Resampling.LANCZOS)
            builds.alpha_composite(cache, (450, (423 + 30 * counter)))
            addition = item.displayed_value.split('%')
            sum = str(float(addition[0]) + 100) + '%'
            ImageDraw.Draw(builds).text((475, (437 + 30 * counter)), item.name, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor = 'lm')
            ImageDraw.Draw(builds).text((780, (437 + 30 * counter)), sum, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor='rm')
            counter += 1
          else:
            cache = Image.open(req.get(item.icon, stream = True).raw)
            cache = cache.resize((int(cache.width * (25/float(cache.height))), 25), Image.Resampling.LANCZOS)
            builds.alpha_composite(cache, (450, (423 + 30 * counter)))
            ImageDraw.Draw(builds).text((475, (437 + 30 * counter)), item.name, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor = 'lm')
            ImageDraw.Draw(builds).text((780, (437 + 30 * counter)), item.displayed_value, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor='rm')
            counter += 1
        else:
          try:
            sum = str(int(item.displayed_value) + int(attributevalue[attributefield.index(item.field)])) 
            ImageDraw.Draw(builds).text((780, (257 + 30 * attributefield.index(item.field))), sum, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor='rm')
            check.append(item.field)
          except ValueError:
            addition = item.displayed_value.split('%')
            attribute = attributevalue[attributefield.index(item.field)].split('%')
            sum = str(float(addition[0]) + float(attribute[0])) + '%'
            ImageDraw.Draw(builds).text((780, (257 + 30 * attributefield.index(item.field))), sum, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor='rm')
            check.append(item.field)
      for index, item in enumerate(attributefield):
        if item not in check:
          ImageDraw.Draw(builds).text((780, (257 + 30 * index)), attributevalue[index], font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 18), fill= (255, 255, 255), anchor='rm')
      lightcone = Image.open(req.get(chardata.light_cone.icon, stream = True).raw)
      lightcone = lightcone.resize((63,65), Image.Resampling.LANCZOS)
      builds.alpha_composite(lightcone, (450,174))
      cache = Image.new('RGBA', builds.size, (255, 255, 255, 0))
      ImageDraw.Draw(cache).rounded_rectangle((530, 211, 560, 236), radius=3, fill= (0, 0, 0, 40))
      ImageDraw.Draw(cache).rounded_rectangle((575, 211, 675, 236), radius=3, fill= (0, 0, 0, 40))
      builds.alpha_composite(cache, (0,0))
      if len(chardata.light_cone.name) > 27:
        ImageDraw.Draw(builds).text((530, 190), f'{chardata.light_cone.name[:24]}...', font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), fill= (255, 255, 255), anchor='lm')
      else:
        ImageDraw.Draw(builds).text((530, 190), chardata.light_cone.name, font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), fill= (255, 255, 255), anchor='lm')
      ImageDraw.Draw(builds).text((535, 225), f'S{chardata.light_cone.superimpose}     Lv. {chardata.light_cone.level}/{chardata.light_cone.max_level}', font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), fill= (255, 255, 255), anchor='lm')
      circle = Image.open("/home/container/elements/circle.png")
      lock = Image.open("/home/container/elements/lock.png")
      lock = lock.resize((15,15), Image.Resampling.LANCZOS)
      for i in range(6):
        if (chardata.eidolon - 1) >= i:
          cache = Image.open(req.get(chardata.eidolon_icons[i], stream = True).raw)
          cache = cache.resize((40,40), Image.Resampling.LANCZOS)
          builds.alpha_composite(circle, (20, (275 + i * 45)))
          builds.alpha_composite(cache, (20, (275 + i * 45)))
        else:
          builds.alpha_composite(circle, (20, (275 + i * 45)))
          builds.alpha_composite(lock, (32, (287 + i * 45)))
      counter=0
      for index, item in enumerate(chardata.traces):	
        if item.type in ['Normal','BPSkill','Ultra','Talent','Maze']:
          cache = Image.open(req.get(item.icon, stream = True).raw)
          cache = cache.resize((40, 40), Image.Resampling.LANCZOS)
          builds.alpha_composite(circle, (380, (300 + 50 * counter)))
          builds.alpha_composite(cache, (380, (300 + 50 * counter)))
          ImageDraw.Draw(builds).text((405, (340 + 50 * counter)), f'{item.level}', font= ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 15), fill= (255, 255, 255), anchor='lm', stroke_width=2, stroke_fill=(0,0,0))
          counter += 1
          if counter == 5:
            break
    def relic(chardata):
      global cache
      mask = Image.open(req.get('https://raw.githubusercontent.com/KT-Yeh/enka-card/master/enka_card/attributes/Assets/artifact_mask.png', stream = True).raw).convert('L')
      cache = Image.new('RGBA', size= (1200, 600), color= (255,255,255, 0))
      counter = 0
      for index, relic in enumerate(chardata.relics):
        counter = 6 + counter
        ImageDraw.Draw(cache).rounded_rectangle((795, counter, 1195, (counter + 93)), fill = (0, 0, 0, 60), radius = 4, outline = (255,255,255))
        relicicon = Image.open(req.get(relic.icon, stream = True).raw)
        relicicon = relicicon.resize((int(relicicon.width * 85/float(relicicon.height)), 85), Image.Resampling.LANCZOS)
        relicicon = relicicon.crop((5,0, relicicon.width, relicicon.height))
        mask = mask.resize((relicicon.width, relicicon.height), Image.NEAREST)
        overlay = Image.new('RGBA', relicicon.size, (0,0,0,0))
        overlay.paste(relicicon, (0,0), mask)
        cache.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(2.5)), (798, counter))
        cache.alpha_composite(overlay, (798, counter))
        ImageDraw.Draw(cache).line((940, counter + 4, 940, counter + 89), fill= (255,255,255))
        statsicon = Image.open(req.get(relic.main_affix.icon, stream = True).raw)
        statsicon = statsicon.resize((35,35), Image.Resampling.LANCZOS)
        cache.alpha_composite(statsicon, (900, counter + 10))
        ImageDraw.Draw(cache).text((930, counter + 55), f'{relic.main_affix.displayed_value}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'rm')
        match relic.rarity:
          case 3:
            rarity = Image.open(req.get('https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/deco/Rarity3.png', stream = True).raw)
            rarity = rarity.resize((int(rarity.width * 30/float(rarity.height)),30), Image.Resampling.LANCZOS)
            cache.alpha_composite(rarity, (868, counter + 60))
          case 4:
            rarity = Image.open(req.get('https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/deco/Rarity4.png', stream = True).raw)
            rarity = rarity.resize((int(rarity.width * 30/float(rarity.height)),30), Image.Resampling.LANCZOS)
            cache.alpha_composite(rarity, (854, counter + 60))
          case 5:
            rarity = Image.open(req.get('https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/deco/Rarity5.png', stream = True).raw)
            rarity = rarity.resize((int(rarity.width * 30/float(rarity.height)),30), Image.Resampling.LANCZOS)
            cache.alpha_composite(rarity, (840, counter + 60))
        ImageDraw.Draw(cache).rounded_rectangle((830, counter + 65, 860, counter + 80), 3, (0,0,0, 100))
        ImageDraw.Draw(cache).text((845, counter + 75), f'+{relic.level}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 15), 'mm')
        for subindex, substat in enumerate(relic.sub_affixes):
          match subindex:
            case 0:
              statsicon = Image.open(req.get(substat.icon, stream = True).raw)
              statsicon = statsicon.resize((35,35), Image.Resampling.LANCZOS)
              cache.alpha_composite(statsicon, (945, counter + 5))
              ImageDraw.Draw(cache).text((985, counter + 23), substat.displayed_value, (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
            case 1:
              statsicon = Image.open(req.get(substat.icon, stream = True).raw)
              statsicon = statsicon.resize((35,35), Image.Resampling.LANCZOS)
              cache.alpha_composite(statsicon, (1070, counter + 5))
              ImageDraw.Draw(cache).text((1115, counter + 23), substat.displayed_value, (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
            case 2:
              statsicon = Image.open(req.get(substat.icon, stream = True).raw)
              statsicon = statsicon.resize((35,35), Image.Resampling.LANCZOS)
              cache.alpha_composite(statsicon, (945, counter + 49))
              ImageDraw.Draw(cache).text((985, counter + 67), substat.displayed_value, (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
            case 3:
              statsicon = Image.open(req.get(substat.icon, stream = True).raw)
              statsicon = statsicon.resize((35,35), Image.Resampling.LANCZOS)
              cache.alpha_composite(statsicon, (1070, counter + 49))
              ImageDraw.Draw(cache).text((1115, counter + 67), substat.displayed_value, (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
        counter = counter + 93
    def playerprofile(playerdata):
      global profile
      profile = Image.new('RGBA',size=(1200, 600), color=(0,0,0,0))
      avatar = Image.open(req.get(playerdata.avatar.icon, stream= True).raw)
      avatar = avatar.resize((140, 140), Image.Resampling.LANCZOS)
      profile.alpha_composite(avatar, (5, 5))
      ImageDraw.Draw(profile).rectangle((-10, -10, 780, 160), outline= (255,255,255), fill = None)
      if playerdata.signature == '':
        info = f'{playerdata.name}'
      else:
        info = f'{playerdata.name} - {playerdata.signature}'
      if len(info) > 31:
        ImageDraw.Draw(profile).text((150, 25), f'{info[:28]}...', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
      else:
        ImageDraw.Draw(profile).text((150, 25), info, (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
      ImageDraw.Draw(profile).line((460, 10, 460, 150), (255,255,255))
      match lang:
        case 'VI':
          ImageDraw.Draw(profile).text((150, 55), f'Cấp khai phá {playerdata.level} - Cấp cân bằng {playerdata.world_level}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
          ImageDraw.Draw(profile).text((150, 85), f'Số thành tựu đã đạt được: {playerdata.achievements}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
          ImageDraw.Draw(profile).text((150, 115), f'Số nhân vật đã có: {playerdata.characters}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
          ImageDraw.Draw(profile).text((620, 65), f'Tiến độ MoC hiện tại:', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
          try:
            moc = user.max_floor
            while '<' in moc:
              moc = moc.replace(moc[moc.find('<'):moc.find('>')+1], '')
            if len(moc) > 24:
              ImageDraw.Draw(profile).text((620, 95), f'{moc[:21]}... {playerdata.forgotten_hall.memory_of_chaos} | {user.floors[0].star_num} sao', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
            else:
              ImageDraw.Draw(profile).text((620, 95), f'{moc} | {user.floors[0].star_num} sao', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
          except:
            ImageDraw.Draw(profile).text((620, 95), f'Không có dữ liệu :(', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
        case 'EN':
          ImageDraw.Draw(profile).text((150, 55), f'TL. {playerdata.level} - Equilibrium Lv. {playerdata.world_level}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
          ImageDraw.Draw(profile).text((150, 85), f'No. of Achievements: {playerdata.achievements}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
          ImageDraw.Draw(profile).text((150, 115), f'No. of Characters obtained: {playerdata.characters}', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'lm')
          ImageDraw.Draw(profile).text((620, 65), f'Current Progress of MoC:', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
          try:
            moc = user.max_floor
            while '<' in moc:
              moc.replace(moc[moc.find('<'):moc.find('>')+1], '')
            if len(moc) > 14:
              ImageDraw.Draw(profile).text((620, 95), f'{moc[:11]}...{moc[len(user.max_floor) - 8:]} | {user.floors[0].star_num} star(s)', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
            else:
              ImageDraw.Draw(profile).text((620, 95), f'{user.max_floor} | {user.floors[0].star_num} star(s)', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
          except:
            ImageDraw.Draw(profile).text((620, 95), f'No Data :(', (255,255,255), ImageFont.truetype(imagepath + 'GMV_DIN_Pro-Bold.ttf', 20), 'mm')
    if interaction.user.id == commanduser:
      select.disabled = True
      match lang:
        case 'VI':
          await msg.edit(content = 'Xin hãy đợi...', view=None)
        case 'EN':
          await msg.edit(content = 'Please wait...', view=None)
      chardata = data.characters[int(select.values[0])] 
      playerdata = data.player
      match chardata.element.id:
        case 'Quantum':
          t1 = Thread(target=card, args= (chardata, 84, 74, 194,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
        case 'Thunder':
          t1 = Thread(target=card, args= (chardata, 146, 95, 160,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
        case 'Physical':
          t1 = Thread(target=card, args= (chardata, 193, 196, 192,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
        case 'Ice':
          t1 = Thread(target=card, args= (chardata, 38, 146, 211,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None) 
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
        case 'Wind':
          t1 = Thread(target=card, args= (chardata,71, 191, 131,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
        case 'Imaginary':
          t1 = Thread(target=card, args= (chardata, 244, 222, 47,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
        case 'Fire':
          t1 = Thread(target=card, args= (chardata, 227, 43, 41,))
          t2 = Thread(target= relic, args = (chardata,))
          t3 = Thread(target= playerprofile, args = (playerdata,))
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang lấy thông tin...', view = None)
            case 'EN':
              await msg.edit(content= 'Fetching Data', view = None)
          t1.start()
          t2.start()
          t3.start()
          time.sleep(10)
          t2.join()
          t1.join()
          t3.join()
          match lang:
            case 'VI':
              await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
            case 'EN':
              await msg.edit(content= 'Completing Image', view = None)
          await msg.edit(content= 'Đang hoàn thiện ảnh...', view= None)
          builds.alpha_composite(cache, (0,0))
          builds.alpha_composite(profile, (0,0))
          byte = BytesIO()
          builds.save(byte, format="PNG")
          byte.seek(0)
          dfile = discord.File(byte, filename ="card.png")
          match lang:
            case 'VI':
              await msg.edit(content = f'Đây là Build của {chardata.name}', view= None,attachments= [dfile])
            case 'EN':
              await msg.edit(content = f'Here is your {chardata.name}\'s build', view= None,attachments= [dfile])
    else:
      match lang:
        case 'VI':
          await msg.edit(content = f'Bạn không phải là người đã thực hiện câu lệnh!', view = view)
        case 'EN':
          await msg.edit(content = f'You are not the one who excuted the command!', view = view)
  match lang:
    case 'VI':
      select = discord.ui.Select(options = characters, placeholder= 'Chọn một nhân vật')
      view = discord.ui.View()
      view.add_item(select)
      msg = await interaction.edit_original_response(content='Hãy chọn một nhân vật', view=view)
    case 'EN':
      select = discord.ui.Select(options = characters, placeholder= 'Choose a character')
      view = discord.ui.View()
      view.add_item(select)
      msg = await interaction.edit_original_response(content='Please choose a character', view=view)
  select.callback = select_callback

@v2.autocomplete('lang')
async def autocompletion(
  interaction: discord.Interaction,
  current: str
) -> typing.List[app_commands.Choice[str]]:
  data = []
  for choice in ['VI', 'EN']:
    if current.upper() in choice.upper():
      data.append(app_commands.Choice(name=choice, value=choice))
  return data

@tree.command(name= 'moc', description= 'Hiển thị tiến độ MoC')
@app_commands.describe(uid = 'Honkai: Star Rail UID', lang = 'Your Prefered Language')
@app_commands.rename(lang = 'language')
async def MoC(interaction: discord.Interaction, uid: int, lang: str):
  nameclient = MihomoAPI(language=Language.VI)
  match lang:
    case 'VI':
      await interaction.response.send_message('Xin hãy đợi...')
      try:
        data: StarrailInfoParsed = await nameclient.fetch_user(uid, replace_icon_name_with_url=True)
        user = await bc.get_starrail_challenge(uid = uid, lang= 'vi-vn')
        characters = await bc.get_starrail_characters(uid = uid, lang= 'vi-vn')
      except MihomoErrors.InvalidParams:
        await interaction.edit_original_response(content= 'UID không hợp lệ!')
      except GenshinErrors.DataNotPublic:
        await interaction.edit_original_response(content= 'Bạn chưa công khai thông tin chiến tích của bạn!')
      floors = []
      floorsname = []
      for i in range(len(user.floors)):
        name = user.floors[i].name
        while '<' in name:
          name = name.replace(name[name.find('<'):name.find('>')+1], '')
        if name[len(name) - 1] != '0':
          floors.append(discord.SelectOption(label = f'Tầng {name[len(name) - 1]}', value = str(i)))
          floorsname.append(f'Tầng {name[len(name) - 1]}')
        else:
          floors.append(discord.SelectOption(label = f'Tầng {name[len(name) - 2:]}', value = str(i)))
          floorsname.append(f'Tầng {name[len(name) - 2:]}')
    case 'EN':
      await interaction.response.send_message('Please wait...')
      try:
        data: StarrailInfoParsed = await nameclient.fetch_user(uid, replace_icon_name_with_url=True)
        user = await bc.get_starrail_challenge(uid = uid, lang= 'en-us')
        characters = await bc.get_starrail_characters(uid = uid, lang= 'en-us')
      except MihomoErrors.InvalidParams:
        await interaction.edit_original_response(content= 'Invalid UID!')
      except GenshinErrors.DataNotPublic:
        await interaction.edit_original_response(content= "You haven't public your Battle Records!")
      floors = []
      for i in range(len(user.floors)):
        name = floors.name
        while '<' in name:
          name = name.replace(name[name.find('<'):name.find('>')+1], '')
        if name[len(name) - 1] != '0':
          floors.append(discord.SelectOption(label = f'Floor {name[len(name) - 1]}', value = str(i)))
          floorsname.append(f'Floor {name[len(name) - 1]}')
        else:
          floors.append(discord.SelectOption(label = f'Floor {name[len(name) - 2:]}', value = str(i)))
          floorsname.append(f'Floor {name[len(name) - 2:]}')
  basic = data.player
  async def select_callback(interaction: discord.Interaction):
    match lang:
      case 'VI':
        await msg.edit(content= 'Xin hãy đợi một lát...', view= None)
      case 'EN':
        await msg.edit(content= 'Please wait...', view= None)
    bg = Image.open(req.get('https://act.hoyolab.com/app/community-game-records-sea/images/abyss_review_bg@pc.faecaa6c.png', stream= True).raw).convert('RGBA')
    cache = Image.new('RGBA',size=(bg.size), color=(255,255,255,0))
    targetfloor = user.floors[int(select.values[0])]
    name = floorsname[int(select.values[0])]
    fname = targetfloor.name
    while '<' in fname:
      fname = fname.replace(fname[fname.find('<'):fname.find('>')+1], '')
    charasid = []
    for item in characters.avatar_list:
      charasid.append(item.id)
    print(charasid)
    if name[len(name) - 1] != '0':
      ImageDraw.Draw(cache).text((348, 75), f'{fname[:len(fname) - 2]}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
    else:
      ImageDraw.Draw(cache).text((348, 75), f'{fname[:len(fname) - 3]}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
    ImageDraw.Draw(cache).text((348, 125), f'{user.begin_time.day}/{user.begin_time.month}/{user.begin_time.year} - {user.end_time.day}/{user.end_time.month}/{user.end_time.year}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
    match lang:
      case 'VI':
        ImageDraw.Draw(cache).text((1044, 75), f'{basic.name} - Cấp khai phá {basic.level}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
        ImageDraw.Draw(cache).text((1044, 125), f'{name} - {targetfloor.star_num} sao - {targetfloor.round_num} lượt', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
      case 'EN':
        ImageDraw.Draw(cache).text((1044, 75), f'{basic.name} - Trailblaze Level {basic.level}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
        ImageDraw.Draw(cache).text((1044, 125), f'{name} - {targetfloor.star_num} star(s) - {targetfloor.round_num} cycle(s)', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 40), 'mm')
    bg.alpha_composite(cache)
    star5 = Image.open(req.get('https://act.hoyolab.com/app/community-game-records-sea/images/character_r_5.99d42eb7.png', stream = True).raw).convert('RGBA')
    star5 = star5.resize((245, 289), Image.Resampling.LANCZOS)
    star4 = Image.open(req.get('https://act.hoyolab.com/app/community-game-records-sea/images/character_r_4.24f329b7.png', stream = True).raw).convert('RGBA')
    star4 = star4.resize((245, 289), Image.Resampling.LANCZOS)
    for index, item in enumerate(targetfloor.node_1.avatars):
      chara = Image.open(req.get(item.icon, stream = True).raw)
      chara = chara.resize((int(chara.width * (289/float(chara.height))), 289), Image.Resampling.LANCZOS)
      cache = Image.new('RGBA', chara.size, (0,0,0,0))
      id = item.id
      match item.rarity:
        case 5:
          cache.alpha_composite(star5, (0,0))
          cache.alpha_composite(chara, (0,0))
        case 4:
          cache.alpha_composite(star4, (0,0))
          cache.alpha_composite(chara, (0,0))
      try:
        eidolon = characters.avatar_list[charasid.index(id)].rank
      except:
        ImageDraw.Draw(cache).text((0,15), f'Unknown', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 30), 'lm', stroke_width= 2, stroke_fill= (0,0,0))
      else:
        ImageDraw.Draw(cache).text((0,15), f'E{eidolon}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 30), 'lm', stroke_width= 2, stroke_fill= (0,0,0))
      bg.alpha_composite(cache, (83 + index * 327, 189))
      lv = f'Lv. {item.level}'
      ImageDraw.Draw(bg).rectangle((83 + index * 327, 438, 83 + index * 327 + 245, 478), (0,0,0))
      ImageDraw.Draw(bg).text((206 + 327 * index, 458), lv, (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 30), 'mm')
    for index, item in enumerate(targetfloor.node_2.avatars):
      chara = Image.open(req.get(item.icon, stream = True).raw)
      chara = chara.resize((int(chara.width * (289/float(chara.height))), 289), Image.Resampling.LANCZOS)
      cache = Image.new('RGBA', chara.size, (0,0,0,0))
      id = item.id
      match item.rarity:
        case 5:
          cache.alpha_composite(star5, (0,0))
          cache.alpha_composite(chara, (0,0))
        case 4:
          cache.alpha_composite(star4, (0,0))
          cache.alpha_composite(chara, (0,0))
      try:
        eidolon = characters.avatar_list[charasid.index(id)].rank
      except:
        ImageDraw.Draw(cache).text((0,15), f'Unknown', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 30), 'lm', stroke_width= 2, stroke_fill= (0,0,0))
      else:
        ImageDraw.Draw(cache).text((0,15), f'E{eidolon}', (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 30), 'lm', stroke_width= 2, stroke_fill= (0,0,0))
      bg.alpha_composite(cache, (83 + index * 327, 498))
      lv = f'Lv. {item.level}'
      ImageDraw.Draw(bg).rectangle((83 + index * 327, 747, 83 + index * 327 + 245, 787), (0,0,0))
      ImageDraw.Draw(bg).text((206 + 327 * index, 767), lv, (255,255,255), ImageFont.truetype('GMV_DIN_Pro-Bold.ttf', 30), 'mm')
    byte = BytesIO()
    bg.save(byte, format="PNG")
    byte.seek(0)
    dfile = discord.File(byte, filename ="card.png")
    match lang:
      case 'VI':
        await msg.edit(content = f'Đây là {name}', view= view,attachments= [dfile])
      case 'EN':
        await msg.edit(content = f'This is {name}', view= view,attachments= [dfile])
  if floors != []:
    match lang:
      case 'VI':
        select = discord.ui.Select(options = floors, placeholder= 'Chọn một tầng')
        view = discord.ui.View()
        view.add_item(select)
        msg = await interaction.edit_original_response(content='Hãy chọn một tầng', view=view)
      case 'EN':
        select = discord.ui.Select(options = floors, placeholder= 'Choose a floor')
        view = discord.ui.View()
        view.add_item(select)
        msg = await interaction.edit_original_response(content='Please choose a floor', view=view)
    select.callback = select_callback
  else:
    match lang:
      case 'VI':
        await interaction.edit_original_response(content= 'Không có dữ liệu! :(')
      case 'EN':
        await interaction.edit_original_response(content= 'No Data! :(')
@MoC.autocomplete('lang')
async def autocompletion(
  interaction: discord.Interaction,
  current: str
) -> typing.List[app_commands.Choice[str]]:
  data = []
  for choice in ['VI', 'EN']:
    if current.upper() in choice.upper():
      data.append(app_commands.Choice(name=choice, value=choice))
  return data

bot.run(TOKEN)
