import sqlite3
# 色表示用
ERROR_COLLAR = '\033[31m' #エラー 赤
NORMAL_COLLAR = '\033[0m' #通常戻す
class Database:
    def __init__(self,app_name:str,db_name:str = "server-file",table_name:str = "datas"):
        self.db_name = db_name
        self.db = sqlite3.connect(
            f"./{app_name}-{db_name}.db",
            isolation_level=None,
        )
    def __enter__(self):
        return self.db.cursor()
    #終了
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        self.db.close()
    def create_table(self):
        """
        テーブルが存在しない場合、テーブルを作る
        """
        with self.db:
            self.db.execute(f"""
                CREATE TABLE IF NOT EXISTS setting_time (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id VARCHAR(20) NOT NULL,
                    channel_id VARCHAR(20) NOT NULL,
                    option_id VARCHAR(10) NOT NULL,
                    call_time VARCHAR(10) NOT NULL,
                    mention_ids TEXT NOT NULL,
                    title TEXT NOT NULL,
                    img TEXT NOT NULL,  -- 画像URL or pass
                    main_text TEXT NOT NULL
                );
            """)
    def set(self, guild_id:str, channel_id:str,option_id:str,call_time:str,mention_ids:str,title:str,main_text:str,img:str = "None")->None:
        """
        チャンネルを設定
        通知時間を設定
        """
        with self.db:
            self.db.execute(f"INSERT OR IGNORE INTO setting_time (guild_id,channel_id,option_id,call_time,mention_ids,title,img,main_text) VALUES (?,?,?,?,?,?,?,?)", (guild_id,channel_id,option_id,call_time,mention_ids,title,img,main_text))
        self.db.commit()
    def get(self,id:str = None):
        """
        通知のみのメッセージを全て取得
        """
        with self.db:
            if id:
                cursor = self.db.execute(f"SELECT * FROM setting_time WHERE id =?", (id,))
            else:
                cursor = self.db.execute(f"SELECT * FROM setting_time")
            rows = cursor.fetchall()
            return rows
    def delete(self,id:str):
        """
        通知を削除
        """
        with self.db:
            self.db.execute(f"DELETE FROM setting_time WHERE id =?", (id,))
        self.db.commit()
    def update(self,id:str,call_time:str,mention_ids:str,title:str,img:str,main_text:str):
        """
        通知を更新
        """
        setting = self.get(id)[0]
        call_time = call_time if call_time is not None else setting[4]
        mention_ids = mention_ids is not None and setting[5]
        title = title if title is not None else setting[6]
        img = img if img is not None else setting[7]
        main_text = main_text if main_text is not None else setting[8]
        with self.db:
            self.db.execute(f"UPDATE setting_time SET call_time=?, mention_ids=?, title=?, img=?, main_text=? WHERE id=?", (call_time, mention_ids, title, img, main_text, id))
        self.db.commit()
    def close(self):
        """
        クローズ
        """
        self.db.close()

if __name__ == '__main__':
    sql_table = Database("test")
    sql_table.create_table()
    sql_table.set("1234567890123456789", "8765432109876543210","day", "10:00","1","あ","aaa","None")
    print(sql_table.get())