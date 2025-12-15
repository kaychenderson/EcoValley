import sqlite3

def test_database():
    conn = sqlite3.connect('game_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tabelas no banco de dados:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\nDados na tabela rankings:")
    cursor.execute("SELECT * FROM rankings")
    rankings = cursor.fetchall()
    
    if rankings:
        for row in rankings:
            print(f"  ID: {row[0]}, User: {row[2]}, Nível: {row[3]}, Tempo: {row[4]}, Pontos: {row[5]}")
    else:
        print("  Nenhum registro encontrado")
    
    print("\nÍndices na tabela rankings:")
    cursor.execute("PRAGMA index_list(rankings);")
    indexes = cursor.fetchall()
    for index in indexes:
        print(f"  - {index[1]}")
    
    conn.close()

if __name__ == '__main__':
    test_database()