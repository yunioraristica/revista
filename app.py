"""
Bot de Subida Automática para Revistas OJS
Versión Render Compatible
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import hashlib
from functools import wraps
import uuid

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configurar clave secreta segura
app.secret_key = os.environ.get('SESSION_SECRET', hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest())
CORS(app)

# Configuración para Render
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SERVER_NAME'] = None  # Importante para Render

# Importar módulos del bot
try:
    from config_manager import ConfigManager
    config_manager = ConfigManager()
    logger.info("✅ ConfigManager importado correctamente")
except Exception as e:
    logger.error(f"❌ Error importando ConfigManager: {str(e)}")
    config_manager = None

# ==================== DECORADORES ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def bot_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Bot-Token') or request.args.get('token')
        if not token:
            return jsonify({'error': 'Token faltante'}), 401
        
        try:
            admin_config = config_manager.get_admin_config()
            if token != admin_config.get('bot_token'):
                return jsonify({'error': 'Token inválido'}), 401
        except:
            return jsonify({'error': 'Error verificando token'}), 500
            
        return f(*args, **kwargs)
    return decorated_function

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página principal"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error en index: {str(e)}")
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Bot OJS Uploader</title></head>
        <body>
            <h1>🤖 Bot OJS Uploader</h1>
            <p>El bot está funcionando correctamente en Render.</p>
            <p><a href="/admin/login">Panel de Administración</a></p>
        </body>
        </html>
        """

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login del administrador"""
    try:
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            try:
                admin_config = config_manager.get_admin_config()
            except:
                # Configuración por defecto si hay error
                admin_config = {
                    'admin_username': 'admin',
                    'admin_password': 'admin123'
                }
            
            if (username == admin_config.get('admin_username') and 
                password == admin_config.get('admin_password')):
                session['admin_logged_in'] = True
                return redirect(url_for('admin_dashboard'))
            
            return render_template('login.html', error='Credenciales inválidas')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error en admin_login: {str(e)}")
        return "Error en el sistema de login. Por favor, intenta más tarde.", 500

@app.route('/admin/logout')
def admin_logout():
    """Logout del administrador"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Panel de administración"""
    try:
        admin_config = config_manager.get_admin_config()
        journal_configs = config_manager.get_all_journal_configs()
        
        return render_template('admin.html', 
                             admin_config=admin_config,
                             journals=journal_configs)
    except Exception as e:
        logger.error(f"Error en admin_dashboard: {str(e)}")
        return "Error cargando el panel de administración.", 500

# ==================== API ENDPOINTS ====================

@app.route('/api/admin/config', methods=['GET'])
@login_required
def get_admin_config_api():
    """Obtener configuración de administrador"""
    try:
        config = config_manager.get_admin_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error get_admin_config_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/update', methods=['POST'])
@login_required
def update_admin_config_api():
    """Actualizar configuración de administrador"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        config_manager.update_admin_config(data)
        return jsonify({'message': 'Configuración actualizada'})
    except Exception as e:
        logger.error(f"Error update_admin_config_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/journals', methods=['GET'])
@bot_token_required
def get_journals_api():
    """Obtener todas las revistas configuradas"""
    try:
        journals = config_manager.get_all_journal_configs()
        return jsonify(journals)
    except Exception as e:
        logger.error(f"Error get_journals_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/journals', methods=['POST'])
@bot_token_required
def add_journal_api():
    """Agregar una nueva revista"""
    try:
        data = request.json
        
        required_fields = ['name', 'host', 'username', 'password', 'default_submission_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} requerido'}), 400
        
        journal_id = config_manager.add_journal_config(data)
        return jsonify({'message': 'Revista agregada', 'journal_id': journal_id})
    except Exception as e:
        logger.error(f"Error add_journal_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@bot_token_required
def upload_files_api():
    """Subir archivos a una revista"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Datos no proporcionados'}), 400
        
        # Simular proceso de subida
        return jsonify({
            'message': 'Subida iniciada (modo simulación)',
            'task_id': str(uuid.uuid4()),
            'status': 'processing'
        })
    except Exception as e:
        logger.error(f"Error upload_files_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def system_status():
    """Verificar estado del sistema"""
    try:
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'environment': 'production'
        })
    except Exception as e:
        logger.error(f"Error system_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS PARA TELEGRAM ====================

@app.route('/telegram/setup', methods=['POST'])
def setup_telegram():
    """Configurar Telegram para Render"""
    try:
        data = request.json or {}
        token = data.get('token', '')
        render_url = data.get('render_url', 'https://revista-amyn.onrender.com')
        
        if not token:
            return jsonify({'error': 'Token requerido'}), 400
        
        # Configurar webhook simple
        import requests
        webhook_url = f"{render_url}/telegram/webhook"
        
        response = requests.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={'url': webhook_url, 'drop_pending_updates': True},
            timeout=10
        )
        
        if response.json().get('ok'):
            return jsonify({
                'message': 'Webhook configurado',
                'webhook_url': webhook_url
            })
        else:
            return jsonify({'error': response.json().get('description')}), 400
            
    except Exception as e:
        logger.error(f"Error setup_telegram: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Webhook para Telegram"""
    try:
        update = request.json
        
        # Responder automáticamente a /start
        if 'message' in update:
            message = update['message']
            text = message.get('text', '')
            chat_id = message['chat']['id']
            
            if text == '/start':
                # Enviar respuesta simple
                import requests
                token = config_manager.get_telegram_config().get('telegram_bot_token', '')
                
                if token:
                    response_text = """
🤖 *Bot OJS Uploader - Activo*

✅ Conectado correctamente a Render
📍 URL: https://revista-amyn.onrender.com
📊 Estado: Online

Envía /help para ver comandos disponibles
                    """
                    
                    requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={
                            'chat_id': chat_id,
                            'text': response_text,
                            'parse_mode': 'Markdown'
                        },
                        timeout=10
                    )
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error telegram_webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno: {str(error)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Excepción no manejada: {str(e)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

# ==================== INICIALIZACIÓN ====================

def init_app():
    """Inicializar la aplicación"""
    try:
        # Crear directorios necesarios
        directories = ['config', 'static', 'templates', 'static/css']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        logger.info("✅ Aplicación inicializada correctamente")
        logger.info(f"✅ URL: https://revista-amyn.onrender.com")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando app: {str(e)}")

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    # Inicializar
    init_app()
    
    # Obtener puerto de Render
    port = int(os.environ.get('PORT', 5000))
    
    # Configurar para producción
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Iniciando servidor en puerto {port}")
    logger.info(f"🔧 Modo debug: {debug_mode}")
    
    # Ejecutar con gunicorn en producción
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
