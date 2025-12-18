"""
Gestor de configuración para el bot OJS
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
        self.journals_config_file = os.path.join(self.config_dir, "journals.json")
        self.telegram_config_file = os.path.join(self.config_dir, "telegram.json")
        
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
        
        # Configuración de revistas
        if not os.path.exists(self.journals_config_file):
            default_journals = {}
            self.save_json(self.journals_config_file, default_journals)
    
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
