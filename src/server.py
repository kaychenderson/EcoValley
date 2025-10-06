from flask import Flask, render_template, request, jsonify, session
from user_dao import UserDAO
from models import User
import os
import subprocess
import threading
import sys
import time

app = Flask(__name__, template_folder='templates')
app.secret_key = 'sua_chave_secreta_super_segura_aqui_12345'
user_dao = UserDAO()

# Dicionário para armazenar sessões ativas (em produção use Redis ou similar)
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
        # Obter dados do usuário diretamente do banco (sem usar session)
        user = user_dao.get_user_by_id(user_id)
        if not user:
            print("❌ ERRO: Usuário não encontrado")
            return False
        
        print(f"🎮 Iniciando jogo para: {user.nickname}")
        print(f"🎯 Nível: {level}")
        print(f"🎨 Skin: {user.skin_selected}")
        
        # Caminho absoluto para o game_launcher.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        game_script = os.path.join(current_dir, 'game_launcher.py')
        
        print(f"📁 Executando: {game_script}")
        
        # Executar o jogo como subprocesso
        process = subprocess.Popen([
            sys.executable, game_script,
            '--nickname', user.nickname,
            '--skin', str(user.skin_selected),
            '--level', str(level)
        ])
        
        # Armazenar processo na sessão ativa
        active_sessions[user_id] = {
            'process': process,
            'running': True,
            'level': level
        }
        
        print("✅ Jogo iniciado com sucesso!")
        
        # Monitorar o processo em uma thread separada
        def monitor_process():
            process.wait()  # Espera o processo terminar
            
            # Atualizar status
            active_sessions[user_id]['running'] = False
            
            # Atualizar progresso se o jogo foi bem-sucedido
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
        print(f"❌ ERRO ao iniciar jogo: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/api/start-game', methods=['POST'])
def api_start_game():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não logado'})
    
    user_id = session['user_id']
    
    # Verificar se já tem jogo rodando para este usuário
    if user_id in active_sessions and active_sessions[user_id]['running']:
        return jsonify({'success': False, 'message': 'Jogo já está em execução'})
    
    data = request.json
    level = data.get('level', 1)
    
    # Verificar se o usuário tem acesso ao nível
    user = user_dao.get_user_by_id(user_id)
    if not user or level > user.level_unlocked:
        return jsonify({'success': False, 'message': 'Nível não desbloqueado'})
    
    print(f"🚀 Solicitado início do jogo - Usuário: {user.nickname}, Nível: {level}")
    
    # Iniciar o jogo em uma thread separada
    thread = threading.Thread(target=run_game_process, args=(user_id, level))
    thread.daemon = True
    thread.start()
    
    # Dar tempo para o processo iniciar
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
        # Verificar se o processo ainda está rodando
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

# API endpoints
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
    
    # Parar jogo se estiver rodando
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

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("⚠️  Pasta 'templates' criada. Certifique-se de adicionar os arquivos HTML.")
    
    print("=" * 50)
    print("🎮 SERVIDOR DO JOGO 2D - VERSÃO CORRIGIDA")
    print("=" * 50)
    print("📋 Instruções:")
    print("1. Acesse: http://localhost:5000")
    print("2. Faça cadastro e login")
    print("3. Selecione skin e nível")
    print("4. Clique em um nível para iniciar o jogo")
    print("5. O Pygame abrirá em uma NOVA JANELA")
    print("=" * 50)
    
    app.run(debug=True, port=5000)