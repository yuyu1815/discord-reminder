from sqlalchemy import create_engine, Column, Integer, String, Text, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, List, Optional, Any, Type
import os

# 宣言的モデルのベースクラスを作成
Base = declarative_base()

# 各ギルドのモデルクラスを動的に作成する関数を定義
def create_setting_time_model(guild_id: str) -> Type[Base]:
    """
    特定のギルドの設定テーブル用のモデルクラスを動的に作成します

    Args:
        guild_id (str): DiscordギルドID

    Returns:
        Type[Base]: ギルド設定用のSQLAlchemyモデルクラス
    """
    class_name = f"SettingTime_{guild_id}"

    # モデルクラスを動的に作成
    return type(class_name, (Base,), {
        '__tablename__': f'setting_time_{guild_id}',
        'id': Column(Integer, primary_key=True, autoincrement=True),
        'channel_id': Column(String(20), nullable=False),
        'option': Column(String(10), nullable=False),
        'day': Column(String(10), nullable=False),
        'week': Column(String(10), nullable=False),
        'call_time': Column(String(10), nullable=False),
        'mention_ids': Column(Text, nullable=False),
        'title': Column(Text, nullable=False),
        'img': Column(Text, nullable=False),
        'main_text': Column(Text, nullable=False)
    })

class SQLAlchemyDatabase:
    """
    元のDatabaseクラスを置き換える、SQLAlchemyを使用したデータベースハンドラクラス
    """
    def __init__(self, app_name: str, db_name: str = "server-file"):
        """
        データベース接続を初期化します

        Args:
            app_name (str): データベースファイルのアプリケーション名プレフィックス
            db_name (str): データベース名サフィックス
        """
        # dbディレクトリが存在することを確認
        os.makedirs("./db", exist_ok=True)

        self.db_name = db_name
        self.app_name = app_name
        self.engine = create_engine(f"sqlite:///./db/{app_name}-{db_name}.db")
        self.Session = sessionmaker(bind=self.engine)
        self.models = {}  # 動的に作成されたモデルのキャッシュ

    def __enter__(self):
        """コンテキストマネージャのenterメソッド"""
        self.session = self.Session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャのexitメソッド"""
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()

    def get_model(self, guild_id: str) -> Type[Base]:
        """
        特定のギルドのモデルを取得または作成します

        Args:
            guild_id (str): DiscordギルドID

        Returns:
            Type[Base]: ギルド用のSQLAlchemyモデルクラス
        """
        if guild_id not in self.models:
            self.models[guild_id] = create_setting_time_model(guild_id)
        return self.models[guild_id]

    def create_table(self, guild_id: str) -> None:
        """
        ギルド用のテーブルが存在しない場合に作成します

        Args:
            guild_id (str): DiscordギルドID
        """
        model = self.get_model(guild_id)
        if not inspect(self.engine).has_table(model.__tablename__):
            model.__table__.create(self.engine)

    def set(self, guild_id: str, channel_id: str, option: str, day: str, week: str, 
            call_time: str, mention_ids: str, title: str, main_text: str, img: str) -> None:
        """
        新しい通知設定を追加します

        Args:
            guild_id (str): DiscordギルドID
            channel_id (str): DiscordチャンネルID
            option (str): 通知オプション (day, week, month, oneday)
            day (str): 日付設定
            week (str): 曜日設定
            call_time (str): 通知送信時刻
            mention_ids (str): メンションするID
            title (str): 通知タイトル
            main_text (str): 通知内容
            img (str): 画像URL
        """
        model = self.get_model(guild_id)
        with self as session:
            new_setting = model(
                channel_id=channel_id,
                option=option,
                day=day,
                week=week,
                call_time=call_time,
                mention_ids=mention_ids,
                title=title,
                main_text=main_text,
                img=img
            )
            session.add(new_setting)

    def get(self, guild_id: str, id: str) -> Optional[Dict[str, Any]]:
        """
        特定の通知設定を取得します

        Args:
            guild_id (str): DiscordギルドID
            id (str): レコードID

        Returns:
            Optional[Dict[str, Any]]: 通知設定の辞書、見つからない場合はNone
        """
        model = self.get_model(guild_id)
        with self as session:
            setting = session.query(model).filter(model.id == id).first()
            if setting:
                return {
                    "id": setting.id,
                    "channel_id": setting.channel_id,
                    "option": setting.option,
                    "day": setting.day,
                    "week": setting.week,
                    "call_time": setting.call_time,
                    "mention_ids": setting.mention_ids,
                    "title": setting.title,
                    "main_text": setting.main_text,
                    "img": setting.img
                }
            return None

    def get_all(self, guild_id: str) -> List[Dict[str, Any]]:
        """
        ギルドのすべての通知設定を取得します

        Args:
            guild_id (str): DiscordギルドID

        Returns:
            List[Dict[str, Any]]: 通知設定の辞書のリスト、見つからない場合は空のリスト
        """
        model = self.get_model(guild_id)
        with self as session:
            settings = session.query(model).all()
            if settings:
                return [
                    {
                        "id": setting.id,
                        "channel_id": setting.channel_id,
                        "option": setting.option,
                        "day": setting.day,
                        "week": setting.week,
                        "call_time": setting.call_time,
                        "mention_ids": setting.mention_ids,
                        "title": setting.title,
                        "main_text": setting.main_text,
                        "img": setting.img
                    }
                    for setting in settings
                ]
            return []

    def delete(self, guild_id: str, id: str) -> None:
        """
        通知設定を削除します

        Args:
            guild_id (str): DiscordギルドID
            id (str): レコードID
        """
        model = self.get_model(guild_id)
        with self as session:
            setting = session.query(model).filter(model.id == id).first()
            if setting:
                session.delete(setting)

    def update_setting_time(self, guild_id: str, id: str, channel_id: Optional[str] = None, 
                           option: Optional[str] = None, day: Optional[str] = None, 
                           week: Optional[str] = None, call_time: Optional[str] = None, 
                           mention_ids: Optional[str] = None, title: Optional[str] = None, 
                           main_text: Optional[str] = None, img: Optional[str] = None) -> None:
        """
        通知設定を更新します

        Args:
            guild_id (str): DiscordギルドID
            id (str): レコードID
            channel_id (Optional[str]): DiscordチャンネルID
            option (Optional[str]): 通知オプション
            day (Optional[str]): 日付設定
            week (Optional[str]): 曜日設定
            call_time (Optional[str]): 通知送信時刻
            mention_ids (Optional[str]): メンションするID
            title (Optional[str]): 通知タイトル
            main_text (Optional[str]): 通知内容
            img (Optional[str]): 画像URL
        """
        model = self.get_model(guild_id)
        with self as session:
            setting = session.query(model).filter(model.id == id).first()
            if setting:
                if channel_id is not None:
                    setting.channel_id = channel_id
                if option is not None:
                    setting.option = option
                if day is not None:
                    setting.day = day
                if week is not None:
                    setting.week = week
                if call_time is not None:
                    setting.call_time = call_time
                if mention_ids is not None:
                    setting.mention_ids = mention_ids
                if title is not None:
                    setting.title = title
                if main_text is not None:
                    setting.main_text = main_text
                if img is not None:
                    setting.img = img

    def close(self) -> None:
        """データベース接続を閉じます"""
        # SQLAlchemyが接続プーリングを処理するため、これは互換性のためのno-opです
        pass

# 後方互換性のため
Database = SQLAlchemyDatabase
