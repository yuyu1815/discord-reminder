import datetime
from pydoc import describe

import discord
from discord import app_commands
from discord.app_commands import Choice
from dotenv import load_dotenv
import os
from sqlite_edit import Database

load_dotenv()
discord_intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=discord_intents,activity=discord.Game("稼働中"))
tree = app_commands.CommandTree(client)
def say_embed(color:int,title:str, message:str, img_url:str = None):
    """
    :param color: 0xで指定してください
    :param title:  title部分
    :param message: 中身
    :param img_url: 画像URL
    :return:　discord.Embed
    """
    embed = discord.Embed(title=title, description=message, color=color)
    if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
        embed.set_image(url=img_url)
    return embed
def say_embed_field(color: int, title: str, message: list[dict[str, str]])->list[discord.Embed]:
    embed:list[discord.Embed] = [discord.Embed(title=title, color=color)]
    for i, item in enumerate(message):
        embed_count = 0
        v_tmp = 0
        for k, v in item.items():
            #vはstrじゃないので修正時気を付けてください
            if len(str(v))+v_tmp > 800:
                embed_count += 1
                v_tmp = 0
                embed[embed_count] = discord.Embed(title=f"{title}({embed_count+1})", color=color)
            else:
                embed[embed_count].add_field(name=k, value=v, inline=True)
                v_tmp += len(str(v))
    return embed
def format_setting(setting):
    id, _, _, setting_type, call_time, _, title, _, _ = setting
    formatted_time = format_time(setting_type, call_time)
    return {"id": id, "title": title, "time": formatted_time}
def format_time(setting_type, call_time):
    if "month" in setting_type:
        # 月
        day, time = call_time.split("-")
        # 第?曜日
        if "/" in time:
            formatted_time = f"第{day.split('/')[0]} {day.split('/')[1]}曜日 {time.split(':')[0]}時{time.split(':')[1]}分{time.split(':')[2]}秒"
        # 日時
        else:
            formatted_time = f"{day}日 {time.split(':')[0]}時{time.split(':')[1]}分{time.split(':')[2]}秒"
    elif "week" in setting_type:
        # 週
        week,time = call_time.split('-')
        formatted_time = f"{week}曜日 {time.split(':')[0]}時{time.split(':')[1]}分{time.split(':')[2]}秒"
    else:
        # 日
        formatted_time = f"{call_time.split(':')[0]}時{call_time.split(':')[1]}分{call_time.split(':')[2]}秒"
    return formatted_time
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await tree.sync()

@tree.command(name='setup',description="初期設定をします")
async def setup(ctx):
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
        db.create_table()
        db.close()
        await ctx.response.send_message(embed=say_embed(color=0x00ff00, title="設定完了",message="設定が完了しました"))
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定中にエラーが発生しました"))
@tree.command(name='one-time',description='1回のみの通知')
@app_commands.describe(day="日時 mm/dd 例(1/1)")
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def one_time(ctx:discord.Interaction,day:str,time:str,mention:discord.Role=None,title:str=None,message:str=None,ico:str=None):
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        if not(1 <= int(day.split("/")[0]) <= 12 and 1 <= int(day.split("/")[1]) <= 31):
            await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="日付が不正です"))
            return
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        db.set(guild_id=str(ctx.guild.id),
               channel_id=str(ctx.channel.id),
               option_id="month",
               call_time=f"{day}-{data_time}",
               mention_ids = str(mention.id) if mention else "None",
               title=str(title) if title else "おしらせ",
               main_text =  message if message else "時間です",
               img=ico if ico else "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎月{day}-{data_time} にメッセージを<#{ctx.channel.id}>に送信するように設定しました"))
    except:
       await ctx.response.send_message(embed=say_embed(color=0xff0000,title="失敗",message="日付、時間の形式が間違えています。"))
    finally:
        db.close()
@tree.command(name='month-time',description='毎月通知します week 引数を使うと曜日を指定することができます')
@app_commands.describe(day="日 or 第?曜日 dd 例(10)")
@app_commands.choices(week=[
    Choice(name="月", value="monday"),
    Choice(name="火", value="tuesday"),
    Choice(name="水", value="wednesday"),
    Choice(name="木", value="thursday"),
    Choice(name="金", value="friday"),
    Choice(name="土", value="saturday"),
    Choice(name="日", value="sunday"),
])
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def month_time(ctx:discord.Interaction,day:str,time:str,week:str = None,mention:discord.Role=None,title:str=None,message:str=None,ico:str=None):
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        day = int(day)
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        if week:
            if 1 < day < 4:
                await ctx.response.send_message(embed=say_embed(color=0xff0000,title="失敗",message="曜日を入力してください"))
                return
            say_day = f"第{day} {week.name}曜日{data_time}"
            day = f"{day}/{week.name}"
        else:
            if 1 < day < 31:
                await ctx.response.send_message(embed=say_embed(color=0xff0000,title="失敗", message="1~31日以内でを入力してください"))
                return
            say_day = f"{day}日{data_time}"
        db.set(guild_id=str(ctx.guild.id),
               channel_id=str(ctx.channel.id),
               option_id="month",
               call_time=f"{day}-{data_time}",
               mention_ids = str(mention.id) if mention else "None",
               title=str(title) if title else "おしらせ",
               main_text =  message if message else "時間です",
               img=ico if ico else "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎月 {say_day} にメッセージを送信するように設定しました"))
    except:
       await ctx.response.send_message(embed=say_embed(color=0xff0000,title="失敗",message="日付、時間の形式が間違えています。"))
    finally:
        db.close()
