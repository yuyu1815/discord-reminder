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
    #終了
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        self.db.close()
    def create_table(self,guild_id:str):
        """
        テーブルが存在しない場合、テーブルを作る
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
    def set(self, guild_id:str, channel_id:str,option:str,day:str,week:str,call_time:str,mention_ids:str,title:str,main_text:str,img:str)->None:
        """
        チャンネルを設定
        通知時間を設定
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
        """
        with self.db:
            self.db.execute(f"DELETE FROM setting_time_{guild_id} WHERE id =?", (id,))
        self.db.commit()
    def update(self,guild_id:str,id:str, channel_id:str,option:str,day:str,week:str,call_time:str,mention_ids:str,title:str,main_text:str,img:str):
        """
        通知を更新
        """
        sql_query = ""
        if channel_id is None and call_time is None and mention_ids is None and title is None and img is None and main_text is None:
            print("更新する項目がありません")
            return
        #指定していないものは昔のものを指定
        setting = self.get_all()
        channel_id = channel_id if not None else setting["channel_id"]
        option = option if not None else setting["option"]
        day = day if not None else setting["day"]
        week = week if not None else setting["week"]
        call_time = call_time if call_time is not None else setting["call_time"]
        mention_ids = mention_ids if mention_ids is not None else setting["mention_ids"]
        title = title if title is not None else setting["title"]
        img = img if img is not None else setting["img"]
        main_text = main_text if main_text is not None else setting["main_text"]
        with self.db:
            #channel_id,option,day,week,call_time,mention_ids,title,img,main_text
            self.db.execute(f"UPDATE setting_time_{guild_id} SET channel_id=?,option=?,day=?,week=?, call_time=?, mention_ids=?, title=?, img=?, main_text=? WHERE id=?",
                            (channel_id,option,day,week,call_time, mention_ids, title, img, main_text,id))
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
    print(sql_table.get_all())