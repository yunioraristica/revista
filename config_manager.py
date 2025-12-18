"""
Gestor de configuración para el bot OJS con Telegram
Autor: Bot OJS Uploader
"""

import json
import os
from datetime import datetime
import uuid

class ConfigManager:
    def __init__(self):
        self.config_dir = "config"
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Archivos de configuración
        self.admin_config_file = os.path.join(self.config_dir, "admin.json")
        self.telegram_config_file = os.path.join(self.config_dir, "telegram.json")  # ⭐ NUEVO
        self.journals_config_file = os.path.join(self.config_dir, "journals.json")
        
        # Inicializar configuraciones por defecto
        self.init_default_configs()
    
    def init_default_configs(self):
        """Inicializar configuraciones por defecto"""
        # Configuración de administrador
        if not os.path.exists(self.admin_config_file):
            default_admin = {
                "admin_username": "admin",
                "admin_password": "admin123",
                "bot_token": str(uuid.uuid4()),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.save_json(self.admin_config_file, default_admin)
        
        # ============================================================
        # ⭐⭐ CONFIGURACIÓN DE TELEGRAM - AQUÍ PONES TUS DATOS ⭐⭐
        # ============================================================
        if not os.path.exists(self.telegram_config_file):
            default_telegram = {
                # 🔑 TOKEN DE TU BOT DE TELEGRAM
                # Obténlo de @BotFather -> /newbot
                # Ejemplo: "6123456789:AAE7t8K9v5gcR2p3qrj1TwZVuXy5v6G7ij1"
                "telegram_bot_token": "PON_AQUI_TU_TOKEN",
                
                # 👤 TU @USUARIO DE TELEGRAM (opcional) y TU ID
                # Tu @usuario: Ejemplo "@yunior_avila13"
                # Tu ID numérico: Obténlo de @userinfobot
                "telegram_admin_username": "@tu_usuario_de_telegram",
                "telegram_admin_user_id": "tu_id_numerico",
                
                # Configuraciones de notificaciones
                "telegram_chat_id": "",
                "notify_on_upload": True,
                "notify_on_error": True,
                "notify_on_login": True,
                "notify_on_startup": True,
                "telegram_webhook_url": "",
                
                # Comandos del bot
                "telegram_commands": {
                    "start": "🚀 Iniciar el bot OJS Uploader",
                    "status": "📊 Ver estado del sistema",
                    "journals": "📚 Listar revistas configuradas",
                    "upload": "⬆️ Subir archivos a revista",
                    "report": "📄 Obtener último reporte",
                    "config": "⚙️ Ver configuración",
                    "help": "❓ Mostrar ayuda"
                },
                
                # Información adicional
                "bot_username": "",  # Se llenará automáticamente
                "bot_name": "OJS Uploader Bot",
                "last_notification": "",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.save_json(self.telegram_config_file, default_telegram)
        # ============================================================
        
        # Configuración de revistas
        if not os.path.exists(self.journals_config_file):
            default_journals = {}
            self.save_json(self.journals_config_file, default_journals)
    
    # ==================== MÉTODOS PARA ADMIN ====================
    def get_admin_config(self):
        """Obtener configuración de administrador"""
        return self.load_json(self.admin_config_file)
    
    def update_admin_config(self, config):
        """Actualizar configuración de administrador"""
        current = self.get_admin_config()
        current.update(config)
        current['updated_at'] = datetime.now().isoformat()
        self.save_json(self.admin_config_file, current)
        return True
    
    # ==================== MÉTODOS PARA TELEGRAM ====================
    def get_telegram_config(self):
        """Obtener configuración de Telegram"""
        return self.load_json(self.telegram_config_file)
    
    def update_telegram_config(self, config):
        """Actualizar configuración de Telegram"""
        current = self.get_telegram_config()
        current.update(config)
        current['updated_at'] = datetime.now().isoformat()
        self.save_json(self.telegram_config_file, current)
        return True
    
    def is_telegram_configured(self):
        """Verificar si Telegram está configurado correctamente"""
        config = self.get_telegram_config()
        
        # Verificar que el token no esté vacío ni sea el placeholder
        token = config.get('telegram_bot_token', '').strip()
        if not token or token == "PON_AQUI_TU_TOKEN":
            return False, "❌ Token del bot no configurado"
        
        # Verificar que el ID de usuario no esté vacío
        user_id = config.get('telegram_admin_user_id', '').strip()
        if not user_id or user_id == "tu_id_numerico":
            return False, "❌ ID de usuario no configurado"
        
        return True, "✅ Telegram configurado correctamente"
    
    def get_telegram_bot_token(self):
        """Obtener token del bot de Telegram"""
        config = self.get_telegram_config()
        token = config.get('telegram_bot_token', '')
        
        # Si todavía tiene el placeholder, retornar vacío
        if token == "PON_AQUI_TU_TOKEN":
            return ""
        return token
    
    def get_telegram_admin_info(self):
        """Obtener información del administrador de Telegram"""
        config = self.get_telegram_config()
        return {
            'username': config.get('telegram_admin_username', '@sin_configurar'),
            'user_id': config.get('telegram_admin_user_id', ''),
            'chat_id': config.get('telegram_chat_id', '')
        }
    
    def set_telegram_bot_info(self, bot_username, bot_name):
        """Actualizar información del bot de Telegram"""
        config = self.get_telegram_config()
        config['bot_username'] = bot_username
        config['bot_name'] = bot_name
        config['updated_at'] = datetime.now().isoformat()
        self.save_json(self.telegram_config_file, config)
        return True
    
    def record_notification(self, message):
        """Registrar última notificación enviada"""
        config = self.get_telegram_config()
        config['last_notification'] = {
            'message': message[:100] + '...' if len(message) > 100 else message,
            'timestamp': datetime.now().isoformat()
        }
        config['updated_at'] = datetime.now().isoformat()
        self.save_json(self.telegram_config_file, config)
    
    def get_telegram_commands(self):
        """Obtener lista de comandos de Telegram"""
        config = self.get_telegram_config()
        return config.get('telegram_commands', {})
    
    def update_telegram_chat_id(self, chat_id):
        """Actualizar ID del chat de Telegram"""
        config = self.get_telegram_config()
        config['telegram_chat_id'] = chat_id
        config['updated_at'] = datetime.now().isoformat()
        self.save_json(self.telegram_config_file, config)
        return True
    
    # ==================== MÉTODOS PARA REVISTAS ====================
    def get_all_journal_configs(self):
        """Obtener todas las configuraciones de revistas"""
        journals = self.load_json(self.journals_config_file)
        
        # Convertir a lista para frontend
        journal_list = []
        for journal_id, config in journals.items():
            config['id'] = journal_id
            journal_list.append(config)
        
        return journal_list
    
    def get_journal_config(self, journal_id):
        """Obtener configuración de una revista específica"""
        journals = self.load_json(self.journals_config_file)
        return journals.get(journal_id)
    
    def add_journal_config(self, config):
        """Agregar nueva configuración de revista"""
        journals = self.load_json(self.journals_config_file)
        
        # Generar ID único
        journal_id = str(uuid.uuid4())[:8]
        
        # Asegurar campos requeridos
        config['id'] = journal_id
        config['created_at'] = datetime.now().isoformat()
        config['updated_at'] = datetime.now().isoformat()
        
        journals[journal_id] = config
        self.save_json(self.journals_config_file, journals)
        
        return journal_id
    
    def update_journal_config(self, journal_id, updates):
        """Actualizar configuración de revista"""
        journals = self.load_json(self.journals_config_file)
        
        if journal_id not in journals:
            return False
        
        journals[journal_id].update(updates)
        journals[journal_id]['updated_at'] = datetime.now().isoformat()
        
        self.save_json(self.journals_config_file, journals)
        return True
    
    def delete_journal_config(self, journal_id):
        """Eliminar configuración de revista"""
        journals = self.load_json(self.journals_config_file)
        
        if journal_id not in journals:
            return False
        
        del journals[journal_id]
        self.save_json(self.journals_config_file, journals)
        return True
    
    # ==================== MÉTODOS UTILITARIOS ====================
    def save_json(self, filepath, data):
        """Guardar datos en archivo JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_json(self, filepath):
        """Cargar datos desde archivo JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    def get_all_configs(self):
        """Obtener todas las configuraciones"""
        return {
            'admin': self.get_admin_config(),
            'telegram': self.get_telegram_config(),
            'journals': self.get_all_journal_configs()
            }
