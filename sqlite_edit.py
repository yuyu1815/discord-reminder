import sqlite3
# 色表示用
ERROR_COLLAR = '\033[31m' #エラー 赤
NORMAL_COLLAR = '\033[0m' #通常戻す
class Database:
    def __init__(self,app_name:str,db_name:str = "server-file"):
        self.db_name = db_name
        self.db = sqlite3.connect(
            f"./bd/{app_name}-{db_name}.db",
            isolation_level=None,
        )
    def __enter__(self):
        return self.db.cursor()
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        self.db.close()
    def create_table(self,guild_id:str):
        """
        テーブルが存在しない場合、テーブルを作る
        Args:
            guild_id (str): サーバーID
        """
        with self.db:
            self.db.execute(f"""
                CREATE TABLE IF NOT EXISTS setting_time_{guild_id} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id VARCHAR(20) NOT NULL,
                    option VARCHAR(10) NOT NULL,
                    day VARCHAR(10) NOT NULL,
                    week VARCHAR(10) NOT NULL,
                    call_time VARCHAR(10) NOT NULL,
                    mention_ids TEXT NOT NULL,
                    title TEXT NOT NULL,
                    img TEXT NOT NULL,  -- 画像URL
                    main_text TEXT NOT NULL
                );
            """)
    def set(self, guild_id:str, channel_id:str,option:str,day:str,week:str,call_time:str,
            mention_ids:str,title:str,main_text:str,img:str)->None:
        """
        messageを送信する設定を保存
        Args:
            guild_id (str): サーバーID
            id (str): レコードID
            channel_id (int, optional): チャンネルID
            option (str, optional): オプション
            day (str, optional): 日
            week (str, optional): 週
            call_time (str, optional): 時間
            mention_ids (str, optional): メンションID
            title (str, optional): タイトル
            main_text (str, optional): 本文
            img (str, optional): 画像
        """
        with self.db:
            self.db.execute(f"""INSERT OR IGNORE INTO setting_time_{guild_id} 
                                (channel_id,option,day,week,call_time,mention_ids,title,img,main_text) VALUES (?,?,?,?,?,?,?,?,?)
                                """,(channel_id,option,day,week,call_time,mention_ids,title,img,main_text)
                            )
        self.db.commit()
    def get(self,guild_id:str,id:str)->dict[str,str]:
        """
        通知のみのメッセージを全て取得
        Args:
            guild_id(str): サーバーID
            id(str): レコードID
        """
        with self.db:
            cursor = self.db.execute(f"SELECT * FROM setting_time_{guild_id} WHERE id = ?",(id))
            rows = cursor.fetchall()[0]
        return {
                    "id":rows[0],
                    "channel_id":rows[1],
                    "option":rows[2],
                    "day":rows[3],
                    "week":rows[4],
                    "call_time":rows[5],
                    "mention_ids":rows[6],
                    "title":rows[7],
                    "main_text":rows[8],
                    "img":rows[9]
                }
    def get_all(self,guild_id:str)->dict[str,str]:
        """
        通知のみのメッセージを全て取得
        Args:
            guild_id(str): サーバーID
        """
        with self.db:
            cursor = self.db.execute(f"SELECT * FROM setting_time_{guild_id}")
            rows = cursor.fetchall()[0]
        return {
                    "id":rows[0],
                    "channel_id":rows[1],
                    "option":rows[2],
                    "day":rows[3],
                    "week":rows[4],
                    "call_time":rows[5],
                    "mention_ids":rows[6],
                    "title":rows[7],
                    "main_text":rows[8],
                    "img":rows[9]
                }
    def delete(self,guild_id:str,id:str):
        """
        通知を削除
        Args:
            guild_id(str): サーバーID
            id(str): レコードID
        """
        with self.db:
            self.db.execute(f"DELETE FROM setting_time_{guild_id} WHERE id =?", (id,))
        self.db.commit()
    def update_setting_time(self, guild_id:str, id:str, channel_id=None, option=None, day=None, week=None, call_time=None,
                            mention_ids=None, title=None, main_text=None, img=None):
        """setting_timeテーブルのレコードを更新する。
        Args:
            guild_id (int): サーバーID
            id (int): レコードID
            channel_id (int, optional): チャンネルID
            option (str, optional): オプション
            day (str, optional): 日
            week (str, optional): 週
            call_time (str, optional): 時間
            mention_ids (str, optional): メンションID
            title (str, optional): タイトル
            main_text (str, optional): 本文
            img (str, optional): 画像
        """
        update_values = []
        params = []

        for column, value in {
            "channel_id": channel_id,
            "option": option,
            "day": day,
            "week": week,
            "call_time": call_time,
            "mention_ids": mention_ids,
            "title": title,
            "main_text": main_text,
            "img": img,
        }.items():
            if value is not None:
                update_values.append(f"{column} = %s")
                params.append(value)

        sql_query = f"UPDATE setting_time_{guild_id} SET {', '.join(update_values)} WHERE id = %s"
        params.append(id)

        with self.db:
            self.db.execute(sql_query, params)
            self.db.commit()
    def close(self):
        """
        dbクローズ
        """
        self.db.close()

if __name__ == '__main__':
    sql_table = Database("test")
    sql_table.create_table()
    sql_table.set("1234567890123456789", "8765432109876543210","day", "10:00","1","あ","aaa","None")
    print(sql_table.get_all())