import os
import sys
import secrets
import hashlib
from datetime import datetime, timedelta
import logging

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import tasks
from dotenv import load_dotenv
from pytz import timezone

from sqlalchemy_models import Database
from utilities import (
    WEEK_CHOICES, create_embed, create_embed_with_fields,
    format_time, format_setting, should_send_notification
)

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discord_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('discord-bot')

# 環境変数の読み込み
load_dotenv()

# 環境変数の確認
TOKEN = os.getenv('TOKEN')
WEB_SERVER_URL = os.getenv('WEB_SERVER_URL', 'http://localhost:5000')
URL_SALT = os.getenv('URL_SALT', 'discord-at-code-reminder-salt-12345')

if not TOKEN:
    logger.critical("Discord TOKENが設定されていません。.envファイルにTOKEN=your_token_hereを追加してください。")
    sys.exit(1)

# Function to generate consistent server URL token
def generate_server_token(server_id: str) -> str:
    """
    Generate a consistent token for a server based on server ID and salt

    Args:
        server_id (str): Discord server ID

    Returns:
        str: Hashed token for server URL
    """
    # Combine server ID with salt
    combined = f"{server_id}:{URL_SALT}"
    # Create SHA-256 hash
    hash_obj = hashlib.sha256(combined.encode())
    # Return first 16 characters of the hex digest
    return hash_obj.hexdigest()[:16]

# グローバル変数の設定
db = Database("Discord")
settings_cache = {}
last_cache_update = datetime.now(timezone('Asia/Tokyo'))
last_checked_minute = -1

# Discordクライアントの初期化
try:
    discord_intents = discord.Intents.all()
    client = discord.Client(intents=discord_intents, activity=discord.Game("稼働中"))
    tree = app_commands.CommandTree(client)
    week = WEEK_CHOICES
    logger.info("Discordクライアントの初期化に成功しました。")
except Exception as e:
    logger.critical(f"Discordクライアントの初期化中にエラーが発生しました: {e}")
    sys.exit(1)

