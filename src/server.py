from flask import Flask, render_template, request, jsonify, session
from user_dao import UserDAO
from models import User
import os
import subprocess
import threading
import sys
import time
from ranking_dao import RankingDAO

app = Flask(__name__, template_folder='templates')
app.secret_key = 'sua_chave_secreta_super_segura_aqui_12345'
user_dao = UserDAO()
ranking_dao = RankingDAO()

active_sessions = {}

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/skin-selection')
def skin_selection():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('skin_selection.html')

@app.route('/level-selection')
def level_selection():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('level_selection.html')

def run_game_process(user_id, level):
    """Executa o jogo Pygame em um processo separado"""
    try:
        user = user_dao.get_user_by_id(user_id)
        if not user:
            print("ERRO: Usuário não encontrado")
            return False
        
        print(f"🎮 Iniciando jogo para: {user.nickname}")
        print(f"🎯 Nível: {level}")
        print(f"🎨 Skin: {user.skin_selected}")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        game_script = os.path.join(current_dir, 'game_launcher.py')
        
        print(f"📁 Executando: {game_script}")
        
        process = subprocess.Popen([
            sys.executable, game_script,
            '--nickname', user.nickname,
            '--skin', str(user.skin_selected),
            '--level', str(level)
        ])
        
        active_sessions[user_id] = {
            'process': process,
            'running': True,
            'level': level
        }
        
        print("✅ Jogo iniciado com sucesso!")
        
        def monitor_process():
            process.wait()
            
            active_sessions[user_id]['running'] = False

            try:
                import json
                if os.path.exists('game_result.json'):
                    with open('game_result.json', 'r') as f:
                        result_data = json.load(f)

                    print(f"📊 Resultado do jogo para {user.nickname}: {result_data}")
                    
                    if result_data.get('success'):
                        try:
                            import requests
                            response = requests.post('http://localhost:5000/api/save-ranking',
                                          json=result_data,
                                          timeout=5)
                            print(f" Resposta do servidor: {response.json()}")
                        except Exception as e:
                            print(f"Erro ao enviar resultado para o servidor: {e}")                 
                    
                    os.remove('game_result.json')
            except Exception as e:
                print(f"Erro ao processar resultado: {e}")
            
            if process.returncode == 0 and level < 3:
                new_level = level + 1
                user.level_unlocked = new_level
                user_dao.update_user(user)
                print(f"🎉 Novo nível desbloqueado para {user.nickname}: {new_level}")
            
            print(f"🛑 Jogo terminado para {user.nickname}")
        
        monitor_thread = threading.Thread(target=monitor_process)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return True
        
    except Exception as e:
        print(f"ERRO ao iniciar jogo: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/api/start-game', methods=['POST'])
def api_start_game():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não logado'})
    
    user_id = session['user_id']
    
    if user_id in active_sessions and active_sessions[user_id]['running']:
        return jsonify({'success': False, 'message': 'Jogo já está em execução'})
    
    data = request.json
    level = data.get('level', 1)
    
    user = user_dao.get_user_by_id(user_id)
    if not user or level > user.level_unlocked:
        return jsonify({'success': False, 'message': 'Nível não desbloqueado'})
    
    print(f"🚀 Solicitado início do jogo - Usuário: {user.nickname}, Nível: {level}")
    
    thread = threading.Thread(target=run_game_process, args=(user_id, level))
    thread.daemon = True
    thread.start()
    
    time.sleep(1)
    
    if user_id in active_sessions and active_sessions[user_id]['running']:
        return jsonify({
            'success': True, 
            'message': f'Jogo nível {level} iniciado! Verifique sua tela.'
        })
    else:
        return jsonify({
            'success': False, 
            'message': 'Falha ao iniciar o jogo. Verifique o console para detalhes.'
        })

@app.route('/api/game-status', methods=['GET'])
def api_game_status():
    if 'user_id' not in session:
        return jsonify({'running': False})
    
    user_id = session['user_id']
    
    if user_id in active_sessions:
        process_info = active_sessions[user_id]
        if process_info['process'].poll() is not None:
            process_info['running'] = False
            return jsonify({'running': False, 'message': 'Jogo terminado'})
        
        return jsonify({'running': True, 'level': process_info['level']})
    
    return jsonify({'running': False})

@app.route('/api/stop-game', methods=['POST'])
def api_stop_game():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    user_id = session['user_id']
    
    if user_id in active_sessions:
        active_sessions[user_id]['process'].terminate()
        active_sessions[user_id]['running'] = False
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = user_dao.login(data['nickname'], data['password'])
    
    if user:
        session['user_id'] = user.id
        session['nickname'] = user.nickname
        return jsonify({'success': True, 'user': {
            'nickname': user.nickname,
            'skin_selected': user.skin_selected,
            'level_unlocked': user.level_unlocked
        }})
    return jsonify({'success': False, 'message': 'Credenciais inválidas'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    
    if user_dao.user_exists(data['nickname']):
        return jsonify({'success': False, 'message': 'Nickname já existe'})
    
    user = User(data['nickname'], data['password'])
    if user_dao.register(user):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Erro no cadastro'})

@app.route('/api/update-skin', methods=['POST'])
def api_update_skin():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não logado'})
    
    data = request.json
    user = user_dao.get_user_by_id(session['user_id'])
    
    if user:
        user.skin_selected = data['skin_index']
        user_dao.update_user(user)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Usuário não encontrado'})

@app.route('/api/get-user-data', methods=['GET'])
def api_get_user_data():
    if 'user_id' not in session:
        return jsonify({'error': 'No user logged in'})
    
    user = user_dao.get_user_by_id(session['user_id'])
    if user:
        return jsonify({
            'nickname': user.nickname,
            'skin_selected': user.skin_selected,
            'level_unlocked': user.level_unlocked
        })
    return jsonify({'error': 'User not found'})

@app.route('/api/update-level-progress', methods=['POST'])
def api_update_level_progress():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    data = request.json
    user = user_dao.get_user_by_id(session['user_id'])
    
    if user:
        new_level = max(user.level_unlocked, data['level_unlocked'])
        user.level_unlocked = new_level
        user.score = max(user.score, data.get('score', 0))
        user_dao.update_user(user)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    user_id = session.get('user_id')
    
    if user_id in active_sessions:
        active_sessions[user_id]['process'].terminate()
        del active_sessions[user_id]
    
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth')
def api_check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})

@app.route('/ranking/<int:level>')
def ranking_page(level):
    if 'user_id' not in session:
        return render_template('login.html')
    
    if level < 1 or level > 3:
        return "Nível inválido", 404
    
    return render_template('ranking.html', level=level)

@app.route('/api/get-rankings/<int:level>', methods=['GET'])
def api_get_rankings(level):
    if level < 1 or level > 3:
        return jsonify({'success': False, 'message': 'Nível inválido'})
    
    rankings = ranking_dao.get_rankings_by_level(level)
    return jsonify({'success': True, 'rankings': rankings})

@app.route('/api/save-ranking', methods=['POST'])
def api_save_ranking():
    try:
        data = request.json
        print(f"Recebido dados para salvar ranking: {data}")

        if not data:
            print("Dados vazios")
            return jsonify({'success': False, 'message': 'Dados vazios'})
        
        if 'nickname' not in data:
            print("Nickname não encontrado nos dados")
            return jsonify({'success': False, 'message': 'Nickname não fornecido'})
        
        nickname = data['nickname']
        print(f"🔍 Buscando usuário: {nickname}")
        
        user = user_dao.get_user_by_nickname(nickname)

        if not user:
            print(f"Usuário '{nickname}' não encontrado no banco de dados")
            
            conn = user_dao.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nickname FROM users")
            all_users = cursor.fetchall()
            conn.close()
            
            print(f"Usuários no banco: {all_users}")
            
            return jsonify({'success': False, 'message': f'Usuário "{nickname}" não encontrado'})
        
        print(f"Usuário encontrado: ID={user.id}, Nickname={user.nickname}")
        
        level = data.get('level', 1)
        completion_time = data.get('completion_time', 0)
        score = data.get('score', 0)

        if completion_time < 0:
            print(f"⚠️ Tempo negativo detectado: {completion_time}. Corrigindo para 0.")
            completion_time = 0
        
        print(f"Salvando ranking para:")
        print(f"Usuário: {nickname}")
        print(f"Nível: {level}")
        print(f"Tempo: {completion_time}ms ({completion_time/1000:.2f}s)")
        print(f"Pontuação: {score}")

        success = ranking_dao.save_ranking(
            user_id=user.id,
            nickname=nickname,
            level=level,
            completion_time=completion_time,
            score=score
        )

        if data.get('success') and level < 3:
            new_level = max(user.level_unlocked, level + 1)
            user.level_unlocked = new_level
            user.score = max(user.score, score)
            user_dao.update_user(user)
            print(f"🎉 Progresso atualizado para {nickname}: nível {new_level}")
        
        print(f"Ranking salvo com sucesso: {success}")
        
        return jsonify({'success': success})
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao salvar ranking: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'})

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Pasta 'templates' criada. Certifique-se de adicionar os arquivos HTML.")
    
    print("=" * 50)
    print("🎮 SERVIDOR DO JOGO 2D - ECOVALLEY")
    print("=" * 50)
    print("📋 Instruções:")
    print("1. Acesse: http://localhost:5000")
    print("2. Faça cadastro e login")
    print("3. Selecione skin e nível")
    print("4. Clique em um nível para iniciar o jogo")
    print("5. O Pygame abrirá em uma NOVA JANELA")
    print("=" * 50)
    
    app.run(debug=True, port=5000)