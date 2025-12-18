"""
Núcleo del Bot OJS Uploader
Basado en la estructura HTML proporcionada
"""

import requests
from bs4 import BeautifulSoup
import os
import zipfile
import io
import time
import logging
import re
from urllib.parse import urljoin, urlparse
import mimetypes

logger = logging.getLogger(__name__)

class OJSUploader:
    """Bot para subir archivos a revistas OJS"""
    
    def __init__(self, host, username, password):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.csrf_token = None
        self.logs = []
        self.uploaded_urls = []
        
    def login(self):
        """Iniciar sesión en OJS basado en la estructura HTML proporcionada"""
        try:
            # 1. Obtener página de login
            login_url = f"{self.host}/login"
            self.log(f"Accediendo a: {login_url}")
            
            response = self.session.get(login_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 2. Buscar formulario de login
            login_form = soup.find('form')
            if not login_form:
                # Intentar encontrar formulario por acción
                login_form = soup.find('form', {'action': lambda x: x and 'login' in x})
            
            if not login_form:
                self.log("No se encontró formulario de login")
                return False
            
            # 3. Extraer campos del formulario
            form_data = {}
            
            # Campos de entrada basados en el HTML proporcionado
            username_field = soup.find('input', {'name': 'username', 'id': 'username'})
            password_field = soup.find('input', {'name': 'password', 'id': 'password', 'type': 'password'})
            
            if not username_field or not password_field:
                self.log("No se encontraron campos de usuario/contraseña")
                return False
            
            # Agregar campos obligatorios
            form_data['username'] = self.username
            form_data['password'] = self.password
            
            # Buscar campos ocultos
            hidden_inputs = login_form.find_all('input', {'type': 'hidden'})
            for hidden in hidden_inputs:
                if hidden.get('name') and hidden.get('value'):
                    form_data[hidden['name']] = hidden['value']
            
            # 4. Enviar formulario
            action = login_form.get('action')
            if action:
                if not action.startswith('http'):
                    action = urljoin(self.host, action)
            else:
                action = login_url
            
            self.log(f"Enviando login a: {action}")
            
            response = self.session.post(action, data=form_data)
            response.raise_for_status()
            
            # 5. Verificar login exitoso
            if 'submissions' in response.url or 'dashboard' in response.url:
                self.log("✅ Login exitoso")
                self.extract_csrf_token(response.text)
                return True
            else:
                self.log("❌ Login fallido - Redirección no esperada")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en login: {str(e)}")
            return False
    
    def extract_csrf_token(self, html_content):
        """Extraer token CSRF del HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Buscar token en meta tags
        meta_token = soup.find('meta', {'name': 'csrf-token'})
        if meta_token and meta_token.get('content'):
            self.csrf_token = meta_token['content']
            self.session.headers['X-CSRF-Token'] = self.csrf_token
            self.log(f"Token CSRF encontrado: {self.csrf_token[:20]}...")
        
        # Buscar token en input hidden
        if not self.csrf_token:
            csrf_input = soup.find('input', {'name': 'csrfToken'})
            if csrf_input and csrf_input.get('value'):
                self.csrf_token = csrf_input['value']
                self.log(f"Token CSRF (input): {self.csrf_token[:20]}...")
    
    def navigate_to_submissions(self):
        """Navegar a la sección de envíos"""
        try:
            submissions_url = f"{self.host}/submissions"
            self.log(f"Navegando a envíos: {submissions_url}")
            
            response = self.session.get(submissions_url)
            response.raise_for_status()
            
            # Extraer submission IDs de la página
            soup = BeautifulSoup(response.text, 'html.parser')
            submission_elements = soup.find_all('div', class_=re.compile(r'.*submission.*id.*', re.I))
            
            submission_ids = []
            for elem in submission_elements:
                text = elem.get_text(strip=True)
                if text.isdigit():
                    submission_ids.append(text)
            
            self.log(f"Encontrados {len(submission_ids)} envíos")
            return submission_ids
            
        except Exception as e:
            self.log(f"❌ Error navegando a envíos: {str(e)}")
            return []
    
    def upload_to_submission(self, submission_id, file_path, file_name=None):
        """Subir archivo a un envío específico basado en la estructura HTML"""
        try:
            # URL para subir archivos
            upload_url = f"{self.host}/submission/wizard/2"
            
            self.log(f"Preparando subida a envío {submission_id}")
            
            # 1. Obtener página de subida
            params = {'submissionId': submission_id}
            response = self.session.get(upload_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 2. Buscar formulario de subida
            upload_form = soup.find('form', {'enctype': 'multipart/form-data'})
            if not upload_form:
                # Buscar botón "Añadir archivo"
                add_file_btn = soup.find('button', class_='pkpButton', string=re.compile(r'Añadir archivo', re.I))
                if add_file_btn:
                    self.log("Botón 'Añadir archivo' encontrado")
                else:
                    self.log("No se encontró formulario de subida")
                    return False
            
            # 3. Leer archivo
            if not file_name:
                file_name = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 4. Preparar datos del formulario
            files = {
                'submissionFile': (file_name, file_content, self.guess_mime_type(file_name))
            }
            
            # 5. Enviar archivo
            self.log(f"Subiendo {file_name} ({len(file_content):,} bytes)")
            
            # Intentar encontrar la URL de subida
            upload_action = None
            if upload_form and upload_form.get('action'):
                upload_action = upload_form['action']
                if not upload_action.startswith('http'):
                    upload_action = urljoin(self.host, upload_action)
            
            if not upload_action:
                upload_action = upload_url
            
            response = self.session.post(
                upload_action,
                params=params,
                files=files,
                data={'submissionId': submission_id}
            )
            
            response.raise_for_status()
            
            # 6. Verificar subida exitosa
            if response.status_code == 200:
                self.log(f"✅ Archivo subido exitosamente: {file_name}")
                
                # Guardar enlace (URL relativa del archivo)
                file_url = f"{self.host}/submission/{submission_id}#files"
                self.uploaded_urls.append({
                    'file': file_name,
                    'url': file_url,
                    'submission_id': submission_id,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
                return True
            else:
                self.log(f"❌ Error en subida: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error subiendo archivo: {str(e)}")
            return False
    
    def download_from_url(self, url, save_path):
        """Descargar archivo desde URL"""
        try:
            self.log(f"Descargando: {url}")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(save_path)
            self.log(f"✅ Descargado: {os.path.basename(save_path)} ({file_size:,} bytes)")
            return True
            
        except Exception as e:
            self.log(f"❌ Error descargando {url}: {str(e)}")
            return False
    
    def create_zip_chunk(self, files, chunk_name, max_size_mb=10):
        """Crear archivo ZIP con tamaño máximo"""
        max_size = max_size_mb * 1024 * 1024
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            total_size = 0
            
            for file_path in files:
                file_size = os.path.getsize(file_path)
                
                if total_size + file_size > max_size:
                    break
                
                zipf.write(file_path, os.path.basename(file_path))
                total_size += file_size
        
        if zip_buffer.tell() > 0:
            zip_path = f"temp/{chunk_name}.zip"
            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            
            self.log(f"📦 ZIP creado: {chunk_name}.zip ({zip_buffer.tell():,} bytes)")
            return zip_path
        
        return None
    
    def upload_from_links(self, links, submission_id=None):
        """Descargar y subir archivos desde enlaces directos"""
        try:
            # 1. Login si es necesario
            if not self.csrf_token:
                if not self.login():
                    return False
            
            # 2. Usar submission_id proporcionado o buscar
            if not submission_id:
                submission_ids = self.navigate_to_submissions()
                if submission_ids:
                    submission_id = submission_ids[0]
                    self.log(f"Usando envío ID: {submission_id}")
                else:
                    self.log("❌ No se encontraron envíos")
                    return False
            
            # 3. Descargar archivos
            downloaded_files = []
            temp_dir = "temp/downloads"
            os.makedirs(temp_dir, exist_ok=True)
            
            for i, url in enumerate(links, 1):
                if not url.strip():
                    continue
                
                file_name = f"file_{i}{self.get_file_extension(url)}"
                file_path = os.path.join(temp_dir, file_name)
                
                if self.download_from_url(url, file_path):
                    downloaded_files.append(file_path)
            
            if not downloaded_files:
                self.log("❌ No se descargaron archivos")
                return False
            
            self.log(f"✅ Descargados {len(downloaded_files)} archivos")
            
            # 4. Crear chunks ZIP de máximo 10MB
            zip_chunks = []
            current_chunk = []
            current_size = 0
            
            for file_path in downloaded_files:
                file_size = os.path.getsize(file_path)
                
                if file_size > 10 * 1024 * 1024:
                    # Archivo individual grande
                    self.log(f"⚠️ Archivo grande ({file_size:,} bytes), se subirá individualmente")
                    zip_chunks.append([file_path])
                    continue
                
                if current_size + file_size > 10 * 1024 * 1024 and current_chunk:
                    # Crear chunk
                    chunk_name = f"chunk_{len(zip_chunks)+1}"
                    zip_path = self.create_zip_chunk(current_chunk, chunk_name)
                    if zip_path:
                        zip_chunks.append([zip_path])
                    current_chunk = [file_path]
                    current_size = file_size
                else:
                    current_chunk.append(file_path)
                    current_size += file_size
            
            # Último chunk
            if current_chunk:
                chunk_name = f"chunk_{len(zip_chunks)+1}"
                zip_path = self.create_zip_chunk(current_chunk, chunk_name)
                if zip_path:
                    zip_chunks.append([zip_path])
            
            # 5. Subir archivos
            successful_uploads = 0
            for chunk in zip_chunks:
                for file_path in chunk:
                    if self.upload_to_submission(submission_id, file_path):
                        successful_uploads += 1
            
            # 6. Generar reporte
            if successful_uploads > 0:
                self.generate_report(submission_id)
            
            self.log(f"✅ Proceso completado: {successful_uploads}/{len(zip_chunks)} archivos subidos")
            return successful_uploads > 0
            
        except Exception as e:
            self.log(f"❌ Error en proceso completo: {str(e)}")
            return False
        finally:
            # Limpieza
            self.cleanup_temp_files()
    
    def get_file_extension(self, url):
        """Obtener extensión de archivo desde URL"""
        # Extraer nombre de archivo
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # Buscar extensión
        if '.' in filename:
            ext = filename[filename.rfind('.'):]
            if len(ext) <= 6:  # Extensiones típicas son cortas
                return ext
        
        # Extensiones comunes
        common_extensions = {
            'pdf': '.pdf',
            'doc': '.doc',
            'docx': '.docx',
            'jpg': '.jpg',
            'jpeg': '.jpeg',
            'png': '.png',
            'zip': '.zip',
            'rar': '.rar',
            'txt': '.txt'
        }
        
        for key, ext in common_extensions.items():
            if key in url.lower():
                return ext
        
        return '.bin'
    
    def guess_mime_type(self, filename):
        """Adivinar tipo MIME"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def generate_report(self, submission_id):
        """Generar archivo de reporte TXT"""
        try:
            report_dir = "reports"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_file = f"{report_dir}/upload_report_{timestamp}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("REPORTE DE SUBIDA - BOT OJS UPLOADER\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Revista: {self.host}\n")
                f.write(f"Usuario: {self.username}\n")
                f.write(f"Envío ID: {submission_id}\n")
                f.write(f"Total archivos subidos: {len(self.uploaded_urls)}\n")
                f.write("\n" + "=" * 60 + "\n\n")
                
                f.write("ARCHIVOS SUBIDOS:\n")
                f.write("-" * 60 + "\n")
                
                for i, upload in enumerate(self.uploaded_urls, 1):
                    f.write(f"\n{i}. {upload['file']}\n")
                    f.write(f"   URL: {upload['url']}\n")
                    f.write(f"   Hora: {upload['timestamp']}\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write("FIN DEL REPORTE\n")
                f.write("=" * 60 + "\n")
            
            self.log(f"📄 Reporte generado: {report_file}")
            return report_file
            
        except Exception as e:
            self.log(f"⚠️ Error generando reporte: {str(e)}")
            return None
    
    def cleanup_temp_files(self):
        """Limpiar archivos temporales"""
        try:
            import shutil
            if os.path.exists('temp'):
                shutil.rmtree('temp')
            os.makedirs('temp', exist_ok=True)
            self.log("🧹 Archivos temporales limpiados")
        except Exception as e:
            self.log(f"⚠️ Error limpiando archivos temporales: {str(e)}")
    
    def log(self, message):
        """Agregar mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs.append(log_message)
        logger.info(log_message)
        print(log_message)
    
    def get_logs(self):
        """Obtener todos los logs"""
        return self.logs[-100:]  # Últimos 100 logs