# コマンド定義
@tree.command(name='onetime', description='1回のみの通知')
@app_commands.describe(day="日時 mm/dd 例(1/1)")
@app_commands.describe(time="時間設定 hh:mm:ss 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def onetime(ctx: discord.Interaction, time: str, day: str = None, mention: discord.Role = None, title: str = None, message: str = None, ico: str = None):
    """'onetime'コマンド (ハイフンなし) - 'one-time'コマンドのエイリアス"""
    try:
        data_time = datetime.strptime(time, '%H:%M:%S').time()
        # 日付が指定されていない場合は今日に設定
        if not day:
            day = datetime.now(timezone('Asia/Tokyo')).strftime('%m/%d')
            # 指定された時間が現在時刻より前の場合、翌日に設定
            if datetime.now(timezone('Asia/Tokyo')).time() > data_time:
                day = (datetime.now(timezone('Asia/Tokyo')) + timedelta(days=1)).strftime('%m/%d')
        # 日付形式チェック (mm/dd)
        elif not (1 <= int(day.split("/")[0]) <= 12 and 1 <= int(day.split("/")[1]) <= 31):
            raise ValueError

        db.set(
            guild_id=str(ctx.guild.id),
            channel_id=str(ctx.channel.id),
            option="oneday",
            day=day,
            week="None",
            call_time=str(data_time),
            mention_ids=str(mention.id) if mention else "None",
            title=str(title) if title else "おしらせ",
            main_text=message if message else "時間です",
            img=ico if ico else "None"
        )

        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="設定完了", message=f"{day} {data_time} にメッセージを<#{ctx.channel.id}>に送信するように設定しました。\n\nWeb UIで管理するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except ValueError:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="日付、時間の形式が間違えています。"))
    except Exception as e:
        logger.error(f"Onetime error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="セットアップコマンドを実行してください"))

@tree.command(name='setup', description="初期設定をします")
async def setup(ctx):
    try:
        db.create_table(guild_id=str(ctx.guild.id))
        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="設定完了", message="設定が完了しました。\n\nWeb UIを使用するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except Exception as e:
        logger.error(f"Setup error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="初期設定中にエラーが発生しました"))

@tree.command(name='one-time', description='1回のみの通知')
@app_commands.describe(day="日時 mm/dd 例(1/1)")
@app_commands.describe(time="時間設定 hh:mm:ss 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def one_time(ctx: discord.Interaction, time: str, day: str = None, mention: discord.Role = None, title: str = None, message: str = None, ico: str = None):
    try:
        data_time = datetime.strptime(time, '%H:%M:%S').time()
        # 日付が指定されていない場合は今日に設定
        if not day:
            day = datetime.now(timezone('Asia/Tokyo')).strftime('%m/%d')
            # 指定された時間が現在時刻より前の場合、翌日に設定
            if datetime.now(timezone('Asia/Tokyo')).time() > data_time:
                day = (datetime.now(timezone('Asia/Tokyo')) + timedelta(days=1)).strftime('%m/%d')
        # 日付形式チェック (mm/dd)
        elif not (1 <= int(day.split("/")[0]) <= 12 and 1 <= int(day.split("/")[1]) <= 31):
            raise ValueError

        db.set(
            guild_id=str(ctx.guild.id),
            channel_id=str(ctx.channel.id),
            option="oneday",
            day=day,
            week="None",
            call_time=str(data_time),
            mention_ids=str(mention.id) if mention else "None",
            title=str(title) if title else "おしらせ",
            main_text=message if message else "時間です",
            img=ico if ico else "None"
        )

        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="設定完了", message=f"{day} {data_time} にメッセージを<#{ctx.channel.id}>に送信するように設定しました。\n\nWeb UIで管理するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except ValueError:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="日付、時間の形式が間違えています。"))
    except Exception as e:
        logger.error(f"One-time error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="セットアップコマンドを実行してください"))

@tree.command(name='month-time', description='毎月通知します week 引数を使うと曜日を指定することができます')
@app_commands.describe(day="日 or 第?曜日 dd 例(10)")
@app_commands.describe(week="曜日設定")
@app_commands.choices(week=week)
@app_commands.describe(time="時間設定 hh:mm:ss 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def month_time(ctx: discord.Interaction, day: int, time: str, week: Choice[str] = None, mention: discord.Role = None, title: str = None, message: str = None, ico: str = None):
    try:
        data_time = datetime.strptime(time, '%H:%M:%S').time()

        if week:
            if not 1 <= day <= 5:
                raise ValueError
            say_day = f"第{day} {week.name}曜日 {data_time}"
            week_value = week.value
        else:
            if not 1 <= day <= 31:
                raise ValueError
            say_day = f"{day}日 {data_time}"
            week_value = "None"

        db.set(
            guild_id=str(ctx.guild.id),
            channel_id=str(ctx.channel.id),
            option="month",
            day=str(day),
            week=week_value if week else "None",
            call_time=str(data_time),
            mention_ids=str(mention.id) if mention else "None",
            title=title if title else "おしらせ",
            main_text=message if message else "時間です",
            img=ico if ico else "None"
        )

        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="設定完了", message=f"毎月 {say_day} にメッセージを送信するように設定しました。\n\nWeb UIで管理するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except ValueError:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="日付、時間の形式が間違えています。"))
    except Exception as e:
        logger.error(f"Month-time error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="セットアップコマンドを実行してください"))

@tree.command(name='week-time', description='毎週通知します')
@app_commands.describe(week="曜日")
@app_commands.choices(week=week)
@app_commands.describe(time="時間設定 hh:mm:ss 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def week_time(ctx: discord.Interaction, week: Choice[str], time: str, mention: discord.Role = None, title: str = None, message: str = None, ico: str = None):
    try:
        data_time = datetime.strptime(time, '%H:%M:%S').time()

        db.set(
            guild_id=str(ctx.guild.id),
            channel_id=str(ctx.channel.id),
            option="week",
            day="None",
            week=week.value,
            call_time=str(data_time),
            mention_ids=str(mention.id) if mention else "None",
            title=str(title) if title else "おしらせ",
            main_text=message if message else "時間です",
            img=ico if ico else "None"
        )

        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="設定完了", message=f"毎週 {week.name}曜日 {data_time} にメッセージを送信するように設定しました。\n\nWeb UIで管理するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except ValueError:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="日付、時間の形式が間違えています。"))
    except Exception as e:
        logger.error(f"Week-time error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="セットアップコマンドを実行してください"))

@tree.command(name='day-time', description="毎日通知します")
@app_commands.describe(time="時間設定 hh:mm:ss 例(6:00:00)")
@app_commands.describe(mention="メンションするロール")
@app_commands.describe(title="タイトル")
@app_commands.describe(message="設定された時間に発する文章")
@app_commands.describe(ico="左上にアイコンとして設定されます")
async def day_time(ctx: discord.Interaction, time: str, mention: discord.Role = None, title: str = None, message: str = None, ico: str = None):
    try:
        data_time = datetime.strptime(time, '%H:%M:%S').time()

        db.set(
            guild_id=str(ctx.guild.id),
            channel_id=str(ctx.channel.id),
            option="day",
            day="None",
            week="None",
            call_time=str(data_time),
            mention_ids=str(mention.id) if mention else "None",
            title=title if title else "おしらせ",
            main_text=message if message else "時間です",
            img=ico if ico else "None"
        )

        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="設定完了", message=f"毎日 {data_time} にメッセージを送信するように設定しました。\n\nWeb UIで管理するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except ValueError:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="日付、時間の形式が間違えています。"))
    except Exception as e:
        logger.error(f"Day-time error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="失敗", message="セットアップコマンドを実行してください"))

@tree.command(name='get-settings', description="現在設定されている通知を表示します")
@app_commands.describe(setting_id="詳しい見た目が見れます")
async def get_settings(ctx: discord.Interaction, setting_id: str = None):
    try:
        if setting_id is None:
            settings = db.get_all(guild_id=str(ctx.guild.id))
            if settings is None or len(settings) == 0:
                await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="現在設定されている通知はありません"))
                return

            await send_all_settings(ctx, settings)
        else:
            await send_specific_setting(ctx, setting_id)
    except Exception as e:
        logger.error(f"Get-settings error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="通知の取得中にエラーが発生しました"))

async def send_all_settings(ctx, settings):
    formatted_settings = []
    for setting in settings:
        formatted_settings.append(format_setting(setting))

    if not formatted_settings:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="現在設定されている通知はありません"))
        return

    embeds = create_embed_with_fields(color=0x0000ff, title="設定中の通知", fields=formatted_settings)

    # 最初の埋め込みメッセージのdescriptionにWeb UIの情報を追加
    web_ui_info = "Web UIで通知を管理するには `/web-ui` コマンドを実行してURLを取得してください。"
    if embeds[0].description:
        embeds[0].description += f"\n\n{web_ui_info}"
    else:
        embeds[0].description = web_ui_info

    await ctx.response.send_message(embed=embeds[0])

    # 埋め込みメッセージのフィールド数が多すぎる場合、分割して送信
    for embed in embeds[1:]:
        await ctx.channel.send(embed=embed)

async def send_specific_setting(ctx, setting_id):
    setting = db.get(guild_id=str(ctx.guild.id), id=setting_id)
    if setting is None:
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="指定された ID の通知は存在しないか、現在設定されていません"))
        return

    formatted_time = format_time(
        setting_type=setting["option"],
        week=setting["week"],
        day=setting["day"],
        time=setting["call_time"]
    )

    web_ui_info = "\n\nWeb UIで通知を管理するには `/web-ui` コマンドを実行してURLを取得してください。"

    if setting["mention_ids"] != "None":
        await ctx.response.send_message(embed=create_embed(
            color=0x0000ff,
            title=f"{setting['title']}({formatted_time})",
            message=f"メンションするロール: <@&{setting['mention_ids']}>\n{setting['main_text']}{web_ui_info}",
            img_url=setting["img"] if setting["img"] != "None" else None
        ))
    else:
        await ctx.response.send_message(embed=create_embed(
            color=0x0000ff,
            title=f"{setting['title']}({formatted_time})",
            message=f"{setting['main_text']}{web_ui_info}",
            img_url=setting["img"] if setting["img"] != "None" else None
        ))

@tree.command(name='del-settings', description="現在設定されている通知を削除します")
@app_commands.describe(setting_id="'/get-settings'で数字は確認してください")
async def del_settings(ctx: discord.Interaction, setting_id: str):
    try:
        setting = db.get(guild_id=str(ctx.guild.id), id=setting_id)
        if setting is None:
            await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="指定された ID の通知は存在しないか、現在設定されていません"))
            return

        db.delete(guild_id=str(ctx.guild.id), id=setting_id)
        await ctx.response.send_message(embed=create_embed(color=0x00ff00, title="削除完了", message="指定された ID の通知を削除しました。\n\nWeb UIで通知を管理するには `/web-ui` コマンドを実行してURLを取得してください。"))
    except Exception as e:
        logger.error(f"Del-settings error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="通知の削除中にエラーが発生しました"))

@tree.command(name='channel-settings', description='設定したものを編集します')
@app_commands.describe(setting_id="'/get-settings'で数字は確認してください")
@app_commands.describe(channel="メッセージチャンネル")
async def channel_settings(ctx: discord.Interaction, setting_id: str, channel: discord.TextChannel):
    try:
        setting = db.get(guild_id=str(ctx.guild.id), id=setting_id)
        if setting is None:
            await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="指定された ID の通知は存在しないか、現在設定されていません"))
            return

        old_channel_id = setting["channel_id"]
        db.update_setting_time(guild_id=str(ctx.guild.id), id=setting_id, channel_id=str(channel.id))

        await ctx.response.send_message(embed=create_embed(
            color=0x00ff00,
            title="編集完了",
            message=f"指定された channel の通知を<#{old_channel_id}>から<#{channel.id}>に編集しました。\n\nWeb UIで通知を管理するには `/web-ui` コマンドを実行してURLを取得してください。"
        ))
    except Exception as e:
        logger.error(f"Channel-settings error: {e}")
        await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="編集中にエラーが発生しました"))

