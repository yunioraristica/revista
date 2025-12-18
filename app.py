"""
Aplicación Flask principal para Bot OJS Uploader
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import json
import logging
from datetime import datetime
import uuid
import hashlib
import requests

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest())

# Token de Telegram (se puede configurar después)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')

class SimpleConfig:
    def __init__(self):
        self.config_dir = "config"
        os.makedirs(self.config_dir, exist_ok=True)
        self.init_configs()
    
    def init_configs(self):
        # Admin config
        if not os.path.exists(f"{self.config_dir}/admin.json"):
            default = {
                "admin_username": "admin",
                "admin_password": "admin123",
                "bot_token": str(uuid.uuid4()),
                "created_at": datetime.now().isoformat()
            }
            with open(f"{self.config_dir}/admin.json", 'w') as f:
                json.dump(default, f, indent=2)
        
        # Telegram config
        if not os.path.exists(f"{self.config_dir}/telegram.json"):
            default = {
                "telegram_bot_token": "",
                "telegram_admin_user_id": "",
                "webhook_url": "",
                "configured_at": "",
                "is_active": False
            }
            with open(f"{self.config_dir}/telegram.json", 'w') as f:
                json.dump(default, f, indent=2)
    
    def get_config(self, name):
        try:
            with open(f"{self.config_dir}/{name}.json", 'r') as f:
                return json.load(f)
        except:
            return {}

config = SimpleConfig()

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página principal"""
    try:
        return render_template('index.html')
    except:
        return """
        <h1>🤖 Bot OJS Uploader</h1>
        <p>✅ Sistema funcionando</p>
        <a href="/admin/login">Panel Admin</a>
        """

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login de administrador"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        admin_config = config.get_config('admin')
        
        if username == admin_config.get('admin_username') and password == admin_config.get('admin_password'):
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        
        return "Credenciales incorrectas"
    
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Panel de administración"""
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')
    
    admin_config = config.get_config('admin')
    telegram_config = config.get_config('telegram')
    
    return f"""
    <h1>⚙️ Panel de Administración</h1>
    <p>Token del bot: {admin_config.get('bot_token', 'No configurado')}</p>
    <p>Telegram configurado: {'✅' if telegram_config.get('is_active') else '❌'}</p>
    <a href="/telegram/setup">Configurar Telegram</a>
    """

# ==================== TELEGRAM ====================

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """Webhook para Telegram"""
    try:
        data = request.json
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            telegram_config = config.get_config('telegram')
            token = telegram_config.get('telegram_bot_token') or TELEGRAM_TOKEN
            
            if not token:
                return jsonify({'error': 'Token no configurado'}), 400
            
            # Comando /start
            if text == '/start':
                response = f"""
🤖 *Bot OJS Uploader - Activo*

✅ Conectado correctamente
📍 URL: https://revista-amyn.onrender.com
🕐 Hora: {datetime.now().strftime('%H:%M:%S')}

Envía /help para ver comandos disponibles
                """
                
                send_telegram_message(token, chat_id, response)
                return jsonify({'status': 'ok'})
            
            # Comando /help
            elif text == '/help':
                response = """
🆘 *Comandos disponibles:*

/start - Iniciar el bot
/help - Mostrar esta ayuda
/status - Ver estado del sistema

📞 *Soporte:* Contacta al administrador
                """
                send_telegram_message(token, chat_id, response)
                return jsonify({'status': 'ok'})
            
            # Comando /status
            elif text == '/status':
                response = f"""
📊 *Estado del Sistema*

✅ Servicio: Activo
📍 URL: https://revista-amyn.onrender.com
🕐 Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 Bot: Conectado a Telegram
⚡ Modo: Render + Webhook
                """
                send_telegram_message(token, chat_id, response)
                return jsonify({'status': 'ok'})
        
        return jsonify({'status': 'ignored'})
        
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({'error': str(e)}), 500

def send_telegram_message(token, chat_id, text):
    """Enviar mensaje a Telegram"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return None

@app.route('/telegram/setup', methods=['GET', 'POST'])
def setup_telegram():
    """Configurar Telegram"""
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        user_id = request.form.get('user_id', '').strip()
        
        if token and user_id:
            # Guardar configuración
            telegram_config = {
                'telegram_bot_token': token,
                'telegram_admin_user_id': user_id,
                'configured_at': datetime.now().isoformat(),
                'is_active': True
            }
            
            with open('config/telegram.json', 'w') as f:
                json.dump(telegram_config, f, indent=2)
            
            # Configurar webhook
            webhook_url = "https://revista-amyn.onrender.com/telegram"
            try:
                # Eliminar webhook anterior
                requests.post(f"https://api.telegram.org/bot{token}/deleteWebhook")
                
                # Configurar nuevo
                response = requests.post(
                    f"https://api.telegram.org/bot{token}/setWebhook",
                    json={'url': webhook_url, 'drop_pending_updates': True}
                )
                
                if response.json().get('ok'):
                    telegram_config['webhook_url'] = webhook_url
                    with open('config/telegram.json', 'w') as f:
                        json.dump(telegram_config, f, indent=2)
                    
                    # Enviar mensaje de confirmación
                    send_telegram_message(token, user_id, 
                        f"✅ *Bot configurado exitosamente*\n\nWebhook: {webhook_url}\n\nEnvía /start para comenzar")
                    
                    return """
                    <h2>✅ Telegram configurado</h2>
                    <p>Ahora envía /start a tu bot en Telegram</p>
                    <a href="/">Volver al inicio</a>
                    """
                else:
                    return f"Error: {response.json().get('description')}"
                    
            except Exception as e:
                return f"Error: {e}"
    
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Configurar Telegram</title></head>
    <body style="padding:50px">
        <h2>🔧 Configurar Telegram</h2>
        <form method="POST">
            <p>Token del bot (de @BotFather):</p>
            <input type="text" name="token" style="width:300px;padding:10px" 
                   placeholder="6123456789:ABCdefGHIjkl..." required>
            
            <p>Tu ID de usuario (de @userinfobot):</p>
            <input type="text" name="user_id" style="width:300px;padding:10px" 
                   placeholder="123456789" required>
            
            <br><br>
            <button type="submit" style="padding:10px 20px">Configurar</button>
        </form>
    </body>
    </html>
    """

# ==================== API ====================

@app.route('/api/status')
def api_status():
    """Estado del sistema"""
    telegram_config = config.get_config('telegram')
    
    return jsonify({
        'status': 'online',
        'service': 'OJS Uploader Bot',
        'url': 'https://revista-amyn.onrender.com',
        'timestamp': datetime.now().isoformat(),
        'telegram_configured': telegram_config.get('is_active', False),
        'telegram_webhook': telegram_config.get('webhook_url', '')
    })

@app.route('/api/test')
def api_test():
    """Endpoint de prueba"""
    return jsonify({'success': True, 'message': 'API funcionando'})

# ==================== INICIO ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Iniciando en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
