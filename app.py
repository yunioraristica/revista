"""
Bot OJS Uploader con Telegram - Render Ready
"""

from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
import requests

app = Flask(__name__)

# Token de tu bot (REEMPLAZA ESTO CON TU TOKEN REAL)
TELEGRAM_TOKEN = "TU_TOKEN_DE_TELEGRAM_AQUI"

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Bot OJS Uploader</title></head>
    <body style="font-family:Arial;padding:50px;text-align:center">
        <h1>🤖 Bot OJS Uploader</h1>
        <p>✅ Desplegado en Render</p>
        <p>URL: https://revista-amyn.onrender.com</p>
        <p><a href="/telegram/setup">🔧 Configurar Telegram</a></p>
    </body>
    </html>
    """

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """Webhook para Telegram"""
    try:
        data = request.json
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            # Respuesta a /start
            if text == '/start':
                response = """
🤖 *Bot OJS Uploader - Activo*

✅ Conectado correctamente
📍 Servidor: Render
📅 Hora: {time}

Envía /help para ver comandos
                """.format(time=datetime.now().strftime('%H:%M:%S'))
                
                send_telegram_message(chat_id, response)
                return jsonify({'status': 'ok'})
            
            # Respuesta a /help
            elif text == '/help':
                help_text = """
🆘 *Comandos disponibles:*
/start - Iniciar bot
/help - Mostrar ayuda
/status - Ver estado

📞 *Soporte:* Contacta al administrador
                """
                send_telegram_message(chat_id, help_text)
                return jsonify({'status': 'ok'})
            
            # Respuesta a /status
            elif text == '/status':
                status_text = f"""
📊 *Estado del Sistema*

✅ Servicio: Activo
📍 URL: https://revista-amyn.onrender.com
🕐 Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 Bot: Conectado
                """
                send_telegram_message(chat_id, status_text)
                return jsonify({'status': 'ok'})
        
        return jsonify({'status': 'ignored'})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def send_telegram_message(chat_id, text):
    """Enviar mensaje a Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return None

@app.route('/telegram/setup', methods=['GET', 'POST'])
def setup_telegram():
    """Configurar Telegram"""
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if token:
            # Actualizar token
            global TELEGRAM_TOKEN
            TELEGRAM_TOKEN = token
            
            # Configurar webhook
            webhook_url = "https://revista-amyn.onrender.com/telegram"
            setup_url = f"https://api.telegram.org/bot{token}/setWebhook"
            
            try:
                response = requests.post(setup_url, json={
                    'url': webhook_url,
                    'drop_pending_updates': True
                })
                
                if response.json().get('ok'):
                    return f"""
                    <h2>✅ Configurado</h2>
                    <p>Ahora envía /start a tu bot en Telegram</p>
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
        <h2>Configurar Telegram</h2>
        <form method="POST">
            <p>Token de tu bot:</p>
            <input type="text" name="token" style="width:300px;padding:10px">
            <br><br>
            <button type="submit">Configurar</button>
        </form>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'online',
        'telegram': 'configured' if TELEGRAM_TOKEN != "TU_TOKEN_DE_TELEGRAM_AQUI" else 'not_configured',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
