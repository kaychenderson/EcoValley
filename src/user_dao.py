import sqlite3
from database import Database
from models import User

class UserDAO:
    def __init__(self):
        self.db = Database()
    
    def register(self, user):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (nickname, password, skin_selected, level_unlocked, score)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.nickname, user.password, user.skin_selected, user.level_unlocked, user.score))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Nickname já existe
        finally:
            conn.close()
    
    def login(self, nickname, password):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE nickname = ? AND password = ?
        ''', (nickname, password))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(
                user_id=user_data[0],
                nickname=user_data[1],
                password=user_data[2],
                skin_selected=user_data[3],
                level_unlocked=user_data[4],
                score=user_data[5]
            )
        return None
    
    def update_user(self, user):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET skin_selected = ?, level_unlocked = ?, score = ?
            WHERE id = ?
        ''', (user.skin_selected, user.level_unlocked, user.score, user.id))
        
        conn.commit()
        conn.close()
    
    def user_exists(self, nickname):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE nickname = ?', (nickname,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def get_user_by_nickname(self, nickname):
        """Obtém um usuário pelo nickname"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE nickname = ?', (nickname,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(
                user_id=user_data[0],
                nickname=user_data[1],
                password=user_data[2],
                skin_selected=user_data[3],
                level_unlocked=user_data[4],
                score=user_data[5]
            )
        return None
    
    def get_user_by_id(self, user_id):
        """Obtém um usuário pelo ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(
                user_id=user_data[0],
                nickname=user_data[1],
                password=user_data[2],
                skin_selected=user_data[3],
                level_unlocked=user_data[4],
                score=user_data[5]
            )
        return None
    
    def update_user_progress(self, user_id, level_unlocked, score):
        """Atualiza apenas o progresso do usuário"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET level_unlocked = ?, score = ?
            WHERE id = ?
        ''', (level_unlocked, score, user_id))
        
        conn.commit()
        conn.close()