"""
Bot de Subida Automática para Revistas OJS
Desplegable en Render.com
Autor: Bot OJS Uploader
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import hashlib
from functools import wraps
import uuid

# Configuración
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest())
CORS(app)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos del bot
from bot_core import OJSUploader
from config_manager import ConfigManager

# Instancias globales
config_manager = ConfigManager()
bot_instances = {}

# Decorador para requerir autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir token de bot
def bot_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Bot-Token') or request.args.get('token')
        if not token or token != config_manager.get_admin_config().get('bot_token'):
            return jsonify({'error': 'Token inválido o faltante'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login del administrador"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_config = config_manager.get_admin_config()
        
        if (username == admin_config.get('admin_username') and 
            password == admin_config.get('admin_password')):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout del administrador"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Panel de administración"""
    admin_config = config_manager.get_admin_config()
    journal_configs = config_manager.get_all_journal_configs()
    
    return render_template('admin.html', 
                         admin_config=admin_config,
                         journals=journal_configs)

# API Endpoints
@app.route('/api/admin/update', methods=['POST'])
@login_required
def update_admin_config():
    """Actualizar configuración del administrador"""
    data = request.json
    
    required_fields = ['admin_username', 'admin_password', 'bot_token']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} requerido'}), 400
    
    config_manager.update_admin_config(data)
    return jsonify({'message': 'Configuración actualizada'})

@app.route('/api/journals', methods=['GET'])
@bot_token_required
def get_journals():
    """Obtener todas las revistas configuradas"""
    journals = config_manager.get_all_journal_configs()
    return jsonify(journals)

@app.route('/api/journals', methods=['POST'])
@bot_token_required
def add_journal():
    """Agregar una nueva revista"""
    data = request.json
    
    required_fields = ['name', 'host', 'username', 'password', 'default_submission_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} requerido'}), 400
    
    journal_id = config_manager.add_journal_config(data)
    return jsonify({'message': 'Revista agregada', 'journal_id': journal_id})

@app.route('/api/journals/<journal_id>', methods=['PUT'])
@bot_token_required
def update_journal(journal_id):
    """Actualizar configuración de revista"""
    data = request.json
    
    if config_manager.update_journal_config(journal_id, data):
        return jsonify({'message': 'Revista actualizada'})
    return jsonify({'error': 'Revista no encontrada'}), 404

@app.route('/api/journals/<journal_id>', methods=['DELETE'])
@bot_token_required
def delete_journal(journal_id):
    """Eliminar revista"""
    if config_manager.delete_journal_config(journal_id):
        return jsonify({'message': 'Revista eliminada'})
    return jsonify({'error': 'Revista no encontrada'}), 404

@app.route('/api/upload', methods=['POST'])
@bot_token_required
def upload_files():
    """Subir archivos a una revista"""
    data = request.json
    
    required_fields = ['journal_id', 'links', 'submission_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} requerido'}), 400
    
    # Obtener configuración de la revista
    journal_config = config_manager.get_journal_config(data['journal_id'])
    if not journal_config:
        return jsonify({'error': 'Revista no encontrada'}), 404
    
    # Crear o reutilizar instancia del bot
    bot_key = f"{data['journal_id']}_{journal_config['username']}"
    if bot_key not in bot_instances:
        bot_instances[bot_key] = OJSUploader(
            host=journal_config['host'],
            username=journal_config['username'],
            password=journal_config['password']
        )
    
    bot = bot_instances[bot_key]
    
    # Iniciar subida en hilo separado
    thread = threading.Thread(
        target=bot.upload_from_links,
        args=(data['links'], data['submission_id'])
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Subida iniciada',
        'task_id': str(uuid.uuid4()),
        'journal': journal_config['name']
    })

@app.route('/api/status/<task_id>')
@bot_token_required
def get_status(task_id):
    """Obtener estado de una tarea"""
    # En una implementación real, esto consultaría una base de datos
    return jsonify({
        'status': 'processing',
        'progress': 50,
        'message': 'Descargando archivos...'
    })

@app.route('/api/download-report/<journal_id>')
@bot_token_required
def download_report(journal_id):
    """Descargar reporte de subidas"""
    report_path = f"reports/{journal_id}_report.txt"
    
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    
    return jsonify({'error': 'Reporte no encontrado'}), 404

# Comandos del bot (simulados)
@app.route('/api/command', methods=['POST'])
@bot_token_required
def handle_command():
    """Manejar comandos del bot"""
    data = request.json
    command = data.get('command', '').lower()
    
    if command == 'help':
        return jsonify({
            'commands': [
                '/help - Mostrar esta ayuda',
                '/journals - Listar revistas configuradas',
                '/add_journal <nombre> <host> <usuario> <contraseña> <id> - Agregar revista',
                '/update_journal <id> <campo> <valor> - Actualizar revista',
                '/upload <journal_id> <submission_id> <links...> - Subir archivos'
            ]
        })
    
    elif command.startswith('journals'):
        journals = config_manager.get_all_journal_configs()
        return jsonify(journals)
    
    elif command.startswith('add_journal'):
        parts = command.split()
        if len(parts) < 6:
            return jsonify({'error': 'Formato: /add_journal nombre host usuario contraseña id'})
        
        journal_data = {
            'name': parts[1],
            'host': parts[2],
            'username': parts[3],
            'password': parts[4],
            'default_submission_id': parts[5]
        }
        
        journal_id = config_manager.add_journal_config(journal_data)
        return jsonify({'message': f'Revista {journal_id} agregada'})
    
    return jsonify({'error': 'Comando no reconocido'})

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('config', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)