@tree.command(name='web-ui', description="Web UIのURLを取得します")
async def web_ui(ctx: discord.Interaction):
    try:
        guild_id = str(ctx.guild.id)

        # 一貫性のあるトークンを生成
        token = generate_server_token(guild_id)

        # サーバー固有のURLを生成
        server_url = f"{WEB_SERVER_URL}/server/{guild_id}/{token}"

        # 最初に応答を送信してからDMを送信する
        try:
            # まず公開チャンネルでの応答を送信
            await ctx.response.send_message(embed=create_embed(
                color=0x00ff00,
                title="Web UI URL",
                message="Web UIのURLをDMで送信します。DMを確認してください。このURLはサーバーのメンバー全員が使用できます。"
            ))

            # 次にDMでURLを送信
            embed = create_embed(
                color=0x00ff00,
                title="Web UI URL",
                message=f"以下のURLからWeb UIにアクセスできます。このURLはサーバーのメンバー全員が使用できます。サーバーのメンバーと共有してください。\n\n{server_url}"
            )
            await ctx.user.send(embed=embed)
        except discord.Forbidden:
            # DMが送信できない場合はフォローアップメッセージで送信
            try:
                await ctx.followup.send(embed=create_embed(
                    color=0x00ff00,
                    title="Web UI URL",
                    message=f"DMを送信できませんでした。以下のURLからWeb UIにアクセスできます。このURLはサーバーのメンバー全員が使用できます。サーバーのメンバーと共有してください。\n\n{server_url}"
                ))
            except Exception as dm_error:
                logger.error(f"DMとフォローアップの両方が失敗しました: {dm_error}")
    except discord.errors.NotFound as nf_error:
        # 10062エラー（Unknown interaction）の場合
        if "10062" in str(nf_error):
            logger.warning(f"インタラクションがタイムアウトしました: {nf_error}")
            # ここでは何もしない - インタラクションはすでにタイムアウトしている
        else:
            logger.error(f"Web-ui NotFound error: {nf_error}")
    except Exception as e:
        logger.error(f"Web-ui error: {e}")
        try:
            await ctx.response.send_message(embed=create_embed(color=0xff0000, title="エラー", message="URLの生成中にエラーが発生しました"))
        except discord.errors.NotFound:
            # インタラクションがすでにタイムアウトしている場合は無視
            pass

