import sqlite3

def check_users():
    conn = sqlite3.connect('game_database.db')
    cursor = conn.cursor()
    
    print("VERIFICANDO BANCO DE DADOS ========================")
   
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\nEstrutura da tabela 'users':")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    cursor.execute("SELECT id, nickname, password, skin_selected, level_unlocked, score FROM users")
    users = cursor.fetchall()
    
    print(f"\nTotal de usuários: {len(users)}")
    for user in users:
        print(f"  ID: {user[0]}, Nickname: '{user[1]}', Nível: {user[4]}, Score: {user[5]}")

    print("\nTabela 'rankings':")
    cursor.execute("SELECT COUNT(*) FROM rankings")
    count = cursor.fetchone()[0]
    print(f"  Total de registros: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, nickname, level, completion_time, score FROM rankings ORDER BY level, completion_time")
        rankings = cursor.fetchall()
        for rank in rankings:
            print(f"  ID: {rank[0]}, Nickname: '{rank[1]}', Nível: {rank[2]}, Tempo: {rank[3]}ms, Score: {rank[4]}")
    
    conn.close()
    print("=====================================================")

if __name__ == '__main__':
    check_users()