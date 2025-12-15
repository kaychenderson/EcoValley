import sqlite3
from database import Database

class RankingDAO:
    def __init__(self):
        self.db = Database()
    
    def save_ranking(self, user_id, nickname, level, completion_time, score):
        """Salva ou atualiza o ranking de um jogador"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, completion_time FROM rankings 
            WHERE user_id = ? AND level = ?
        ''', (user_id, level))
        
        existing = cursor.fetchone()
        
        if existing:
            existing_id, existing_time = existing
            print(f"Registro existente encontrado para usuário {user_id} no nível {level} com tempo {existing_time}ms")

            if completion_time < existing_time:
                cursor.execute('''
                    UPDATE rankings 
                    SET completion_time = ?, score = ?, created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (completion_time, score, existing_id))
                print("Ranking atualizado (tempo melhor)")
            else:
                print("Ranking mantido (tempo não melhorou)")
        else:
            cursor.execute('''
                INSERT INTO rankings (user_id, nickname, level, completion_time, score)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, nickname, level, completion_time, score))
            print("Novo ranking inserido")
        
        conn.commit()
        conn.close()
        return True
    
    def get_rankings_by_level(self, level, limit=10):
        """Obtém os melhores tempos para um nível específico"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nickname, completion_time, score, created_at
            FROM rankings 
            WHERE level = ?
            ORDER BY completion_time ASC
            LIMIT ?
        ''', (level, limit))
        
        rankings = []
        for row in cursor.fetchall():
            nickname, completion_time, score, created_at = row
            
            total_seconds = completion_time // 1000
            seconds = total_seconds % 60
            minutes = completion_time // 60000
            milliseconds = completion_time % 1000
            
            rankings.append({
                'nickname': nickname,
                'completion_time': completion_time,
                'time_formatted': f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}",
                'score': score,
                'created_at': created_at
            })
        
        print(f"Encontramos {len(rankings)} rankings para o nível {level}")
        for r in rankings:
            print(f" - {r['nickname']}: {r['time_formatted']} (Tempo: {r['completion_time']}ms, Score: {r['score']})")
            
        conn.close()
        return rankings
    
    def get_user_ranking(self, user_id, level):
        """Obtém o ranking de um usuário específico em um nível"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nickname, completion_time, score, created_at
            FROM rankings 
            WHERE user_id = ? AND level = ?
        ''', (user_id, level))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            nickname, completion_time, score, created_at = row
            
            minutes = completion_time // 60000
            seconds = (completion_time % 60000) // 1000
            milliseconds = completion_time % 1000
            
            return {
                'nickname': nickname,
                'completion_time': completion_time,
                'time_formatted': f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}",
                'score': score,
                'created_at': created_at
            }
        return None