@tree.command(name='week-time', description='毎週通知します')
@app_commands.describe(week="曜日")
@app_commands.choices(week=[
    Choice(name="月", value="monday"),
    Choice(name="火", value="tuesday"),
    Choice(name="水", value="wednesday"),
    Choice(name="木", value="thursday"),
    Choice(name="金", value="friday"),
    Choice(name="土", value="saturday"),
    Choice(name="日", value="sunday"),
])
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def week_time(ctx: discord.Interaction, week: Choice[str],time:str,mention:discord.Role=None,title:str=None,message:str=None,ico:str=None): # 引数名をdaysからweekに変更
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        db.set(guild_id=str(ctx.guild.id),
               channel_id=str(ctx.channel.id),
               option_id="week",
               call_time=f"{week.name}-{data_time}",
               mention_ids = str(mention.id) if mention else "None",
               title=str(title.name) if title else "おしらせ",
               main_text =  message.name if message else "時間です",
               img=ico.name if ico else "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎週 {week.name} 曜日 {data_time} にメッセージを送信するように設定しました"))
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="設定中にエラーが発生しました"))
    finally:
        db.close()
@tree.command(name='day-time', description="毎日通知します")
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def day_time(ctx: discord.Interaction,time:str,mention:discord.Role=None,title:str=None,message:str=None,ico:str=None): # 引数名をdaysからweekに変更
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        db.set(guild_id=str(ctx.guild.id),
               channel_id=str(ctx.channel.id),
               option_id="day",
               call_time=str(data_time),
               mention_ids=str(mention.id) if mention else "None",
               title=title if title else "おしらせ",
               main_text=message if message else "時間です",
               img=ico if ico else "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎日 {data_time} にメッセージを送信するように設定しました"))
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="設定中にエラーが発生しました"))
    finally:
        db.close()
@tree.command(name='get-settings', description="現在設定されている通知を表示します")
@app_commands.describe(setting_id="詳しい見た目が見れます")
async def get_settings(ctx: discord.Interaction,setting_id:str=None):
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
        settings = db.get()
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    if settings is None:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="現在設定されている通知はありません"))
        return

    if setting_id is None:
        await send_all_settings(ctx, settings)
    else:
        await send_specific_setting(ctx, db, setting_id)

async def send_all_settings(ctx, settings):
    formatted_settings = []
    for setting in settings:
        formatted_settings.append(format_setting(setting))
    embeds = say_embed_field(color=0x0000ff, title="設定中のメンション", message=formatted_settings)
    #文字数が多すぎる場合
    if len(embeds) > 1:
        await ctx.response.send_message(embeds=embeds[0])
        for embed in embeds[1:]:
            await ctx.channel.send(embed=embed)
    await ctx.response.send_message(embed=embeds[0])

async def send_specific_setting(ctx, db, setting_id):
    setting = db.get(setting_id)
    if setting is None:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="指定された ID の通知は存在しないか、現在設定されていません"))
        return
    _, _, _, setting_type, call_time, mention_ids, title, img, main_text  = setting[0]
    formatted_time = format_time(setting_type, call_time)
    if mention_ids != "None":
        await ctx.response.send_message(embed=say_embed(color=0x0000ff, title=f"{title}({formatted_time})", message=f"メンションするロール: <@&{mention_ids}>\n{main_text}",img_url=img if img != "None" else None))
    else:
        await ctx.response.send_message(embed=say_embed(color=0x0000ff, title=f"{title}({formatted_time})", message=main_text,img_url=img if img != "None" else None) )

@tree.command(name='del-settings', description="現在設定されている通知を削除します")
@app_commands.describe(setting_id="'/get-settings'で数字は確認してください")
async def del_settings(ctx: discord.Interaction,setting_id:str):
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        db.delete(setting_id)
        await ctx.response.send_message(embed=say_embed(color=0x00ff00, title="削除完了", message="指定された ID の通知を削除しました"))
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="指定された ID の通知が存在しないか、現在設定されていません"))

@tree.command(name='channel-settings', description='設定したものを編集します')
@app_commands.describe(setting_id="'/get-settings'で数字は確認してください")
@app_commands.describe(channel="メッセージチャンネル")
async def channel_settings(ctx: discord.Interaction,setting_id:str,channel:discord.TextChannel):
    try:
        db=Database(f"./db/Discord-{ctx.guild.id}")
        db_data= db.get(id=setting_id)
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        if db_data is None:
            await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="指定された ID の通知は存在しないか、現在設定されていません"))
            return
        db.update(id=setting_id,channel_id=str(channel.id))
        await ctx.response.send_message(embed=say_embed(color=0x00ff00, title="編集完了", message=f"指定された channel の通知を<#{db_data[3]}>から<#{channel.id}>に編集しました"))
    except Exception as e:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="編集中にエラーが発生しました"))
client.run(os.getenv('TOKEN'))