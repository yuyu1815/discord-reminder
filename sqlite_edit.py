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
    def __str__(self):
        cursor = self.db.execute("SELECT * FROM setting_time;")
        rows = cursor.fetchall()
        return str(rows)
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
                    option_id INTEGER NOT NULL,
                    call_time VARCHAR(10) NOT NULL,
                    mention_ids TEXT NOT NULL
                );
            """)
    def set(self, guild_id:str, channel_id:str,option_id:str,call_time:str,mention_ids:str)->None:
        """
        チャンネルを設定
        通知時間を設定
        """
        with self.db:
            self.db.execute(f"INSERT OR IGNORE INTO setting_time (guild_id,channel_id,option_id,call_time,mention_ids) VALUES (?,?,?,?,?)", (guild_id,channel_id,option_id,call_time,mention_ids))
        self.db.commit()
if __name__ == '__main__':
    sql_table = Database("test")
    sql_table.create_table()
    sql_table.set("1234567890123456789", "8765432109876543210","day", "10:00","1")
    print(sql_table)