mkdir server
python3 -m http.server -d server &
python3 main.py

#!/bin/bash
echo "🚀 Iniciando Bot OJS Uploader en Render..."
echo "=========================================="

# Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p templates static/css config
mkdir -p server

# Verificar que existen los templates básicos
if [ ! -f "templates/index.html" ]; then
    echo "📄 Creando index.html básico..."
    cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Bot OJS Uploader</title>
<style>
body{font-family:Arial;background:#f0f0f0;padding:50px;text-align:center}
.box{background:white;padding:40px;border-radius:10px;max-width:600px;margin:0 auto}
.btn{display:inline-block;padding:12px 30px;background:#3498db;color:white;text-decoration:none;border-radius:6px;margin:10px}
</style>
</head>
<body>
<div class="box">
<h1>🤖 Bot OJS Uploader</h1>
<p>✅ Desplegado en Render</p>
<p>📍 URL: https://revista-amyn.onrender.com</p>
<a href="/admin/login" class="btn">🔧 Panel Admin</a>
<a href="/telegram/setup" class="btn">🤖 Config Telegram</a>
<p style="margin-top:30px">Usuario: admin | Contraseña: admin123</p>
</div>
</body>
</html>
EOF
fi

if [ ! -f "templates/login.html" ]; then
    echo "📄 Creando login.html..."
    cat > templates/login.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Login</title>
<style>
body{font-family:Arial;background:#f0f0f0;padding:50px}
.login-box{background:white;padding:40px;border-radius:10px;width:100%;max-width:400px;margin:0 auto}
input{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd}
button{width:100%;padding:12px;background:#2c3e50;color:white;border:none}
</style>
</head>
<body>
<div class="login-box">
<h2>🔐 Login Admin</h2>
<form method="POST">
<input type="text" name="username" placeholder="Usuario" required>
<input type="password" name="password" placeholder="Contraseña" required>
<button type="submit">Entrar</button>
</form>
<p style="color:#666">Usuario: admin | Contraseña: admin123</p>
</div>
</body>
</html>
EOF
fi

# Crear archivo de configuración si no existe
if [ ! -f "config/admin.json" ]; then
    echo "⚙️ Creando configuración inicial..."
    python3 -c "
import json, uuid
from datetime import datetime
config = {
    'admin_username': 'admin',
    'admin_password': 'admin123',
    'bot_token': str(uuid.uuid4()),
    'created_at': datetime.now().isoformat()
}
with open('config/admin.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Configuración admin creada')
    "
fi

# Iniciar servidor HTTP estático en segundo plano (opcional)
echo "🌐 Iniciando servidor HTTP estático en puerto 8080..."
python3 -m http.server 8080 -d server > /dev/null 2>&1 &
HTTP_PID=$!
echo "✅ Servidor HTTP iniciado (PID: $HTTP_PID) en: http://localhost:8080"

# Iniciar la aplicación Flask principal
echo "🚀 Iniciando aplicación Flask en puerto \$PORT..."
python3 app.py &
FLASK_PID=$!
echo "✅ Flask iniciado (PID: $FLASK_PID)"

# Iniciar bot de Telegram si existe el archivo
if [ -f "telegram_bot.py" ]; then
    echo "🤖 Iniciando bot de Telegram..."
    python3 telegram_bot.py &
    TELEGRAM_PID=$!
    echo "✅ Telegram bot iniciado (PID: $TELEGRAM_PID)"
fi

# Mostrar información
echo ""
echo "=========================================="
echo "✅ TODOS LOS SERVICIOS INICIADOS"
echo "🌐 Flask App: https://revista-amyn.onrender.com"
echo "📊 Estado API: https://revista-amyn.onrender.com/api/status"
echo "🔧 Admin: https://revista-amyn.onrender.com/admin/login"
echo "🤖 Config Telegram: https://revista-amyn.onrender.com/telegram/setup"
echo "=========================================="

# Mantener el script corriendo
echo ""
echo "📊 Monitoreando procesos..."
echo "Presiona Ctrl+C para detener todos los servicios"
echo ""

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo todos los servicios..."
    kill $HTTP_PID 2>/dev/null
    kill $FLASK_PID 2>/dev/null
    kill $TELEGRAM_PID 2>/dev/null
    echo "✅ Servicios detenidos"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT SIGTERM

# Mantener script activo monitoreando
while true; do
    sleep 60
    echo "🔄 Servicios activos: $(date)"
done
