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
    if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
        return discord.Embed(title=title, description=message, color=color, url=img_url)
    else:
        return discord.Embed(title=title, description=message, color=color)
def say_embed_field(color: int, title: str, message: list[dict[str, str]]):
    embed = discord.Embed(title=title, color=color)
    for i, item in enumerate(message):
        for k, v in item.items():
            embed.add_field(name=f"{i+1}. {k}", value=v, inline=True)
    return embed
def say_auto_msg(color:int,option_id,title,setting_type, call_time, img, main_text):
    embed = discord.Embed(title=f"{title}({call_time})", description=main_text, color=color)
    if img:
        embed.set_image(url=img)
    return embed
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await tree.sync()

@tree.command(name='set_up',description="初期設定をします")
async def set_up(ctx):
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
        day = int(day)
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        db.set(guild_id=str(ctx.guild.id),
               channel_id=str(ctx.channel.id),
               option_id="month",
               call_time=f"{day}-{data_time}",
               mention_ids = str(mention.id) if mention else "None",
               title=str(title.name) if title else "おしらせ",
               main_text =  message.name if message else "時間です",
               img=ico.name if ico else "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎月{day}-{data_time} にメッセージを送信するように設定しました"))
    except:
       await ctx.response.send_message(embed=say_embed(color=0xff0000,title="失敗",message="日付、時間の形式が間違えています。"))
    finally:
        db.close()
@tree.command(name='month-time',description='毎月通知します')
@app_commands.describe(day="日時 mm/dd 例(1/1)")
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def month_time(ctx:discord.Interaction,day:str,time:str,mention:discord.Role=None,title:str=None,message:str=None,ico:str=None):
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    try:
        day = int(day)
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        db.set(guild_id=str(ctx.guild.id),
               channel_id=str(ctx.channel.id),
               option_id="month",
               call_time=f"{day}-{data_time}",
               mention_ids = str(mention.id) if mention else "None",
               title=str(title.name) if title else "おしらせ",
               main_text =  message.name if message else "時間です",
               img=ico.name if ico else "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎月{day}-{data_time} にメッセージを送信するように設定しました"))
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
               title=str(title.name) if title else "おしらせ",
               main_text=message.name if message else "時間です",
               img=ico.name if ico else "None")
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
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    settings = db.get()
    if settings is None:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="現在設定されている通知はありません"))
        return
    formatted_settings = []
    if setting_id is None:
        for setting in settings:
            id, _, _, setting_type, call_time, _, title, _, _ = setting
            if "month" in setting_type:
                formatted_time = f"{call_time.split('/')[0]}月 {call_time.split('/')[1]}日"
            elif "week" in setting_type:
                formatted_time = f"{call_time.split('-')[0]}曜日 {call_time.split('-')[1].split(':')[0]}時{call_time.split('-')[1].split(':')[1]}分"
            else:
                formatted_time = f"{call_time.split(':')[0]}時{call_time.split(':')[1]}分"

            formatted_settings.append({"id": id, "title": title, "time": formatted_time})
        await ctx.response.send_message(embed=say_embed_field(color=0x0000ff,title="設定中のメンション", message=formatted_settings))
    else:
        setting = db.get(setting_id)
        if setting is None:
            await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="指定された ID の通知は存在しないか、現在設定されていません"))
            return
        _, _, _, setting_type, call_time, mention_ids, title, img, main_text  = setting[0]
        if "month" in setting_type:
            formatted_time = f"{call_time.split('/')[0]}月 {call_time.split('/')[1]}日"
        elif "week" in setting_type:
            formatted_time = f"{call_time.split('-')[0]}曜日 {call_time.split('-')[1].split(':')[0]}時{call_time.split('-')[1].split(':')[1]}分"
        else:
            formatted_time = f"{call_time.split(':')[0]}時{call_time.split(':')[1]}分"
        if mention_ids != "None":
            await ctx.response.send_message(mention_ids,embed=say_embed(color=0x0000ff, title=f"{title}({formatted_time})", message=main_text,img_url=img if img != "None" else None))
        else:
            await ctx.response.send_message(embed=say_embed(color=0x0000ff, title=f"{title}({formatted_time})", message=main_text,img_url=img if img != "None" else None) )
    db.close()
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

@tree.command(name='edit-settings', description='設定したものを編集します')
@app_commands.describe(setting_id="'/get-settings'で数字は確認してください")
@app_commands.describe(setting="頻度設定")
@app_commands.choices(setting=[
    Choice(name="1回", value="oneday"),
    Choice(name="毎日", value="day"),
    Choice(name="毎週", value="week"),
    Choice(name="毎月", value="month"),
])
@app_commands.describe(day="日")
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
async def edit_settings(ctx: discord.Interaction,setting_id:str,setting:str=None,day:str=None,week:str=None,time:str=None,mention:discord.Role=None,title:str=None,message:str=None,ico:str=None):
    channel = client.get_channel(int(ctx.channel.id))
    try:
        db = Database(f"./db/Discord-{ctx.guild.id}")
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="初期設定してください"))
        return
    formatted_time = None
    # 日
    if setting == "oneday" and time:
        formatted_time = time
    # 週
    elif setting == "week" and week and time:
        formatted_time = f"{week}-{time}"
    # 月
    elif setting == "month" and "/" in day and time:
        formatted_time = f"{day}-{time}"
    elif (setting == "week" and (week or time)) or (setting == "month" and (day or time)):
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="時間を設定する場合は日を両方入れてください"))
        return
    try:
        #mention.id がNoneの場合の処理
        mention_id = mention.id if mention else None
        db.update(id=setting_id,call_time=formatted_time,mention_ids=mention_id, title=title, img=ico, main_text=message)
        _, _, _, setting_type, call_time, mention_ids, title, img, main_text = db.get(setting_id)[0]
        if "month" in setting_type:
            formatted_time = f"{call_time.split('/')[0]}月 {call_time.split('/')[1]}日"
        elif "week" in setting_type:
            formatted_time = f"{call_time.split('-')[0]}曜日 {call_time.split('-')[1].split(':')[0]}時{call_time.split('-')[1].split(':')[1]}分"
        else:
            formatted_time = f"{call_time.split(':')[0]}時{call_time.split(':')[1]}分"
        await ctx.channel.send(embed=say_embed(color=0x0000ff, title=f"{title}({formatted_time})", message=main_text,img_url=img if img != "None" else None))

        await ctx.response.send_message(embed=say_embed(color=0x00ff00, title="編集完了", message="指定された ID の通知を編集しました"))
    except Exception as e:
        print(f"Error: {e}")
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="編集中にエラーが発生しました"))


client.run(os.getenv('TOKEN'))