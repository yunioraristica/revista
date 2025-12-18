# 🤖 Bot OJS Uploader

Bot de subida automática para revistas Open Journal Systems (OJS). Sube archivos automáticamente a cualquier revista OJS como la Revista 16 de Abril, comprimiendo en ZIP de 10MB y generando reportes completos.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![Render](https://img.shields.io/badge/Deploy-Render-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Características Principales

### 🔐 **Gestión de Credenciales Segura**
- **Usuario/Contraseña dentro del bot** - No en el código
- **Panel de administración** protegido con login
- **Token de API** para integraciones
- Soporte para múltiples revistas simultáneas

### 📤 **Subida Automática Inteligente**
- **Descarga desde enlaces directos** (PDF, DOCX, imágenes, etc.)
- **Compresión automática** en chunks de 10MB
- **Subida a OJS** usando la estructura HTML real
- **Soporte para cualquier revista OJS** (16 de Abril, UO Ediciones, etc.)

### 📊 **Gestión Completa**
- **ID de envío configurable** (ej: 2415 para Revista 16 de Abril)
- **Reportes TXT** con todos los enlaces subidos
- **Logs detallados** de todas las operaciones
- **Interfaz web** responsive y moderna

### ⚙️ **Configuración Flexible**
- **Host personalizable** - Cualquier revista OJS
- **Comandos por terminal** integrados
- **API RESTful** para automatización
- **Variables de entorno** para producción

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/ojs-uploader-bot.git
cd ojs-uploader-bot
