import datetime
from pydoc import describe

import discord
from discord import app_commands
from discord.app_commands import Choice
from dotenv import load_dotenv
import os
from sqlite_edit import Database

db = Database("Discord")
db.create_table()
load_dotenv()
discord_intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=discord_intents,activity=discord.Game("稼働中"))
tree = app_commands.CommandTree(client)
def is_integer(value)->bool:
    if value is None:
        return True
    try:
        int(value)
        return True
    except ValueError:
        return False
def say_embed(color:int,title:str, message:str, img_url:str = None):
    """
    :param color: 0xで指定してください
    :param title:  title部分
    :param message: 中身
    :param img_url: 画像URL
    :return:　discord.Embed
    """
    if img_url:
        return discord.Embed(title=title, description=message, color=color, url=img_url)
    else:
        return discord.Embed(title=title, description=message, color=color)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await tree.sync()

@tree.command(name='set-channel',description="チャンネルを設定します")
async def set_channel(ctx):
    # ここにチャンネルを設定する処理を追加
    await ctx.response.send_message("チャンネルを設定するコマンドはまだ実装されていません。")

@tree.command(name='month-time',description='毎月通知します')
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
async def month_time(ctx:discord.Interaction,day:str,time:str,role:discord.Role=None):
    try:
        day = int(day)
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        if role is not None:
            db.set(str(ctx.guild.id), str(ctx.channel.id), "month", f"{day}-{data_time}", str(role.id))
        else:
            db.set(str(ctx.guild.id), str(ctx.channel.id), "month", f"{day}-{data_time}", "None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎月{day}-{data_time} にメッセージを送信するように設定しました"))
    except:
       await ctx.response.send_message(embed=say_embed(color=0xff0000,title="失敗",message="日付、時間の形式が間違えています。"))
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
async def week_time(ctx: discord.Interaction, week: Choice[str],time:str,role:discord.Role=None): # 引数名をdaysからweekに変更
    try:
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        if role is not None:
            db.set(str(ctx.guild.id),str(ctx.channel.id),"week",f"{week.name}-{data_time}",str(role.id))
        else:
            db.set(str(ctx.guild.id),str(ctx.channel.id),"week",f"{week.name}-{data_time}","None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎週 {week.name} 曜日 {data_time} にメッセージを送信するように設定しました"))
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="設定中にエラーが発生しました"))
@tree.command(name='day-time', description="毎日通知します")
@app_commands.describe(time="時間設定 hh:mm 例(6:00:00)")
async def week_time(ctx: discord.Interaction,time:str,role:discord.Role=None): # 引数名をdaysからweekに変更
    try:
        data_time = datetime.datetime.strptime(time, '%H:%M:%S').time()
        if role is not None:
            db.set(str(ctx.guild.id),str(ctx.channel.id),"day",str(data_time),str(role.id))
        else:
            db.set(str(ctx.guild.id),str(ctx.channel.id),"day",str(data_time),"None")
        await ctx.response.send_message(embed=say_embed(color=0x00ff00,title="設定完了",message=f"毎日 {data_time} にメッセージを送信するように設定しました"))
    except:
        await ctx.response.send_message(embed=say_embed(color=0xff0000, title="エラー", message="設定中にエラーが発生しました"))

client.run(os.getenv('TOKEN'))

