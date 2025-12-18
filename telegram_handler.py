"""
Manejador de Telegram para Render
"""

import logging
import requests
import json
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class TelegramHandler:
    """Manejador de Telegram para el bot en Render"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.base_url = "https://api.telegram.org/bot"
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """Cargar configuración"""
        self.config = self.config_manager.get_telegram_config()
    
    def get_bot_token(self):
        """Obtener token del bot"""
        token = self.config.get('telegram_bot_token', '')
        # Verificar si es placeholder
        if token in ['', 'PON_AQUI_TU_TOKEN', 'TU_TOKEN']:
            return None
        return token
    
    def get_admin_id(self):
        """Obtener ID del administrador"""
        return self.config.get('telegram_admin_user_id', '')
    
    def is_configured(self):
        """Verificar si Telegram está configurado"""
        token = self.get_bot_token()
        admin_id = self.get_admin_id()
        return bool(token and admin_id)
    
    def setup_webhook(self, render_url):
        """Configurar webhook en Telegram para Render"""
        try:
            token = self.get_bot_token()
            if not token:
                logger.error("Token de Telegram no configurado")
                return False
            
            # Construir URL del webhook
            webhook_url = f"{render_url}/telegram/webhook"
            
            # Configurar webhook en Telegram
            url = f"{self.base_url}{token}/setWebhook"
            payload = {
                'url': webhook_url,
                'drop_pending_updates': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info(f"✅ Webhook configurado: {webhook_url}")
                
                # Actualizar configuración
                self.config['telegram_webhook_url'] = webhook_url
                self.config_manager.update_telegram_config(self.config)
                
                return True
            else:
                logger.error(f"❌ Error configurando webhook: {result.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en setup_webhook: {str(e)}")
            return False
    
    def delete_webhook(self):
        """Eliminar webhook de Telegram"""
        try:
            token = self.get_bot_token()
            if not token:
                return False
            
            url = f"{self.base_url}{token}/deleteWebhook"
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Webhook eliminado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando webhook: {str(e)}")
            return False
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Enviar mensaje a Telegram"""
        try:
            token = self.get_bot_token()
            if not token:
                return False
            
            url = f"{self.base_url}{token}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            # Intentar enviar sin bloquear
            def send_async():
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"📤 Mensaje enviado a {chat_id}")
                except Exception as e:
                    logger.error(f"❌ Error enviando mensaje: {str(e)}")
            
            # Enviar en hilo separado
            thread = threading.Thread(target=send_async)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en send_message: {str(e)}")
            return False
    
    def send_to_admin(self, text):
        """Enviar mensaje al administrador"""
        admin_id = self.get_admin_id()
        if admin_id:
            return self.send_message(admin_id, text)
        return False
    
    def handle_webhook_update(self, update):
        """Manejar actualizaciones del webhook"""
        try:
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')
                
                if text == '/start':
                    response = self.get_start_message()
                    self.send_message(chat_id, response)
                    return True
                    
                elif text == '/help':
                    response = self.get_help_message()
                    self.send_message(chat_id, response)
                    return True
                    
                elif text == '/status':
                    response = self.get_status_message()
                    self.send_message(chat_id, response)
                    return True
                    
                elif text.startswith('/upload'):
                    # Implementar lógica de subida
                    self.send_message(chat_id, "⏳ Procesando subida...")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error manejando webhook: {str(e)}")
            return False
    
    def get_start_message(self):
        """Mensaje de inicio del bot"""
        return """
🤖 *Bienvenido al Bot OJS Uploader*

*Comandos disponibles:*
/start - Mostrar este mensaje
/status - Ver estado del sistema  
/help - Mostrar ayuda
/journals - Listar revistas configuradas

*Configurado para:*
- Subida automática a revistas OJS
- Compresión en ZIP de 10MB
- Reportes completos en TXT

📍 *Estado:* ✅ Activo
        """
    
    def get_help_message(self):
        """Mensaje de ayuda"""
        return """
🆘 *Ayuda - Bot OJS Uploader*

*¿Qué puedo hacer?*
• Subir archivos automáticamente a revistas OJS
• Descargar desde enlaces directos
• Comprimir en chunks de 10MB
• Generar reportes en TXT

*Configuración necesaria:*
1. Revista OJS (ej: Revista 16 de Abril)
2. Usuario y contraseña
3. ID de envío

*Soporte:* Contacta al administrador
        """
    
    def get_status_message(self):
        """Mensaje de estado"""
        config_status = "✅" if self.is_configured() else "❌"
        journals = self.config_manager.get_all_journal_configs()
        
        return f"""
📊 *Estado del Sistema*

*Configuración Telegram:* {config_status}
*Revistas configuradas:* {len(journals)}
*Webhook:* {'✅ Activo' if self.config.get('telegram_webhook_url') else '❌ Inactivo'}

*Última actividad:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📍 *Servidor:* Render.com
        """
    
    def test_connection(self):
        """Probar conexión con Telegram"""
        try:
            token = self.get_bot_token()
            if not token:
                return False, "Token no configurado"
            
            url = f"{self.base_url}{token}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                return True, f"✅ Conectado: @{bot_info.get('username')}"
            else:
                return False, f"❌ Error: {data.get('description')}"
                
        except Exception as e:
            return False, f"❌ Error: {str(e)}"