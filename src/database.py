import sqlite3
import os

class Database:
    def __init__(self):
        self.db_path = "game_database.db"
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                skin_selected INTEGER DEFAULT 1,
                level_unlocked INTEGER DEFAULT 1,
                score INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)