# 通知ループ
@tasks.loop(seconds=1)
async def time_loop():
    """毎秒、送信すべき通知があるか確認します（最適化版）"""
    global last_cache_update, last_checked_minute, settings_cache

    try:
        current_time = datetime.now(timezone('Asia/Tokyo'))
        current_minute = current_time.minute

        # 1分ごとにキャッシュを更新（または初回実行時）
        if (current_time - last_cache_update).total_seconds() >= 60 or not settings_cache:
            await update_settings_cache()
            last_cache_update = current_time

        # 同じ分をすでにチェック済みの場合はスキップ
        if current_minute == last_checked_minute:
            return

        last_checked_minute = current_minute

        # キャッシュされた設定を使用して通知をチェック
        for guild_id, guild_settings in settings_cache.items():
            try:
                guild = client.get_guild(int(guild_id))
                if not guild:
                    continue

                for setting in guild_settings:
                    if should_send_notification(setting, current_time):
                        await send_notification(guild, setting)

                        # 一回限りの通知の場合、キャッシュから削除
                        if setting["option"] == "oneday":
                            settings_cache[guild_id] = [s for s in guild_settings if s["id"] != setting["id"]]
            except Exception as e:
                logger.error(f"ギルド {guild_id} の処理中にエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"time_loop でエラーが発生しました: {e}")

@time_loop.error
async def time_loop_error(error):
    """通知ループでエラーが発生した場合のハンドラ"""
    logger.error(f"通知ループでエラーが発生しました: {error}")

    # 接続エラーの場合は再接続を試みる
    if isinstance(error, discord.errors.ConnectionClosed):
        logger.warning("接続が閉じられました。再接続を試みます...")

    # ループが停止した場合は再開を試みる
    if not time_loop.is_running():
        try:
            time_loop.restart()
            logger.info("通知ループを再開しました。")
        except Exception as e:
            logger.critical(f"通知ループの再開に失敗しました: {e}")
            # 致命的なエラーの場合はボットを再起動
            await client.close()

async def update_settings_cache():
    """すべてのギルドの設定をキャッシュに読み込みます"""
    global settings_cache

    try:
        settings_cache = {}

        # ボットが参加しているすべてのギルドを取得
        for guild in client.guilds:
            guild_id = str(guild.id)

            try:
                # テーブルが存在しない場合は作成
                db.create_table(guild_id=guild_id)

                # このギルドのすべての設定を取得
                settings = db.get_all(guild_id=guild_id)
                if settings:
                    settings_cache[guild_id] = settings
            except Exception as e:
                logger.error(f"ギルド {guild_id} の設定キャッシュ更新中にエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"設定キャッシュの更新中にエラーが発生しました: {e}")

async def send_notification(guild, setting):
    """設定に基づいて通知を送信します"""
    try:
        channel_id = int(setting["channel_id"])
        channel = guild.get_channel(channel_id)

        if not channel:
            logger.warning(f"ギルド {guild.id} でチャンネル {channel_id} が見つかりません")
            return

        # メンションテキストを準備
        mention_text = ""
        if setting["mention_ids"] != "None":
            mention_text = f"<@&{setting['mention_ids']}> "

        # 通知を送信
        await channel.send(
            content=mention_text,
            embed=create_embed(
                color=0x0000ff,
                title=setting["title"],
                message=setting["main_text"],
                img_url=setting["img"] if setting["img"] != "None" else None
            )
        )

        # 1回限りの通知の場合、送信後に削除
        if setting["option"] == "oneday":
            db.delete(guild_id=str(guild.id), id=str(setting["id"]))
    except Exception as e:
        logger.error(f"通知の送信中にエラーが発生しました: {e}")

# イベントハンドラ
@client.event
async def on_ready():
    try:
        logger.info('ログインしました: {0.user}'.format(client))

        # コマンドツリーの同期
        try:
            await tree.sync()
            logger.info("コマンドツリーの同期に成功しました。")
        except Exception as e:
            logger.error(f"コマンドツリーの同期中にエラーが発生しました: {e}")
            # 致命的ではないので続行

        # 通知ループの開始または再開
        try:
            # ループが既に実行中かチェック
            if time_loop.is_running():
                logger.info("通知ループは既に実行中です。")
            else:
                time_loop.start()
                logger.info("通知ループを開始しました。")

            # 設定キャッシュを更新
            await update_settings_cache()
            logger.info("設定キャッシュを更新しました。")
        except Exception as e:
            logger.critical(f"通知ループの開始中にエラーが発生しました: {e}")
            # これは致命的なエラーなので、ボットを再起動する必要がある
            await client.close()
    except Exception as e:
        logger.critical(f"起動処理中に予期せぬエラーが発生しました: {e}")
        await client.close()

# 接続エラー時のイベントハンドラ
@client.event
async def on_disconnect():
    logger.warning("Discordサーバーから切断されました。再接続を試みます...")

# 再接続時のイベントハンドラ
@client.event
async def on_resumed():
    logger.info("Discordサーバーに再接続しました。")

# ボットを実行
try:
    logger.info("ボットを起動しています...")
    # reconnect=Trueを明示的に設定して、接続が切れた場合に自動的に再接続を試みるようにする
    client.run(TOKEN, reconnect=True)
except discord.LoginFailure:
    logger.critical("ログインに失敗しました。TOKENが正しいか確認してください。")
    sys.exit(1)
except discord.errors.ConnectionClosed as e:
    logger.error(f"接続が閉じられました: {e}. 再接続を試みます。")
    # 再接続は client.run の reconnect=True パラメータによって処理される
except Exception as e:
    logger.critical(f"ボットの実行中に予期せぬエラーが発生しました: {e}")
    sys.exit(1)
finally:
    logger.info("ボットを終了しています...")
